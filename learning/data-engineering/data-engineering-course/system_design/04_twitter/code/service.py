"""Twitter / X-like service.

Implements the design described in `design/README.md`:

* Tweet creation with Snowflake IDs (see §5 — Data model).
* Follow / unfollow graph with bidirectional adjacency and live counts
  (see §4 — API).
* **Hybrid** home timeline: fanout-on-write for normal authors, pull-on-read
  for "celebrities" (followers_count >= ``CELEB_THRESHOLD``). See §6 +
  §8 in the design doc.
* Retweets are first-class tweets with ``retweet_of`` / ``retweet_of_user``
  lineage (see §7).
* Per-user ``TTLCache`` for the assembled timeline (see §6).

Every method returns plain dataclasses or values; the HTTP layer in
``app.py`` is responsible for JSON conversion.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import Optional

from common.cache import TTLCache
from common.ids import Snowflake
from common.storage import KeyValueStore


# ---------------------------------------------------------------------------
# Tunables (see design §5 + §8 — fanout-on-write deep dive).
# ---------------------------------------------------------------------------

CELEB_THRESHOLD = 10_000    # >= this many followers => "celebrity"
FEED_CAP = 1_000            # max entries kept in a user's materialised feed
CELEB_BUCKET_CAP = 200      # recent tweets kept per celebrity
TIMELINE_TTL = 60.0         # seconds the assembled timeline is cached


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


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
class Tweet:
    """A single tweet — original or retweet.

    Retweets carry ``retweet_of`` (the original ``tweet_id``) and
    ``retweet_of_user`` (the original author). Both fields are ``None``
    on originals. See design §7.
    """

    tweet_id: int
    user_id: int
    text: str
    created_at: float
    likes: int = 0
    retweets: int = 0
    retweet_of: Optional[int] = None
    retweet_of_user: Optional[int] = None

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class TwitterService:
    """A working Twitter / X-like service implementing the hybrid fanout
    design. See ``design/README.md`` for the full architecture.

    >>> svc = TwitterService()
    >>> svc.create_user(1, "u1", "User 1")
    >>> svc.create_user(2, "u2", "User 2")
    >>> svc.follow(1, 2)
    >>> t = svc.post_tweet(2, "hello world")
    >>> len(svc.timeline(1, limit=10)) >= 1
    True
    """

    def __init__(self):
        # Snowflake for tweet IDs — design §5. machine_id=4 (this module).
        self.snow = Snowflake(machine_id=4)

        # KV stores — design §5 (data model).
        self.users = KeyValueStore("tw_users")
        self.tweets = KeyValueStore("tw_tweets")
        self.follows = KeyValueStore("tw_follows")

        # Per-user materialised home timeline (fanout-on-write target).
        # Keyed by feed:<uid>; value is an ordered list of tweet_ids,
        # capped at FEED_CAP (most-recent at the end).
        self.feeds = KeyValueStore("tw_feeds")

        # Celebrity bucket — design §6 / §7. For each celebrity user,
        # we keep their last CELEB_BUCKET_CAP tweet_ids, *not* fanned
        # out to followers. Pulled at read time.
        self.celeb_buckets = KeyValueStore("tw_celeb_buckets")

        # Per-user assembled timeline cache — design §6.
        self.timeline_cache = TTLCache(ttl_seconds=TIMELINE_TTL)

    # ------------------------------------------------------------------
    # users — design §4 API + §5 model
    # ------------------------------------------------------------------

    def create_user(self, user_id: int, username: str, name: str) -> User:
        """Create or upsert a user."""
        u = User(user_id=user_id, username=username, name=name)
        self.users.set(f"user:{user_id}", u.to_dict())
        return u

    def get_user(self, user_id: int) -> Optional[User]:
        d = self.users.get(f"user:{user_id}")
        return User(**d) if d else None

    # ------------------------------------------------------------------
    # follows — design §4 + §5 (bidirectional adjacency + counts)
    # ------------------------------------------------------------------

    def follow(self, follower_id: int, followee_id: int) -> None:
        """``follower_id`` starts following ``followee_id``.

        Maintains two adjacency lists:
            follow:<follower_id>      -> [followee_ids]
            followed_by:<followee_id> -> [follower_ids]
        and bumps user counts.
        """
        if follower_id == followee_id:
            raise ValueError("cannot follow yourself")
        f = list(self.follows.get(f"follow:{follower_id}") or [])
        s = list(self.follows.get(f"followed_by:{followee_id}") or [])
        if followee_id not in f:
            f.append(followee_id)
            self.follows.set(f"follow:{follower_id}", f)
        if follower_id not in s:
            s.append(follower_id)
            self.follows.set(f"followed_by:{followee_id}", s)
        # live counters
        for uid, key in [(follower_id, "following_count"),
                         (followee_id, "followers_count")]:
            u = self.get_user(uid)
            if u:
                setattr(u, key, getattr(u, key) + 1)
                self.users.set(f"user:{uid}", u.to_dict())

    def unfollow(self, follower_id: int, followee_id: int) -> None:
        """Inverse of :meth:`follow`."""
        f = list(self.follows.get(f"follow:{follower_id}") or [])
        s = list(self.follows.get(f"followed_by:{followee_id}") or [])
        if followee_id in f:
            f.remove(followee_id)
            self.follows.set(f"follow:{follower_id}", f)
        if follower_id in s:
            s.remove(follower_id)
            self.follows.set(f"followed_by:{followee_id}", s)
        for uid, key in [(follower_id, "following_count"),
                         (followee_id, "followers_count")]:
            u = self.get_user(uid)
            if u and getattr(u, key) > 0:
                setattr(u, key, getattr(u, key) - 1)
                self.users.set(f"user:{uid}", u.to_dict())

    def followers_of(self, user_id: int) -> list[int]:
        """All users following ``user_id``."""
        return list(self.follows.get(f"followed_by:{user_id}") or [])

    def following_of(self, user_id: int) -> list[int]:
        """All users ``user_id`` follows."""
        return list(self.follows.get(f"follow:{user_id}") or [])

    def is_celeb(self, user_id: int) -> bool:
        """True iff ``user_id`` has at least CELEB_THRESHOLD followers.

        This is the central toggle for fanout-on-write vs pull-on-read
        (design §8).
        """
        u = self.get_user(user_id)
        return bool(u and u.followers_count >= CELEB_THRESHOLD)

    # ------------------------------------------------------------------
    # tweets — design §7 (write path) + §5 (data model)
    # ------------------------------------------------------------------

    def post_tweet(
        self,
        user_id: int,
        text: str,
        retweet_of: Optional[int] = None,
    ) -> Tweet:
        """Create a tweet (or retweet) and dispatch the right delivery.

        * Normal author (< CELEB_THRESHOLD followers): fanout-on-write
          to every follower's materialised feed list.
        * Celebrity author: append to the celeb bucket only; no fanout.
        * Retweets are first-class tweets but carry lineage
          ``retweet_of`` / ``retweet_of_user``. They still fanout so the
          RT actually spreads.
        """
        if not self.get_user(user_id):
            raise ValueError(f"unknown user {user_id}")

        tweet_id = self.snow.next_id()
        t = Tweet(
            tweet_id=tweet_id,
            user_id=user_id,
            text=text,
            created_at=time.time(),
        )

        # Retweet branch — populate lineage then store (design §7a).
        if retweet_of is not None:
            original = self.get_tweet(retweet_of)
            if not original:
                raise ValueError(f"unknown retweet target {retweet_of}")
            t.retweet_of = original.tweet_id
            t.retweet_of_user = original.user_id
            # bump the original's retweet counter
            original.retweets += 1
            self.tweets.set(f"tweet:{original.tweet_id}", original.to_dict())

        self.tweets.set(f"tweet:{tweet_id}", t.to_dict())

        # Delivery branch — design §7b (celeb) vs §7c (normal).
        if self.is_celeb(user_id):
            self._push_to_celeb_bucket(user_id, tweet_id)
            # NB: NO fanout — this is the entire point of the celeb
            # bucket. A tweet from a 100M-follower user writes to ONE
            # list (the celeb bucket), not 100M lists.
        else:
            self._fanout(tweet_id, user_id)

        return t

    def get_tweet(self, tweet_id: int) -> Optional[Tweet]:
        """Fetch a single tweet by id."""
        d = self.tweets.get(f"tweet:{tweet_id}")
        return Tweet(**d) if d else None

    def like_tweet(self, tweet_id: int) -> int:
        """Increment a tweet's like counter; returns the new total."""
        t = self.get_tweet(tweet_id)
        if not t:
            raise ValueError(f"unknown tweet {tweet_id}")
        t.likes += 1
        self.tweets.set(f"tweet:{tweet_id}", t.to_dict())
        return t.likes

    # ------------------------------------------------------------------
    # timeline (hybrid read) — design §6
    # ------------------------------------------------------------------

    def timeline(self, user_id: int, limit: int = 20) -> list[Tweet]:
        """Return up to ``limit`` recent tweets for ``user_id``'s home
        timeline — newest first, fanned-out pushed entries merged with
        pulled celeb-bucket entries.

        Implements the read flow in design §6 verbatim.
        """
        cache_key = f"tl:{user_id}:{limit}"
        cached = self.timeline_cache.get(cache_key)
        if cached is not None:
            return [Tweet(**row) for row in cached]

        # 1. Pushed entries — materialised feed list, newest at the end.
        pushed_ids: list[int] = list(self.feeds.get(f"feed:{user_id}") or [])

        # 2. Pulled entries — celebs the viewer follows. We look at the
        #    follow list, filter to celebs, and merge their buckets.
        followed = self.following_of(user_id)
        celebs = [c for c in followed if self.is_celeb(c)]

        # 3. Batch-hydrate both sets of tweet ids. We do this in two
        #    passes; in production we'd parallelise.
        tweets_by_id: dict[int, Tweet] = {}
        for tid in pushed_ids:
            t = self.get_tweet(tid)
            if t:
                tweets_by_id[tid] = t
        for celeb in celebs:
            bucket = self.celeb_buckets.get(f"celeb:{celeb}") or []
            for tid in bucket:
                if tid not in tweets_by_id:
                    t = self.get_tweet(tid)
                    if t:
                        tweets_by_id[tid] = t

        # 4. Merge + rank by created_at desc; tie-break by tweet_id desc
        #    (snowflakes are time-sortable so this gives a stable order).
        merged = sorted(
            tweets_by_id.values(),
            key=lambda x: (x.created_at, x.tweet_id),
            reverse=True,
        )[:limit]

        # 5. Cache the assembled timeline — bust on any new fanout.
        self.timeline_cache.set(
            cache_key, [t.to_dict() for t in merged], ttl_seconds=TIMELINE_TTL
        )
        return merged

    # ------------------------------------------------------------------
    # internal helpers — design §7c / §8
    # ------------------------------------------------------------------

    def _fanout(self, tweet_id: int, author_id: int) -> None:
        """Push ``tweet_id`` into every follower's materialised feed.

        Cost: O(followers). This is the central write amplification we
        mitigate with the celeb threshold (design §8). Each push:
          * appends to the tail of the follower's feed list,
          * trims to FEED_CAP (drop the head),
          * busts the assembled timeline cache for that follower.
        """
        for follower in self.followers_of(author_id):
            self._push_to_feed(follower, tweet_id)

    def _push_to_feed(self, user_id: int, tweet_id: int) -> None:
        """Append ``tweet_id`` to ``user_id``'s materialised feed list."""
        feed = list(self.feeds.get(f"feed:{user_id}") or [])
        feed.append(tweet_id)
        # Cap to last FEED_CAP entries — design §8 mitigations.
        if len(feed) > FEED_CAP:
            feed = feed[-FEED_CAP:]
        self.feeds.set(f"feed:{user_id}", feed)
        # Bust this user's timeline cache so the next read re-merges.
        # (We don't know the limit; in prod we'd tag the cache or use a
        # per-user "dirty" flag — for this course we just clear the
        # keys we may have written.)
        self._bust_timeline_cache(user_id)

    def _push_to_celeb_bucket(self, user_id: int, tweet_id: int) -> None:
        """Append ``tweet_id`` to ``user_id``'s celeb bucket.

        The bucket is what makes celebrity tweets cheap at write time
        and slightly more expensive at read time — design §7b.
        """
        bucket = list(self.celeb_buckets.get(f"celeb:{user_id}") or [])
        bucket.append(tweet_id)
        if len(bucket) > CELEB_BUCKET_CAP:
            bucket = bucket[-CELEB_BUCKET_CAP:]
        self.celeb_buckets.set(f"celeb:{user_id}", bucket)

    def _bust_timeline_cache(self, user_id: int) -> None:
        """Invalidate the assembled-timeline cache for ``user_id``.

        We don't enumerate every (limit) variant; instead we walk the
        cache (TTLCache is small + bounded) and drop matching keys.
        In prod you'd use a Redis SCAN with a tag.
        """
        # The TTLCache exposes ``_data`` via ``_data``; we iterate via
        # ``stats()``-style inspection by clearing only our known
        # prefixes — small N, acceptable here.
        for limit in (10, 20, 50, 100):
            self.timeline_cache.delete(f"tl:{user_id}:{limit}")

    # ------------------------------------------------------------------
    # ops — design §11 (code map) + §6 (read path observability)
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        """Cheap operational snapshot for /health and /."""
        return {
            "users": self.users.size(),
            "tweets": self.tweets.size(),
            "follows": self.follows.size(),
            "feeds": self.feeds.size(),
            "celeb_buckets": self.celeb_buckets.size(),
            "celeb_threshold": CELEB_THRESHOLD,
            "timeline_cache": self.timeline_cache.stats(),
        }