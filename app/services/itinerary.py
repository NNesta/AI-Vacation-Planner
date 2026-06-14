from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.chat.messages import chat
from app.ai.prompts.itineraries_prompt import get_prompts
from app.models.activity import Activity
from app.models.itinerary_day import ItineraryDay
from app.schemas.itinerary.itinerary_request import CreateItineraryRequest
from .trip import get_trip
import json

MAX_TOKENS = 1000


async def create_itinerary(itinerary_data: CreateItineraryRequest, db: AsyncSession):
    days = []
    for day_item in itinerary_data.itinerary_days:
        activities = []
        for activity in day_item.activities:
            new_activity = Activity(title=activity.title)
            activities.append(new_activity)

        day = ItineraryDay(
            trip_id=itinerary_data.trip_id,
            day_number=day_item.day,
            activities=activities,
        )
        days.append(day)
    db.add_all(days)
    await db.commit()
    await db.refresh(days[0])
    return dict(trip_id=itinerary_data.trip_id, itineraries=days)


async def get_all_itineraries(db: AsyncSession):
    result = await db.execute(select(ItineraryDay))
    itineraries = result.scalars().all()
    return itineraries


async def generate_itineraries(trip_id, db: AsyncSession):
    trip = await get_trip(trip_id, db=db)

    user_prompts, system_prompt = get_prompts(
        trip.title,
        trip.start_datetime,
        trip.end_datetime,
        trip.destination,
        trip.budget,
        trip.trip_style,
        trip.description,
    )
    response = chat(
        MAX_TOKENS,
        user_prompts,
        system_prompt,
        stop_sequences=["```"],
    )
    return json.loads(response.strip())
