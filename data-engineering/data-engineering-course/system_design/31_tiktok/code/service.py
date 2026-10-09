"""TikTok-style short-form video service.

This is the *core* of the system — the HTTP layer in `app.py` is a
thin wrapper around it. The class implements:

  * User + video metadata persistence (KeyValueStore).
  * A read-through TTLCache for hot video metadata.
  * View recording with `watch_pct` so the For You ranking can
    weight "completed watches" higher than mere impressions.
  * A For You feed: combine recency, engagement (likes/views /
    average watch time), and a user-affinity score from watch
    history (we model affinity as Jaccard on tag sets).
  * A per-user TTLCache of pre-ranked For You feeds (60s TTL).

The video *bytes* are out of scope here — the same S3/CDN story
from the YouTube/Netflix module applies. The interesting design
question for TikTok is the *ranking* path: how do you take 1 M
candidate videos and return 20 that this specific user is most
likely to watch through to the end.
"""

from __future__ import annotations

import math
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from threading import RLock
from typing import Optional

from common.cache import TTLCache
from common.ids import Snowflake
from common.storage import KeyValueStore

# Sliding window length for the For You engagement signal (seconds).
ENGAGEMENT_WINDOW_SECONDS = 60 * 60 * 24  # 24h

# Capped per-user watch history (used by the affinity signal).
MAX_WATCH_HISTORY = 500

# Number of candidate videos considered before ranking.
FORYOU_CANDIDATE_POOL = 200

# TTL for the per-user For You cache.
FORYOU_CACHE_TTL_SECONDS = 60.0

