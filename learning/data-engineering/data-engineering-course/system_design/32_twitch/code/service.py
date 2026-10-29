"""Twitch-style live streaming + chat service.

This is the *core* of the system — the HTTP layer in `app.py` is a
thin wrapper around it. The class implements:

  * Stream lifecycle: start, end, fetch metadata.
  * Per-stream chat: post, fetch, and an in-process pub/sub
    subscription mechanism used to drive the SSE endpoint.
  * Live viewer count: tracked via heartbeat. A viewer is
    considered live if they posted a heartbeat in the last
    `HEARTBEAT_TIMEOUT_S` seconds. The count decays as viewers
    drop their heartbeat.
  * Game directory listing (`/api/streams?game=...`).
  * In-memory persistence via KeyValueStore (streams, chat log)
    and TTLCache (chat subscribe connections + viewer heartbeat
    timestamps).

The video *bytes* path is out of scope — the same CDN/edge story
from the YouTube/Netflix lesson applies. The interesting design
question for Twitch is the **chat fanout**: how do you deliver a
chat message to 100 K concurrent subscribers in well under a second,
across many shards.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field, asdict
from threading import RLock
from typing import Optional

from common.cache import TTLCache
from common.ids import Snowflake
from common.storage import KeyValueStore

# How long a viewer's heartbeat stays fresh (seconds). A viewer
# is "live" if their last heartbeat was within this window.
HEARTBEAT_TIMEOUT_S = 30.0

# Cap on the persisted chat log we keep per stream.
MAX_CHAT_LOG = 10_000

# Cap on the number of subscribers per stream we hold in memory.
# At ~100 bytes per queue subscriber, 50 K subscribers ≈ 5 MB.
MAX_SUBSCRIBERS_PER_STREAM = 50_000


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass
class User:
    user_id: int
    name: str
    created_at: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Stream:
    stream_id: int
    user_id: int  # the broadcaster
    title: str
    game: str
    created_at: float
    ended_at: Optional[float] = None
    live: bool = True
    peak_viewers: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ChatMessage:
    msg_id: int
    stream_id: int
    user_id: int
    body: str
    created_at: float

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class TwitchService:
    """A working Twitch-style live-streaming + chat service.

    >>> svc = TwitchService()
    >>> u = svc.create_user("alice")
    >>> s = svc.start_stream(u.user_id, "playing zelda", "zelda")
    >>> s.stream_id > 0
    True
    >>> m = svc.post_chat(s.stream_id, u.user_id, "hi chat")
    >>> m.body
    'hi chat'
    """

    def __init__(
        self,
        store: Optional[KeyValueStore] = None,
        cache: Optional[TTLCache] = None,
        id_gen: Optional[Snowflake] = None,
        heartbeat_timeout_s: float = HEARTBEAT_TIMEOUT_S,
    ):
        self.store = store or KeyValueStore("twitch_service")
        self.cache = cache or TTLCache(
            ttl_seconds=heartbeat_timeout_s * 2,
            max_entries=100_000,
        )
        self.id_gen = id_gen or Snowflake(machine_id=32)
        self.heartbeat_timeout_s = heartbeat_timeout_s

        # Per-stream in-process subscriber queues for SSE fanout.
        # Each subscriber is a (id, queue.Queue) tuple. The id is
        # used to unsubscribe cleanly.
        self._subscribers: dict[int, dict[str, "queue.Queue"]] = {}
        # Live viewer heartbeats: stream_id -> {viewer_id: ts}
        self._viewers: dict[int, dict[int, float]] = {}
        # Capped per-stream chat log (deque of dict).
        self._chat_logs: dict[int, deque] = {}

        self._lock = RLock()

    # ---- users ---------------------------------------------------------

    def create_user(self, name: str) -> User:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        user = User(
            user_id=self.id_gen.next_id(),
            name=name.strip(),
            created_at=time.time(),
        )
        self.store.set(self._k_user(user.user_id), user.to_dict())
        return user

    def get_user(self, user_id: int) -> Optional[User]:
        data = self.store.get(self._k_user(user_id))
        return User(**data) if data else None

    # ---- stream lifecycle ---------------------------------------------

    def start_stream(
        self, user_id: int, title: str, game: str
    ) -> Stream:
        """Start a new live stream."""
        if not isinstance(title, str) or not title.strip():
            raise ValueError("title must be a non-empty string")
        if not isinstance(game, str) or not game.strip():
            raise ValueError("game must be a non-empty string")
        if not self.store.exists(self._k_user(user_id)):
            raise ValueError(f"unknown user_id {user_id}")

        stream_id = self.id_gen.next_id()
        stream = Stream(
            stream_id=stream_id,
            user_id=user_id,
            title=title.strip(),
            game=game.strip().lower(),
            created_at=time.time(),
            ended_at=None,
            live=True,
            peak_viewers=0,
        )
        self._persist_stream(stream)
        return stream

    def end_stream(self, stream_id: int) -> Optional[Stream]:
        """End a live stream. Returns the updated record or None."""
        stream = self.get_stream(stream_id)
        if stream is None:
            return None
        with self._lock:
            stream.live = False
            stream.ended_at = time.time()
        self._persist_stream(stream)
        # Close all subscriber queues for this stream.
        self._close_subscribers(stream_id)
        return stream

    def get_stream(self, stream_id: int) -> Optional[Stream]:
        data = self.store.get(self._k_stream(stream_id))
        return Stream(**data) if data else None

    def list_streams(
        self, game: Optional[str] = None, live_only: bool = True
    ) -> list[Stream]:
        """List streams, optionally filtered by game and live state."""
        out: list[Stream] = []
        for k, data in self.store.scan("stream:"):
            if not k.startswith("stream:") or not isinstance(data, dict):
                continue
            try:
                s = Stream(**data)
            except TypeError:
                continue
            if live_only and not s.live:
                continue
            if (
                game is not None
                and s.game.lower() != game.strip().lower()
            ):
                continue
            out.append(s)
        out.sort(key=lambda s: s.created_at, reverse=True)
        return out

    # ---- chat ----------------------------------------------------------

    def post_chat(
        self, stream_id: int, user_id: int, body: str
    ) -> ChatMessage:
        """Post a chat message to a stream and fan out to subscribers."""
        if not isinstance(body, str) or not body.strip():
            raise ValueError("body must be a non-empty string")
        if len(body) > 500:
            raise ValueError("body must be 500 chars or fewer")
        if not self.store.exists(self._k_user(user_id)):
            raise ValueError(f"unknown user_id {user_id}")
        stream = self.get_stream(stream_id)
        if stream is None:
            raise ValueError(f"unknown stream_id {stream_id}")
        if not stream.live:
            raise ValueError("cannot chat: stream is not live")

        msg = ChatMessage(
            msg_id=self.id_gen.next_id(),
            stream_id=stream_id,
            user_id=user_id,
            body=body.strip(),
            created_at=time.time(),
        )
        # Persist a capped log.
        with self._lock:
            log = self._chat_logs.setdefault(
                stream_id, deque(maxlen=MAX_CHAT_LOG)
            )
            log.append(msg.to_dict())
        # Fan out to in-process subscribers.
        self._fanout(stream_id, msg)
        return msg

    def get_chat_log(
        self, stream_id: int, limit: int = 100
    ) -> list[dict]:
        """Return the most recent chat messages for a stream."""
        with self._lock:
            log = list(self._chat_logs.get(stream_id, ()))
        if not log:
            # Cold cache → try to rebuild from store (here we keep
            # the log in memory; in production this would be
            # Cassandra / ScyllaDB).
            return []
        if limit <= 0:
            return []
        return log[-limit:]

    def subscribe(self, stream_id: int) -> tuple[str, "queue.Queue"]:
        """Subscribe to a stream's chat fanout.

        Returns ``(subscription_id, queue)``. The caller pulls
        messages off the queue (SSE). They MUST call
        ``unsubscribe(stream_id, subscription_id)`` to release the
        slot.
        """
        import queue

        sub_id = uuid.uuid4().hex
        q: "queue.Queue" = queue.Queue(maxsize=1000)
        with self._lock:
            subs = self._subscribers.setdefault(stream_id, {})
            # Bound subscribers to keep memory predictable.
            if len(subs) >= MAX_SUBSCRIBERS_PER_STREAM:
                raise RuntimeError(
                    f"stream {stream_id} subscriber limit reached"
                )
            subs[sub_id] = q
        return sub_id, q

    def unsubscribe(self, stream_id: int, sub_id: str) -> None:
        with self._lock:
            subs = self._subscribers.get(stream_id)
            if subs and sub_id in subs:
                del subs[sub_id]

    def _fanout(self, stream_id: int, msg: ChatMessage) -> None:
        """Push a chat message to all in-process subscribers."""
        import queue

        with self._lock:
            subs = dict(self._subscribers.get(stream_id, {}))
        payload = msg.to_dict()
        for sub_id, q in subs.items():
            try:
                q.put_nowait(payload)
            except queue.Full:
                # Slow consumer — drop the message for that
                # subscriber rather than block the producer.
                pass

    def _close_subscribers(self, stream_id: int) -> None:
        with self._lock:
            subs = self._subscribers.pop(stream_id, None)
        if not subs:
            return
        # Send a sentinel to wake up SSE handlers.
        for q in subs.values():
            try:
                q.put_nowait({"__end__": True})
            except Exception:
                pass

    # ---- viewer count via heartbeat ----------------------------------

    def heartbeat(
        self, stream_id: int, viewer_id: int
    ) -> dict:
        """Record a viewer's heartbeat; returns current viewer count."""
        if not self.store.exists(self._k_user(viewer_id)):
            raise ValueError(f"unknown viewer_id {viewer_id}")
        stream = self.get_stream(stream_id)
        if stream is None:
            raise ValueError(f"unknown stream_id {stream_id}")
        if not stream.live:
            raise ValueError("stream is not live")
        now = time.time()
        with self._lock:
            viewers = self._viewers.setdefault(stream_id, {})
            viewers[viewer_id] = now
            self._evict_stale_viewers(viewers, now)
            count = len(viewers)
            if count > stream.peak_viewers:
                stream.peak_viewers = count
                self._persist_stream(stream)
        return {
            "stream_id": stream_id,
            "viewer_id": viewer_id,
            "viewers": count,
            "peak_viewers": stream.peak_viewers,
            "ts": now,
        }

    def viewer_count(self, stream_id: int) -> int:
        """Return the current live viewer count for a stream."""
        with self._lock:
            viewers = self._viewers.get(stream_id, {})
            self._evict_stale_viewers(viewers, time.time())
            return len(viewers)

    def _evict_stale_viewers(
        self, viewers: dict[int, float], now: float
    ) -> None:
        cutoff = now - self.heartbeat_timeout_s
        stale = [vid for vid, ts in viewers.items() if ts < cutoff]
        for vid in stale:
            viewers.pop(vid, None)

    # ---- stats / internals --------------------------------------------

    def total_streams(self) -> int:
        return sum(
            1 for k, _ in self.store.scan("stream:")
            if k.startswith("stream:")
        )

    def live_streams(self) -> int:
        return sum(
            1
            for k, d in self.store.scan("stream:")
            if k.startswith("stream:")
            and isinstance(d, dict)
            and d.get("live", False)
        )

    def cache_stats(self) -> dict:
        return self.cache.stats()

    def subscriber_count(self, stream_id: int) -> int:
        with self._lock:
            return len(self._subscribers.get(stream_id, {}))

    # ---- key naming ---------------------------------------------------

    @staticmethod
    def _k_user(uid: int) -> str:
        return f"user:{uid}"

    @staticmethod
    def _k_stream(sid: int) -> str:
        return f"stream:{sid}"

    def _persist_stream(self, stream: Stream) -> None:
        self.store.set(self._k_stream(stream.stream_id), stream.to_dict())
