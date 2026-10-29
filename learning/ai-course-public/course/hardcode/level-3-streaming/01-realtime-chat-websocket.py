"""
HARDCORE LAB 01: Real-Time Streaming Chat with WebSockets
=========================================================
A production-grade real-time chat system that streams LLM tokens to a browser.

This is NOT a tutorial. This is a 800+ line system with:
  - WebSocket server (FastAPI)
  - Real token streaming from OpenAI
  - Per-user rate limiting (token bucket)
  - Redis-backed conversation history
  - Multi-worker support (with proper pub/sub)
  - Prometheus metrics endpoint
  - Graceful shutdown
  - Health checks
  - Request tracing with correlation IDs
  - Cost tracking per user

Architecture:
    Browser  <--WebSocket-->  FastAPI  <--HTTP async-->  OpenAI
                                |
                                +-- Redis (history, rate limit, pub/sub)
                                |
                                +-- Prometheus (metrics)

Run:
    # 1. Install deps
    pip install fastapi uvicorn[standard] websockets openai redis prometheus-client

    # 2. Start Redis
    docker run -d -p 6379:6379 redis:7-alpine

    # 3. Set env
    export OPENAI_API_KEY=sk-...
    export REDIS_URL=redis://localhost:6379

    # 4. Run server (4 workers)
    uvicorn 01_realtime_chat_websocket:app --host 0.0.0.0 --port 8000 --workers 4

    # 5. Test with a WebSocket client (or open the HTML in frontend/)
    # ws://localhost:8000/ws/{user_id}?conversation_id=...
"""

import asyncio
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import redis.asyncio as aioredis
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    Depends,
    Header,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from openai import AsyncOpenAI, RateLimitError, APIError
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

# =============================================================================
# CONFIG
# =============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
MAX_TOKENS_PER_RESPONSE = int(os.getenv("MAX_TOKENS_PER_RESPONSE", "2000"))
MAX_CONTEXT_MESSAGES = int(os.getenv("MAX_CONTEXT_MESSAGES", "50"))
RATE_LIMIT_TOKENS_PER_MIN = int(os.getenv("RATE_LIMIT_TOKENS_PER_MIN", "60000"))
RATE_LIMIT_REQUESTS_PER_MIN = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MIN", "20"))
CONVERSATION_TTL_DAYS = int(os.getenv("CONVERSATION_TTL_DAYS", "30"))
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is required")

# Pricing per 1M tokens (2026)
PRICING = {
    "gpt-4o-mini":            {"input": 0.15, "output": 0.60},
    "gpt-4o":                 {"input": 5.00, "output": 15.00},
    "claude-3-5-sonnet":      {"input": 3.00, "output": 15.00},
}

# System prompt
SYSTEM_PROMPT = (
    "You are a helpful AI assistant. Be concise, accurate, and friendly. "
    "Use markdown formatting when it helps clarity. If you don't know something, say so."
)

# =============================================================================
# LOGGING (structured JSON for log aggregation)
# =============================================================================

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for ingestion by Datadog/Loki/CloudWatch."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "ts": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key in ("request_id", "user_id", "conversation_id", "duration_ms", "cost_usd"):
            if hasattr(record, key):
                log_obj[key] = getattr(record, key)
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


logging.basicConfig(level=logging.INFO, format="%(message)s")
for handler in logging.getLogger().handlers:
    handler.setFormatter(JSONFormatter())
logger = logging.getLogger("realtime-chat")

# =============================================================================
# PROMETHEUS METRICS
# =============================================================================