# Weights for the For You score (see `rank_foryou`).
W_RECENCY = 1.0
W_ENGAGEMENT = 2.0
W_AFFINITY = 3.0


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
    caption: str
    duration_s: int
    tags: list = field(default_factory=list)
    created_at: float = 0.0
    views: int = 0
    likes: int = 0
    total_watch_s: float = 0.0  # accumulated watch_pct * duration_s / 100
    play_count: int = 0  # how many views contributed to total_watch_s
    original_url: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class TikTokService:
    """A working TikTok-style short-form video service.

    >>> svc = TikTokService()
    >>> u = svc.create_user("alice")
    >>> v = svc.post_video(u.user_id, "hi world", 15, tags=["cat", "funny"])
    >>> v.video_id > 0
    True
    >>> svc.get_video(v.video_id).caption
    'hi world'
    """

    def __init__(
        self,
        store: Optional[KeyValueStore] = None,
        cache: Optional[TTLCache] = None,
        foryou_cache: Optional[TTLCache] = None,
        cache_ttl_seconds: float = 300.0,
        foryou_ttl_seconds: float = FORYOU_CACHE_TTL_SECONDS,
        id_gen: Optional[Snowflake] = None,
        candidate_pool: int = FORYOU_CANDIDATE_POOL,
        window_seconds: int = ENGAGEMENT_WINDOW_SECONDS,
    ):
        self.store = store or KeyValueStore("tiktok_service")
        self.cache = cache or TTLCache(
            ttl_seconds=cache_ttl_seconds, max_entries=10_000
        )
        self.foryou_cache = foryou_cache or TTLCache(
            ttl_seconds=foryou_ttl_seconds, max_entries=50_000
        )
        self.cache_ttl = cache_ttl_seconds
        self.foryou_ttl = foryou_ttl_seconds
        self.id_gen = id_gen or Snowflake(machine_id=31)
        self.candidate_pool = candidate_pool
        self.window_seconds = window_seconds

        # Per-video engagement event deque — bounded ring of (ts, watch_s).
        # Used by the engagement signal.
        self._engagement: dict[int, deque] = defaultdict(deque)
        # Per-user watch history (most recent first, capped).
        # Each entry: (video_id, watch_pct)
        self._watch_history: dict[int, deque] = defaultdict(
            lambda: deque(maxlen=MAX_WATCH_HISTORY)
        )
        # In-memory tag → video set, for quick candidate generation.
        # Rebuilt on demand.
        self._tag_index: dict[str, set] = defaultdict(set)

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

    # ---- posting videos ------------------------------------------------

    def post_video(
        self,
        user_id: int,
        caption: str,
        duration_s: int,
        tags: Optional[list] = None,
    ) -> Video:
        """Record metadata for a freshly posted short-form video.

        Mirrors `POST /api/videos`. Bytes flow to S3 / CDN in
        parallel; we just persist the metadata here.
        """
        if not isinstance(caption, str):
            raise ValueError("caption must be a string")
        if not isinstance(duration_s, int) or duration_s <= 0:
            raise ValueError("duration_s must be a positive int")
        if duration_s > 600:  # 10-minute hard cap for "short-form"
            raise ValueError("duration_s cannot exceed 600 (10 min)")
        if not self.store.exists(self._k_user(user_id)):
            raise ValueError(f"unknown user_id {user_id}")
        clean_tags = self._clean_tags(tags or [])

        video_id = self.id_gen.next_id()
        video = Video(
            video_id=video_id,
            user_id=user_id,
            caption=caption.strip(),
            duration_s=duration_s,
            tags=clean_tags,
            created_at=time.time(),
            views=0,
            likes=0,
            total_watch_s=0.0,
            play_count=0,
            original_url=f"s3://tiktok/{video_id}/original.mp4",
        )
        self._persist_video(video)
        with self._lock:
            for t in clean_tags:
                self._tag_index[t].add(video_id)
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
        return Video(**cached) if cached else Video(**data)

    # ---- views + engagement -------------------------------------------

    def record_view(
        self,
        video_id: int,
        user_id: int,
        watch_pct: float = 100.0,
    ) -> Optional[Video]:
        """Record a view of ``video_id`` by ``user_id`` with watch percentage.

        Updates lifetime counters, the in-memory engagement deque,
        and the user's watch history. ``watch_pct`` is a float in
        [0, 100]; we use it to weight the average watch time.
        """
        video = self.get_video(video_id)
        if video is None:
            return None
        if not self.store.exists(self._k_user(user_id)):
            raise ValueError(f"unknown user_id {user_id}")
        if not isinstance(watch_pct, (int, float)) or not (
            0.0 <= float(watch_pct) <= 100.0
        ):
            raise ValueError("watch_pct must be a number in [0, 100]")

        watch_pct = float(watch_pct)
        contributed_s = (watch_pct / 100.0) * float(video.duration_s)
        now = time.time()
        with self._lock:
            video.views += 1
            video.total_watch_s += contributed_s
            video.play_count += 1
            dq = self._engagement[video_id]
            cutoff = now - self.window_seconds
            while dq and dq[0][0] < cutoff:
                dq.popleft()
            dq.append((now, contributed_s))
            if len(dq) > 5_000:
                dq.popleft()
            # Most-recent-first watch history.
            self._watch_history[user_id].appendleft(
                (video_id, watch_pct)
            )

        self._persist_video(video)
        # Invalidate this user's For You cache — engagement changed.
        self.foryou_cache.delete(self._k_foryou(user_id))
        return video

    def like_video(
        self, video_id: int, user_id: int
    ) -> Optional[Video]:
        """Add a like from ``user_id`` to ``video_id``."""
        video = self.get_video(video_id)
        if video is None:
            return None
        if not self.store.exists(self._k_user(user_id)):
            raise ValueError(f"unknown user_id {user_id}")
        with self._lock:
            video.likes += 1
        self._persist_video(video)
        return video

    # ---- For You feed --------------------------------------------------

    def foryou(self, user_id: int, limit: int = 20) -> list[tuple[int, str, float]]:
        """Return the For You feed for ``user_id``.

        A 60-second cached list of ``(video_id, caption, score)``,
        ranked by:
            score = w_recency * recency
                  + w_engagement * engagement
                  + w_affinity * affinity

        Candidates are pulled from the user's watch-history tags
        (the *affinity* signal). If the user has no history, we
        fall back to the most recently uploaded videos.
        """
        if limit <= 0:
            return []
        # Cold path: never-seen user — return recency-only.
        if not self.store.exists(self._k_user(user_id)):
            return self._foryou_cold_start(limit)

        cache_key = self._k_foryou(user_id)
        cached = self.foryou_cache.get(cache_key)
        if cached:
            return cached[:limit]

        ranked = self._rank_foryou(user_id, limit=self.candidate_pool)
        # Cache only the top-K, but return what was asked.
        self.foryou_cache.set(
            cache_key, ranked, self.foryou_ttl
        )
        return ranked[:limit]

    def _rank_foryou(
        self, user_id: int, limit: int
    ) -> list[tuple[int, str, float]]:
        """Score candidates and return the top-``limit``."""
        candidates = self._candidate_videos(user_id, limit)
        if not candidates:
            return []

        # User's tag set for affinity.
        affinity_set = self._user_tag_set(user_id)
        now = time.time()

        scored: list[tuple[int, str, float]] = []
        for video_id in candidates:
            v = self.get_video(video_id)
            if v is None:
                continue
            recency = self._recency_score(v, now)
            engagement = self._engagement_score(v)
            affinity = self._affinity_score(v, affinity_set)
            score = (
                W_RECENCY * recency
                + W_ENGAGEMENT * engagement
                + W_AFFINITY * affinity
            )
            scored.append((v.video_id, v.caption, score))

        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[:limit]

    def _candidate_videos(
        self, user_id: int, limit: int
    ) -> list[int]:
        """Build a candidate set for ranking.

        Strategy: union over the user's watched-tags of all videos
        tagged with that tag, plus the most recent uploads the user
        has not seen. Deduplicate, drop already-watched.
        """
        with self._lock:
            watched_set = {
                vid for vid, _ in self._watch_history.get(user_id, ())
            }
            user_tags: set[str] = set()
            for vid, _ in self._watch_history.get(user_id, ()):
                v = self.get_video(vid)
                if v is not None:
                    user_tags.update(v.tags)

            candidates: set[int] = set()
            if user_tags:
                for t in user_tags:
                    candidates.update(self._tag_index.get(t, set()))
            # Always mix in the global recent uploads as exploration.
            for vid, _ in self.store.scan("video:"):
                if not isinstance(_, dict):
                    continue
                candidates.add(vid)
                if len(candidates) >= limit * 5:
                    break

        candidates -= watched_set
        # Bound the candidate pool to keep ranking cheap.
        if len(candidates) > limit:
            candidates = set(list(candidates)[:limit])
        return list(candidates)

    def _recency_score(self, video: Video, now: float) -> float:
        """Exponential decay with a ~6h half-life."""
        age_s = max(0.0, now - video.created_at)
        half_life_s = 6 * 3600.0
        return math.pow(0.5, age_s / half_life_s)

    def _engagement_score(self, video: Video) -> float:
        """Like-rate + watch-through-rate, normalized to ~[0, 1]."""
        views = max(1, video.views)
        like_rate = video.likes / views
        # Average watch %, capped at 1.0.
        avg_watch_pct = (
            (video.total_watch_s / views) / max(1, video.duration_s)
        )
        avg_watch_pct = min(1.0, avg_watch_pct)
        return 0.5 * like_rate + 0.5 * avg_watch_pct

    def _affinity_score(
        self, video: Video, user_tags: set[str]
    ) -> float:
        """Jaccard similarity between the video's tags and user's tags."""
        if not video.tags or not user_tags:
            return 0.0
        v_set = set(video.tags)
        inter = v_set & user_tags
        union = v_set | user_tags
        if not union:
            return 0.0
        return len(inter) / len(union)

    def _user_tag_set(self, user_id: int) -> set[str]:
        with self._lock:
            tags: set[str] = set()
            for vid, _ in self._watch_history.get(user_id, ()):
                v = self.get_video(vid)
                if v is not None:
                    tags.update(v.tags)
        return tags

    def _foryou_cold_start(
        self, limit: int
    ) -> list[tuple[int, str, float]]:
        """No history: rank all videos by recency alone."""
        out: list[tuple[int, float, int, str]] = []
        now = time.time()
        for k, data in self.store.scan("video:"):
            if not k.startswith("video:") or not isinstance(data, dict):
                continue
            try:
                v = Video(**data)
            except TypeError:
                continue
            out.append(
                (v.video_id, self._recency_score(v, now), 0.0, v.caption)
            )
        out.sort(key=lambda x: x[1], reverse=True)
        return [
            (vid, cap, score) for vid, score, _, cap in out[:limit]
        ]

    # ---- stats / internals --------------------------------------------

    def total_videos(self) -> int:
        return sum(
            1 for k, _ in self.store.scan("video:") if k.startswith("video:")
        )

    def cache_stats(self) -> dict:
        return {
            "video_cache": self.cache.stats(),
            "foryou_cache": self.foryou_cache.stats(),
        }

    # ---- key naming ---------------------------------------------------

    @staticmethod
    def _k_user(uid: int) -> str:
        return f"user:{uid}"

    @staticmethod
    def _k_video(vid: int) -> str:
        return f"video:{vid}"

    @staticmethod
    def _k_foryou(uid: int) -> str:
        return f"foryou:{uid}"

    @staticmethod
    def _clean_tags(tags) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for t in tags or []:
            if not isinstance(t, str):
                continue
            t = t.strip().lower()
            if not t or t in seen:
                continue
            seen.add(t)
            out.append(t)
        return out

    def _persist_video(self, video: Video) -> None:
        data = video.to_dict()
        self.store.set(self._k_video(video.video_id), data)
        # Invalidate cache so the next read sees updated counters.
        self.cache.set(self._k_video(video.video_id), data, self.cache_ttl)
