from dataclasses import dataclass

import httpx

from app.config import settings
from app.errors import TransientError
from app.storage import ALLOWED, extension

DEEPGRAM_URL = "https://api.deepgram.com/v1/listen"


@dataclass
class Utterance:
    speaker: int
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    duration: float
    languages: list[str]
    utterances: list[Utterance]


async def transcribe(audio: bytes, filename: str) -> Transcript:
    params = {
        "model": settings.deepgram_model,
        "language": settings.deepgram_language,
        "diarize": "true",
        "utterances": "true",
        "smart_format": "true",
    }
    headers = {"Authorization": f"Token {settings.deepgram_api_key}",
               "Content-Type": ALLOWED.get(extension(filename), "application/octet-stream")}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(300, connect=10)) as client:
            r = await client.post(DEEPGRAM_URL, params=params, headers=headers, content=audio)
    except httpx.HTTPError as e:
        raise TransientError(f"Deepgram unreachable: {e!r}") from e

    if r.status_code == 429 or r.status_code >= 500:
        raise TransientError(f"Deepgram {r.status_code}")
    if r.status_code != 200:
        raise ValueError(f"Deepgram {r.status_code}: {r.text[:300]}")
    return parse(r.json())


def parse(body: dict) -> Transcript:
    alt = body["results"]["channels"][0]["alternatives"][0]
    utterances = [Utterance(speaker=u.get("speaker", 0), start=u["start"], end=u["end"],
                            text=u["transcript"].strip())
                  for u in body["results"].get("utterances", []) if u["transcript"].strip()]
    return Transcript(duration=body["metadata"]["duration"],
                      languages=alt.get("languages", []),
                      utterances=utterances)
