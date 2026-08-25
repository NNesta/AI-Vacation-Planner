"""
Thin wrapper around a persistent Chroma collection: the vector database
that stores travel chunk text, metadata, and embeddings, and answers
semantic-search queries at request time.
"""
from __future__ import annotations

from pathlib import Path

import chromadb
from chromadb.api.models.Collection import Collection

from app.config import CHROMA_DIR, COLLECTION_NAME, VECTORIZER_PATH
from app.embeddings import TfidfEmbeddingFunction
from app.pdf_loader import Chunk


def load_embedding_function() -> TfidfEmbeddingFunction:
    """Load the TF-IDF vectorizer fitted during ingestion."""
    if not VECTORIZER_PATH.exists():
        raise RuntimeError(
            "No fitted vectorizer found. Run `python scripts/ingest.py` first "
            "to build the knowledge base."
        )
    return TfidfEmbeddingFunction.load(VECTORIZER_PATH)


def get_collection(embedding_function: TfidfEmbeddingFunction) -> Collection:
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )


def reset_collection(embedding_function: TfidfEmbeddingFunction) -> Collection:
    """Drop and recreate the collection - used when re-ingesting from scratch."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(collection: Collection, chunks: list[Chunk], batch_size: int = 64) -> None:
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        collection.add(
            ids=[c.id for c in batch],
            documents=[c.text for c in batch],
            metadatas=[c.metadata for c in batch],
        )


def query(collection: Collection, query_text: str, top_k: int) -> dict:
    return collection.query(
        query_texts=[query_text],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