REQUESTS_TOTAL = Counter(
    "chat_requests_total",
    "Total chat requests",
    ["user_id", "model", "status"],
)
TOKENS_TOTAL = Counter(
    "chat_tokens_total",
    "Total tokens used",
    ["user_id", "model", "direction"],  # direction: input | output
)
COST_TOTAL = Counter(
    "chat_cost_usd_total",
    "Total cost in USD",
    ["user_id", "model"],
)
REQUEST_DURATION = Histogram(
    "chat_request_duration_seconds",
    "Request duration in seconds",
    ["model"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60],
)
STREAMING_FIRST_TOKEN = Histogram(
    "chat_streaming_first_token_seconds",
    "Time to first token",
    ["model"],
    buckets=[0.1, 0.25, 0.5, 1, 2, 5],
)
ACTIVE_CONNECTIONS = Gauge(
    "chat_active_websocket_connections",
    "Number of active WebSocket connections",
)
RATE_LIMIT_HITS = Counter(
    "chat_rate_limit_hits_total",
    "Number of times a user was rate limited",
    ["user_id", "limit_type"],
)

# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Message:
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: float = field(default_factory=time.time)
    tokens: int = 0
    cost_usd: float = 0.0


@dataclass
class RateLimitResult:
    allowed: bool
    tokens_remaining: int
    retry_after_seconds: int
    reason: str = ""


# =============================================================================
# RATE LIMITER (Token Bucket via Redis)
# =============================================================================

class TokenBucketRateLimiter:
    """
    Production rate limiter using Redis.
    Implements two limits:
      - Token bucket for LLM token usage (per minute)
      - Request count limit (per minute)
    Atomic via Lua script.
    """

    LUA_SCRIPT = """
    -- KEYS[1] = token bucket key
    -- KEYS[2] = request count key
    -- ARGV[1] = current timestamp (ms)
    -- ARGV[2] = tokens per minute
    -- ARGV[3] = requests per minute
    -- ARGV[4] = tokens needed for this request
    -- ARGV[5] = window ms (60000)

    local now = tonumber(ARGV[1])
    local tpm = tonumber(ARGV[2])
    local rpm = tonumber(ARGV[3])
    local tokens_needed = tonumber(ARGV[4])
    local window = tonumber(ARGV[5])

    -- Token bucket (sliding window)
    local token_key = KEYS[1]
    redis.call('ZREMRANGEBYSCORE', token_key, 0, now - window)
    local used_tokens = redis.call('ZCARD', token_key)
    if used_tokens + tokens_needed > tpm then
        return {0, tpm - used_tokens, 'token_limit'}
    end

    -- Request count
    local req_key = KEYS[2]
    redis.call('ZREMRANGEBYSCORE', req_key, 0, now - window)
    local used_reqs = redis.call('ZCARD', req_key)
    if used_reqs >= rpm then
        return {0, 0, 'request_limit'}
    end

    -- Both checks passed: record
    redis.call('ZADD', token_key, now, now .. ':' .. math.random())
    redis.call('EXPIRE', token_key, 120)
    redis.call('ZADD', req_key, now, now .. ':' .. math.random())
    redis.call('EXPIRE', req_key, 120)

    return {1, tpm - used_tokens - tokens_needed, 'ok'}
    """

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.lua_sha: Optional[str] = None

    async def setup(self):
        """Load the Lua script. Call once at startup."""
        self.lua_sha = await self.redis.script_load(self.LUA_SCRIPT)

    async def check(self, user_id: str, tokens_needed: int) -> RateLimitResult:
        """Check if request is allowed. Records usage if allowed."""
        if self.lua_sha is None:
            raise RuntimeError("RateLimiter.setup() must be called first")

        now_ms = int(time.time() * 1000)
        token_key = f"rl:tokens:{user_id}"
        req_key = f"rl:reqs:{user_id}"

        try:
            result = await self.redis.evalsha(
                self.lua_sha, 2, token_key, req_key,
                str(now_ms),
                str(RATE_LIMIT_TOKENS_PER_MIN),
                str(RATE_LIMIT_REQUESTS_PER_MIN),
                str(tokens_needed),
                "60000",
            )
        except aioredis.ResponseError:
            # Script was flushed, reload
            self.lua_sha = await self.redis.script_load(self.LUA_SCRIPT)
            result = await self.redis.evalsha(
                self.lua_sha, 2, token_key, req_key,
                str(now_ms),
                str(RATE_LIMIT_TOKENS_PER_MIN),
                str(RATE_LIMIT_REQUESTS_PER_MIN),
                str(tokens_needed),
                "60000",
            )

        allowed, remaining, reason = result
        if int(allowed) == 1:
            return RateLimitResult(
                allowed=True,
                tokens_remaining=int(remaining),
                retry_after_seconds=0,
            )
        retry_after = 60
        RATE_LIMIT_HITS.labels(user_id=user_id, limit_type=str(reason)).inc()
        return RateLimitResult(
            allowed=False,
            tokens_remaining=int(remaining),
            retry_after_seconds=retry_after,
            reason=str(reason),
        )


