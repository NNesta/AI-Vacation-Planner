from langchain_mcp_adapters.tools import to_fastmcp
from mcp.server.fastmcp import FastMCP

from app.agents.tools import MCP_TOOLS

mcp = FastMCP(
    "vacation-planner-travel",
    tools=[to_fastmcp(tool) for tool in MCP_TOOLS],
    log_level="WARNING",
)


if __name__ == "__main__":
    mcp.run()
