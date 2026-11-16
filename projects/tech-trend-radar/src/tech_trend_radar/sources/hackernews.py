"""Hacker News, via the public Firebase and Algolia APIs.

Two calls, for two different jobs:

* **Firebase** gives the front page — the items the community has *voted* on.
  These carry strong engagement, but only for the current front page, so they
  say nothing about the recent background rate.
* **Algolia** gives everything posted in a time window. That is what the
  burst detector needs: a count of how many stories mentioned a topic in the
  last 48 hours, and how many mentioned it in the week before that.

Neither needs a key.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..config import Settings
from ..http import HttpClient, normalise_engagement
from ..models import Post
from .base import BaseAdapter

FIREBASE_TOP = "https://hacker-news.firebaseio.com/v0/topstories.json"
FIREBASE_ITEM = "https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
ALGOLIA_BY_DATE = "https://hn.algolia.com/api/v1/search_by_date"
ALGOLIA_SEARCH = "https://hn.algolia.com/api/v1/search"


class HackerNewsAdapter(BaseAdapter):
    """Front-page stories plus a recent-story sweep."""

    name = "hackernews"

    def fetch(self, client: HttpClient, settings: Settings) -> list[Post]:
        posts: list[Post] = []
        seen: set[str] = set()

        posts.extend(self._front_page(client, settings, seen))
        posts.extend(self._recent_stories(client, settings, seen))
        return posts

    def _front_page(
        self, client: HttpClient, settings: Settings, seen: set[str]
    ) -> list[Post]:
        """The voted-on front page. Strong signal, no time history."""
        ids = client.get_json(FIREBASE_TOP)
        if not isinstance(ids, list):
            return []

        weight = settings.platform_weight(self.name)
        limit = min(settings.limit, 30)
        posts: list[Post] = []

        for item_id in ids[:limit]:
            item = client.get_json(FIREBASE_ITEM.format(item_id=item_id))
            if not item or item.get("type") != "story":
                continue
            title = (item.get("title") or "").strip()
            if not title:
                continue
            key = str(item["id"])
            if key in seen:
                continue
            seen.add(key)

            raw = float(item.get("score") or 0) + float(item.get("descendants") or 0) * 0.5
            posts.append(
                Post(
                    platform=self.name,
                    native_id=key,
                    title=title,
                    published=datetime.fromtimestamp(item["time"], tz=timezone.utc),
                    weight=normalise_engagement(raw, weight),
                    raw_engagement=raw,
                    url=item.get("url") or "",
                    author=item.get("by") or "",
                    tags=("hackernews",),
                    extra={
                        "points": item.get("score", 0),
                        "comments": item.get("descendants", 0),
                    },
                )
            )
        return posts

    def _recent_stories(
        self, client: HttpClient, settings: Settings, seen: set[str]
    ) -> list[Post]:
        """Everything posted in the recent window. This is the burst input."""
        since = int(
            datetime.now(timezone.utc).timestamp()
            - (settings.recent_window_hours + settings.baseline_window_hours) * 3600
        )
        data = client.get_json(
            ALGOLIA_BY_DATE,
            params={
                "tags": "story",
                "numericFilters": f"created_at_i>{since}",
                "hitsPerPage": settings.limit,
            },
        )
        weight = settings.platform_weight(self.name)
        posts: list[Post] = []

        for hit in data.get("hits", []):
            title = (hit.get("title") or hit.get("story_title") or "").strip()
            if not title:
                continue
            native_id = str(hit.get("objectID") or hit.get("story_id") or "")
            if not native_id or native_id in seen:
                continue
            seen.add(native_id)

            points = float(hit.get("points") or 0)
            comments = float(hit.get("num_comments") or 0)
            raw = points + comments * 0.5
            created = hit.get("created_at_i")
            published = (
                datetime.fromtimestamp(created, tz=timezone.utc)
                if created
                else datetime.now(timezone.utc)
            )
            posts.append(
                Post(
                    platform=self.name,
                    native_id=native_id,
                    title=title,
                    published=published,
                    weight=normalise_engagement(raw, weight),
                    raw_engagement=raw,
                    url=hit.get("url") or "",
                    author=hit.get("author") or "",
                    tags=("hackernews",),
                    extra={"points": points, "comments": comments},
                )
            )
        return posts