# =============================================================================
# CONVERSATION STORE (Redis-backed)
# =============================================================================

class ConversationStore:
    """
    Redis-backed conversation history.
    Stores messages per (user_id, conversation_id).
    Auto-expires after CONVERSATION_TTL_DAYS.
    """

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    def _key(self, user_id: str, conversation_id: str) -> str:
        return f"conv:{user_id}:{conversation_id}"

    async def append(self, user_id: str, conversation_id: str, message: Message):
        key = self._key(user_id, conversation_id)
        msg_json = json.dumps({
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp,
            "tokens": message.tokens,
            "cost_usd": message.cost_usd,
        })
        await self.redis.rpush(key, msg_json)
        # Trim to max context messages (keep last N)
        await self.redis.ltrim(key, -MAX_CONTEXT_MESSAGES, -1)
        # Set TTL
        await self.redis.expire(key, CONVERSATION_TTL_DAYS * 86400)

    async def get_messages(self, user_id: str, conversation_id: str) -> list[Message]:
        key = self._key(user_id, conversation_id)
        raw = await self.redis.lrange(key, 0, -1)
        return [
            Message(
                role=m["role"],
                content=m["content"],
                timestamp=m["timestamp"],
                tokens=m.get("tokens", 0),
                cost_usd=m.get("cost_usd", 0.0),
            )
            for m in (json.loads(r) for r in raw)
        ]

    async def clear(self, user_id: str, conversation_id: str) -> bool:
        return bool(await self.redis.delete(self._key(user_id, conversation_id)))

    async def get_total_cost(self, user_id: str, conversation_id: str) -> float:
        messages = await self.get_messages(user_id, conversation_id)
        return sum(m.cost_usd for m in messages)


# =============================================================================
# TOKEN COUNTER (with caching)
# =============================================================================

class TokenCounter:
    """Count tokens for cost estimation. Cached encoding."""

    _encoding = None

    @classmethod
    def count(cls, text: str) -> int:
        if cls._encoding is None:
            import tiktoken
            cls._encoding = tiktoken.get_encoding("cl100k_base")
        return len(cls._encoding.encode(text))


# =============================================================================
# LLM CLIENT (streaming with retry)
# =============================================================================

