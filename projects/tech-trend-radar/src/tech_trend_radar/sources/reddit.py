"""Reddit, via the OAuth API — available only when credentials are present.

Reddit's anonymous JSON endpoint answers 403 for datacenter traffic, so this
source cannot be credential-free. It is therefore *absent* from the registry
unless `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` are set, rather than
being present and failing every run.

That is the whole design: the default radar needs no account anywhere, and a
user who has one can add a source without the project needing to know.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..config import Settings
from ..http import HttpClient, normalise_engagement
from ..models import Post
from .base import BaseAdapter

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
LISTING_URL = "https://oauth.reddit.com/r/{subreddit}/new"

#: The subreddits watched when Reddit is enabled. Each one is a different
#: corner of the tech conversation, so a topic trending in more than one of
#: them is corroborated by construction.
DEFAULT_SUBREDDITS = ("technology", "programming", "artificial", "webdev")


class RedditAdapter(BaseAdapter):
    """New posts from a set of tech subreddits."""

    name = "reddit"

    def __init__(self, subreddits: tuple[str, ...] = DEFAULT_SUBREDDITS) -> None:
        self.subreddits = subreddits

    def available(self, settings: Settings) -> bool:
        return settings.reddit_enabled

    def fetch(self, client: HttpClient, settings: Settings) -> list[Post]:
        token = self._token(client, settings)
        if not token:
            return []

        headers = {"Authorization": f"bearer {token}"}
        weight = settings.platform_weight(self.name)
        seen: set[str] = set()
        posts: list[Post] = []

        for subreddit in self.subreddits:
            try:
                data = client.get_json(
                    LISTING_URL.format(subreddit=subreddit),
                    params={"limit": min(settings.limit, 50)},
                    headers=headers,
                )
            except Exception:  # noqa: BLE001 - one subreddit must not stop the rest
                continue

            for child in (data.get("data") or {}).get("children", []):
                item = child.get("data") or {}
                title = (item.get("title") or "").strip()
                native_id = str(item.get("id") or "")
                if not title or not native_id or native_id in seen:
                    continue
                seen.add(native_id)

                score = float(item.get("score") or 0)
                comments = float(item.get("num_comments") or 0)
                ratio = float(item.get("upvote_ratio") or 0)
                raw = score + comments * 0.5 + ratio * 5

                created = item.get("created_utc")
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
                        url=item.get("url_overridden_by_dest") or "",
                        author=item.get("author") or "",
                        tags=("reddit", subreddit),
                        description=(item.get("selftext") or "")[:500],
                        extra={
                            "subreddit": subreddit,
                            "score": int(score),
                            "comments": int(comments),
                        },
                    )
                )
        return posts

    def _token(self, client: HttpClient, settings: Settings) -> str:
        """Exchange the client credentials for a bearer token."""
        try:
            response = client._client.post(  # noqa: SLF001 - one deliberate use
                TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                },
                auth=(settings.reddit_client_id, settings.reddit_client_secret),
                headers={"User-Agent": settings.reddit_user_agent},
            )
            response.raise_for_status()
            return response.json().get("access_token", "")
        except Exception:  # noqa: BLE001 - a bad token must not kill the run
            return ""
