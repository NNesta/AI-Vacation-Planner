
from __future__ import annotations

from chromadb import Documents, EmbeddingFunction, Embeddings

from app.config import SENTENCE_TRANSFORMER_MODEL


class SentenceTransformerEmbeddingFunction(EmbeddingFunction):
  
    @staticmethod
    def name() -> str:
        return "sentence_transformer"

    def __init__(self, model_name: str = SENTENCE_TRANSFORMER_MODEL):
        from sentence_transformers import SentenceTransformer  # lazy import

        self.model_name = model_name
        self._model = SentenceTransformer(model_name)

    def __call__(self, input: Documents) -> Embeddings:  # noqa: A002 (chromadb API)
        vectors = self._model.encode(
            list(input), normalize_embeddings=True, show_progress_bar=False
        )
        return vectors.tolist()


def load_embedding_function() -> SentenceTransformerEmbeddingFunction:

    return SentenceTransformerEmbeddingFunction()
