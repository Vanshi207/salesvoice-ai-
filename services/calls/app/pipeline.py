import logging

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload
from sqlalchemy.pool import NullPool

from salesvoice_common import events

from app import llm, storage, stt
from app.config import settings
from app.metrics import compute_metrics
from app.models import Analysis, Call, Segment

log = logging.getLogger("pipeline")


def mmss(seconds: float) -> str:
    return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"


def format_transcript(segments: list[Segment], rep_speaker: int) -> str:
    return "\n".join(f"[{mmss(seg.start_s)}] {'REP' if seg.speaker == rep_speaker else 'CUSTOMER'}: {seg.text}"
                     for seg in segments)


def open_db():
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def set_status(s: AsyncSession, call: Call, status: str) -> None:
    call.status = status
    await s.commit()
    log.info(f"call {call.id} -> {status}")


async def run(s: AsyncSession, redis: Redis, call_id: str) -> None:
    call = await s.scalar(select(Call).where(Call.id == call_id)
                          .options(selectinload(Call.segments), selectinload(Call.analysis)))
    if call is None:
        log.warning(f"call {call_id} not found, skipping")
        return
    if call.status == "done":
        return

    # 1. Speech-to-text
    await set_status(s, call, "transcribing")
    transcript = await stt.transcribe(storage.read(call.audio_path), call.filename)
    if not transcript.utterances:
        raise ValueError("No speech detected in the recording")
    call.segments = [Segment(position=i, speaker=u.speaker, start_s=u.start, end_s=u.end, text=u.text)
                     for i, u in enumerate(transcript.utterances)]
    call.duration_s = transcript.duration
    call.languages = ",".join(transcript.languages) or None
    call.rep_speaker = call.segments[0].speaker

    # 2. Metrics (plain Python) + 3. LLM analysis
    await set_status(s, call, "analyzing")
    metrics = compute_metrics(call.segments, call.rep_speaker, transcript.duration)
    result = await llm.analyze(format_transcript(call.segments, call.rep_speaker), metrics)

    # 4. Save (update if it exists, so a retry never duplicates)
    fields = dict(summary=result.summary, sentiment=result.sentiment, intent=result.intent,
                  lead_score=result.lead_score, result=result.model_dump(), metrics=metrics,
                  llm_model=llm.model_name())
    if call.analysis:
        for k, v in fields.items():
            setattr(call.analysis, k, v)
    else:
        call.analysis = Analysis(**fields)
    call.status, call.error = "done", None
    await s.commit()
    log.info(f"call {call.id} -> done (score {result.lead_score})")

    # 5. Tell the rest of the system
    await events.publish(redis, settings.events_stream, "call.analyzed", {
        "call_id": call.id, "lead_id": call.lead_id, "owner_id": call.owner_id,
        "lead_score": result.lead_score, "intent": result.intent, "sentiment": result.sentiment,
        "follow_up_requested": result.follow_up_requested,
    })


async def mark_failed(call_id: str, error: str) -> None:
    engine, Session = open_db()
    try:
        async with Session() as s:
            call = await s.get(Call, call_id)
            if call:
                call.status, call.error = "failed", error[:1000]
                await s.commit()
    finally:
        await engine.dispose()
    log.error(f"call {call_id} -> failed: {error}")


async def process_call(call_id: str) -> None:
    engine, Session = open_db()
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        async with Session() as s:
            await run(s, redis, call_id)
    finally:
        await redis.aclose()
        await engine.dispose()
