FROM python:3.11-slim AS build
WORKDIR /build
COPY packages/common /build/common
COPY services/knowledge/requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt ./common

FROM python:3.11-slim
RUN useradd --create-home app
WORKDIR /app
COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels
ENV FASTEMBED_CACHE_PATH=/models
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')" \
    && chown -R app /models
COPY services/knowledge/ .
USER app
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
