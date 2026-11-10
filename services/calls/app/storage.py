from pathlib import Path

from app.config import settings

ALLOWED = {".mp3": "audio/mpeg", ".wav": "audio/wav", ".m4a": "audio/mp4", ".ogg": "audio/ogg"}


def extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def save(call_id: str, filename: str, data: bytes) -> str:
    folder = Path(settings.audio_dir)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{call_id}{extension(filename)}"
    path.write_bytes(data)
    return str(path)


def read(path: str) -> bytes:
    return Path(path).read_bytes()


def delete(path: str) -> None:
    Path(path).unlink(missing_ok=True)
