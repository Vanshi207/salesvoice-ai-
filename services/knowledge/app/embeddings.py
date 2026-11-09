import asyncio

from fastembed import TextEmbedding

from app.config import settings


class Embedder:
    def __init__(self) -> None:
        self.model: TextEmbedding | None = None

    def load(self) -> None:
        self.model = TextEmbedding(settings.embedding_model)

    def _embed(self, texts: list[str]) -> list[list[float]]:
        assert self.model is not None, "call load() first"
        return [vec.tolist() for vec in self.model.embed(texts)]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(self._embed, texts)


embedder = Embedder()
