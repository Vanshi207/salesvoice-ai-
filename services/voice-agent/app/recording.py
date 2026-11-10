import io
import wave

import httpx
from loguru import logger

from app.config import settings
from app.context import CallContext


def to_wav(pcm: bytes, sample_rate: int, channels: int) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm)
    return buf.getvalue()


async def upload_recording(ctx: CallContext, pcm: bytes, sample_rate: int, channels: int) -> None:
    """Send the finished call to the calls service, which analyses it (Build 3 pipeline)."""
    if not ctx.lead_id or not pcm:
        logger.info("no lead or no audio, recording not uploaded")
        return
    files = {"file": ("agent-call.wav", to_wav(pcm, sample_rate, channels), "audio/wav")}
    data = {"lead_id": ctx.lead_id, "source": "agent"}
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{settings.calls_url}/calls", headers=ctx.headers(), files=files, data=data)
        logger.info(f"recording uploaded: {r.status_code} {r.text[:120]}")
    except httpx.HTTPError as e:
        logger.error(f"recording upload failed: {e!r}")
