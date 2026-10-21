"""
FastAPI backend for the production AI SaaS — Week 1 (Vercel → AWS track).

This is the minimum viable backend a Vercel-hosted Next.js frontend talks to:
- a chat endpoint that streams tokens,
- a /healthz probe, and
- CORS configured for the production frontend domain only.

The course teaches the deployment half in Week 2 of this track; this file is
the surface that gets deployed. It deliberately has *no* auth here —
production auth is added in Week 2 via Clerk on the frontend + a JWT verifier
on the backend. Putting a placeholder auth here is the most common Week 1 bug.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------


class Settings(BaseSettings):
    """Loaded from environment, .env.example documents the keys.

    Order of precedence (highest first):
      1. process environment
      2. .env file
      3. defaults below

    `model_config` is what tells pydantic-settings to load .env. The
    `extra="ignore"` is load-bearing: missing keys from a partially-provisioned
    environment would otherwise fail validation at startup.
    """

    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5-mini", alias="OPENAI_MODEL")
    allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        alias="ALLOWED_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()  # type: ignore[call-arg]


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Single-turn chat request body.

    `messages` mirrors the OpenAI wire format: alternating user/assistant.
    Field naming is camelCase deliberately — the frontend typescript expects
    exactly these keys. A `snake_case` rename here is the second-most-common
    Week 1 bug.
    """

    messages: list[dict[str, str]] = Field(min_length=1)


# --------------------------------------------------------------------------
# App factory
# --------------------------------------------------------------------------


app = FastAPI(
    title="AI Engineer Production — Backend",
    version="0.1.0",
    description="FastAPI backend deployed first to Vercel, then migrated to AWS.",
)

# Narrow CORS. Wildcards here defeat any future credentialed requests and
# are the single most common production-misconfiguration in student code.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


client = AsyncOpenAI(api_key=settings.openai_api_key)


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Cheap liveness probe. Returns the same shape on every call."""
    return {"status": "ok"}


async def _stream_chat(req: ChatRequest) -> AsyncIterator[bytes]:
    """Yield SSE-style chunks for the OpenAI response.

    We use Server-Sent Events rather than raw streaming JSON because:
      - it survives proxies (Vercel, CloudFront, App Runner) that buffer responses,
      - it lets the frontend start painting after token 1, and
      - it survives reconnects without re-running the model call.

    The OpenAI stream returns ChatCompletionChunk objects; the only field that
    matters is `choices[0].delta.content` — empty deltas are filtered out
    because they fire for role markers and tool calls, not real text.
    """
    stream = await client.chat.completions.create(
        model=settings.openai_model,
        messages=req.messages,  # type: ignore[arg-type]
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            # SSE format: each data line ends with two newlines.
            yield f"data: {delta}\n\n".encode("utf-8")
    yield b"data: [DONE]\n\n"


@app.post("/chat")
async def chat(
    req: ChatRequest,
    _: Annotated[str | None, Header()] = None,
) -> StreamingResponse:
    """Stream a chat completion back as Server-Sent Events.

    The `Accept: text/event-stream` header check happens in the upstream
    Edge (Vercel) or API Gateway (AWS), not here — keeping that out of this
    file is intentional so the same handler serves both deployments.
    """
    return StreamingResponse(
        _stream_chat(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disables nginx buffering if proxied
        },
    )


# --------------------------------------------------------------------------
# Order-of-registration note
# --------------------------------------------------------------------------
#
# This file is small enough that route ordering doesn't matter yet. Once
# you add a custom 404 handler or a global middleware that intercepts
# `/chat`, register those LAST or they'll swallow your real routes. See
# ai-coder-coding-agents/.../notes/context-strategy.md §5 for the canonical
# example of the bug.
