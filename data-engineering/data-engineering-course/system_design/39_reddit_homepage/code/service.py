"""Reddit-style service: subreddits, posts, votes, hot-score ranking."""

from __future__ import annotations

import math
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Optional

from common.cache import TTLCache
from common.ids import Snowflake
from common.storage import KeyValueStore


EPOCH = 1_577_836_800  # 2020-01-01 UTC seconds; Reddit-style constant
HOT_TIME_DIVISOR = 45_000  # seconds; Reddit uses ~45k seconds


def hot_score(upvotes: int, downvotes: int, ts: float) -> float:
    """Reddit's hot-score, simplified Wilson-style formula."""
    s = upvotes - downvotes
    if s == 0:
        order = 0
    elif s > 0:
        order = math.log10(max(s, 1))
    else:
        order = -math.log10(max(-s, 1))
    sign = 1 if s > 0 else (-1 if s < 0 else 0)
    return order * sign + (ts - EPOCH) / HOT_TIME_DIVISOR


@dataclass
class Subreddit:
    subreddit_id: int
    name: str
    description: str = ""
    subscribers: int = 0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Post:
    post_id: int
    subreddit_id: int
    user_id: int
    title: str
    body: str
    created_at: float
    upvotes: int = 0
    downvotes: int = 0
    score: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


class RedditService:
    """A working Reddit-style service.

    >>> svc = RedditService()
    >>> s = svc.create_subreddit("python", "Python lang")
    >>> u = svc.create_user(1, "alice")
    >>> svc.subscribe(1, s.subreddit_id)
    >>> p = svc.create_post(1, s.subreddit_id, "hello", "")
    >>> svc.vote(p.post_id, 1, 1)
    >>> top = svc.subreddit_top(s.subreddit_id, limit=5)
    >>> top[0]['post_id'] == p.post_id
    True
    """

    def __init__(self):
        self.snow = Snowflake(machine_id=39)
        self.sub_store = KeyValueStore("reddit_subreddits")
        self.post_store = KeyValueStore("reddit_posts")
        self.user_store = KeyValueStore("reddit_users")
        self.subs = KeyValueStore("reddit_subs")  # user -> [subreddit_ids]
        self.votes = KeyValueStore("reddit_votes")  # (post_id, user_id) -> dir
        self.list_cache = TTLCache(ttl_seconds=30)

    # ---- users --------------------------------------------------------

    def create_user(self, user_id: int, username: str) -> dict:
        d = {"user_id": user_id, "username": username, "karma": 0}
        self.user_store.set(f"user:{user_id}", d)
        return d

    # ---- subreddits ---------------------------------------------------

    def create_subreddit(self, name: str, description: str = "") -> Subreddit:
        sid = self.snow.next_id()
        s = Subreddit(subreddit_id=sid, name=name, description=description)
        self.sub_store.set(f"sub:{sid}", s.to_dict())
        return s

    def get_subreddit(self, subreddit_id: int) -> Optional[Subreddit]:
        d = self.sub_store.get(f"sub:{subreddit_id}")
        return Subreddit(**d) if d else None

    def subscribe(self, user_id: int, subreddit_id: int) -> None:
        subs = self.subs.get(f"subs:{user_id}") or []
        if subreddit_id not in subs:
            subs.append(subreddit_id)
            self.subs.set(f"subs:{user_id}", subs)
        s = self.get_subreddit(subreddit_id)
        if s:
            s.subscribers += 1
            self.sub_store.set(f"sub:{subreddit_id}", s.to_dict())

    # ---- posts --------------------------------------------------------

    def create_post(self, user_id: int, subreddit_id: int,
                    title: str, body: str = "") -> Post:
        pid = self.snow.next_id()
        p = Post(
            post_id=pid,
            subreddit_id=subreddit_id,
            user_id=user_id,
            title=title,
            body=body,
            created_at=time.time(),
        )
        self.post_store.set(f"post:{pid}", p.to_dict())
        self.list_cache.delete(f"list:{subreddit_id}")
        return p

    def get_post(self, post_id: int) -> Optional[Post]:
        d = self.post_store.get(f"post:{post_id}")
        return Post(**d) if d else None

    def posts_in(self, subreddit_id: int) -> list[Post]:
        out = []
        for _k, v in self.post_store.scan("post:"):
            if v.get("subreddit_id") == subreddit_id:
                out.append(Post(**v))
        return out

    # ---- votes --------------------------------------------------------

    def vote(self, post_id: int, user_id: int, direction: int) -> dict:
        """direction in {-1, 0, 1}; 0 means retract."""
        if direction not in (-1, 0, 1):
            raise ValueError("direction must be -1, 0, or 1")
        p = self.get_post(post_id)
        if not p:
            raise ValueError("post not found")
        key = f"vote:{post_id}:{user_id}"
        prev = self.votes.get(key)
        if prev == direction:
            return p.to_dict()
        # Adjust counts
        if prev == 1:
            p.upvotes -= 1
        elif prev == -1:
            p.downvotes -= 1
        if direction == 1:
            p.upvotes += 1
        elif direction == -1:
            p.downvotes += 1
        p.score = p.upvotes - p.downvotes
        self.post_store.set(f"post:{post_id}", p.to_dict())
        if direction == 0:
            self.votes.delete(key)
        else:
            self.votes.set(key, direction)
        self.list_cache.delete(f"list:{p.subreddit_id}")
        return p.to_dict()

    # ---- ranked lists -------------------------------------------------

    def subreddit_top(self, subreddit_id: int, limit: int = 25,
                       sort: str = "hot") -> list[dict]:
        cache_key = f"list:{subreddit_id}:{sort}:{limit}"
        cached = self.list_cache.get(cache_key)
        if cached is not None:
            return cached
        posts = self.posts_in(subreddit_id)
        if sort == "hot":
            scored = [(hot_score(p.upvotes, p.downvotes, p.created_at), p)
                      for p in posts]
            scored.sort(key=lambda x: x[0], reverse=True)
            out = [p.to_dict() | {"hot_score": s} for s, p in scored[:limit]]
        elif sort == "new":
            posts.sort(key=lambda p: p.created_at, reverse=True)
            out = [p.to_dict() for p in posts[:limit]]
        elif sort == "top":
            posts.sort(key=lambda p: p.score, reverse=True)
            out = [p.to_dict() for p in posts[:limit]]
        else:
            raise ValueError(f"unknown sort: {sort}")
        self.list_cache.set(cache_key, out)
        return out

    def home(self, user_id: int, limit: int = 50) -> list[dict]:
        """Merge top posts from each subscribed subreddit."""
        subs = self.subs.get(f"subs:{user_id}") or []
        merged: list[dict] = []
        for sid in subs:
            merged.extend(self.subreddit_top(sid, limit=limit))
        # Dedupe by post_id and re-sort by hot_score
        seen: dict[int, dict] = {}
        for item in merged:
            pid = item["post_id"]
            if pid not in seen or item.get("hot_score", 0) > seen[pid].get("hot_score", 0):
                seen[pid] = item
        out = sorted(seen.values(), key=lambda p: p.get("hot_score", 0), reverse=True)
        return out[:limit]

    def stats(self) -> dict:
        return {
            "subreddits": self.sub_store.size(),
            "posts": self.post_store.size(),
            "users": self.user_store.size(),
            "votes": self.votes.size(),
            "cache": self.list_cache.stats(),
        }
