"""
Contextualist Agent

Connects to all four MCP servers concurrently and collects raw contextual
signals for a given topic and city.  Each MCP server is spawned as a
subprocess via the STDIO transport and torn down after the tool call completes.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Add project root to path so sibling packages resolve
_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT))

from protocol.messages import Signal

_SERVERS_DIR = _ROOT / "mcp-servers"


async def _call_tool(server_script: Path, tool_name: str, tool_args: dict) -> str:
    """Spawn a server subprocess, call one tool, return the raw text result."""
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_script)],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, tool_args)
            if result.content:
                return result.content[0].text
            return "{}"


class ContextualistAgent:
    """
    Fetches raw contextual data from all MCP servers.

    Call ``gather(topic, city)`` to get a list of Signal objects, one per
    data source.  All four sources are fetched concurrently.
    """

    async def fetch_news(self, topic: str, count: int = 5) -> Signal:
        server = _SERVERS_DIR / "world_data" / "server.py"
        try:
            raw = await _call_tool(server, "get_news", {"topic": topic, "count": count})
            return Signal(source="news", data=json.loads(raw))
        except Exception as exc:
            return Signal(source="news", data={"articles": []}, error=str(exc))

    async def fetch_weather(self, city: str) -> Signal:
        server = _SERVERS_DIR / "weather" / "server.py"
        try:
            raw = await _call_tool(server, "get_current_weather", {"city": city})
            return Signal(source="weather", data=json.loads(raw))
        except Exception as exc:
            return Signal(source="weather", data={}, error=str(exc))

    async def fetch_finance(self, topic: Optional[str] = None) -> Signal:
        server = _SERVERS_DIR / "finance" / "server.py"
        try:
            market_raw = await _call_tool(server, "get_market_summary", {})
            market = json.loads(market_raw)

            tickers_data: dict = {"tickers": []}
            if topic:
                try:
                    tickers_raw = await _call_tool(
                        server, "search_tickers", {"query": topic, "max_results": 3}
                    )
                    tickers_data = json.loads(tickers_raw)
                except Exception:
                    pass

            return Signal(
                source="finance",
                data={**market, **tickers_data},
            )
        except Exception as exc:
            return Signal(source="finance", data={"indices": [], "tickers": []}, error=str(exc))

    async def fetch_images(self, query: str, count: int = 3) -> Signal:
        server = _SERVERS_DIR / "media" / "server.py"
        try:
            raw = await _call_tool(server, "search_images", {"query": query, "count": count})
            return Signal(source="media", data=json.loads(raw))
        except Exception as exc:
            return Signal(source="media", data={"images": []}, error=str(exc))

    async def gather(self, topic: str, city: str) -> list[Signal]:
        """Fetch all signals concurrently and return them as a list."""
        news, weather, finance, images = await asyncio.gather(
            self.fetch_news(topic),
            self.fetch_weather(city),
            self.fetch_finance(topic),
            self.fetch_images(topic),
            return_exceptions=False,
        )
        return [news, weather, finance, images]
