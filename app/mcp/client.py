from __future__ import annotations

import sys
from contextlib import AsyncExitStack, asynccontextmanager

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

MCP_SERVERS = {
    "travel": {
        "transport": "stdio",
        "command": sys.executable,
        "args": ["-m", "app.mcp.server"],
    },
}

_tools: list[BaseTool] = []


@asynccontextmanager
async def connect_mcp():
    client = MultiServerMCPClient(MCP_SERVERS)
    async with AsyncExitStack() as stack:
        for name in MCP_SERVERS:
            session = await stack.enter_async_context(client.session(name))
            _tools.extend(await load_mcp_tools(session, server_name=name))
        yield
        _tools.clear()


def get_mcp_tools() -> list[BaseTool]:
    return list(_tools)
