from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.activity import Activity
from app.models.itinerary import Itinerary
from app.schemas.itinerary.itinerary_request import CreateItineraryRequest


async def create_itinerary(itinerary_data: CreateItineraryRequest, db: AsyncSession):
    days = []
    for day_item in itinerary_data.itineraries:
        activities = []
        for activity in day_item.activities:
            new_activity = Activity(title=activity)
            activities.append(new_activity)

        day = Itinerary(
            trip_id=itinerary_data.trip_id,
            day=day_item.day,
            activities=activities,
        )
        days.append(day)
    db.add_all(days)
    await db.commit()
    await db.refresh(days[0])
    return dict(trip_id=itinerary_data.trip_id, itineraries=days)


async def get_all_itineraries(db: AsyncSession):
    result = await db.execute(select(Itinerary))
    itineraries = result.scalars().all()
    return itineraries
