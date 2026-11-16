"""The shared shapes every source adapter produces.

One `Post` type for every platform. That is what makes the rest of the
project simple: the burst detector does not know or care whether a post came
from Hacker News or a YouTube channel, only that it has a title, a timestamp,
and an engagement weight.

Engagement is normalised onto one scale at the adapter boundary, because the
platforms disagree wildly — a Hacker News story with 500 points is a much
bigger event than a dev.to post with 500 reactions.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


#: A stable identifier for a post. Hashing the platform plus the platform's
#: own id keeps the same story from being counted twice when two adapters
#: report it, without depending on the title staying unchanged.
def post_id(platform: str, native_id: str) -> str:
    digest = hashlib.sha1(f"{platform}:{native_id}".encode()).hexdigest()
    return digest[:16]


@dataclass(slots=True)
class Post:
    """One item observed on one platform.

    `title` is the signal used for topic extraction. `published` is the moment
    the item appeared — the timestamp burst detection is built on, because
    acceleration is a statement about *when* things happened.

    `weight` is the engagement figure, already normalised. `raw_engagement`
    keeps the original number so the report can say "142 points" instead of
    "0.71 normalised units".
    """

    platform: str
    native_id: str
    title: str
    published: datetime
    weight: float
    raw_engagement: float = 0.0
    url: str = ""
    author: str = ""
    tags: tuple[str, ...] = ()
    description: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return post_id(self.platform, self.native_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "platform": self.platform,
            "native_id": self.native_id,
            "title": self.title,
            "published": self.published.isoformat(),
            "weight": round(self.weight, 6),
            "raw_engagement": self.raw_engagement,
            "url": self.url,
            "author": self.author,
            "tags": list(self.tags),
            "description": self.description,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Post:
        published = data["published"]
        if isinstance(published, str):
            published = datetime.fromisoformat(published)
        return cls(
            platform=data["platform"],
            native_id=data["native_id"],
            title=data["title"],
            published=published,
            weight=data["weight"],
            raw_engagement=data.get("raw_engagement", 0.0),
            url=data.get("url", ""),
            author=data.get("author", ""),
            tags=tuple(data.get("tags", ())),
            description=data.get("description", ""),
            extra=data.get("extra", {}),
        )


@dataclass(slots=True)
class FetchResult:
    """What one adapter managed to collect on one run.

    A source that failed is not an error for the whole run: it is a source
    with no posts and a recorded reason. `error` is set, `ok` is False, and
    the radar ranks on whatever did arrive.
    """

    platform: str
    posts: list[Post] = field(default_factory=list)
    ok: bool = True
    error: str = ""
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "ok": self.ok,
            "error": self.error,
            "fetched_at": self.fetched_at.isoformat(),
            "duration_ms": round(self.duration_ms, 3),
            "post_count": len(self.posts),
            "posts": [p.to_dict() for p in self.posts],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FetchResult:
        return cls(
            platform=data["platform"],
            posts=[Post.from_dict(p) for p in data.get("posts", [])],
            ok=data.get("ok", True),
            error=data.get("error", ""),
            fetched_at=datetime.fromisoformat(data["fetched_at"]),
            duration_ms=data.get("duration_ms", 0.0),
        )
