import asyncio
import socket
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from redis.asyncio import Redis
from sqlalchemy import text

from salesvoice_common.events import consume
from salesvoice_common.logging import request_id_var, setup_logging

from app.config import settings
from app.db import db
from app.events_consumer import handle
from app.routes import router

log = setup_logging(settings.service_name, settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("leads service starting")
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    consumer = asyncio.create_task(
        consume(redis, "events", group="leads", consumer=socket.gethostname(), handler=handle))
    consumer.add_done_callback(
        lambda t: t.cancelled() or log.error(f"event consumer stopped: {t.exception()!r}"))
    yield
    consumer.cancel()
    with suppress(asyncio.CancelledError):
        await consumer
    await redis.aclose()
    await db.dispose()


app = FastAPI(title="SalesVoice leads service", lifespan=lifespan)


@app.middleware("http")
async def request_id(request: Request, call_next):
    request_id_var.set(request.headers.get("x-request-id", "-"))
    return await call_next(request)


app.include_router(router)


@app.get("/health")
async def health():
    async with db.engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok", "service": "leads"}
