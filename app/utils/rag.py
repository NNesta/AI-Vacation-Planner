
from __future__ import annotations

from dataclasses import dataclass

import anthropic

from app.utils.config import (
    ANTHROPIC_API_KEY,
    CLAUDE_MAX_TOKENS,
    CLAUDE_MODEL,
    MAX_RELEVANT_DISTANCE,
    TOP_K,
)
from app.utils.vector_store import query as vector_query
from app.ai.prompts.itineraries_prompt import RAG_SYSTEM_PROMPT


@dataclass
class RetrievedChunk:
    text: str
    source: str
    destination: str
    distance: float


@dataclass
class RagResult:
    answer: str
    used_context: bool
    sources: list[RetrievedChunk]


def retrieve(collection, question: str, top_k: int = TOP_K) -> list[RetrievedChunk]:
    raw = vector_query(collection, question, top_k)
    if not raw["documents"] or not raw["documents"][0]:
        return []

    results = []
    for text, meta, distance in zip(
        raw["documents"][0], raw["metadatas"][0], raw["distances"][0]
    ):
        results.append(
            RetrievedChunk(
                text=text,
                source=meta.get("source", "unknown"),
                destination=meta.get("destination", "unknown"),
                distance=distance,
            )
        )
    return results


def _format_context(chunks: list[RetrievedChunk]) -> str:
    blocks = []
    for i, c in enumerate(chunks, start=1):
        blocks.append(
            f"[{i}] Destination: {c.destination} (source: {c.source})\n{c.text}"
        )
    return "\n\n---\n\n".join(blocks)


def answer_question(collection, question: str, top_k: int = TOP_K) -> RagResult:
    retrieved = retrieve(collection, question, top_k=top_k)
    relevant = [c for c in retrieved if c.distance <= MAX_RELEVANT_DISTANCE]

    if relevant:
        context_block = _format_context(relevant)
        user_message = (
            f"Travel knowledge base context:\n\n{context_block}\n\n"
            f"Question: {question}"
        )
        used_context = True
    else:
        user_message = (
            f"No relevant passages were found in the travel knowledge base for "
            f"this question. Question: {question}\n\n"
            f"Answer from your general knowledge, and briefly mention that this "
            f"specific detail isn't covered in the knowledge base yet."
        )
        used_context = False

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=CLAUDE_MAX_TOKENS,
        system=RAG_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    answer_text = "".join(
        block.text for block in response.content if block.type == "text"
    )

    return RagResult(answer=answer_text, used_context=used_context, sources=relevant)
