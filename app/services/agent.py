"""Service layer for the conversational agent."""

from __future__ import annotations

from base64 import b64encode
from uuid import uuid4

from langchain_core.messages import HumanMessage

from app.agents.graph import collect_tool_calls, final_text, get_agent_graph
from app.core.config import settings


async def chat(
    message: str,
    thread_id: str | None = None,
    trip_id: str | None = None,
    image: bytes | None = None,
    image_type: str | None = None,
) -> dict:
    """Send one turn to the agent and return its answer.

    ``thread_id`` identifies a conversation; pass the one returned by a previous
    call to continue it, or omit it to start fresh.
    """
    thread_id = thread_id or str(uuid4())

    # Trip context goes in the user turn, so the agent can decide for itself
    # whether the trip actually needs to be read.
    content = message
    if trip_id:
        content = f"{message}\n\n(The trip this is about has id {trip_id}.)"
    if image:
        content = [
            {"type": "image", "base64": b64encode(image).decode(), "mime_type": image_type},
            {"type": "text", "text": content},
        ]

    result = await get_agent_graph().ainvoke(
        {"messages": [HumanMessage(content=content)]},
        {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": settings.AGENT_RECURSION_LIMIT,
        },
    )

    # Only report the tools called this turn, not the whole thread's history.
    new_messages = result["messages"][-_turn_length(result["messages"]) :]

    return {
        "thread_id": thread_id,
        "answer": final_text(result["messages"]),
        "tools_used": collect_tool_calls(new_messages),
    }


def _turn_length(messages: list) -> int:
    """How many messages were added since the last human turn (inclusive)."""
    for offset, message in enumerate(reversed(messages)):
        if isinstance(message, HumanMessage):
            return offset + 1
    return len(messages)
