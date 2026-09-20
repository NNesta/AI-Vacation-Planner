from fastapi import APIRouter

from app.schemas.agent import ChatRequest, ChatResponse
from app.services import agent_services

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask the tool-using travel agent",
    description=(
        "Sends a message to the LangGraph agent. The agent decides which tools to "
        "call — trip lookup, travel knowledge base, weather, place search, "
        "distances, cost estimates — runs them, and answers from the results.\n\n"
        "Pass the returned `thread_id` on the next call to continue the conversation."
    ),
)
async def chat(payload: ChatRequest) -> ChatResponse:
    result = await agent_services.chat(
        message=payload.message,
        thread_id=payload.thread_id,
        trip_id=str(payload.trip_id) if payload.trip_id else None,
    )
    return ChatResponse(**result)
