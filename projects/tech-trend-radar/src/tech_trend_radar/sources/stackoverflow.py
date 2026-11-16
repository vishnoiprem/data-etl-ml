"""Stack Overflow, via the public StackExchange API.

One request per tag, not one request for all of them. The `tagged`
parameter takes a semicolon-separated union, but the API silently returns
*zero results* for a union of five or more tags — and even at three or four
the result count collapses, because the query is an AND across the union
members rather than a true OR. Asking one tag at a time and merging the
results is the only way to actually see every tag's questions.

The `/questions` endpoint with `sort=creation` gives the recency signal and
the tag list gives the topic. StackExchange enforces a daily quota per IP
(300 as of writing); one call per watched tag stays well inside it.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..config import STACKOVERFLOW_TAGS, Settings
from ..http import HttpClient, normalise_engagement
from ..models import Post
from .base import BaseAdapter

QUESTIONS_URL = "https://api.stackexchange.com/2.3/questions"

#: The watched tags, as a tuple. The semicolon form is kept in config for
#: reference, but each tag is queried separately for the reason above.
WATCHED_TAGS = tuple(t for t in STACKOVERFLOW_TAGS.split(";") if t)


class StackOverflowAdapter(BaseAdapter):
    """Recently asked questions across the watched tags."""

    name = "stackoverflow"

    def fetch(self, client: HttpClient, settings: Settings) -> list[Post]:
        weight = settings.platform_weight(self.name)
        posts: list[Post] = []
        seen: set[str] = set()

        for tag in WATCHED_TAGS:
            try:
                data = client.get_json(
                    QUESTIONS_URL,
                    params={
                        "site": "stackoverflow",
                        "order": "desc",
                        "sort": "creation",
                        "pagesize": min(settings.limit, 100),
                        "tagged": tag,
                    },
                )
            except Exception:  # noqa: BLE001 - one tag must not stop the others
                continue

            for item in data.get("items", []):
                post = self._to_post(item, weight)
                if post is None or post.native_id in seen:
                    continue
                seen.add(post.native_id)
                posts.append(post)
        return posts

    def _to_post(self, item: dict, weight: float) -> Post | None:
        title = (item.get("title") or "").strip()
        if not title:
            return None

        score = float(item.get("score") or 0)
        answers = float(item.get("answer_count") or 0)
        views = float(item.get("view_count") or 0)
        # Views are unbounded and accumulate forever, so they are damped
        # heavily relative to votes and answers, which are both current.
        raw = max(score, 0) + answers * 1.5 + views * 0.01

        created = item.get("creation_date")
        published = (
            datetime.fromtimestamp(created, tz=timezone.utc)
            if created
            else datetime.now(timezone.utc)
        )

        return Post(
            platform=self.name,
            native_id=str(item.get("question_id")),
            title=title,
            published=published,
            weight=normalise_engagement(raw, weight),
            raw_engagement=raw,
            url=item.get("link") or "",
            author=(item.get("owner") or {}).get("display_name", ""),
            tags=tuple(item.get("tags") or ()),
            extra={
                "score": int(score),
                "answers": int(answers),
                "views": int(views),
                "is_answered": bool(item.get("is_answered")),
            },
        )
