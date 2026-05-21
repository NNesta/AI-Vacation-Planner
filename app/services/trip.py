from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.trip import Trip
from app.models.user import User
from app.models.user_trips import UserTrip
from ..schemas.trip import trip_request


async def create_trip(
    trip_data: trip_request.CreateTripRequest, db: AsyncSession, current_user: User
):
    new_trip = Trip(
        destination=trip_data.destination,
        budget=trip_data.budget,
        days=trip_data.days,
        trip_style=trip_data.trip_style,
        creator_id=current_user.id,
    )
    db.add(new_trip)
    await db.commit()
    await db.refresh(new_trip)
    return new_trip


async def apply_for_trip(trip_id: UUID, db: AsyncSession, current_user: User):
    result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(
            detail="Trip not found", status_code=status.HTTP_404_NOT_FOUND
        )
    if trip.creator_id == current_user.id:
        raise HTTPException(
            detail="Not allowed to  apply on your own trip",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    trip.user_trips.append(UserTrip(trip_id=trip_id, user_id=current_user.id))
    await db.commit()
    return trip


async def get_trips(db: AsyncSession):
    result = await db.execute(
        select(Trip)
        .options(selectinload(Trip.user_trips))
        .options(selectinload(Trip.creator))
        .options(selectinload(Trip.itinerary_days))
    )
    trips = result.scalars().all()
    print(trips[3].user_trips)
    return trips


async def get_trip(trip_id: UUID, db: AsyncSession):
    result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(
            detail="Trip not found", status_code=status.HTTP_404_NOT_FOUND
        )
    return trip


async def update_trip(
    trip_id: UUID,
    trip_data: trip_request.UpdateTripRequest,
    db: AsyncSession,
    current_user: User,
):
    result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(
            detail="Trip not found", status_code=status.HTTP_404_NOT_FOUND
        )
    if trip.creator_id != current_user.id:
        raise HTTPException(
            detail="Not allowed to update this trip",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    update_data = trip_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(trip, field, value)
    await db.commit()
    await db.refresh(trip)
    return trip


async def delete_trip(trip_id: UUID, db: AsyncSession):
    result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(
            detail="Trip not found", status_code=status.HTTP_404_NOT_FOUND
        )
    await db.delete(trip)
    await db.commit()
