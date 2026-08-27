from uuid import UUID

from fastapi import APIRouter, status, Request

from app.db.session import DbSession
from app.schemas.itinerary.itinerary_request import CreateItineraryRequest, Itinerary, AskRequest, SourceOut
from app.schemas.itinerary.itinerary_response import (
    ItineraryCreateResponse, AskResponse
)
from app.services import itinerary as itinerary_service
from app.utils.config import  TOP_K
from app.utils.rag import RagResult, answer_question
from app.utils.vector_store import get_collection, load_embedding_function

router = APIRouter()
state ={}

@router.post(
    "/", response_model=ItineraryCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_itinerary(itinerary_data: CreateItineraryRequest, db: DbSession):
    return await itinerary_service.create_itinerary(itinerary_data, db)


@router.get("/generate/{trip_id}", response_model=list[Itinerary])
async def generate_itineraries(trip_id: UUID, db: DbSession):
    validated_data, error = await itinerary_service.generate_itineraries(trip_id, db)
    if error:
        return error
    return validated_data


@router.get("/", response_model=list[Itinerary])
async def get_all_itineraries(db: DbSession):
    return await itinerary_service.get_all_itineraries(db)

@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, request: Request):
    collection = request.app.state.collection
    result: RagResult = answer_question(
        collection, req.query, top_k=req.top_k or TOP_K
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

