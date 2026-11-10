from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from sqlalchemy import text

from salesvoice_common.logging import request_id_var, setup_logging

from app.config import settings
from app.db import db
from app.routes import router

log = setup_logging(settings.service_name, settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("calls service starting")
    yield
    await db.dispose()


app = FastAPI(title="SalesVoice calls service", lifespan=lifespan)


@app.middleware("http")
async def request_id(request: Request, call_next):
    request_id_var.set(request.headers.get("x-request-id", "-"))
    return await call_next(request)


app.include_router(router)


@app.get("/health")
async def health():
    async with db.engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok", "service": "calls"}
