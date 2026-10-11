"""Apify X.com scraper adapter.

Real X.com data via Apify's hosted scrapers (rotating residential IPs,
ToS-clean by being a paid service). The Actor runs in Apify's cloud,
returns JSON, and we normalize to the project's `RawTweet` shape.

Default Actor: `dannyquek/x-twitter-scraper` — well-maintained, ~$0.40
per 1k tweets. Fallback: `apidojo/tweet-scraper` if the first is down.

Setup (5 min, free tier works):
  1. Sign up at https://apify.com (no card required for free tier;
     $5 monthly credit is enough for ~12k tweets).
  2. Account → Settings → Integrations → Personal API tokens → copy.
  3. Add to .env:  APIFY_TOKEN=apify_api_xxxxxxxxxxxxxxxx
  4. Set source:   TWEET_SOURCE=apify

API:
  POST https://api.apify.com/v2/acts/{actor}/runs
  Body: { "searchTerms": [...], "tweetsDesired": N, ... }
  → returns { id: run_id, ... }
  GET  /v2/actor-runs/{run_id}/dataset/items → list[tweet]
  Or:   /v2/datasets/{dataset_id}/items

Cost model:
  ~$0.0003-0.0005 per tweet on the default Actor. The free tier
  ($5/mo) buys ~12k tweets, plenty for the demo and 5-min polling
  against ~10 tracked tags.
"""
from __future__ import annotations

import asyncio
import os
import time
from datetime import UTC, datetime
from typing import Any

import requests
from loguru import logger

from src.sources.base import AdapterError, RawTweet, SourceAdapter

# Apify X.com scraper Actors. First is the default; the rest are
# fallbacks if the primary is unavailable or rate-limited.
DEFAULT_ACTORS = [
    "dannyquek/x-twitter-scraper",       # ~$0.40/1k, fast
    "apidojo/tweet-scraper",             # ~$0.50/1k, well-tested
    "kaitoeasyapi/twitter-x-scraper",    # alternative
]


