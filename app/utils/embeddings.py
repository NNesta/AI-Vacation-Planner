"""
Embedding function for the vector store.

By default, Chroma's built-in embedding function downloads a pretrained
sentence-transformer model (all-MiniLM-L6-v2) the first time it runs. If
you have unrestricted internet access, that's the better choice for
semantic quality - just delete this file's usage in vector_store.py and
pass `embedding_functions.DefaultEmbeddingFunction()` instead, or plug in
a hosted embedding API (OpenAI, Cohere, Voyage AI, etc).

This project ships a small TF-IDF based embedding function instead, so it
runs fully offline with no model download required. It fits a vocabulary
over the knowledge base at ingestion time and reuses that exact fitted
vectorizer at query time (loaded from disk), which keeps indexing and
querying consistent - the same requirement that applies to any embedding
model in a RAG pipeline.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

import joblib
from chromadb import EmbeddingFunction, Documents, Embeddings
from sklearn.feature_extraction.text import TfidfVectorizer

from app.config import VECTORIZER_PATH


class TfidfEmbeddingFunction(EmbeddingFunction):
    """A chromadb-compatible embedding function backed by TF-IDF."""

    def __init__(self, vectorizer: TfidfVectorizer | None = None):
        self._vectorizer = vectorizer

    @property
    def is_fitted(self) -> bool:
        return self._vectorizer is not None

    def fit(self, corpus: List[str]) -> None:
        self._vectorizer = TfidfVectorizer(
            max_features=4096,
            ngram_range=(1, 2),
            stop_words="english",
        )
        self._vectorizer.fit(corpus)

    def save(self, path: Path = VECTORIZER_PATH) -> None:
        if not self.is_fitted:
            raise RuntimeError("Cannot save an unfitted vectorizer.")
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._vectorizer, path)

    @classmethod
    def load(cls, path: Path = VECTORIZER_PATH) -> "TfidfEmbeddingFunction":
        vectorizer = joblib.load(path)
        return cls(vectorizer=vectorizer)

    def __call__(self, input: Documents) -> Embeddings:  # noqa: A002 (chromadb API)
        if not self.is_fitted:
            raise RuntimeError(
                "Embedding function has not been fitted or loaded yet. "
                "Run the ingestion script first."
            )
        matrix = self._vectorizer.transform(list(input))
        return matrix.toarray().tolist()
