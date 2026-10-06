"""Itinerary business logic.

Manual CRUD stays here; AI generation is delegated to the LangGraph workflow in
``app/agents/itinerary_graph.py``.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.itinerary_graph import get_itinerary_graph
from app.db.session import async_session_local
from app.models.activity import Activity
from app.models.itinerary import Itinerary as ItineraryModel
from app.schemas.itinerary.itinerary_request import CreateItineraryRequest


async def create_itinerary(itinerary_data: CreateItineraryRequest, db: AsyncSession):
    """Create an itinerary manually, from a client-supplied plan."""
    days = []
    for day_item in itinerary_data.itineraries:
        activities = [
            Activity(title=activity.title, description=activity.description)
            for activity in day_item.activities
        ]
        days.append(
            ItineraryModel(
                trip_id=itinerary_data.trip_id,
                day=day_item.day,
                details=day_item.model_dump(mode="json"),
                activities=activities,
            )
        )
    db.add_all(days)
    await db.commit()
    for day in days:
        await db.refresh(day)
    return {"trip_id": itinerary_data.trip_id, "itineraries": days}


async def get_all_itineraries(db: AsyncSession):
    result = await db.execute(select(ItineraryModel).order_by(ItineraryModel.day))
    return result.scalars().all()


async def get_trip_itineraries(trip_id: UUID, db: AsyncSession):
    result = await db.execute(
        select(ItineraryModel)
        .where(ItineraryModel.trip_id == trip_id)
        .order_by(ItineraryModel.day)
    )
    return result.scalars().all()


async def replace_trip_itineraries(trip_id: UUID, days: list[dict]) -> list[ItineraryModel]:
    """Overwrite a trip's itinerary with ``days`` in a single transaction.

    Called from the workflow's ``persist`` node, which has no request session of
    its own, so it opens one here.
    """
    async with async_session_local() as session:
        existing = await session.execute(
            select(ItineraryModel).where(ItineraryModel.trip_id == trip_id)
        )
        for stale in existing.scalars().all():
            await session.delete(stale)

        rows = [
            ItineraryModel(
                trip_id=trip_id,
                day=day["day"],
                details=day,
                activities=[
                    Activity(
                        title=activity["title"],
                        description=activity.get("description"),
                    )
                    for activity in day.get("activities", [])
                ],
            )
            for day in days
        ]
        session.add_all(rows)
        await session.commit()
        return rows


async def generate_itineraries(
    trip_id: UUID,
    user_request: str | None = None,
    save: bool = True,
) -> dict:
    """Run the agentic itinerary workflow for a trip.

    Returns the workflow's final state: the itinerary plus which tools the agent
    chose, so callers can see how the plan was built.
    """
    from app.core.config import settings

    final_state = await get_itinerary_graph().ainvoke(
        {
            "trip_id": str(trip_id),
            "user_request": user_request,
            "save": save,
        },
        {"recursion_limit": settings.AGENT_RECURSION_LIMIT * 2},
    )

    return {
        "trip_id": trip_id,
        "itinerary": final_state.get("itinerary") or [],
        "tools_used": final_state.get("tools_used") or [],
        "research": final_state.get("research"),
        "issues": final_state.get("issues") or [],
        "saved": bool(final_state.get("saved")),
        "error": final_state.get("error"),
    }
