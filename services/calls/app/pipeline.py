import logging

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload
from sqlalchemy.pool import NullPool

from salesvoice_common import events

from app import storage, stt
from app.config import settings
from app.metrics import compute_metrics
from app.models import Call, Segment

log = logging.getLogger("pipeline")


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

    # 2. Metrics (plain Python)
    metrics = compute_metrics(call.segments, call.rep_speaker, transcript.duration)
    log.info(f"call {call.id} metrics: {metrics}")
    await set_status(s, call, "done")
    # 3D: LLM analysis goes here, then events.publish


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
