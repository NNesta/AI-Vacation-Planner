
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.utils.config import PDF_DIR  # noqa: E402
from app.utils.embeddings import load_embedding_function  # noqa: E402
from app.utils.pdf_loader import load_and_chunk_pdfs  # noqa: E402
from app.utils.vector_store import add_chunks, reset_collection  # noqa: E402


def main() -> None:
    print(f"Loading PDFs from {PDF_DIR} ...")
    chunks = load_and_chunk_pdfs(PDF_DIR)
    if not chunks:
        print(f"No PDFs found in {PDF_DIR}. Add some .pdf files and re-run.")
        return
    print(f"Loaded {len(chunks)} chunks from PDFs.")

    print("Loading sentence-transformer embedding model ...")
    embedding_fn = load_embedding_function()

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
