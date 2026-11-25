"""Live stdio MCP integration test for gmail-calendar (read-only list_events)."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

DEFAULT_PRIVATE_DIR = "/Users/pirogan4ik/Desktop/private"


async def run_integration_test() -> None:
    """Start gmail-calendar over stdio, list tools, and call list_events(days_ahead=1)."""
    project_dir = Path(__file__).resolve().parent
    env = dict(os.environ)
    env.setdefault("GOOGLE_PRIVATE_DIR", DEFAULT_PRIVATE_DIR)

    params = StdioServerParameters(
        command="uv",
        args=["--directory", str(project_dir), "run", "gmail-calendar"],
        env=env,
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tool_names = [tool.name for tool in tools_result.tools]
            print("Registered tools:", json.dumps(tool_names))

            response = await session.call_tool("list_events", {"days_ahead": 1})
            print("is_error:", response.is_error)
            for block in response.content:
                text = getattr(block, "text", None)
                if text is not None:
                    try:
                        parsed = json.loads(text)
                        print("list_events response:", json.dumps(parsed, indent=2, ensure_ascii=False))
                    except json.JSONDecodeError:
                        print("list_events response:", text)
                else:
                    print("list_events block:", block)


if __name__ == "__main__":
    asyncio.run(run_integration_test())
