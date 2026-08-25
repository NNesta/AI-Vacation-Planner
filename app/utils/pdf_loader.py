"""
Reads travel PDFs from disk and splits them into overlapping text chunks
ready for embedding. This is the "chunking" stage of the RAG pipeline.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader

from app.config import CHUNK_OVERLAP_CHARS, CHUNK_SIZE_CHARS, PDF_DIR


@dataclass
class Chunk:
    id: str
    text: str
    metadata: dict = field(default_factory=dict)


def _extract_pdf_text(pdf_path: Path) -> str:
    """Extract raw text from every page of a PDF and join it."""
    reader = PdfReader(str(pdf_path))
    pages = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        pages.append(page_text)
    return "\n\n".join(pages)


def _clean_text(text: str) -> str:
    # Collapse excess whitespace left over from PDF text extraction.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_into_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def _chunk_paragraphs(
    paragraphs: Iterable[str],
    chunk_size: int = CHUNK_SIZE_CHARS,
    overlap: int = CHUNK_OVERLAP_CHARS,
) -> list[str]:
    """
    Greedily pack paragraphs into chunks up to `chunk_size` characters,
    so chunk boundaries fall on paragraph breaks rather than mid-sentence.
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


def _destination_from_filename(pdf_path: Path) -> str:
    return pdf_path.stem.replace("_", " ").title()


def load_and_chunk_pdfs(pdf_dir: Path = PDF_DIR) -> list[Chunk]:
    """Load every PDF in pdf_dir, chunk it, and attach metadata to each chunk."""
    pdf_dir = Path(pdf_dir)
    chunks: list[Chunk] = []

    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        raw_text = _extract_pdf_text(pdf_path)
        cleaned = _clean_text(raw_text)
        paragraphs = _split_into_paragraphs(cleaned)
        text_chunks = _chunk_paragraphs(paragraphs)

        destination = _destination_from_filename(pdf_path)
        for i, chunk_text in enumerate(text_chunks):
            chunks.append(
                Chunk(
                    id=f"{pdf_path.stem}::chunk-{i}",
                    text=chunk_text,
                    metadata={
                        "source": pdf_path.name,
                        "destination": destination,
                        "chunk_index": i,
                    },
                )
            )

    return chunks
