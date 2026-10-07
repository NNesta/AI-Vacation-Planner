from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.graph import get_agent_graph
from app.agents.itinerary_graph import get_itinerary_graph
from app.api.router import api_router_v1
from app.mcp.client import connect_mcp
from app.utils.vector_store import get_collection, load_embedding_function

origins = ["*"]

DESCRIPTION = """
Plan trips end-to-end with an AI agent.

**Phase 5 — Frameworks & orchestration.** `POST /api/v1/agent/chat` and
`POST /api/v1/itineraries/generate/{trip_id}` run LangGraph graphs in which the
model chooses which tools to call: the travel knowledge base (RAG), weather,
place lookup, distances, cost estimates and the trip record itself.

**Phase 6 — Multimodal AI & MCP.** The weather, maps and pricing tools are
served by an MCP server (`app/mcp/server.py`) that the agent connects to as an
MCP client. The `/api/v1/multimodal` endpoints add voice and image input:
create a trip by speaking, talk to the agent and get a spoken answer back, or
ask about a photo.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Loading the embedding model and compiling the graphs is slow, so it
    # happens once at startup rather than on the first request.
    async with connect_mcp():
        app.state.collection = get_collection(load_embedding_function())
        app.state.agent_graph = get_agent_graph()
        app.state.itinerary_graph = get_itinerary_graph()

        yield


app = FastAPI(
    title="AI Vacation Planner API",
    description=DESCRIPTION,
    version="0.6.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=[],
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
app.include_router(api_router_v1)
