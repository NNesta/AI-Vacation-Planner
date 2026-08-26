
from __future__ import annotations

import re
from typing import Iterable

from app.config import CHUNK_OVERLAP_CHARS, CHUNK_SIZE_CHARS


def clean_text(text: str) -> str:
    """Collapse excess whitespace, e.g. left over from PDF text extraction."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_into_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def chunk_paragraphs(
    paragraphs: Iterable[str],
    chunk_size: int = CHUNK_SIZE_CHARS,
    overlap: int = CHUNK_OVERLAP_CHARS,
) -> list[str]:
    """
    Greedily pack paragraphs into chunks up to `chunk_size` characters.
    A paragraph longer than chunk_size on its own is split with a sliding
    window and overlap so no content is lost.
    """
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len(para) > chunk_size:
            if current:
                chunks.append(current.strip())
                current = ""
            start = 0
            while start < len(para):
                end = start + chunk_size
                chunks.append(para[start:end].strip())
                start = end - overlap
            continue

        candidate = f"{current}\n\n{para}".strip() if current else para
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current.strip())
            current = para

    if current:
        chunks.append(current.strip())

    return chunks


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE_CHARS,
    overlap: int = CHUNK_OVERLAP_CHARS,
) -> list[str]:
    """Convenience wrapper: clean -> split into paragraphs -> pack into chunks."""
    cleaned = clean_text(text)
    paragraphs = split_into_paragraphs(cleaned)
    return chunk_paragraphs(paragraphs, chunk_size=chunk_size, overlap=overlap)
