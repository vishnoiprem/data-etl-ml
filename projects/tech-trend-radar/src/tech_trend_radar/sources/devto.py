"""dev.to, via the public articles API.

One call, not one per tag. The `tags` parameter takes a comma-separated list
and returns the *union* of those tags — the singular `tag` parameter takes
exactly one tag and a comma-separated value under it silently returns zero
articles. Asking for all six watched tags at once is both correct and one
request instead of six, which matters because dev.to rate-limits bursts of
requests.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..config import DEVTO_TAGS, Settings
from ..http import HttpClient, normalise_engagement
from ..models import Post
from .base import BaseAdapter

ARTICLES_URL = "https://dev.to/api/articles"


class DevToAdapter(BaseAdapter):
    """Popular dev.to articles across a set of tags."""

    name = "devto"

    #: dev.to's community tags. `discuss`, `career`, `beginners` and the rest
    #: describe the *post*, not a technology — a post about Rust tagged
    #: `discuss` is still a post about Rust.
    source_markers = frozenset(
        {
            "discuss",
            "career",
            "beginners",
            "opensource",
            "productivity",
            "webdev",
            "devchallenge",
            "hacktoberfest",
            "community",
            "devto",
            "learning",
            "showdev",
            "help",
        }
    )

    def fetch(self, client: HttpClient, settings: Settings) -> list[Post]:
        data = client.get_json(
            ARTICLES_URL,
            params={
                "per_page": min(settings.limit, 100),
                "top": 7,
                "tags": ",".join(DEVTO_TAGS),
            },
        )
        if not isinstance(data, list):
            return []

        weight = settings.platform_weight(self.name)
        posts: list[Post] = []

        for article in data:
            title = (article.get("title") or "").strip()
            native_id = str(article.get("id") or article.get("url") or "")
            if not title or not native_id:
                continue

            reactions = float(article.get("public_reactions_count") or 0)
            comments = float(article.get("comments_count") or 0)
            raw = reactions + comments * 1.5

            article_tags = tuple(article.get("tag_list") or ())
            posts.append(
                Post(
                    platform=self.name,
                    native_id=native_id,
                    title=title,
                    published=_parse_timestamp(article.get("published_at")),
                    weight=normalise_engagement(raw, weight),
                    raw_engagement=raw,
                    url=article.get("url") or "",
                    author=(article.get("user") or {}).get("name", ""),
                    tags=article_tags,
                    description=(article.get("description") or "").strip(),
                    extra={
                        "reactions": int(reactions),
                        "comments": int(comments),
                        "reading_time_minutes": article.get("reading_time_minutes"),
                    },
                )
            )
        return posts


def _parse_timestamp(value: str | None) -> datetime:
    """dev.to returns ISO-8601 with a trailing `Z`."""
    if not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)
