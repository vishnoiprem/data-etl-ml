"""YouTube / Netflix-style video service.

This module is the *core* of the system — the HTTP layer in `app.py`
is a thin wrapper around it. The class implements:

  * User + video metadata persistence (KeyValueStore).
  * A read-through TTLCache for hot video metadata.
  * View recording with a per-video ring buffer of recent view
    timestamps — this is the data structure the trending query reads.
  * A simple co-watch recommendation engine over the watch history.

The video *bytes* are out of scope here. We model the metadata path
and the structure the transcoder / CDN would consume.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from threading import RLock
from typing import Optional

from common.cache import TTLCache
from common.ids import Snowflake
from common.storage import KeyValueStore

# Sliding window length for "trending" — 60 seconds, in seconds.
TRENDING_WINDOW_SECONDS = 60

# Bucket size for the per-video recent-view deque.
MAX_RECENT_VIEWS = 10_000

# Capped per-user watch history (used by co-watch recommendation).
MAX_WATCH_HISTORY = 500

# Top-K similar users we consider when scoring a recommendation.
RECOMMEND_TOP_USERS = 25


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
class Video:
    video_id: int
    user_id: int
    title: str
    duration_s: int
    created_at: float
    views: int = 0
    renditions: list = field(default_factory=lambda: ["240p", "480p", "720p", "1080p"])
    original_url: str = ""
    comments: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class VideoService:
    """A working video service.

    >>> svc = VideoService()
    >>> u = svc.create_user("alice")
    >>> v = svc.upload_video(u.user_id, "lesson 1", 600)
    >>> v.video_id > 0
    True
    >>> svc.get_video(v.video_id).title
    'lesson 1'
    """

    def __init__(
        self,
        store: Optional[KeyValueStore] = None,
        cache: Optional[TTLCache] = None,
        cache_ttl_seconds: float = 300.0,
        id_gen: Optional[Snowflake] = None,
        window_seconds: int = TRENDING_WINDOW_SECONDS,
    ):
        self.store = store or KeyValueStore("video_service")
        self.cache = cache or TTLCache(
            ttl_seconds=cache_ttl_seconds, max_entries=10_000
        )
        self.cache_ttl = cache_ttl_seconds
        self.id_gen = id_gen or Snowflake(machine_id=6)
        self.window_seconds = window_seconds

        # Per-video ring of recent view timestamps — used by `trending`.
        self._recent_views: dict[int, deque] = defaultdict(deque)
        # Per-user watch history (most recent first, capped).
        self._watch_history: dict[int, deque] = defaultdict(
            lambda: deque(maxlen=MAX_WATCH_HISTORY)
        )

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

    # ---- video upload --------------------------------------------------

    def upload_video(
        self, user_id: int, title: str, duration_s: int
    ) -> Video:
        """Record metadata for a freshly uploaded video.

        The actual bytes flow to S3 / the transcoder in parallel; we
        just persist the metadata here and reserve a stable video_id.
        """
        if not isinstance(title, str) or not title.strip():
            raise ValueError("title must be a non-empty string")
        if not isinstance(duration_s, int) or duration_s <= 0:
            raise ValueError("duration_s must be a positive int")
        if not self.store.exists(self._k_user(user_id)):
            raise ValueError(f"unknown user_id {user_id}")

        video_id = self.id_gen.next_id()
        video = Video(
            video_id=video_id,
            user_id=user_id,
            title=title.strip(),
            duration_s=duration_s,
            created_at=time.time(),
            views=0,
            renditions=["240p", "480p", "720p", "1080p"],
            original_url=f"s3://videos/{video_id}/original.mp4",
            comments=[],
        )
        self._persist_video(video)
        return video

    # ---- reads ---------------------------------------------------------

    def get_video(self, video_id: int) -> Optional[Video]:
        """Read-through cache lookup. Populates the TTLCache on miss."""
        cache_key = self._k_video(video_id)
        cached = self.cache.get(cache_key)
        if cached:
            return Video(**cached)
        data = self.store.get(cache_key)
        if not data:
            return None
        self.cache.set(cache_key, data, self.cache_ttl)
        return Video(**data)

    def add_comment(self, video_id: int, user_id: int, text: str) -> None:
        video = self.get_video(video_id)
        if video is None:
            raise ValueError(f"unknown video_id {video_id}")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")
        video.comments.append(
            {"user_id": user_id, "text": text.strip(), "ts": time.time()}
        )
        self._persist_video(video)

    # ---- views + trending ---------------------------------------------

    def record_view(self, video_id: int, user_id: int) -> Optional[Video]:
        """Record a view of ``video_id`` by ``user_id``.

        Updates the lifetime counter, the in-memory recent-view deque,
        and the user's watch history. Returns the updated video (or
        ``None`` if the video doesn't exist).
        """
        video = self.get_video(video_id)
        if video is None:
            return None

        now = time.time()
        with self._lock:
            # Lifetime counter — the persistent truth.
            video.views += 1
            # Sliding-window deque — the trending signal.
            dq = self._recent_views[video_id]
            cutoff = now - self.window_seconds
            while dq and dq[0] < cutoff:
                dq.popleft()
            dq.append(now)
            if len(dq) > MAX_RECENT_VIEWS:
                # Bound memory; drop the oldest even within the window.
                dq.popleft()
            # Per-user history (capped) — the co-watch signal.
            self._watch_history[user_id].appendleft(video_id)

        self._persist_video(video)
        return video

    def trending(self, limit: int = 10) -> list[tuple[int, int, str]]:
        """Top-``limit`` videos by views in the last ``window_seconds``.

        Returns a list of ``(video_id, views_in_window, title)`` sorted
        descending by the in-window view count.
        """
        if limit <= 0:
            return []
        now = time.time()
        cutoff = now - self.window_seconds

        # Snapshot then score outside the lock — we don't want I/O
        # (get_video) inside the critical section.
        with self._lock:
            counts: list[tuple[int, int]] = []
            for video_id, dq in self._recent_views.items():
                # Drop expired head entries.
                while dq and dq[0] < cutoff:
                    dq.popleft()
                if dq:
                    counts.append((video_id, len(dq)))

        counts.sort(key=lambda x: x[1], reverse=True)
        top = counts[:limit]

        out: list[tuple[int, int, str]] = []
        for video_id, n in top:
            v = self.get_video(video_id)
            if v is None:
                continue
            out.append((video_id, n, v.title))
        return out

    # ---- recommendation ------------------------------------------------

    def recommend(self, user_id: int, limit: int = 10) -> list[tuple[int, str, int]]:
        """Co-watch top-``limit`` for ``user_id``.

        Algorithm:
          1. Take the user's recent watch set W.
          2. For each video in W, walk the watch history of every
             other user who watched it; accumulate similarity weight
             per other user.
          3. Aggregate candidate videos from the top-K similar users,
             scored by sum of similarity weights.
          4. Drop videos already in W; return top-N by score.
        """
        if limit <= 0:
            return []
        with self._lock:
            my_history = list(self._watch_history.get(user_id, ()))
        my_set = set(my_history)
        if not my_set:
            # Cold user: fall back to globally popular videos.
            return self._recommend_cold_start(limit)

        # Step 2: who else watched what I watched?
        similarity: dict[int, int] = defaultdict(int)
        for vid in my_history:
            for other_uid, hist in self._watch_history.items():
                if other_uid == user_id:
                    continue
                if vid in set(hist):  # set() is cheap for small histories
                    similarity[other_uid] += 1

        if not similarity:
            return self._recommend_cold_start(limit)

        # Step 3: aggregate candidate videos.
        top_similar = sorted(
            similarity.items(), key=lambda x: x[1], reverse=True
        )[:RECOMMEND_TOP_USERS]
        scores: dict[int, int] = defaultdict(int)
        for other_uid, weight in top_similar:
            for vid in self._watch_history.get(other_uid, ()):
                if vid in my_set:
                    continue
                scores[vid] += weight

        if not scores:
            return self._recommend_cold_start(limit)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[
            :limit
        ]
        out: list[tuple[int, str, int]] = []
        for video_id, score in ranked:
            v = self.get_video(video_id)
            if v is None:
                continue
            out.append((video_id, v.title, score))
        return out

    def _recommend_cold_start(
        self, limit: int
    ) -> list[tuple[int, str, int]]:
        """No history for this user — fall back to globally popular."""
        if limit <= 0:
            return []
        scored: list[tuple[int, int, str]] = []
        for video_id, dq in self._recent_views.items():
            if not dq:
                continue
            v = self.get_video(video_id)
            if v is None:
                continue
            scored.append((video_id, len(dq), v.title))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [
            (vid, title, n) for vid, n, title in scored[:limit]
        ]

    # ---- stats / internals --------------------------------------------

    def total_videos(self) -> int:
        return sum(
            1 for k, _ in self.store.scan("video:") if k.startswith("video:")
        )

    def cache_stats(self) -> dict:
        return self.cache.stats()

    # ---- key naming ---------------------------------------------------

    @staticmethod
    def _k_user(uid: int) -> str:
        return f"user:{uid}"

    @staticmethod
    def _k_video(vid: int) -> str:
        return f"video:{vid}"

    def _persist_video(self, video: Video) -> None:
        data = video.to_dict()
        self.store.set(self._k_video(video.video_id), data)
        # Invalidate the cache so the next read sees the new views / comments.
        self.cache.set(self._k_video(video.video_id), data, self.cache_ttl)