class ApifyXAdapter(SourceAdapter):
    """Adapter for Apify-hosted X.com scrapers.

    Runs are async on Apify's side; we poll the run-status endpoint
    until SUCCEEDED, then pull the dataset. Total turn-around is
    usually 10-60s for ~20 tweets.
    """

    name = "apify"

    def __init__(
        self,
        token: str | None = None,
        actor: str | None = None,
        max_wait_sec: int = 90,
        poll_interval_sec: float = 2.0,
    ):
        self.token = token or os.environ.get("APIFY_TOKEN", "")
        self.actor = actor or os.environ.get("APIFY_ACTOR", DEFAULT_ACTORS[0])
        self.max_wait_sec = max_wait_sec
        self.poll_interval_sec = poll_interval_sec
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        # Health-check cache: avoid hitting /v2/users/me on every fetch().
        # Token doesn't change at runtime, so 5-min cache is fine.
        self._health_checked_at: float = 0.0
        self._health_ok: bool = False

    # ── Public API ──────────────────────────────────────────────────

    def is_healthy(self, force_check: bool = False) -> bool:
        """Cheap liveness check: /v2/users/me with our token.

        Cached for 5 minutes (or until `force_check=True`).
        """
        if not self.token:
            return False
        now = time.monotonic()
        if not force_check and (now - self._health_checked_at) < 300:
            return self._health_ok
        try:
            r = self.session.get(
                "https://api.apify.com/v2/users/me", timeout=5
            )
            self._health_ok = r.status_code == 200
        except requests.RequestException as e:
            logger.debug(f"apify health check failed: {e}")
            self._health_ok = False
        self._health_checked_at = now
        return self._health_ok

    async def fetch(self, query: str, max_results: int = 30) -> list[RawTweet]:
        """Run an Actor for one search term, return up to `max_results` tweets.

        Most Apify X scrapers take a list of search terms and a
        `tweetsDesired` count. We send [query] with `max_results * 1.5`
        to leave room for parsing dedupes.
        """
        if not self.token:
            raise AdapterError("APIFY_TOKEN not set — see src/sources/apify_x.py docstring")

        run_id = await self._start_run(query, max_results)
        items = await self._wait_for_dataset(run_id)
        tweets = [self._parse_item(it, query) for it in items if it]
        tweets = [t for t in tweets if t is not None]
        return tweets[:max_results]

    async def close(self) -> None:
        self.session.close()

    # ── Internals ───────────────────────────────────────────────────

    async def _start_run(self, query: str, max_results: int) -> str:
        """Kick off an Actor run, return the run id."""
        url = f"https://api.apify.com/v2/acts/{self.actor}/runs"
        # Payload shape differs slightly per Actor; the dannyquek one
        # accepts `searchTerms` + `tweetsDesired` (others similar).
        payload = {
            "searchTerms": [query.lstrip("$#")],
            "tweetsDesired": max(int(max_results * 1.5), 20),
            "includeSearchTerms": False,
            "lang": "en",
        }
        try:
            resp = await asyncio.to_thread(
                self.session.post, url, json=payload, timeout=15
            )
        except requests.RequestException as e:
            raise AdapterError(f"start_run network error: {e}")
        if resp.status_code in (401, 403):
            raise AdapterError(
                f"apify auth failed ({resp.status_code}) — check APIFY_TOKEN"
            )
        if resp.status_code == 404:
            raise AdapterError(
                f"apify actor {self.actor!r} not found — try setting APIFY_ACTOR env"
            )
        if resp.status_code >= 400:
            raise AdapterError(f"apify start_run {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        run_id = data.get("data", {}).get("id")
        if not run_id:
            raise AdapterError(f"apify returned no run id: {data}")
        logger.debug(f"apify run started: id={run_id} query={query!r}")
        return run_id

    async def _wait_for_dataset(self, run_id: str) -> list[dict]:
        """Poll run status until SUCCEEDED, then return dataset items."""
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
        deadline = time.monotonic() + self.max_wait_sec
        last_status = "UNKNOWN"
        while time.monotonic() < deadline:
            try:
                resp = await asyncio.to_thread(
                    self.session.get, status_url, timeout=10
                )
            except requests.RequestException as e:
                logger.debug(f"apify poll network error: {e}")
                await asyncio.sleep(self.poll_interval_sec)
                continue
            if resp.status_code >= 400:
                raise AdapterError(f"apify status {resp.status_code}: {resp.text[:200]}")
            data = resp.json()
            last_status = data.get("data", {}).get("status", "UNKNOWN")
            if last_status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
                break
            await asyncio.sleep(self.poll_interval_sec)
        if last_status != "SUCCEEDED":
            raise AdapterError(
                f"apify run {run_id} ended with status {last_status}"
            )

        # Pull dataset
        dataset_id = (
            data.get("data", {}).get("defaultDatasetId")
            or data.get("data", {}).get("datasetId")
        )
        if not dataset_id:
            raise AdapterError("apify run succeeded but no dataset id")
        items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
        resp = await asyncio.to_thread(self.session.get, items_url, timeout=30)
        if resp.status_code >= 400:
            raise AdapterError(f"apify dataset fetch {resp.status_code}")
        items = resp.json()
        if not isinstance(items, list):
            raise AdapterError(f"apify dataset not a list: {type(items)}")
        return items

    @staticmethod
    def _parse_item(it: dict[str, Any], query: str) -> RawTweet | None:
        """Map an Apify X.com scraper output row to `RawTweet`.

        Different Actors use slightly different field names; we handle
        the common ones (dannyquek, apidojo, kaitoeasyapi).
        """
        try:
            # ID — Apify uses string tweet ids
            tid = it.get("id") or it.get("tweetId") or it.get("tweet_id")
            if tid is None:
                return None
            tid = int(tid)

            # Timestamp
            ts_raw = (
                it.get("createdAt")
                or it.get("created_at")
                or it.get("timestamp")
                or it.get("date")
            )
            if isinstance(ts_raw, (int, float)):
                # Some Actors return epoch ms
                ts_raw = ts_raw / 1000.0 if ts_raw > 1e12 else ts_raw
                ts = datetime.fromtimestamp(float(ts_raw), tz=UTC)
            elif isinstance(ts_raw, str):
                ts = _parse_iso(ts_raw)
            else:
                ts = datetime.now(UTC)

            # Author
            author = (
                it.get("author", {}).get("userName")
                if isinstance(it.get("author"), dict)
                else None
            ) or it.get("username") or it.get("userName") or it.get("user") or "unknown"

            # Text
            text = (
                it.get("text")
                or it.get("full_text")
                or it.get("fullText")
                or it.get("tweetText")
                or ""
            )

            # Engagement
            likes = int(it.get("likeCount", it.get("likes", 0)) or 0)
            retweets = int(it.get("retweetCount", it.get("retweets", it.get("retweet_count", 0))) or 0)
            followers = 0
            if isinstance(it.get("author"), dict):
                followers = int(it["author"].get("followers", 0) or 0)

            # URL
            url = it.get("url") or it.get("tweetUrl") or it.get("tweet_url") or ""
            if not url and it.get("author", {}).get("userName"):
                uname = it["author"]["userName"]
                url = f"https://x.com/{uname}/status/{tid}"

            return RawTweet(
                id=tid,
                ts=ts,
                author=author if isinstance(author, str) else str(author),
                text=text,
                likes=likes,
                retweets=retweets,
                followers=followers,
                url=url,
                symbol_tags=[query] if query else [],
            )
        except (ValueError, TypeError, KeyError) as e:
            logger.debug(f"apify parse skip: {e} on row {it.get('id')}")
            return None


def _parse_iso(s: str) -> datetime:
    """Parse an ISO-8601 string, tolerating trailing 'Z'."""
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        # Last-ditch: try common date formats
        for fmt in ("%Y-%m-%d %H:%M:%S", "%a %b %d %H:%M:%S %z %Y", "%Y-%m-%dT%H:%M:%S.%f"):
            try:
                dt = datetime.strptime(s, fmt)
                break
            except ValueError:
                continue
        else:
            return datetime.now(UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)
