"""Streaming client for any OpenAI-compatible chat endpoint (Ollama, Groq,
OpenRouter, Gemini's OpenAI mode, vLLM, ...).

The model never searches or decides facts here: it only re-explains evidence
that retrieval + the grounded answerer already produced, and its output is
verified (see explain.py) before the UI keeps it.
"""
from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from .settings import Settings


class LLMError(RuntimeError):
    pass


def is_configured(s: Settings) -> bool:
    return bool(s.model_gateway_url.strip())


async def stream_chat(messages: list[dict], s: Settings,
                      transport: httpx.AsyncBaseTransport | None = None) -> AsyncIterator[str]:
    """Yield content deltas. Raises LLMError on any transport/protocol failure."""
    url = s.model_gateway_url.rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json"}
    if s.model_gateway_key:
        headers["Authorization"] = f"Bearer {s.model_gateway_key}"
    body = {
        "model": s.model_name, "messages": messages, "stream": True,
        "temperature": 0.1, "max_tokens": s.model_max_tokens,
    }
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(s.model_timeout_s, connect=5.0), transport=transport
        ) as client:
            async with client.stream("POST", url, json=body, headers=headers) as r:
                if r.status_code != 200:
                    detail = (await r.aread()).decode(errors="replace")[:200]
                    raise LLMError(f"model endpoint returned {r.status_code}: {detail}")
                async for line in r.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        return
                    try:
                        delta = json.loads(data)["choices"][0].get("delta", {}).get("content")
                    except (ValueError, KeyError, IndexError, TypeError):
                        continue
                    if delta:
                        yield delta
    except httpx.HTTPError as e:
        raise LLMError(f"cannot reach the model at {s.model_gateway_url}: {e.__class__.__name__}") from e
