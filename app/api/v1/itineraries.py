from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status

from app.db.session import DbSession
from app.schemas.agent import GenerateItineraryRequest, GeneratedItineraryResponse
from app.schemas.itinerary.itinerary_request import (
    AskRequest,
    CreateItineraryRequest,
    SourceOut,
)
from app.schemas.itinerary.itinerary_response import (
    AskResponse,
    Itinerary,
    ItineraryCreateResponse,
)
from app.services import itinerary as itinerary_service
from app.utils.config import TOP_K
from app.utils.rag import RagResult, answer_question

router = APIRouter()


@router.post(
    "/", response_model=ItineraryCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_itinerary(itinerary_data: CreateItineraryRequest, db: DbSession):
    """Create an itinerary manually from a client-supplied day-by-day plan."""
    return await itinerary_service.create_itinerary(itinerary_data, db)


@router.post(
    "/generate/{trip_id}",
    response_model=GeneratedItineraryResponse,
    summary="Generate an itinerary with the AI agent",
    description=(
        "Runs the LangGraph itinerary workflow: the trip is loaded, a research "
        "agent decides which tools to call (knowledge base, weather, places, "
        "cost), a structured itinerary is drafted from the findings, reviewed "
        "against the trip's dates and budget, re-drafted if it fails, and saved."
    ),
)
async def generate_itinerary(
    trip_id: UUID,
    db: DbSession,
    payload: GenerateItineraryRequest | None = None,
) -> GeneratedItineraryResponse:
    options = payload or GenerateItineraryRequest()
    result = await itinerary_service.generate_itineraries(
        trip_id, user_request=options.user_request, save=options.save
    )

    error = result.get("error")
    if error and not result["itinerary"]:
        not_found = "no trip found" in error or "not a valid trip id" in error
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
            if not_found
            else status.HTTP_502_BAD_GATEWAY,
            detail=error,
        )

    return GeneratedItineraryResponse(**result)


@router.get("/", response_model=list[Itinerary])
async def get_all_itineraries(db: DbSession):
    return await itinerary_service.get_all_itineraries(db)


@router.get("/{trip_id}", response_model=list[Itinerary])
async def get_trip_itineraries(trip_id: UUID, db: DbSession):
    """Return the stored itinerary for a single trip."""
    return await itinerary_service.get_trip_itineraries(trip_id, db)


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask the knowledge base directly (phase 4 RAG)",
    description=(
        "Straight retrieve-then-answer over the travel knowledge base, with no "
        "tool selection. Kept alongside `/agent/chat`, which supersedes it."
    ),
)
def ask(req: AskRequest, request: Request):
    collection = request.app.state.collection
    result: RagResult = answer_question(collection, req.query, top_k=req.top_k or TOP_K)

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
