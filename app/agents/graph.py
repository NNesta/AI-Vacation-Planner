"""The conversational tool-using agent.

    START -> agent -> (tools -> agent)* -> END

``agent`` is the model, bound to every travel tool. ``tools_condition`` routes
to the tool node whenever the model asked for a tool call, and back to END once
it answers in plain text. This is the phase 5 flow:

    user request -> agent decides -> tool(s) run -> LLM combines -> response
"""

from __future__ import annotations

from functools import lru_cache

from langchain_core.messages import AIMessage, AnyMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.agents.llm import get_chat_model
from app.agents.prompts import AGENT_SYSTEM_PROMPT, today_str
from app.agents.state import AgentState
from app.agents.tools import TRAVEL_TOOLS
from app.mcp.client import get_mcp_tools


def build_agent_graph(checkpointer=None) -> CompiledStateGraph:
    """Compile the ReAct agent graph.

    Pass a checkpointer to give the agent memory across turns; calls then need a
    ``thread_id`` in their config.
    """
    tools = [*TRAVEL_TOOLS, *get_mcp_tools()]
    model = get_chat_model().bind_tools(tools)

    async def agent(state: AgentState) -> dict:
        # The system prompt is prepended per call rather than stored in state so
        # it never accumulates in the checkpointed history.
        system = SystemMessage(content=AGENT_SYSTEM_PROMPT.format(today=today_str()))
        response = await model.ainvoke([system, *state["messages"]])
        return {"messages": [response]}

    builder = StateGraph(AgentState)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "agent")
    # tools_condition -> "tools" when the last message has tool calls, else END.
    builder.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    builder.add_edge("tools", "agent")

    return builder.compile(checkpointer=checkpointer)


@lru_cache(maxsize=1)
def get_agent_graph() -> CompiledStateGraph:
    """Process-wide agent with in-memory conversation checkpointing.

    ``InMemorySaver`` keeps threads in this process only — swap it for
    ``AsyncPostgresSaver`` to survive restarts or run more than one worker.
    """
    return build_agent_graph(checkpointer=InMemorySaver())


def collect_tool_calls(messages: list[AnyMessage]) -> list[str]:
    """Names of the tools the model chose, in order, for response transparency."""
    return [
        call["name"]
        for message in messages
        if isinstance(message, AIMessage)
        for call in (message.tool_calls or [])
    ]


def final_text(messages: list[AnyMessage]) -> str:
    """Text of the last assistant message, flattening Anthropic block lists."""
    for message in reversed(messages):
        if not isinstance(message, AIMessage):
            continue
        content = message.content
        if isinstance(content, str) and content.strip():
            return content
        if isinstance(content, list):
            text = "".join(
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            )
            if text.strip():
                return text
    return ""
