import uuid
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from salesvoice_common.logging import request_id_var, setup_logging
from salesvoice_common.security import InvalidToken, decode_token

from app import ratelimit
from app.config import PUBLIC_ROUTES, settings

log = setup_logging(settings.service_name, settings.log_level)

HOP_BY_HOP = {"connection", "keep-alive", "transfer-encoding", "te", "trailer", "upgrade",
              "proxy-authorization", "proxy-authenticate", "host", "content-length"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0))
    app.state.redis = Redis.from_url(settings.redis_url)
    log.info(f"gateway routing to: {settings.routes()}")
    yield
    await app.state.http.aclose()
    await app.state.redis.aclose()


app = FastAPI(title="SalesVoice API gateway", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
                   expose_headers=["X-Request-ID"])


def error(status: int, detail: str) -> JSONResponse:
    return JSONResponse({"detail": detail}, status_code=status,
                        headers={"X-Request-ID": request_id_var.get()})


@app.get("/health")
async def health():
    results = {}
    for name, url in settings.routes().items():
        try:
            r = await app.state.http.get(f"{url}/health", timeout=3)
            results[name] = "ok" if r.status_code == 200 else f"error {r.status_code}"
        except httpx.HTTPError:
            results[name] = "unreachable"
    overall = "ok" if all(v == "ok" for v in results.values()) else "degraded"
    return {"status": overall, "services": results}


@app.api_route("/api/{service}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(service: str, path: str, request: Request) -> Response:
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    request_id_var.set(rid)

    target = settings.routes().get(service)
    if not target:
        return error(404, f"Unknown service '{service}'")

    user = None
    if (service, path.rstrip("/")) not in PUBLIC_ROUTES:
        auth = request.headers.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            return error(401, "Missing bearer token")
        try:
            user = decode_token(auth[7:], settings.jwt_secret, settings.jwt_algorithm)
        except InvalidToken:
            return error(401, "Invalid or expired token")

    client_ip = request.client.host if request.client else "unknown"
    who = f"user:{user.sub}" if user else f"ip:{client_ip}"
    limit = settings.rate_limit_per_minute
    if (service, path) == ("auth", "login"):
        who, limit = f"login:{client_ip}", settings.login_rate_limit_per_minute
    if not await ratelimit.allow(app.state.redis, who, limit):
        return error(429, "Too many requests, slow down")

    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in HOP_BY_HOP and not k.lower().startswith("x-user-")}
    headers["X-Request-ID"] = rid
    if user:
        headers["X-User-Id"] = user.sub
        headers["X-User-Role"] = user.role

    try:
        upstream = await app.state.http.request(
            request.method, f"{target}/{path}", params=request.query_params,
            content=await request.body(), headers=headers)
    except httpx.HTTPError as e:
        log.error(f"{service} unreachable: {e!r}")
        return error(503, f"Service '{service}' is unavailable")

    log.info(f"{request.method} /api/{service}/{path} -> {upstream.status_code}")
    out_headers = {k: v for k, v in upstream.headers.items() if k.lower() not in HOP_BY_HOP}
    out_headers["X-Request-ID"] = rid
    return Response(content=upstream.content, status_code=upstream.status_code, headers=out_headers)
