from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chat.messages import call_llm
from app.ai.prompts.itineraries_prompt_v2 import get_prompts, get_retry_prompt
from app.models.activity import Activity
from app.models.itinerary import Itinerary as ItineraryModel
from app.schemas.itinerary.itinerary_request import (
    CreateItineraryRequest,
    Itinerary,
    validate_with_model,
)

from .trip import get_trip

n_retry = 4
MAX_TOKENS = 2000


async def create_itinerary(itinerary_data: CreateItineraryRequest, db: AsyncSession):
    days = []
    for day_item in itinerary_data.itineraries:
        activities = []
        for activity in day_item.activities:
            new_activity = Activity(
                title=activity.title, description=activity.description
            )
            activities.append(new_activity)

        day = ItineraryModel(
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
    result = await db.execute(select(ItineraryModel))
    itineraries = result.scalars().all()
    return itineraries


async def generate_itineraries(trip_id, db: AsyncSession):

    trip = await get_trip(trip_id, db=db)

    prompts, system_prompt = get_prompts(
        trip.title,
        trip.start_datetime,
        trip.end_datetime,
        trip.destination,
        trip.budget,
        trip.trip_style,
        trip.description,
    )
    return validate_llm_response(prompts, system_prompt, Itinerary)


async def save_ai_itineraries(trip_id, db: AsyncSession):

    itineraries = await generate_itineraries(trip_id, db)


def validate_llm_response(prompts, system_prompt, data_model, n_retry=3):
    response_content = call_llm(
        MAX_TOKENS,
        prompts,
        system_prompt,
        temperature=0.8,
        stop_sequences=["```"],
    )
    current_prompts = prompts
    for attempt in range(n_retry + 1):

        validated_data, validation_error = validate_with_model(
            data_model, response_content
        )
        if validation_error:
            if attempt < n_retry:
                print(f"retry {attempt} of {n_retry} failed, trying again")
            else:
                print(f"Max retries reached. Last Error: {validation_error}")
                return None, "Max retries reached. Last Error: {validation_error}"
            validation_retry_prompt = get_retry_prompt(
                current_prompts, response_content, validation_error
            )
            print(validation_retry_prompt)
            response_content = call_llm(
                MAX_TOKENS,
                validation_retry_prompt,
                system_prompt,
                temperature=0.8,
                stop_sequences=["```"],
            )
            print(response_content)
            current_prompts = validation_retry_prompt
            continue

        return validated_data, None
