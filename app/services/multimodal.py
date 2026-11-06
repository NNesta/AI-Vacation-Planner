from __future__ import annotations

from datetime import datetime, time, timezone

from fastapi import HTTPException, status
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm import get_chat_model
from app.agents.prompts import SPOKEN_REPLY_PROMPT, TRIP_FROM_SPEECH_PROMPT, today_str
from app.models.user import User
from app.schemas.multimodal import SpokenTripDetails
from app.schemas.trip.trip_request import CreateTripRequest
from app.services.agent import chat
from app.services.trip import create_trip
from app.utils.speech import SYNTHESIS_ERRORS, synthesize, transcribe

TRIP_DAY_START = time(9, tzinfo=timezone.utc)
TRIP_DAY_END = time(18, tzinfo=timezone.utc)


async def _transcribe(audio: bytes) -> str:
    try:
        transcript = await transcribe(audio)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"could not read the audio: {exc}",
        ) from exc
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="no speech was detected in the audio",
        )
    return transcript


async def create_trip_from_speech(audio: bytes, db: AsyncSession, current_user: User) -> dict:
    transcript = await _transcribe(audio)

    extractor = get_chat_model(temperature=0).with_structured_output(SpokenTripDetails)
    details = await extractor.ainvoke(
        [
            SystemMessage(content=TRIP_FROM_SPEECH_PROMPT.format(today=today_str())),
            HumanMessage(content=transcript),
        ]
    )

    missing = [
        field
        for field in ("destination", "start_date", "end_date")
        if getattr(details, field) is None
    ]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"transcript": transcript, "missing": missing},
        )

    try:
        payload = CreateTripRequest.model_validate(
            {
                **details.model_dump(
                    include={"title", "description", "destination", "budget"},
                    exclude_none=True,
                ),
                "start_datetime": datetime.combine(details.start_date, TRIP_DAY_START),
                "end_datetime": datetime.combine(details.end_date, TRIP_DAY_END),
            }
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"transcript": transcript, "errors": [e["msg"] for e in exc.errors()]},
        ) from exc

    return {"transcript": transcript, "trip": await create_trip(payload, db, current_user)}


async def voice_chat(
    audio: bytes, thread_id: str | None = None, trip_id: str | None = None
) -> dict:
    transcript = await _transcribe(audio)
    result = await chat(
        message=f"{transcript}\n\n{SPOKEN_REPLY_PROMPT}",
        thread_id=thread_id,
        trip_id=trip_id,
    )

    try:
        speech = await synthesize(result["answer"])
    except SYNTHESIS_ERRORS as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"speech synthesis failed: {exc}",
        ) from exc

    return {**result, "transcript": transcript, "audio": speech}
