FROM python:3.11-slim AS build
WORKDIR /build
COPY packages/common /build/common
COPY services/calls/requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt ./common

FROM python:3.11-slim
RUN useradd --create-home app && mkdir -p /data/audio && chown app /data/audio
WORKDIR /app
COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels
COPY services/calls/ .
USER app
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
