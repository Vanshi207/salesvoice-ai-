from datetime import datetime
from typing import Literal

import phonenumbers
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.config import settings

Stage = Literal["new", "contacted", "hot", "follow_up", "won", "lost"]
Language = Literal["en", "hi", "hi-en"]


def normalize_phone(raw: str) -> str:
    try:
        num = phonenumbers.parse(raw, settings.default_phone_region)
    except phonenumbers.NumberParseException:
        raise ValueError("not a phone number")
    if not phonenumbers.is_valid_number(num):
        raise ValueError("invalid phone number")
    return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)


class LeadCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    phone: str
    email: EmailStr | None = None
    company: str | None = Field(default=None, max_length=120)
    language: Language = "hi-en"
    consent: bool = False
    notes: str | None = None

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str) -> str:
        return normalize_phone(v)


class LeadUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = None
    email: EmailStr | None = None
    company: str | None = None
    language: Language | None = None
    stage: Stage | None = None
    consent: bool | None = None
    dnd: bool | None = None
    notes: str | None = None

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str | None) -> str | None:
        return normalize_phone(v) if v is not None else v


class LeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    name: str
    phone: str
    email: str | None
    company: str | None
    language: str
    stage: str
    score: int | None
    consent: bool
    consent_at: datetime | None
    dnd: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class LeadPage(BaseModel):
    items: list[LeadOut]
    total: int
    limit: int
    offset: int


class FollowUpCreate(BaseModel):
    scheduled_at: datetime
    note: str | None = None


class FollowUpOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    lead_id: str
    scheduled_at: datetime
    note: str | None
    status: str
    created_by: str
    created_at: datetime
