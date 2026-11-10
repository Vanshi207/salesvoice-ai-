from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CallOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    lead_id: str
    owner_id: str
    source: str
    status: str
    filename: str
    size_bytes: int
    duration_s: float | None
    languages: str | None
    rep_speaker: int
    error: str | None
    created_at: datetime


class CallPage(BaseModel):
    items: list[CallOut]
    total: int
    limit: int
    offset: int


class SegmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    speaker: int
    start_s: float
    end_s: float
    text: str


class AnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    summary: str
    sentiment: str
    intent: str
    lead_score: int
    result: dict
    metrics: dict
    llm_model: str


class CallDetail(CallOut):
    segments: list[SegmentOut]
    analysis: AnalysisOut | None


class CallUpdate(BaseModel):
    rep_speaker: int = Field(ge=0, le=5)
