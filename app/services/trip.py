from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.trips import Trip
from ..schemas.trip import trip_request


async def create_trip(trip_data: trip_request.CreateTripRequest, db: AsyncSession):
    new_trip = Trip(
        destination=trip_data.destination,
        budget=trip_data.budget,
        days=trip_data.days,
        trip_style=trip_data.trip_style,
    )
    db.add(new_trip)
    await db.commit()
    await db.refresh(new_trip)
    return new_trip


async def get_trips(db: AsyncSession):
    result = await db.execute(
        select(Trip)
        .options(selectinload(Trip.users))
        .options(selectinload(Trip.creator))
    )
    trips = result.scalars().all()
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
    trip_id: UUID, update_data: trip_request.UpdateTripRequest, db: AsyncSession
):
    result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(
            detail="Trip not found", status_code=status.HTTP_404_NOT_FOUND
        )


async def delete_trip(trip_id: UUID, db: AsyncSession):
    result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(
            detail="Trip not found", status_code=status.HTTP_404_NOT_FOUND
        )
    await db.delete(trip)
    await db.commit()
