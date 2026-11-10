import json
from typing import Literal

import httpx
from pydantic import BaseModel, ValidationError, field_validator

from app.config import settings
from app.errors import TransientError


class Objection(BaseModel):
    category: Literal["price", "timing", "trust", "need", "competitor", "authority", "other"]
    quote: str
    handled: bool


class CallAnalysis(BaseModel):
    summary: str
    sentiment: Literal["positive", "neutral", "negative", "mixed"]
    intent: Literal["high", "medium", "low", "none"]
    lead_score: int
    score_reasons: list[str]
    objections: list[Objection]
    next_steps: list[str]
    follow_up_requested: bool

    @field_validator("lead_score")
    @classmethod
    def clamp(cls, v: int) -> int:
        return max(0, min(100, v))


SYSTEM_PROMPT = """You are an expert B2B sales coach analysing a phone call between a sales REP and a CUSTOMER.
The call may be in English, Hindi or Hinglish (mixed). Write summary, reasons and next steps in English.
Keep objection quotes in the customer's ORIGINAL words and language.

Lead score rubric (0-100):
- Start at 50.
- +10 each: clear need/pain, budget mentioned or not an issue, decision timeline given, is the decision maker, asked for demo/trial/follow-up.
- -15 each: says not interested, already bought from a competitor, asks not to be called again.
- -5 for each objection the rep did not handle.
Give 2-4 short score_reasons that explain the number.
Only use facts from the transcript. If something was not discussed, do not invent it."""


def build_prompt(transcript: str, metrics: dict) -> str:
    return f"Call metrics: {json.dumps(metrics)}\n\nTranscript:\n{transcript}"


async def _gemini(prompt: str) -> str:
    from google import genai
    from google.genai import errors, types

    client = genai.Client(api_key=settings.gemini_api_key)
    try:
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=CallAnalysis,
                temperature=0.2,
            ),
        )
    except errors.APIError as e:
        if e.code == 429 or (e.code or 0) >= 500:
            raise TransientError(f"Gemini {e.code}") from e
        raise
    except httpx.HTTPError as e:
        raise TransientError(f"Gemini unreachable: {e!r}") from e
    return response.text


async def _groq(prompt: str) -> str:
    schema = json.dumps(CallAnalysis.model_json_schema())
    body = {
        "model": settings.groq_model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nReply ONLY with JSON matching this schema:\n{schema}"},
            {"role": "user", "content": prompt},
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post("https://api.groq.com/openai/v1/chat/completions", json=body,
                                  headers={"Authorization": f"Bearer {settings.groq_api_key}"})
    except httpx.HTTPError as e:
        raise TransientError(f"Groq unreachable: {e!r}") from e
    if r.status_code == 429 or r.status_code >= 500:
        raise TransientError(f"Groq {r.status_code}")
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


PROVIDERS = {"gemini": (_gemini, lambda: settings.gemini_model),
             "groq": (_groq, lambda: settings.groq_model)}


def model_name() -> str:
    return f"{settings.llm_provider}:{PROVIDERS[settings.llm_provider][1]()}"


async def analyze(transcript: str, metrics: dict) -> CallAnalysis:
    call_llm = PROVIDERS[settings.llm_provider][0]
    prompt = build_prompt(transcript, metrics)
    last_error = None
    for _ in range(2):
        raw = await call_llm(prompt)
        try:
            return CallAnalysis.model_validate_json(raw)
        except ValidationError as e:
            last_error = e
    raise ValueError(f"LLM returned invalid JSON twice: {last_error}")
