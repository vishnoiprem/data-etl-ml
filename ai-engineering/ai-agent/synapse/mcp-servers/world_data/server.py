"""
World Data MCP Server — wraps NewsAPI to expose recent headlines as tools.

Run standalone:  python mcp-servers/world_data/server.py
Agents connect via stdio transport.
"""

import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load .env from project root (two levels up from this file)
load_dotenv(Path(__file__).parent.parent.parent / ".env")

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
NEWS_API_BASE = "https://newsapi.org/v2"

mcp = FastMCP("World Data Server")


@mcp.tool()
async def get_news(topic: str, count: int = 5) -> str:
    """Fetch recent news articles about a topic from NewsAPI.

    Args:
        topic: Search query / topic string.
        count: Number of articles to return (max 10).

    Returns:
        JSON string with a list of articles.
    """
    if not NEWS_API_KEY:
        return json.dumps({"error": "NEWS_API_KEY not configured", "articles": []})

    count = min(count, 10)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{NEWS_API_BASE}/everything",
                params={
                    "q": topic,
                    "pageSize": count,
                    "sortBy": "publishedAt",
                    "language": "en",
                    "apiKey": NEWS_API_KEY,
                },
            )
        data = r.json()
        if data.get("status") != "ok":
            return json.dumps({"error": data.get("message", "API error"), "articles": []})

        articles = [
            {
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "url": a.get("url", ""),
                "published_at": a.get("publishedAt", ""),
                "source": a.get("source", {}).get("name", ""),
                "author": a.get("author", ""),
            }
            for a in data.get("articles", [])[:count]
            if a.get("title") and "[Removed]" not in a.get("title", "")
        ]
        return json.dumps({"articles": articles, "count": len(articles)})

    except Exception as exc:
        return json.dumps({"error": str(exc), "articles": []})


@mcp.tool()
async def get_top_headlines(country: str = "us", count: int = 5) -> str:
    """Fetch today's top headlines for a country.

    Args:
        country: ISO 3166-1 alpha-2 country code (e.g. 'us', 'gb').
        count: Number of headlines (max 10).

    Returns:
        JSON string with a list of headline articles.
    """
    if not NEWS_API_KEY:
        return json.dumps({"error": "NEWS_API_KEY not configured", "articles": []})

    count = min(count, 10)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{NEWS_API_BASE}/top-headlines",
                params={"country": country, "pageSize": count, "apiKey": NEWS_API_KEY},
            )
        data = r.json()
        articles = [
            {
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "url": a.get("url", ""),
                "published_at": a.get("publishedAt", ""),
                "source": a.get("source", {}).get("name", ""),
            }
            for a in data.get("articles", [])[:count]
            if a.get("title") and "[Removed]" not in a.get("title", "")
        ]
        return json.dumps({"articles": articles, "count": len(articles)})

    except Exception as exc:
        return json.dumps({"error": str(exc), "articles": []})


if __name__ == "__main__":
    mcp.run()
