from salesvoice_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "knowledge"
    db_schema: str = "knowledge"

    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dim: int = 384
    chunk_size: int = 800
    chunk_overlap: int = 150
    max_upload_mb: int = 10


settings = Settings()
