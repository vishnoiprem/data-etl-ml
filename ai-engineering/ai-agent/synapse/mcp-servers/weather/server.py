"""
Weather MCP Server — wraps OpenWeatherMap to expose current conditions and
short-range forecast as tools.

Run standalone:  python mcp-servers/weather/server.py
Agents connect via stdio transport.
"""

import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(Path(__file__).parent.parent.parent / ".env")

OWM_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OWM_BASE = "https://api.openweathermap.org/data/2.5"

mcp = FastMCP("Weather Server")


@mcp.tool()
async def get_current_weather(city: str) -> str:
    """Fetch current weather conditions for a city.

    Args:
        city: City name, optionally with country code (e.g. 'London,GB').

    Returns:
        JSON string with temperature, description, humidity, wind, etc.
    """
    if not OWM_API_KEY:
        return json.dumps({"error": "OPENWEATHER_API_KEY not configured"})

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{OWM_BASE}/weather",
                params={"q": city, "appid": OWM_API_KEY, "units": "metric"},
            )
        if r.status_code != 200:
            return json.dumps({"error": f"HTTP {r.status_code}: {r.text}"})

        d = r.json()
        result = {
            "city": d.get("name", city),
            "country": d.get("sys", {}).get("country", ""),
            "temperature_c": d.get("main", {}).get("temp"),
            "feels_like_c": d.get("main", {}).get("feels_like"),
            "humidity_pct": d.get("main", {}).get("humidity"),
            "description": d.get("weather", [{}])[0].get("description", ""),
            "wind_speed_ms": d.get("wind", {}).get("speed"),
            "visibility_m": d.get("visibility"),
            "pressure_hpa": d.get("main", {}).get("pressure"),
        }
        return json.dumps(result)

    except Exception as exc:
        return json.dumps({"error": str(exc)})


@mcp.tool()
async def get_forecast(city: str, days: int = 3) -> str:
    """Fetch a short-range weather forecast (3-hour intervals).

    Args:
        city: City name, optionally with country code.
        days: Number of days ahead to include (1–5).

    Returns:
        JSON string with a list of forecast periods.
    """
    if not OWM_API_KEY:
        return json.dumps({"error": "OPENWEATHER_API_KEY not configured", "forecast": []})

    days = max(1, min(days, 5))
    cnt = days * 8  # 8 × 3-hour slots per day

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{OWM_BASE}/forecast",
                params={"q": city, "appid": OWM_API_KEY, "units": "metric", "cnt": cnt},
            )
        if r.status_code != 200:
            return json.dumps({"error": f"HTTP {r.status_code}: {r.text}", "forecast": []})

        data = r.json()
        periods = [
            {
                "datetime": item.get("dt_txt", ""),
                "temperature_c": item.get("main", {}).get("temp"),
                "description": item.get("weather", [{}])[0].get("description", ""),
                "wind_speed_ms": item.get("wind", {}).get("speed"),
                "humidity_pct": item.get("main", {}).get("humidity"),
            }
            for item in data.get("list", [])
        ]
        return json.dumps({"city": city, "forecast": periods})

    except Exception as exc:
        return json.dumps({"error": str(exc), "forecast": []})


if __name__ == "__main__":
    mcp.run()
