"""Database tools — let the agent read the trip it is planning for.

These tools open their own short-lived read-only session. Handing the request
session to a tool would tie its lifetime to a graph node that may run many
turns later, so the agent gets its own instead.
"""

from __future__ import annotations

from uuid import UUID

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import async_session_local
from app.models.itinerary import Itinerary
from app.models.trip import Trip


class TripInput(BaseModel):
    trip_id: str = Field(description="UUID of the trip to read.")


def _trip_to_dict(trip: Trip) -> dict:
    nights = (trip.end_datetime - trip.start_datetime).days
    return {
        "trip_id": str(trip.id),
        "title": trip.title,
        "description": trip.description,
        "destination": trip.destination,
        "start_date": trip.start_datetime.date().isoformat(),
        "end_date": trip.end_datetime.date().isoformat(),
        # A trip from the 1st to the 5th spans 5 days, not 4.
        "days": max(nights + 1, 1),
        "budget": float(trip.budget) if trip.budget is not None else None,
        "trip_style": trip.trip_style.value
        if hasattr(trip.trip_style, "value")
        else str(trip.trip_style),
    }


async def load_trip(trip_id: UUID) -> dict | None:
    """Fetch a trip as a plain dict, or ``None`` if it does not exist."""
    async with async_session_local() as session:
        result = await session.execute(select(Trip).where(Trip.id == trip_id))
        trip = result.scalar_one_or_none()
        return _trip_to_dict(trip) if trip else None


@tool("get_trip_details", args_schema=TripInput)
async def get_trip_details(trip_id: str) -> dict:
    """Look up a saved trip: destination, dates, length, budget and travel style.

    Call this first whenever the user refers to "my trip" or gives a trip id, so
    the plan is built from the stored dates and budget instead of assumptions.
    """
    try:
        trip = await load_trip(UUID(trip_id))
    except ValueError:
        return {"error": f"{trip_id!r} is not a valid trip id"}
    if trip is None:
        return {"error": f"no trip found with id {trip_id}"}
    return trip


@tool("get_saved_itinerary", args_schema=TripInput)
async def get_saved_itinerary(trip_id: str) -> dict:
    """Read the itinerary already saved for a trip, day by day.

    Use this before changing, extending or critiquing an existing plan, so you
    build on what is stored rather than silently replacing it.
    """
    try:
        parsed = UUID(trip_id)
    except ValueError:
        return {"error": f"{trip_id!r} is not a valid trip id"}

    async with async_session_local() as session:
        result = await session.execute(
            select(Itinerary)
            .where(Itinerary.trip_id == parsed)
            .options(selectinload(Itinerary.activities))
            .order_by(Itinerary.day)
        )
        days = result.scalars().all()

    if not days:
        return {
            "trip_id": trip_id,
            "days": [],
            "note": "No itinerary saved yet for this trip.",
        }

    return {
        "trip_id": trip_id,
        "days": [
            {
                "day": day.day,
                "activities": [
                    {"title": a.title, "description": a.description}
                    for a in day.activities
                ],
                **({"details": day.details} if day.details else {}),
            }
            for day in days
        ],
    }
