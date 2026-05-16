from fastapi import APIRouter, status

from app.db.session import DbSession
from app.schemas.itinerary.itinerary_request import CreateItineraryRequest
from app.schemas.itinerary.itinerary_response import ItineraryResponse
from app.services import itinerary as itinerary_service


router = APIRouter()


@router.post("/", response_model=ItineraryResponse, status_code=status.HTTP_201_CREATED)
async def create_itinerary(itinerary_data: CreateItineraryRequest, db: DbSession):
    return await itinerary_service.create_itinerary(itinerary_data, db)
