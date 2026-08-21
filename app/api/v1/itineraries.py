from uuid import UUID

from fastapi import APIRouter, status

from app.db.session import DbSession
from app.schemas.itinerary.itinerary_request import CreateItineraryRequest, Itinerary
from app.schemas.itinerary.itinerary_response import (
    ItineraryCreateResponse,
)
from app.services import itinerary as itinerary_service

router = APIRouter()


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
