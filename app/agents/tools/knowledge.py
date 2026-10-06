"""RAG tool — the phase 4 travel knowledge base, exposed as an agent tool.

Chroma and SentenceTransformers are synchronous and CPU-bound, so every call is
pushed onto a worker thread rather than blocking the event loop.
"""

from __future__ import annotations

from functools import lru_cache

import anyio
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.utils.config import MAX_RELEVANT_DISTANCE, TOP_K
from app.utils.rag import RetrievedChunk, retrieve
from app.utils.vector_store import get_collection, load_embedding_function

SNIPPET_CHARS = 700


class KnowledgeInput(BaseModel):
    query: str = Field(
        description="What to look up, phrased as a full question or topic, "
        "e.g. 'gorilla trekking permit rules in Volcanoes National Park'."
    )
    top_k: int = Field(
        default=TOP_K, ge=1, le=10, description="How many passages to retrieve."
    )


@lru_cache(maxsize=1)
def _collection():
    """Build the Chroma collection once per process (the embedder is ~90 MB)."""
    return get_collection(load_embedding_function())


def _search(query: str, top_k: int) -> list[RetrievedChunk]:
    chunks = retrieve(_collection(), query, top_k=top_k)
    return [c for c in chunks if c.distance <= MAX_RELEVANT_DISTANCE]


@tool("search_travel_knowledge", args_schema=KnowledgeInput)
async def search_travel_knowledge(query: str, top_k: int = TOP_K) -> dict:
    """Search the curated travel knowledge base of destination guides and local tips.

    Use this first for anything about specific parks, permits, opening hours,
    local customs, hidden gems or practical on-the-ground logistics. The content
    comes from official visitor guides, so prefer it over your own general
    knowledge when the two disagree.

    Returns matching passages with their source document. An empty `passages`
    list means the knowledge base does not cover the topic — say so, then answer
    from general knowledge and label it as such.
    """
    try:
        chunks = await anyio.to_thread.run_sync(_search, query, top_k)
    except Exception as exc:  # Chroma raises a wide range of backend errors
        return {
            "error": f"knowledge base unavailable: {exc}",
            "query": query,
            "passages": [],
        }

    passages = [
        {
            "destination": chunk.destination,
            "source": chunk.source,
            "relevance": round(1.0 - chunk.distance, 3),
            "text": (
                chunk.text[:SNIPPET_CHARS] + "..."
                if len(chunk.text) > SNIPPET_CHARS
                else chunk.text
            ),
        }
        for chunk in chunks
    ]

    return {
        "query": query,
        "count": len(passages),
        "passages": passages,
        "note": (
            "Nothing relevant in the knowledge base for this query."
            if not passages
            else "Passages come from curated destination guides — cite the source."
        ),
    }
