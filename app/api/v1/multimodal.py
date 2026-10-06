from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status

from app.core.config import settings
from app.core.dependancies import CurrentUser
from app.db.session import DbSession
from app.schemas.agent import ChatResponse
from app.schemas.multimodal import VoiceTripResponse
from app.services import agent_services, multimodal_services

router = APIRouter()

IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


async def _read(upload: UploadFile, max_mb: int) -> bytes:
    data = await upload.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"{upload.filename} is empty",
        )
    if len(data) > max_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"{upload.filename} is larger than {max_mb} MB",
        )
    return data


@router.post(
    "/voice/trips",
    response_model=VoiceTripResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a trip by voice",
    description=(
        "Upload a recording (WAV, MP3, M4A, OGG or WebM) of the traveller "
        "describing the trip. It is transcribed with Whisper, the destination, "
        "dates, budget and interests are extracted with Claude, and the trip is "
        "saved for the logged-in user.\n\n"
        "Returns 422 with the transcript and the `missing` fields when the "
        "recording does not give a destination and dates."
    ),
)
async def create_trip_by_voice(
    audio: Annotated[UploadFile, File(description="Recording of the traveller describing the trip.")],
    db: DbSession,
    current_user: CurrentUser,
):
    return await multimodal_services.create_trip_from_speech(
        await _read(audio, settings.MAX_AUDIO_MB), db, current_user
    )


@router.post(
    "/voice/chat",
    response_class=Response,
    responses={
        200: {
            "content": {"audio/mpeg": {}},
            "description": "The agent's answer, spoken, as an MP3 file.",
        }
    },
    summary="Talk to the travel agent and hear the answer",
    description=(
        "Upload a spoken question. It is transcribed with Whisper and sent to the "
        "same tool-using agent as `/agent/chat` (trip records, knowledge base and "
        "the MCP travel tools); the answer comes back as speech.\n\n"
        "Response headers: `X-Thread-Id` (pass back as `thread_id` to continue "
        "the conversation), `X-Transcript` (URL-encoded) and `X-Tools-Used`."
    ),
)
async def voice_chat(
    audio: Annotated[UploadFile, File(description="Recording of the traveller's question.")],
    thread_id: Annotated[str | None, Form()] = None,
    trip_id: Annotated[UUID | None, Form()] = None,
) -> Response:
    result = await multimodal_services.voice_chat(
        await _read(audio, settings.MAX_AUDIO_MB),
        thread_id=thread_id,
        trip_id=str(trip_id) if trip_id else None,
    )
    return Response(
        content=result["audio"],
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": 'attachment; filename="answer.mp3"',
            "X-Thread-Id": result["thread_id"],
            "X-Transcript": quote(result["transcript"]),
            "X-Tools-Used": ",".join(result["tools_used"]),
        },
    )


@router.post(
    "/image/chat",
    response_model=ChatResponse,
    summary="Ask the travel agent about a photo",
    description=(
        "Upload a JPEG, PNG, GIF or WebP photo with an optional question. Claude "
        "works out what and where the photo shows, then the agent can use its "
        "tools — weather, places, distances, costs, the knowledge base — to plan "
        "around it."
    ),
)
async def image_chat(
    image: Annotated[UploadFile, File(description="Photo of a place, landmark, menu, sign or map.")],
    message: Annotated[str, Form(min_length=1, max_length=4000)] = (
        "Where is this, and how could I plan a trip around it?"
    ),
    thread_id: Annotated[str | None, Form()] = None,
    trip_id: Annotated[UUID | None, Form()] = None,
) -> ChatResponse:
    if image.content_type not in IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="send a JPEG, PNG, GIF or WebP image",
        )
    result = await agent_services.chat(
        message=message,
        thread_id=thread_id,
        trip_id=str(trip_id) if trip_id else None,
        image=await _read(image, settings.MAX_IMAGE_MB),
        image_type=image.content_type,
    )
    return ChatResponse(**result)
