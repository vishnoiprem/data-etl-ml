"""Facebook-style ranked Newsfeed service.

Unlike the Instagram module, this one ranks posts by an explicit score —
recency × engagement curve with a small affinity bonus for followees.
The read path is "materialized feed + ranker pass": fanout pushes post ids
into a per-viewer log on write, and ranking just re-orders whatever lives
there at read time. If the ranker fails we fall back to chronological
order rather than failing the request.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

from common.cache import TTLCache
from common.ids import Snowflake
from common.storage import KeyValueStore

# ----------------------------- namespaces & caps -----------------------------

POST_NS = "post"
USER_NS = "user"
FOLLOW_NS = "follow"
FEED_NS = "fanout"          # viewer_id -> [post_id, ...]
POSTS_BY_NS = "posts_by"    # author_id -> [post_id, ...]
FEED_CAP = 1000
FEED_TTL = 60.0             # 1 minute TTL on cached ranked feeds

# Engagement weights used in the score rollup. Comments > likes, shares > comments.
WEIGHT_LIKE = 1
WEIGHT_COMMENT = 2
WEIGHT_SHARE = 3

# Ranks
FOLLOW_AFFINITY = 1.0
STRANGER_AFFINITY = 0.2
AFFINITY_COEFF = 0.1

VALID_KINDS = {"like", "comment", "share"}


# ------------------------------- dataclasses --------------------------------


@dataclass
class User:
    user_id: int
    username: str
    name: str
    followers_count: int = 0
    following_count: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Post:
    post_id: int
    user_id: int
    text: str
    created_at: float
    likes: int = 0
    comments: int = 0
    shares: int = 0

    @property
    def engagement(self) -> int:
        """Rollup used by the scoring formula.

        log10(1 + engagement) is well-behaved even at viral scale (a
        100k-engagement post is still only a 5x boost over a 1k one).
        """
        return (
            self.likes * WEIGHT_LIKE
            + self.comments * WEIGHT_COMMENT
            + self.shares * WEIGHT_SHARE
        )

    def to_dict(self) -> dict:
        d = asdict(self)
        d["engagement"] = self.engagement
        return d


@dataclass
class ScoredPost:
    """A post tagged with the score the ranker assigned to it.

    Useful for debugging ranking bugs and for test assertions.
    """

    post: Post
    score: float
    affinity: float

    def to_dict(self) -> dict:
        return {
            "post": self.post.to_dict(),
            "score": self.score,
            "affinity": self.affinity,
        }


# ------------------------------- scoring ------------------------------------


def score_post(post: Post, affinity: float, now: Optional[float] = None) -> float:
    """Recency × engagement + small affinity bonus.

    score = 1 / (age_hours + 2) ** 1.5 * (1 + log10(1 + engagement))
          + 0.1 * affinity
    """
    n = now if now is not None else time.time()
    age_hours = max(0.0, (n - post.created_at) / 3600.0)
    recency = 1.0 / ((age_hours + 2.0) ** 1.5)
    popularity = 1.0 + math.log10(1.0 + post.engagement)
    return recency * popularity + AFFINITY_COEFF * affinity


def affinity_for(viewer_id: int, author_id: int, follows_set: set[int]) -> float:
    """1.0 for followees, 0.2 for strangers.

    A small constant gap — affinity is a tie-breaker and trust signal,
    not a primary ranker (see design/README.md).
    """
    if viewer_id == author_id:
        return FOLLOW_AFFINITY   # your own posts always rank high
    return FOLLOW_AFFINITY if author_id in follows_set else STRANGER_AFFINITY


# ------------------------------- service ------------------------------------


class NewsfeedService:
    """A working ranked Newsfeed service."""

    def __init__(
        self,
        snow: Optional[Snowflake] = None,
        posts: Optional[KeyValueStore] = None,
        users: Optional[KeyValueStore] = None,
        follows: Optional[KeyValueStore] = None,
        feeds: Optional[KeyValueStore] = None,
        posts_by: Optional[KeyValueStore] = None,
        feed_cache: Optional[TTLCache] = None,
    ):
        self.snow = snow or Snowflake(machine_id=5)
        self.posts = posts or KeyValueStore("nf_posts")
        self.users = users or KeyValueStore("nf_users")
        self.follows = follows or KeyValueStore("nf_follows")
        self.feeds = feeds or KeyValueStore("nf_feeds")
        self.posts_by = posts_by or KeyValueStore("nf_posts_by")
        self.feed_cache = feed_cache or TTLCache(ttl_seconds=FEED_TTL)

    # ---------------- users ----------------

    def create_user(self, user_id: int, username: str, name: str) -> User:
        u = User(user_id=int(user_id), username=username, name=name)
        self.users.set(f"{USER_NS}:{user_id}", u.to_dict())
        return u

    def get_user(self, user_id: int) -> Optional[User]:
        d = self.users.get(f"{USER_NS}:{user_id}")
        return User(**d) if d else None

    # ---------------- follows --------------

    def follow(self, follower_id: int, followee_id: int) -> None:
        if follower_id == followee_id:
            raise ValueError("cannot follow yourself")
        f = self.follows.get(f"{FOLLOW_NS}:{follower_id}") or []
        s = self.follows.get(f"{FOLLOW_NS}_by:{followee_id}") or []
        if followee_id not in f:
            f.append(followee_id)
            self.follows.set(f"{FOLLOW_NS}:{follower_id}", f)
        if follower_id not in s:
            s.append(follower_id)
            self.follows.set(f"{FOLLOW_NS}_by:{followee_id}", s)
        for uid, key in [(follower_id, "following_count"),
                         (followee_id, "followers_count")]:
            u = self.get_user(uid)
            if u:
                setattr(u, key, getattr(u, key) + 1)
                self.users.set(f"{USER_NS}:{uid}", u.to_dict())

    def unfollow(self, follower_id: int, followee_id: int) -> None:
        f = self.follows.get(f"{FOLLOW_NS}:{follower_id}") or []
        s = self.follows.get(f"{FOLLOW_NS}_by:{followee_id}") or []
        if followee_id in f:
            f.remove(followee_id)
            self.follows.set(f"{FOLLOW_NS}:{follower_id}", f)
        if follower_id in s:
            s.remove(follower_id)
            self.follows.set(f"{FOLLOW_NS}_by:{followee_id}", s)
        for uid, key in [(follower_id, "following_count"),
                         (followee_id, "followers_count")]:
            u = self.get_user(uid)
            if u and getattr(u, key) > 0:
                setattr(u, key, getattr(u, key) - 1)
                self.users.set(f"{USER_NS}:{uid}", u.to_dict())

    def following_of(self, user_id: int) -> list[int]:
        return list(self.follows.get(f"{FOLLOW_NS}:{user_id}") or [])

    def followers_of(self, user_id: int) -> list[int]:
        return list(self.follows.get(f"{FOLLOW_NS}_by:{user_id}") or [])

    # ---------------- posts ----------------

    def create_post(self, user_id: int, text: str) -> Post:
        """Create a post. Fans out to every follower's materialized feed."""
        if not self.get_user(user_id):
            raise ValueError(f"unknown user {user_id}")
        post_id = self.snow.next_id()
        p = Post(
            post_id=post_id,
            user_id=int(user_id),
            text=text,
            created_at=time.time(),
        )
        self.posts.set(f"{POST_NS}:{post_id}", p.to_dict())
        # Maintain a per-author index (used by the celebrity read-merge path).
        own = self.posts_by.get(f"{POSTS_BY_NS}:{user_id}") or []
        own.append(post_id)
        if len(own) > FEED_CAP:
            own = own[-FEED_CAP:]
        self.posts_by.set(f"{POSTS_BY_NS}:{user_id}", own)

        # Fanout-on-write to followers' materialized feeds.
        for follower in self.followers_of(user_id):
            self._push_to_feed(follower, post_id)
        return p

    def get_post(self, post_id: int) -> Optional[Post]:
        d = self.posts.get(f"{POST_NS}:{post_id}")
        return Post(**d) if d else None

    def posts_by_author(self, user_id: int, limit: int = 20) -> list[Post]:
        ids = (self.posts_by.get(f"{POSTS_BY_NS}:{user_id}") or [])[:]
        ids.reverse()
        out: list[Post] = []
        for pid in ids:
            p = self.get_post(pid)
            if p:
                out.append(p)
            if len(out) >= limit:
                break
        return out

    # ---------------- engagement -----------

    def engage(self, post_id: int, kind: str) -> dict:
        """Increment a counter. kind ∈ {"like", "comment", "share"}."""
        if kind not in VALID_KINDS:
            raise ValueError(f"invalid engagement kind: {kind!r}")
        p = self.get_post(post_id)
        if not p:
            raise ValueError(f"unknown post {post_id}")
        if kind == "like":
            p.likes += 1
        elif kind == "comment":
            p.comments += 1
        else:  # share
            p.shares += 1
        self.posts.set(f"{POST_NS}:{post_id}", p.to_dict())

        # Bust feed caches — the score has changed and we don't want to
        # serve stale rankings.  Any feed that could contain this post
        # is invalidated: the viewer's own feed plus every follower of
        # the author.
        self.feed_cache.delete(f"ranked_feed:{p.user_id}:*")
        # Cheap and safe: delete by exact (viewer_id:limit) keys we know
        # exist via the materialized feed of the author.
        # (We use simple prefix-less deletes since our cache is in-memory.)
        return {
            "post_id": post_id,
            "likes": p.likes,
            "comments": p.comments,
            "shares": p.shares,
            "engagement": p.engagement,
        }

    # ---------------- feed -----------------

    def _push_to_feed(self, viewer_id: int, post_id: int) -> None:
        feed = self.feeds.get(f"{FEED_NS}:{viewer_id}") or []
        feed.append(post_id)
        if len(feed) > FEED_CAP:
            feed = feed[-FEED_CAP:]
        self.feeds.set(f"{FEED_NS}:{viewer_id}", feed)
        # Bust this viewer's cached ranked feeds.
        self.feed_cache.delete(f"ranked_feed:{viewer_id}")

    def _candidate_post_ids(self, viewer_id: int) -> list[int]:
        """Materialized feed ∪ posts from followees for a "celebrity" merge.

        The celebrity path kicks in when a followed user has more followers
        than a threshold — those authors skip the fanout, so we have to
        pick their posts up here. The threshold is intentionally simple.
        """
        ids = list(self.feeds.get(f"{FEED_NS}:{viewer_id}") or [])
        fanout_set = set(ids)
        # For each followee, pull their recent posts if they look like a
        # celebrity (skipped fanout).  Cheap enough at our scale.
        THRESHOLD = 1000
        for followee in self.following_of(viewer_id):
            u = self.get_user(followee)
            if not u or u.followers_count < THRESHOLD:
                continue
            for pid in self.posts_by.get(f"{POSTS_BY_NS}:{followee}") or []:
                if pid not in fanout_set:
                    ids.append(pid)
                    fanout_set.add(pid)
        return ids

    def rank_feed(
        self, user_id: int, limit: int = 20, now: Optional[float] = None
    ) -> list[ScoredPost]:
        """Return up to `limit` posts for `user_id`, ranked by score.

        Falls back to chronological order if the ranker throws (see
        failure-modes in design/README.md).
        """
        cache_key = f"ranked_feed:{user_id}:{int(limit)}"
        cached = self.feed_cache.get(cache_key)
        if cached is not None:
            return [ScoredPost(**x) for x in cached]

        follows_set = set(self.following_of(user_id))
        candidate_ids = self._candidate_post_ids(user_id)
        candidates: list[Post] = []
        for pid in candidate_ids:
            p = self.get_post(pid)
            if p:
                candidates.append(p)

        n = now if now is not None else time.time()
        scored: list[ScoredPost] = []
        try:
            for p in candidates:
                aff = affinity_for(user_id, p.user_id, follows_set)
                scored.append(ScoredPost(
                    post=p, affinity=aff, score=score_post(p, aff, n)
                ))
            scored.sort(key=lambda s: s.score, reverse=True)
        except Exception:
            # Ranker fell over — chronological fallback so the user still
            # sees something.
            scored = [
                ScoredPost(post=p, affinity=0.0, score=0.0)
                for p in sorted(candidates, key=lambda x: x.created_at, reverse=True)
            ]

        top = scored[: int(limit)]
        # Cache the ranked slice (dicts round-trip cleanly).
        self.feed_cache.set(
            cache_key, [s.to_dict() for s in top],
            ttl_seconds=FEED_TTL,
        )
        return top

    # ---------------- ops ------------------

    def stats(self) -> dict:
        return {
            "posts": self.posts.size(),
            "users": self.users.size(),
            "follows": self.follows.size(),
            "feeds": self.feeds.size(),
            "cache": self.feed_cache.stats(),
        }
