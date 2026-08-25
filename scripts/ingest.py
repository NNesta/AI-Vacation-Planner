"""
Offline indexing pipeline for the Vacation Planner travel knowledge base.

Run this whenever you add, remove, or update PDFs in data/pdfs/:

    python scripts/ingest.py

It reads every PDF in data/pdfs/, chunks the text, fits (or re-fits) the
embedding vectorizer over the whole corpus, embeds every chunk, and writes
everything into the persistent Chroma collection in data/chroma_db/.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.utils.config import PDF_DIR, VECTORIZER_PATH  # noqa: E402
from app.utils.embeddings import TfidfEmbeddingFunction  # noqa: E402
from app.utils.pdf_loader import load_and_chunk_pdfs  # noqa: E402
from app.utils.vector_store import add_chunks, reset_collection  # noqa: E402


def main() -> None:
    print(f"Loading PDFs from {PDF_DIR} ...")
    chunks = load_and_chunk_pdfs(PDF_DIR)
    if not chunks:
        print(f"No PDFs found in {PDF_DIR}. Add some .pdf files and re-run.")
        return
    print(f"Loaded {len(chunks)} chunks from PDFs.")

    print("Fitting embedding vectorizer over the full corpus ...")
    embedding_fn = TfidfEmbeddingFunction()
    embedding_fn.fit([c.text for c in chunks])
    embedding_fn.save(VECTORIZER_PATH)
    print(f"Saved vectorizer to {VECTORIZER_PATH}")

    print("Rebuilding vector collection ...")
    collection = reset_collection(embedding_fn)
    add_chunks(collection, chunks)
    print(f"Indexed {collection.count()} chunks into the vector database.")

    print("\nSample chunk:")
    print("-" * 60)
    sample = chunks[0]
    print(f"id: {sample.id}")
    print(f"metadata: {sample.metadata}")
    print(sample.text[:300] + ("..." if len(sample.text) > 300 else ""))


if __name__ == "__main__":
    main()
