"""Syndication.pub JSON adapter (fallback for Nitter).

Author: Prem Vishnoi <pvishnoi@avilx.com>

Uses `https://syndication.twitter.com/srv/timeline-profile/screen-name/{handle}`
which returns a JSON object with timeline entries. The endpoint
requires the screen-name (handle), not a free-text query — so this
adapter is useful for **profile polling**, not for cashtag search.

If you want to use it as a fallback, configure handles in your .env
(e.g. `@Bitcoin`, `@ethereum`, `@solaborate`). The adapter takes a
"query" string but interprets it as a handle (strip leading @).
"""
from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests
from loguru import logger

from src.sources.base import AdapterError, RawTweet, SourceAdapter


class SyndicationAdapter(SourceAdapter):
    name = "syndication"

    ENDPOINT = "https://syndication.twitter.com/srv/timeline-profile/screen-name/{handle}"

    def __init__(
        self,
        user_agent: str = "Mozilla/5.0",
        timeout: float = 5.0,
    ):
        self.user_agent = user_agent
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
        self._last_used: float = 0.0
        self._min_gap: float = 2.0  # generous: 1 req per 2s

    async def fetch(self, query: str, max_results: int = 30) -> List[RawTweet]:
        handle = query.lstrip("@").strip()
        if not handle:
            raise AdapterError("empty handle")

        gap = time.monotonic() - self._last_used
        if gap < self._min_gap:
            await asyncio.sleep(self._min_gap - gap)
        self._last_used = time.monotonic()

        url = self.ENDPOINT.format(handle=handle)
        try:
            resp = await asyncio.to_thread(self.session.get, url, timeout=self.timeout)
        except requests.RequestException as e:
            raise AdapterError(f"GET {url}: {e}")

        if resp.status_code != 200:
            raise AdapterError(f"{resp.status_code} from syndication for {handle}")
        try:
            data = resp.json()
        except ValueError as e:
            raise AdapterError(f"non-JSON response from syndication: {e}")

        return self._parse(data, max_results)

    def is_healthy(self) -> bool:
        return True  # syndication rarely rate-limits profiles

    async def close(self) -> None:
        self.session.close()

    def _parse(self, data: dict, max_results: int) -> List[RawTweet]:
        # Timeline entries live under data["timeline"]["entries"]; each has
        # .tweet.id_str, .tweet.text, .tweet.user.screen_name, etc.
        out: List[RawTweet] = []
        entries = (data.get("timeline", {}) or {}).get("entries", []) or []
        for entry in entries[:max_results]:
            tweet = (entry.get("tweet") or {})
            if not tweet:
                continue
            try:
                tid = int(tweet.get("id_str", 0))
                txt = tweet.get("text", "") or ""
                # Strip URLs and resolve entities for hashtags/cashtags
                txt = self._clean_text(txt)
                user = tweet.get("user", {}) or {}
                author = user.get("name") or user.get("screen_name") or "unknown"
                # Stats
                likes = int(tweet.get("favorite_count", 0) or 0)
                retweets = int(tweet.get("retweet_count", 0) or 0)
                followers = int(user.get("followers_count", 0) or 0)
                # Timestamp
                ts_str = tweet.get("created_at", "")
                ts = self._parse_twitter_date(ts_str) or datetime.now(timezone.utc)
                url = f"https://twitter.com/{user.get('screen_name', '')}/status/{tid}"

                out.append(
                    RawTweet(
                        id=tid,
                        ts=ts,
                        author=author,
                        text=txt,
                        likes=likes,
                        retweets=retweets,
                        followers=followers,
                        url=url,
                        symbol_tags=[],
                    )
                )
            except Exception as e:
                logger.debug(f"syndication parse skip: {e}")
                continue
        return out

    @staticmethod
    def _clean_text(text: str) -> str:
        # Replace pic.twitter.com URLs and t.co links with empty
        import re
        text = re.sub(r"https?://\S+", "", text)
        # Decode common HTML entities
        text = (
            text.replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
            .replace("&#39;", "'")
        )
        return text.strip()

    @staticmethod
    def _parse_twitter_date(s: str) -> Optional[datetime]:
        if not s:
            return None
        try:
            # Twitter format: "Wed Oct 10 13:45:21 +0000 2026"
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(s)
        except (TypeError, ValueError):
            return None
