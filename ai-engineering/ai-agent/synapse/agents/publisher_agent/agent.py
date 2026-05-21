"""
Publisher Agent

Converts a ScoutResponse (raw signals) into a polished Markdown article using
the Anthropic Claude API.  The agent builds a structured prompt from every
available signal and streams the result back via the messages API.
"""

import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import anthropic
from dotenv import load_dotenv

_ROOT = Path(__file__).parent.parent.parent
load_dotenv(_ROOT / ".env")
sys.path.insert(0, str(_ROOT))

from protocol.a2a import BaseAgent, Message, bus
from protocol.messages import PublishRequest, PublishResponse, ScoutResponse, Signal

DEFAULT_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-7")


def _format_news(signal: Optional[Signal]) -> str:
    if not signal or signal.error:
        return "No news data available."
    articles = signal.data.get("articles", [])
    if not articles:
        return "No news articles found."
    lines = []
    for i, a in enumerate(articles[:5], 1):
        title = a.get("title", "Untitled")
        source = a.get("source", "Unknown")
        desc = a.get("description", "")
        pub = a.get("published_at", "")[:10]
        lines.append(f"{i}. **{title}** ({source}, {pub})\n   {desc}")
    return "\n".join(lines)


def _format_weather(signal: Optional[Signal]) -> str:
    if not signal or signal.error:
        return "Weather data unavailable."
    d = signal.data
    if "error" in d:
        return f"Weather error: {d['error']}"
    return (
        f"**{d.get('city', '')}**, {d.get('country', '')} — "
        f"{d.get('temperature_c', 'N/A')}°C, {d.get('description', '')}. "
        f"Humidity: {d.get('humidity_pct', 'N/A')}%. "
        f"Wind: {d.get('wind_speed_ms', 'N/A')} m/s."
    )


def _format_finance(signal: Optional[Signal]) -> str:
    if not signal or signal.error:
        return "Market data unavailable."
    lines = []

    indices = signal.data.get("indices", [])
    if indices:
        lines.append("**Major Indices:**")
        for idx in indices:
            change = idx.get("change_pct")
            change_str = f"{change:+.2f}%" if change is not None else "N/A"
            price = idx.get("price", "N/A")
            lines.append(f"  - {idx['name']}: {price} ({change_str})")

    tickers = signal.data.get("tickers", [])
    if tickers:
        lines.append("**Related Stocks:**")
        for t in tickers:
            change = t.get("change_pct")
            change_str = f"{change:+.2f}%" if change is not None else "N/A"
            lines.append(f"  - {t['symbol']}: ${t.get('price', 'N/A')} ({change_str})")

    return "\n".join(lines) if lines else "No market data."


def _format_images(signal: Optional[Signal]) -> str:
    if not signal or signal.error:
        return "No images found."
    images = signal.data.get("images", [])
    if not images:
        return "No images found."
    descs = [f"- {img.get('description', 'image')} (by {img.get('photographer', 'unknown')})"
             for img in images]
    return "\n".join(descs)


def _build_prompt(scout: ScoutResponse) -> str:
    news_sig = scout.get_signal("news")
    weather_sig = scout.get_signal("weather")
    finance_sig = scout.get_signal("finance")
    media_sig = scout.get_signal("media")

    today = date.today().strftime("%B %d, %Y")

    return f"""You are a world-class journalist writing a daily intelligence brief for a busy professional.

**Assignment details:**
- Topic: {scout.topic}
- City focus: {scout.city}
- Date: {today}

**Contextual data gathered by our scout system:**

## Latest News
{_format_news(news_sig)}

## Weather in {scout.city}
{_format_weather(weather_sig)}

## Financial Markets
{_format_finance(finance_sig)}

## Supporting Images Available
{_format_images(media_sig)}

---

**Your task:** Write a compelling, well-structured daily brief (500–700 words) in Markdown.

Structure it as follows:
1. A punchy **H1 headline** that grabs attention
2. A **dateline** on its own line: *{scout.city} — {today}*
3. An **opening paragraph** that sets the scene and hooks the reader
4. **2–3 body paragraphs** that weave together the news, local conditions, and market context into a coherent narrative
5. A **"Markets at a Glance"** section (bullet list of key index moves)
6. A **forward-looking closing paragraph** with insight or outlook

Guidelines:
- Be factual, balanced, and professional in tone
- Make market data feel relevant to the story — don't just list numbers
- Reference the weather only if contextually meaningful
- Do NOT fabricate facts beyond what is provided
- Format nicely in Markdown (headers, bold, bullet lists where appropriate)
"""


class PublisherAgent(BaseAgent):
    """
    Generates a Markdown article from a ScoutResponse using the Claude API.

    Usage (direct async call)::

        agent = PublisherAgent()
        response = await agent.publish(PublishRequest(scout_response=scout))

    Usage via A2A bus::

        response = await bus.send(Message(
            sender="scout_agent",
            recipient="publisher_agent",
            type="publish_request",
            payload=PublishRequest(scout_response=scout),
        ))
    """

    name = "publisher_agent"

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        super().__init__(bus)
        self.model = model
        self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

    async def publish(self, request: PublishRequest) -> PublishResponse:
        """Generate a Markdown article from the scout's signals."""
        prompt = _build_prompt(request.scout_response)

        message = self._client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )

        article = message.content[0].text if message.content else "Article generation failed."

        return PublishResponse(
            article=article,
            metadata={
                "model": self.model,
                "topic": request.scout_response.topic,
                "city": request.scout_response.city,
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
            },
        )

    async def receive(self, message: Message):
        """A2A bus handler — accepts publish_request messages."""
        if message.type != "publish_request":
            raise ValueError(f"PublisherAgent does not handle message type '{message.type}'")
        request: PublishRequest = message.payload
        return await self.publish(request)
