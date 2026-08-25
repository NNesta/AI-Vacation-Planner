from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import ANTHROPIC_API_KEY, TOP_K
from app.rag import RagResult, answer_question
from app.vector_store import get_collection, load_embedding_function

state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the fitted embedding function and open the persistent Chroma
    # collection once at startup, rather than on every request.
    try:
        embedding_fn = load_embedding_function()
        state["collection"] = get_collection(embedding_fn)
        state["ready"] = True
    except RuntimeError as exc:
        # Knowledge base hasn't been ingested yet - the API can still start,
        # but /ask will return a clear error until `scripts/ingest.py` runs.
        state["ready"] = False
        state["error"] = str(exc)
    yield
    state.clear()


app = FastAPI(title="Vacation Planner RAG API", lifespan=lifespan)


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, description="The traveler's question")
    top_k: int | None = Field(None, ge=1, le=10)


class SourceOut(BaseModel):
    source: str
    destination: str
    distance: float
    snippet: str


class AskResponse(BaseModel):
    answer: str
    used_knowledge_base: bool
    sources: list[SourceOut]


@app.get("/health")
def health():
    return {"status": "ok", "knowledge_base_ready": state.get("ready", False)}


@app.get("/search")
def search(q: str, top_k: int = TOP_K):
    """Raw retrieval endpoint - useful for debugging what the vector search returns."""
    _ensure_ready()
    from app.rag import retrieve

    chunks = retrieve(state["collection"], q, top_k=top_k)
    return {
        "query": q,
        "results": [
            {
                "source": c.source,
                "destination": c.destination,
                "distance": c.distance,
                "text": c.text,
            }
            for c in chunks
        ],
    }


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    _ensure_ready()
    if not ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY is not set on the server.",
        )

    result: RagResult = answer_question(
        state["collection"], req.query, top_k=req.top_k or TOP_K
    )

    return AskResponse(
        answer=result.answer,
        used_knowledge_base=result.used_context,
        sources=[
            SourceOut(
                source=c.source,
                destination=c.destination,
                distance=round(c.distance, 4),
                snippet=(c.text[:280] + "...") if len(c.text) > 280 else c.text,
            )
            for c in result.sources
        ],
    )


def _ensure_ready():
    if not state.get("ready"):
        raise HTTPException(
            status_code=503,
            detail=state.get(
                "error",
                "Knowledge base not ready. Run `python scripts/ingest.py` first.",
            ),
        )
