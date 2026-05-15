from typing import List
from uuid import UUID
from fastapi import APIRouter, status
from app.db.session import DbSession
from ...schemas.trip import trip_request, trip_response, trip_safe_response
from ...services import trip_services


router = APIRouter()


@router.post(
    "/",
    response_model=List[trip_safe_response.CreateTripResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_trip(payload: trip_request.CreateTripRequest, db: DbSession):
    return await trip_services.create_trip(payload, db=db)


@router.get("/", response_model=List[trip_response.TripResponse])
async def get_trips(db: DbSession):
    return await trip_services.get_trips(db=db)


@router.get("/:trip_id", response_model=trip_response.TripResponse)
async def get_trip(trip_id: UUID, db: DbSession):
    return await trip_services.get_trip(trip_id, db=db)


@router.put("/:trip_id", response_model=List[trip_response.TripResponse])
async def update_trip(
    trip_id: UUID, update_data: trip_request.UpdateTripRequest, db: DbSession
):
    return await trip_services.update_trip(trip_id, update_data, db=db)


@router.delete("/:trip_id", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(trip_id: UUID, db: DbSession):
    return await trip_services.delete_trip(trip_id, db=db)
