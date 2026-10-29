"""Instagram-like service: photos, follows, fanout-on-write feed."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Optional

from common.cache import TTLCache
from common.ids import Snowflake
from common.storage import KeyValueStore

PHOTO_NS = "photo"
USER_NS = "user"
FOLLOW_NS = "follow"
FEED_CAP = 1000
FEED_TTL = 60.0


@dataclass
class Photo:
    photo_id: int
    user_id: int
    caption: str
    image_url: str
    created_at: float
    likes: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class User:
    user_id: int
    username: str
    name: str
    followers_count: int = 0
    following_count: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


class InstagramService:
    """A working Instagram-style service.

    >>> svc = InstagramService()
    >>> svc.create_user(1, "u1", "User 1")
    >>> svc.create_user(2, "u2", "User 2")
    >>> svc.follow(1, 2)
    >>> p = svc.upload(2, "caption", image_data=b"...")
    >>> feed = svc.feed(1, limit=10)
    >>> len(feed) >= 1
    True
    """

    def __init__(self):
        self.snow = Snowflake(machine_id=3)
        self.photos = KeyValueStore("ig_photos")
        self.users = KeyValueStore("ig_users")
        self.follows = KeyValueStore("ig_follows")
        # user_id -> list of photo_ids (deque persisted as list)
        self.feeds = KeyValueStore("ig_feeds")
        self.feed_cache = TTLCache(ttl_seconds=FEED_TTL)

    # ---- users --------------------------------------------------------

    def create_user(self, user_id: int, username: str, name: str) -> User:
        u = User(user_id=user_id, username=username, name=name)
        self.users.set(f"user:{user_id}", u.to_dict())
        return u

    def get_user(self, user_id: int) -> Optional[User]:
        d = self.users.get(f"user:{user_id}")
        return User(**d) if d else None

    # ---- follows ------------------------------------------------------

    def follow(self, follower_id: int, followee_id: int) -> None:
        if follower_id == followee_id:
            raise ValueError("cannot follow yourself")
        f = self.follows.get(f"follow:{follower_id}") or []
        s = self.follows.get(f"followed_by:{followee_id}") or []
        if followee_id not in f:
            f.append(followee_id)
            self.follows.set(f"follow:{follower_id}", f)
        if follower_id not in s:
            s.append(follower_id)
            self.follows.set(f"followed_by:{followee_id}", s)
        # Update counts
        for uid, key in [(follower_id, "following_count"),
                         (followee_id, "followers_count")]:
            u = self.get_user(uid)
            if u:
                setattr(u, key, getattr(u, key) + 1)
                self.users.set(f"user:{uid}", u.to_dict())

    def unfollow(self, follower_id: int, followee_id: int) -> None:
        f = self.follows.get(f"follow:{follower_id}") or []
        s = self.follows.get(f"followed_by:{followee_id}") or []
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
        return list(self.follows.get(f"followed_by:{user_id}") or [])

    def following_of(self, user_id: int) -> list[int]:
        return list(self.follows.get(f"follow:{user_id}") or [])

    # ---- photos -------------------------------------------------------

    def upload(self, user_id: int, caption: str, image_data: bytes = b"") -> Photo:
        photo_id = self.snow.next_id()
        image_url = f"https://cdn.example.com/photos/{photo_id}.jpg"
        p = Photo(
            photo_id=photo_id,
            user_id=user_id,
            caption=caption,
            image_url=image_url,
            created_at=time.time(),
        )
        self.photos.set(f"photo:{photo_id}", p.to_dict())
        # fanout-on-write: push to every follower's feed
        for follower in self.followers_of(user_id):
            self._push_to_feed(follower, photo_id)
        return p

    def get_photo(self, photo_id: int) -> Optional[Photo]:
        d = self.photos.get(f"photo:{photo_id}")
        return Photo(**d) if d else None

    def photos_by(self, user_id: int, limit: int = 20) -> list[Photo]:
        out = []
        for _k, v in self.photos.scan(f"photo:"):
            if int(_k.split(":")[1]) and v["user_id"] == user_id:
                out.append(Photo(**v))
            if len(out) >= limit:
                break
        out.sort(key=lambda x: x.created_at, reverse=True)
        return out

    def like(self, photo_id: int) -> int:
        p = self.get_photo(photo_id)
        if not p:
            raise ValueError("photo not found")
        p.likes += 1
        self.photos.set(f"photo:{photo_id}", p.to_dict())
        return p.likes

    # ---- feed ---------------------------------------------------------

    def _push_to_feed(self, user_id: int, photo_id: int) -> None:
        feed = self.feeds.get(f"feed:{user_id}") or []
        feed.append(photo_id)
        # cap to last N
        if len(feed) > FEED_CAP:
            feed = feed[-FEED_CAP:]
        self.feeds.set(f"feed:{user_id}", feed)
        # bust feed cache
        self.feed_cache.delete(f"feed:{user_id}")

    def feed(self, user_id: int, limit: int = 20) -> list[Photo]:
        cache_key = f"feed:{user_id}:{limit}"
        cached = self.feed_cache.get(cache_key)
        if cached is not None:
            return [Photo(**p) for p in cached]
        ids = self.feeds.get(f"feed:{user_id}") or []
        ids = list(reversed(ids))[:limit]
        out = []
        for pid in ids:
            p = self.get_photo(pid)
            if p:
                out.append(p)
        self.feed_cache.set(cache_key, [p.to_dict() for p in out])
        return out

    # ---- ops ----------------------------------------------------------

    def stats(self) -> dict:
        return {
            "photos": self.photos.size(),
            "users": self.users.size(),
            "follows": self.follows.size(),
            "feeds": self.feeds.size(),
            "cache": self.feed_cache.stats(),
        }