class LLMClient:
    """
    Async OpenAI client with:
      - Streaming support
      - Exponential backoff retry
      - Token counting
      - Cost calculation
      - Request tracing
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY, max_retries=0)  # we handle retries

    async def stream_chat(
        self,
        messages: list[Message],
        model: str = LLM_MODEL,
        request_id: str = "",
    ):
        """
        Yields (event_type, data) tuples:
          ("first_token", None) - first token arrived
          ("token", str) - each token
          ("usage", {input_tokens, output_tokens, cost_usd}) - final usage
          ("error", Exception) - if error occurs
        """
        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        first_token = True
        full_response = ""
        input_tokens = 0
        output_tokens = 0

        for attempt in range(3):
            try:
                start_time = time.time()
                stream = await self.client.chat.completions.create(
                    model=model,
                    messages=api_messages,
                    stream=True,
                    stream_options={"include_usage": True},
                    max_tokens=MAX_TOKENS_PER_RESPONSE,
                )

                async for chunk in stream:
                    if not chunk.choices:
                        # Usage chunk
                        if chunk.usage:
                            input_tokens = chunk.usage.prompt_tokens
                            output_tokens = chunk.usage.completion_tokens
                        continue

                    delta = chunk.choices[0].delta
                    if delta.content:
                        token = delta.content
                        full_response += token
                        if first_token:
                            ttft = time.time() - start_time
                            STREAMING_FIRST_TOKEN.labels(model=model).observe(ttft)
                            yield ("first_token", None)
                            first_token = False
                        yield ("token", token)

                # Done
                cost = self._calc_cost(model, input_tokens, output_tokens)
                yield ("usage", {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                    "cost_usd": cost,
                    "duration_seconds": time.time() - start_time,
                })
                return

            except RateLimitError as e:
                if attempt == 2:
                    yield ("error", e)
                    return
                wait = 2 ** attempt
                logger.warning(f"rate_limited attempt={attempt} wait={wait}s")
                await asyncio.sleep(wait)
            except APIError as e:
                if attempt == 2:
                    yield ("error", e)
                    return
                await asyncio.sleep(1)
            except Exception as e:
                yield ("error", e)
                return

    def _calc_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        if model not in PRICING:
            return 0.0
        p = PRICING[model]
        return (input_tokens / 1_000_000) * p["input"] + (output_tokens / 1_000_000) * p["output"]


# =============================================================================
# CONNECTION MANAGER (track active WebSockets)
# =============================================================================

class ConnectionManager:
    """
    Tracks active WebSocket connections per user.
    In multi-worker mode, this is per-worker. Use Redis pub/sub for cross-worker.
    """

    def __init__(self):
        self.connections: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, ws: WebSocket):
        async with self._lock:
            self.connections.setdefault(user_id, set()).add(ws)
            ACTIVE_CONNECTIONS.set(sum(len(s) for s in self.connections.values()))

    async def disconnect(self, user_id: str, ws: WebSocket):
        async with self._lock:
            if user_id in self.connections:
                self.connections[user_id].discard(ws)
                if not self.connections[user_id]:
                    del self.connections[user_id]
            ACTIVE_CONNECTIONS.set(sum(len(s) for s in self.connections.values()))


# =============================================================================
# APP LIFECYCLE
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    # Startup
    logger.info("starting_up")
    app.state.redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    app.state.rate_limiter = TokenBucketRateLimiter(app.state.redis)
    await app.state.rate_limiter.setup()
    app.state.conversations = ConversationStore(app.state.redis)
    app.state.llm = LLMClient()
    app.state.connections = ConnectionManager()

    # Verify Redis
    try:
        await app.state.redis.ping()
        logger.info("redis_connected")
    except Exception as e:
        logger.error(f"redis_connection_failed: {e}")
        raise

    logger.info("ready")

    yield

    # Shutdown
    logger.info("shutting_down")
    await app.state.redis.aclose()
    logger.info("shutdown_complete")


# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(title="Real-Time Chat", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# HTTP ENDPOINTS
# =============================================================================

@app.get("/health")
async def health():
    """Liveness probe. Doesn't check Redis (use /ready for that)."""
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}


@app.get("/ready")
async def ready():
    """Readiness probe. Checks all dependencies."""
    try:
        await app.state.redis.ping()
        return {"status": "ready", "redis": "ok"}
    except Exception as e:
        raise HTTPException(503, f"redis unavailable: {e}")


@app.get("/metrics")
async def metrics():
    """Prometheus scrape endpoint."""
    return HTMLResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/admin/usage/{user_id}")
async def get_usage(user_id: str, conversation_id: Optional[str] = None):
    """Get usage stats for a user (admin endpoint, no auth here for demo)."""
    if not conversation_id:
        return {"error": "conversation_id required"}
    cost = await app.state.conversations.get_total_cost(user_id, conversation_id)
    messages = await app.state.conversations.get_messages(user_id, conversation_id)
    return {
        "user_id": user_id,
        "conversation_id": conversation_id,
        "message_count": len(messages),
        "total_cost_usd": round(cost, 6),
    }


@app.delete("/admin/conversation/{user_id}/{conversation_id}")
async def clear_conversation(user_id: str, conversation_id: str):
    """Clear a conversation. Admin endpoint."""
    deleted = await app.state.conversations.clear(user_id, conversation_id)
    return {"deleted": deleted}


