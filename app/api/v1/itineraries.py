from fastapi import APIRouter, status
from typing import List
from app.db.session import DbSession
from app.schemas.itinerary.itinerary_request import CreateItineraryRequest
from app.schemas.itinerary.itinerary_response import ItineraryCreateResponse
from app.services import itinerary as itinerary_service


router = APIRouter()


@router.post(
    "/", response_model=ItineraryCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_itinerary(itinerary_data: CreateItineraryRequest, db: DbSession):
    return await itinerary_service.create_itinerary(itinerary_data, db)
