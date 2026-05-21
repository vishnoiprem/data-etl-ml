"""
Media Engine MCP Server — wraps the Unsplash API to expose royalty-free image
search as tools.

Run standalone:  python mcp-servers/media/server.py
Agents connect via stdio transport.

Fallback: when UNSPLASH_ACCESS_KEY is absent, returns placeholder Picsum URLs
so the rest of the pipeline still works.
"""

import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(Path(__file__).parent.parent.parent / ".env")

UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")
UNSPLASH_BASE = "https://api.unsplash.com"

mcp = FastMCP("Media Engine Server")


def _placeholder_images(query: str, count: int) -> list[dict]:
    """Generate deterministic placeholder images when Unsplash is unavailable."""
    return [
        {
            "url": f"https://picsum.photos/seed/{query.replace(' ', '_')}_{i}/800/500",
            "thumb": f"https://picsum.photos/seed/{query.replace(' ', '_')}_{i}/400/250",
            "description": f"Image {i + 1} for: {query}",
            "photographer": "Lorem Picsum",
            "source": "placeholder",
        }
        for i in range(count)
    ]


@mcp.tool()
async def search_images(query: str, count: int = 3) -> str:
    """Search for high-quality images related to a query term.

    Args:
        query: Search term, e.g. 'climate change', 'stock market'.
        count: Number of images to return (max 6).

    Returns:
        JSON string with a list of image objects (url, thumb, description,
        photographer).
    """
    count = max(1, min(count, 6))

    if not UNSPLASH_KEY:
        photos = _placeholder_images(query, count)
        return json.dumps({"images": photos, "source": "placeholder"})

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{UNSPLASH_BASE}/search/photos",
                params={
                    "query": query,
                    "per_page": count,
                    "orientation": "landscape",
                    "client_id": UNSPLASH_KEY,
                },
            )
        if r.status_code != 200:
            photos = _placeholder_images(query, count)
            return json.dumps({"images": photos, "source": "placeholder", "api_error": r.text})

        data = r.json()
        photos = [
            {
                "url": p["urls"]["regular"],
                "thumb": p["urls"]["thumb"],
                "description": p.get("alt_description") or p.get("description") or query,
                "photographer": p["user"]["name"],
                "photographer_url": p["user"]["links"]["html"],
                "source": "unsplash",
            }
            for p in data.get("results", [])[:count]
        ]

        if not photos:
            photos = _placeholder_images(query, count)

        return json.dumps({"images": photos, "source": "unsplash" if photos else "placeholder"})

    except Exception as exc:
        photos = _placeholder_images(query, count)
        return json.dumps({"images": photos, "source": "placeholder", "error": str(exc)})


@mcp.tool()
async def get_random_image(topic: str) -> str:
    """Fetch one random image related to a topic.

    Args:
        topic: Topic keyword.

    Returns:
        JSON string with a single image object.
    """
    result = await search_images(topic, 1)
    data = json.loads(result)
    images = data.get("images", [])
    return json.dumps(images[0] if images else {"error": "no image found"})


if __name__ == "__main__":
    mcp.run()
