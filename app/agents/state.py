"""Graph state definitions.

LangGraph merges each node's returned dict into the state. ``messages`` uses the
``add_messages`` reducer so nodes append to the conversation instead of
replacing it; every other key is last-write-wins.
"""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State for the conversational ReAct agent."""

    messages: Annotated[list[AnyMessage], add_messages]


class ItineraryState(TypedDict, total=False):
    """State for the itinerary workflow.

    ``total=False`` because nodes populate these progressively.
    """

    trip_id: str
    user_request: str | None
    save: bool

    trip: dict[str, Any] | None
    research: str | None
    tools_used: list[str]

    itinerary: list[dict[str, Any]] | None
    issues: list[str]
    attempts: int

    saved: bool
    error: str | None
