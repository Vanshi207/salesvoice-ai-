import re


def clean(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_sentences(paragraph: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?।])\s+", paragraph) if s.strip()]


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    pieces: list[str] = []
    for para in clean(text).split("\n\n"):
        pieces.extend(split_sentences(para) if len(para) > size else [para])

    chunks: list[str] = []
    current = ""
    for piece in pieces:
        if len(piece) > size:
            parts = [piece[i:i + size] for i in range(0, len(piece), size - overlap)]
        else:
            parts = [piece]
        for part in parts:
            if current and len(current) + 1 + len(part) > size:
                chunks.append(current)
                current = current[-overlap:] + " " + part
            else:
                current = f"{current} {part}".strip()
    if current:
        chunks.append(current)
    return chunks
