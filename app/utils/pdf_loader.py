
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader

from app.chunking import chunk_text
from app.config import PDF_DIR


@dataclass
class Chunk:
    id: str
    text: str
    metadata: dict = field(default_factory=dict)


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract raw text from every page of a PDF and join it."""
    reader = PdfReader(str(pdf_path))
    pages = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        pages.append(page_text)
    return "\n\n".join(pages)


def _destination_from_filename(pdf_path: Path) -> str:
    return pdf_path.stem.replace("_", " ").title()


def load_and_chunk_pdfs(pdf_dir: Path = PDF_DIR) -> list[Chunk]:
    """Load every PDF in pdf_dir, chunk it, and attach metadata to each chunk."""
    pdf_dir = Path(pdf_dir)
    chunks: list[Chunk] = []

    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        raw_text = extract_pdf_text(pdf_path)
        text_chunks = chunk_text(raw_text)

        destination = _destination_from_filename(pdf_path)
        for i, chunk_body in enumerate(text_chunks):
            chunks.append(
                Chunk(
                    id=f"{pdf_path.stem}::chunk-{i}",
                    text=chunk_body,
                    metadata={
                        "source": pdf_path.name,
                        "destination": destination,
                        "chunk_index": i,
                    },
                )
            )

    return chunks
