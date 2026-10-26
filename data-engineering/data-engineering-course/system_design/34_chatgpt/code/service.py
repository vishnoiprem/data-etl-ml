"""Conversational Chat (à la ChatGPT) — core service.

A conversation-memory chat service with a streaming mock LLM. Real
ChatGPT features modelled here:

    * Conversation = an ordered message log
    * Context window = the last N tokens/messages are sent on every call
    * Streaming = tokens are emitted one at a time (SSE)
    * System prompt = the model's persona / guardrails
    * Per-conversation model selection

The LLM is a deterministic mock. It walks the latest user message,
picks a template, and emits tokens one-by-one. The architecture —
conversations, context window, streaming — is real and runnable.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field, asdict
from typing import Generator, Optional

from common.cache import LRUCache, TTLCache
from common.storage import KeyValueStore


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


SUPPORTED_MODELS = ("gpt-4o-mini", "gpt-4o", "claude-haiku", "mock-fast")
DEFAULT_MODEL = "mock-fast"

# How many of the most recent messages to send to the LLM as context.
DEFAULT_CONTEXT_WINDOW = 8

# Soft cap on characters per message; we trim long messages to keep the
# in-memory context reasonable.
MAX_MESSAGE_CHARS = 4_000


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str
    created_at: float = field(default_factory=lambda: time.time())
    tokens: int = 0  # rough estimate

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Conversation:
    conversation_id: int
    user_id: str
    model: str
    system_prompt: str
    created_at: float = field(default_factory=lambda: time.time())
    messages: list[ChatMessage] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "model": self.model,
            "system_prompt": self.system_prompt,
            "created_at": self.created_at,
            "messages": [m.to_dict() for m in self.messages],
        }


# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------


_WORD_RE = re.compile(r"\S+")


def estimate_tokens(text: str) -> int:
    """Very rough token estimate: 1 token ≈ 0.75 words."""
    if not text:
        return 0
    return max(1, int(len(_WORD_RE.findall(text)) * 1.34))


# ---------------------------------------------------------------------------
# Mock LLM
# ---------------------------------------------------------------------------


_MOCK_OPENERS = (
    "Sure, ",
    "Great question — ",
    "Here's the deal: ",
    "Let me think. ",
    "Absolutely. ",
    "Good catch. ",
)

_MOCK_FILLERS = (
    "the key thing to remember is that this depends on context. ",
    "in practice, you'd typically start by clarifying the goal, then walk through the tradeoffs. ",
    "there's no single right answer, but a reasonable default is to keep things simple and only add complexity when you have evidence you need it. ",
    "the way I'd approach it is to start small, measure, and iterate. ",
    "a few principles tend to hold up well: keep state explicit, write down assumptions, and prefer boring technology. ",
)

_MOCK_CLOSERS = (
    " Want me to go deeper on any of that?",
    " Let me know if you want a code example.",
    " Hope that helps — happy to clarify.",
    " I can also sketch an architecture if that's useful.",
)


def _mock_complete(messages: list[ChatMessage], model: str) -> str:
    """Deterministic mock LLM. Picks a template from message contents."""
    last_user = next((m for m in reversed(messages) if m.role == "user"), None)
    if last_user is None:
        return "(no user message to respond to)"

    text = last_user.content.lower()
    opener = _MOCK_OPENERS[hash(text) % len(_MOCK_OPENERS)]
    closer = _MOCK_CLOSERS[hash(model + text) % len(_MOCK_CLOSERS)]

    # Choose fillers based on which intent keywords show up.
    if any(k in text for k in ("code", "function", "class", "bug", "error", "stacktrace")):
        body = "when you're debugging, isolate the smallest reproducer first, then check the assumptions. "
    elif any(k in text for k in ("design", "architect", "scale", "system")):
        body = _MOCK_FILLERS[0]
    elif any(k in text for k in ("how", "why", "explain", "what is")):
        body = _MOCK_FILLERS[1]
    else:
        body = _MOCK_FILLERS[hash(text) % len(_MOCK_FILLERS)]

    return f"{opener}{body}{closer}"


def stream_tokens(text: str) -> Generator[str, None, None]:
    """Yield a mock LLM's reply one token at a time.

    Tokens are short (words + spaces). This is the function the SSE
    endpoint calls in a loop.
    """
    for tok in re.findall(r"\S+\s*", text):
        yield tok


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ChatService:
    """Conversational chat with a streaming mock LLM.

    >>> svc = ChatService()
    >>> c = svc.create_conversation("u1", "mock-fast")
    >>> m = svc.add_message(c.conversation_id, "user", "hello world")
    >>> reply = svc.complete(c.conversation_id)
    >>> reply.role
    'assistant'
    >>> len(reply.content) > 0
    True
    """

    CACHE_TTL = 30.0  # seconds — small, since the user is in the loop

    def __init__(
        self,
        store: Optional[KeyValueStore] = None,
        cache: Optional[TTLCache] = None,
        context_window: int = DEFAULT_CONTEXT_WINDOW,
    ):
        self.store = store or KeyValueStore("chatgpt")
        self.cache = cache or TTLCache(ttl_seconds=self.CACHE_TTL)
        # Per-conversation LRU of recent completions, used by /stream.
        self._completion_cache: LRUCache = LRUCache(max_entries=512)
        self.context_window = context_window
        self._next_id = self._max_id() + 1

    def _max_id(self) -> int:
        best = 0
        for k, _ in self.store.scan("conv:"):
            try:
                best = max(best, int(k.split(":")[1]))
            except (IndexError, ValueError):
                continue
        return best

    # ---- conversations -------------------------------------------------

    def create_conversation(
        self,
        user_id: str,
        model: str = DEFAULT_MODEL,
        system_prompt: str = "You are a helpful, concise assistant.",
    ) -> Conversation:
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id is required")
        if model not in SUPPORTED_MODELS:
            raise ValueError(
                f"unsupported model '{model}'. supported: {SUPPORTED_MODELS}"
            )
        cid = self._next_id
        self._next_id += 1
        conv = Conversation(
            conversation_id=cid,
            user_id=user_id,
            model=model,
            system_prompt=system_prompt,
        )
        # Persist the system prompt as the first message.
        conv.messages.append(ChatMessage(role="system", content=system_prompt))
        self._persist(conv)
        return conv

    def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        d = self.store.get(f"conv:{conversation_id}")
        if not d:
            return None
        msgs = [ChatMessage(**m) for m in d.get("messages", [])]
        return Conversation(
            conversation_id=d["conversation_id"],
            user_id=d["user_id"],
            model=d["model"],
            system_prompt=d["system_prompt"],
            created_at=d.get("created_at", 0.0),
            messages=msgs,
        )

    def list_conversations(self, user_id: Optional[str] = None) -> list[Conversation]:
        out: list[Conversation] = []
        for k, _ in self.store.scan("conv:"):
            cid = int(k.split(":")[1])
            c = self.get_conversation(cid)
            if c and (user_id is None or c.user_id == user_id):
                out.append(c)
        out.sort(key=lambda c: c.conversation_id)
        return out

    # ---- messages ------------------------------------------------------

    def _trim(self, content: str) -> str:
        if len(content) > MAX_MESSAGE_CHARS:
            return content[:MAX_MESSAGE_CHARS] + "…"
        return content

    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
    ) -> ChatMessage:
        conv = self.get_conversation(conversation_id)
        if not conv:
            raise ValueError("conversation not found")
        if role not in ("user", "assistant", "system"):
            raise ValueError("role must be one of user|assistant|system")
        if not content or not isinstance(content, str):
            raise ValueError("content is required")
        msg = ChatMessage(
            role=role,
            content=self._trim(content),
            tokens=estimate_tokens(content),
        )
        conv.messages.append(msg)
        self._persist(conv)
        return msg

    # ---- completion ----------------------------------------------------

    def _context_messages(self, conv: Conversation) -> list[ChatMessage]:
        """Take the system prompt + the last N messages."""
        if not conv.messages:
            return []
        system = conv.messages[0] if conv.messages[0].role == "system" else None
        rest = conv.messages[1:] if system else conv.messages
        recent = rest[-self.context_window:]
        return ([system] if system else []) + recent

    def complete(self, conversation_id: int) -> ChatMessage:
        """Generate a (non-streamed) reply and append it to the conversation."""
        conv = self.get_conversation(conversation_id)
        if not conv:
            raise ValueError("conversation not found")
        ctx = self._context_messages(conv)
        # Cache key: a digest of context + model.
        cache_key = f"complete:{conv.model}:{hash(tuple((m.role, m.content) for m in ctx))}"
        cached = self._completion_cache.get(cache_key)
        if cached is not None:
            text = cached
        else:
            text = _mock_complete(ctx, conv.model)
            self._completion_cache.set(cache_key, text)
        msg = ChatMessage(role="assistant", content=text, tokens=estimate_tokens(text))
        conv.messages.append(msg)
        self._persist(conv)
        return msg

    def stream(self, conversation_id: int) -> Generator[ChatMessage, None, None]:
        """Yield chunks of the reply as the mock LLM emits tokens.

        Yields full ``ChatMessage`` objects with growing ``content``.
        The HTTP layer (SSE) just serializes each one.
        """
        conv = self.get_conversation(conversation_id)
        if not conv:
            raise ValueError("conversation not found")
        ctx = self._context_messages(conv)
        full_text = _mock_complete(ctx, conv.model)

        accumulated = ""
        final_msg: Optional[ChatMessage] = None
        for tok in stream_tokens(full_text):
            accumulated += tok
            yield ChatMessage(role="assistant", content=accumulated, tokens=estimate_tokens(accumulated))
        # Persist the final reply.
        final_msg = ChatMessage(
            role="assistant",
            content=accumulated,
            tokens=estimate_tokens(accumulated),
        )
        conv.messages.append(final_msg)
        self._persist(conv)

    # ---- stats ---------------------------------------------------------

    def stats(self) -> dict:
        n_conv = sum(1 for _ in self.store.scan("conv:"))
        total_messages = 0
        total_tokens = 0
        for k, _ in self.store.scan("conv:"):
            c = self.get_conversation(int(k.split(":")[1]))
            if c:
                total_messages += len(c.messages)
                total_tokens += sum(m.tokens for m in c.messages)
        return {
            "conversations": n_conv,
            "messages": total_messages,
            "tokens_estimate": total_tokens,
            "context_window": self.context_window,
            "completion_lru": self._completion_cache.stats(),
        }

    # ---- internals -----------------------------------------------------

    def _persist(self, conv: Conversation) -> None:
        self.store.set(f"conv:{conv.conversation_id}", conv.to_dict())
