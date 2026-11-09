from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    filename: str
    status: str
    chunk_count: int
    error: str | None
    uploaded_by: str
    created_at: datetime


class SearchIn(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    min_score: float = Field(default=0.3, ge=0, le=1)


class SearchHit(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    text: str
    score: float


class SearchOut(BaseModel):
    query: str
    hits: list[SearchHit]