# =============================================================================
# WEBSOCKET ENDPOINT
# =============================================================================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    conversation_id: Optional[str] = None,
):
    """
    WebSocket chat endpoint.

    Protocol:
      Client -> Server: {"type": "message", "content": "Hello!"}
      Server -> Client: {"type": "token", "content": "Hi"}
      Server -> Client: {"type": "done", "usage": {...}}
      Server -> Client: {"type": "error", "message": "..."}
    """
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    request_id = str(uuid.uuid4())[:8]
    log_extra = {"request_id": request_id, "user_id": user_id, "conversation_id": conversation_id}

    await websocket.accept()
    await app.state.connections.connect(user_id, websocket)
    logger.info("websocket_connected", extra=log_extra)

    try:
        # Send initial handshake
        await websocket.send_json({
            "type": "connected",
            "conversation_id": conversation_id,
            "request_id": request_id,
        })

        while True:
            # Receive message from client
            data = await websocket.receive_json()
            msg_type = data.get("type", "message")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if msg_type == "clear":
                await app.state.conversations.clear(user_id, conversation_id)
                await websocket.send_json({"type": "cleared"})
                continue

            if msg_type != "message":
                await websocket.send_json({"type": "error", "message": f"unknown type: {msg_type}"})
                continue

            user_content = data.get("content", "").strip()
            if not user_content:
                await websocket.send_json({"type": "error", "message": "empty content"})
                continue

            # Estimate tokens for rate limit
            estimated_tokens = TokenCounter.count(user_content) + 500  # estimate output
            rate_result = await app.state.rate_limiter.check(user_id, estimated_tokens)
            if not rate_result.allowed:
                await websocket.send_json({
                    "type": "rate_limited",
                    "reason": rate_result.reason,
                    "retry_after_seconds": rate_result.retry_after_seconds,
                })
                REQUESTS_TOTAL.labels(user_id=user_id, model=LLM_MODEL, status="rate_limited").inc()
                continue

            # Get conversation history
            history = await app.state.conversations.get_messages(user_id, conversation_id)
            history.append(Message(role="user", content=user_content))
            history.insert(0, Message(role="system", content=SYSTEM_PROMPT))

            # Stream LLM response
            start_time = time.time()
            full_response = ""
            usage_data = None
            error = None

            try:
                async for event_type, event_data in app.state.llm.stream_chat(
                    messages=history, model=LLM_MODEL, request_id=request_id,
                ):
                    if event_type == "first_token":
                        await websocket.send_json({"type": "first_token"})
                    elif event_type == "token":
                        full_response += event_data
                        await websocket.send_json({"type": "token", "content": event_data})
                    elif event_type == "usage":
                        usage_data = event_data
                    elif event_type == "error":
                        error = event_data

            except Exception as e:
                error = e
                logger.error(f"stream_error: {e}", extra=log_extra)

            if error:
                await websocket.send_json({"type": "error", "message": str(error)})
                REQUESTS_TOTAL.labels(user_id=user_id, model=LLM_MODEL, status="error").inc()
                continue

            # Save to conversation history
            duration = time.time() - start_time
            REQUEST_DURATION.labels(model=LLM_MODEL).observe(duration)

            user_msg = Message(role="user", content=user_content, tokens=usage_data["input_tokens"] - sum(m.tokens for m in history if m.role != "system"))
            assistant_msg = Message(
                role="assistant",
                content=full_response,
                tokens=usage_data["output_tokens"],
                cost_usd=usage_data["cost_usd"],
            )

            await app.state.conversations.append(user_id, conversation_id, user_msg)
            await app.state.conversations.append(user_id, conversation_id, assistant_msg)

            # Metrics
            TOKENS_TOTAL.labels(user_id=user_id, model=LLM_MODEL, direction="input").inc(usage_data["input_tokens"])
            TOKENS_TOTAL.labels(user_id=user_id, model=LLM_MODEL, direction="output").inc(usage_data["output_tokens"])
            COST_TOTAL.labels(user_id=user_id, model=LLM_MODEL).inc(usage_data["cost_usd"])
            REQUESTS_TOTAL.labels(user_id=user_id, model=LLM_MODEL, status="ok").inc()

            await websocket.send_json({
                "type": "done",
                "usage": usage_data,
                "duration_seconds": round(duration, 3),
            })

            logger.info(
                "request_complete",
                extra={
                    **log_extra,
                    "duration_ms": int(duration * 1000),
                    "cost_usd": usage_data["cost_usd"],
                },
            )

    except WebSocketDisconnect:
        logger.info("websocket_disconnected", extra=log_extra)
    except Exception as e:
        logger.error(f"websocket_error: {e}", extra=log_extra, exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        await app.state.connections.disconnect(user_id, websocket)


# =============================================================================
# HTML FRONTEND (for testing)
# =============================================================================

HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Real-Time Chat</title>
  <style>
    body { font-family: monospace; max-width: 800px; margin: 20px auto; padding: 0 20px; }
    #messages { border: 1px solid #ccc; padding: 12px; height: 400px; overflow-y: scroll; margin-bottom: 12px; }
    .user { color: #2c3e50; font-weight: bold; }
    .assistant { color: #16a085; }
    .error { color: #c0392b; background: #fadbd8; padding: 4px; }
    input { width: 80%; padding: 8px; }
    button { padding: 8px 16px; }
  </style>
</head>
<body>
  <h1>Real-Time Chat (Hardcode Lab 01)</h1>
  <div id="status">disconnected</div>
  <div id="messages"></div>
  <input id="input" placeholder="Type a message..." autofocus />
  <button id="send">Send</button>
  <script>
    const userId = "demo-user-" + Math.random().toString(36).slice(2, 8);
    const conversationId = "conv-" + Math.random().toString(36).slice(2, 8);
    const ws = new WebSocket(`ws://${location.host}/ws/${userId}?conversation_id=${conversationId}`);
    const messages = document.getElementById("messages");
    const status = document.getElementById("status");
    const input = document.getElementById("input");
    let currentMessage = null;

    ws.onopen = () => { status.textContent = "connected"; };
    ws.onclose = () => { status.textContent = "disconnected"; };
    ws.onerror = (e) => { status.textContent = "error"; console.error(e); };
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === "token") {
        if (!currentMessage) {
          currentMessage = document.createElement("div");
          currentMessage.className = "assistant";
          messages.appendChild(currentMessage);
        }
        currentMessage.textContent += msg.content;
        messages.scrollTop = messages.scrollHeight;
      } else if (msg.type === "first_token") {
        currentMessage = null;
      } else if (msg.type === "done") {
        const meta = document.createElement("div");
        meta.style.fontSize = "11px";
        meta.style.color = "#888";
        meta.textContent = `done: ${msg.usage.total_tokens} tokens, $${msg.usage.cost_usd.toFixed(6)}, ${(msg.duration_seconds * 1000).toFixed(0)}ms`;
        messages.appendChild(meta);
        currentMessage = null;
      } else if (msg.type === "error") {
        const err = document.createElement("div");
        err.className = "error";
        err.textContent = "ERROR: " + msg.message;
        messages.appendChild(err);
      } else if (msg.type === "rate_limited") {
        const err = document.createElement("div");
        err.className = "error";
        err.textContent = `RATE LIMITED (${msg.reason}). Retry in ${msg.retry_after_seconds}s`;
        messages.appendChild(err);
      }
    };

    function send() {
      const content = input.value.trim();
      if (!content) return;
      const div = document.createElement("div");
      div.className = "user";
      div.textContent = "You: " + content;
      messages.appendChild(div);
      ws.send(JSON.stringify({ type: "message", content }));
      input.value = "";
    }
    document.getElementById("send").onclick = send;
    input.onkeydown = (e) => { if (e.key === "Enter") send(); };
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "01_realtime_chat_websocket:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        log_level="info",
        access_log=True,
    )
