"""Nitter public-mirror adapter.

Author: Prem Vishnoi <pvishnoi@avilx.com>

Scrapes public Nitter mirrors (e.g. nitter.net, nitter.privacydev.net).
Uses BeautifulSoup to parse tweet HTML.

Politeness:
- 1 request per second per mirror (token bucket)
- 30s minimum gap between requests to the same mirror
- 24h denylist after a 403
- Rotates mirrors on failure

Notes:
- Nitter HTML structure: `.timeline-item` for tweets, `.tweet-content` for
  body, `.tweet-date a` for URL, `.icon-heart`, `.icon-retweet`, etc. for
  counters. This module is robust to small class-name variations.
"""
from __future__ import annotations

import asyncio
import hashlib
import re
import time
from datetime import UTC, datetime

import requests
from bs4 import BeautifulSoup
from loguru import logger

from src.sources.base import AdapterError, RawTweet, SourceAdapter

# ── Politeness primitives ──────────────────────────────────────────────


class TokenBucket:
    """Refills 1 token per `rate` seconds; max `burst` tokens."""

    def __init__(self, rate: float = 1.0, burst: int = 2):
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.last
                self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
                self.last = now
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                wait = (1.0 - self.tokens) / self.rate
                await asyncio.sleep(wait)


# ── Adapter ────────────────────────────────────────────────────────────


class NitterMirrorAdapter(SourceAdapter):
    name = "nitter"

    def __init__(
        self,
        mirrors: list[str],
        user_agent: str = "Mozilla/5.0",
        timeout: float = 5.0,
        min_mirror_gap_sec: float = 30.0,
        deny_duration_sec: float = 24 * 3600,
    ):
        self.mirrors = list(mirrors)
        self.user_agent = user_agent
        self.timeout = timeout
        self.min_mirror_gap_sec = min_mirror_gap_sec
        self.deny_duration_sec = deny_duration_sec

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
        self.bucket = TokenBucket(rate=1.0, burst=2)
        self._mirror_last_used: dict[str, float] = {}
        self._mirror_denied_until: dict[str, float] = {}
        # Mirror that served the last successful fetch (used for URL rewriting).
        self._active_mirror: str | None = None

    # ── Public API ───────────────────────────────────────────────────

    async def fetch(self, query: str, max_results: int = 30) -> list[RawTweet]:
        """Fetch a query by trying each healthy mirror in turn.

        Returns a (possibly empty) list. Raises AdapterError only if
        every mirror is denylisted OR every attempt errors out.
        """
        if not self.mirrors:
            raise AdapterError("no mirrors configured")

        clean_q = self._normalize_query(query)
        last_err: Exception | None = None
        for mirror in self._healthy_mirrors():
            try:
                html = await self._fetch_one(mirror, clean_q)
                self._active_mirror = mirror
                return self._parse(html, query, max_results)
            except AdapterError as e:
                last_err = e
                logger.warning(f"nitter[{mirror}] failed: {e}; rotating")
                continue
        raise AdapterError(f"all mirrors failed: {last_err}")

    def is_healthy(self) -> bool:
        return bool(self._healthy_mirrors())

    async def close(self) -> None:
        self.session.close()

    # ── Internals ────────────────────────────────────────────────────

    def _healthy_mirrors(self) -> list[str]:
        now = time.monotonic()
        return [
            m for m in self.mirrors
            if self._mirror_denied_until.get(m, 0) <= now
        ]

    def _normalize_query(self, q: str) -> str:
        q = q.strip()
        # Nitter's search uses the `q` param; cashtags/hashtags go through verbatim.
        if q.startswith(("$", "#")):
            return q.lstrip("$#")
        return q

    async def _fetch_one(self, mirror: str, query: str) -> str:
        # Respect min gap between requests to same mirror
        last = self._mirror_last_used.get(mirror, 0.0)
        gap = time.monotonic() - last
        if gap < self.min_mirror_gap_sec:
            await asyncio.sleep(self.min_mirror_gap_sec - gap)

        await self.bucket.acquire()
        url = f"https://{mirror}/search?f=tweets&q={requests.utils.quote(query)}"

        try:
            # requests is sync; run in a thread to keep the adapter async-friendly
            resp = await asyncio.to_thread(self.session.get, url, timeout=self.timeout)
        except requests.RequestException as e:
            raise AdapterError(f"GET {url}: {e}")

        self._mirror_last_used[mirror] = time.monotonic()

        if resp.status_code == 403:
            self._mirror_denied_until[mirror] = time.monotonic() + self.deny_duration_sec
            raise AdapterError(f"403 from {mirror} (denied for 24h)")
        if resp.status_code == 429:
            raise AdapterError(f"429 from {mirror} (rate limit)")
        if resp.status_code >= 400:
            raise AdapterError(f"{resp.status_code} from {mirror}")
        if not resp.text:
            raise AdapterError(f"empty body from {mirror}")

        return resp.text

    def _parse(self, html: str, query: str, max_results: int) -> list[RawTweet]:
        soup = BeautifulSoup(html, "lxml")
        items = soup.select(".timeline-item")
        if not items:
            # alternate selectors (some mirrors use different classes)
            items = soup.select(".tweet")

        tweets: list[RawTweet] = []
        for item in items[:max_results]:
            try:
                tweets.append(self._parse_one(item, query))
            except Exception as e:
                logger.debug(f"nitter parse skip: {e}")
                continue
        return tweets

    def _parse_one(self, item, query: str) -> RawTweet:
        # Author
        author_el = item.select_one(".fullname, .tweet-name, .display-name")
        author = (author_el.get_text(strip=True) if author_el else "unknown") or "unknown"

        # Text
        text_el = item.select_one(".tweet-content, .tweet-body")
        text = (text_el.get_text(" ", strip=True) if text_el else "") or ""

        # URL / id
        link_el = item.select_one(".tweet-link, .tweet-date a, a.tweet-link")
        url = link_el["href"] if link_el and link_el.has_attr("href") else ""
        # Preserve the mirror we actually scraped from so the URL isn't a 404.
        if url.startswith("/"):
            url = f"https://{self._active_mirror or self.mirrors[0]}{url}"
        # NOTE: cannot use `or` here — tweet_id=0 is a valid id, and
        # `0 or stable_id` would short-circuit to the stable_id fallback.
        extracted = self._extract_id(url)
        tweet_id = extracted if extracted is not None else self._stable_id(text, author)

        # Stats
        likes = self._parse_stat(item, ".icon-heart, .heart, [data-count-likes]")
        retweets = self._parse_stat(item, ".icon-retweet, .retweet, [data-count-retweets]")
        self._parse_stat(item, ".icon-comment, .reply, [data-count-replies]")

        # Timestamp — best-effort; fall back to now
        ts = self._parse_timestamp(item)

        return RawTweet(
            id=int(tweet_id),
            ts=ts,
            author=author,
            text=text,
            likes=likes,
            retweets=retweets,
            followers=0,
            url=url,
            symbol_tags=[query] if query else [],
        )

    @staticmethod
    def _extract_id(url: str) -> int | None:
        if not url:
            return None
        # Nitter URLs: /user/status/1234567890
        m = re.search(r"/status/(\d+)", url)
        if m:
            return int(m.group(1))
        # Or just a trailing number
        m = re.search(r"(\d{10,})", url)
        return int(m.group(1)) if m else None

    @staticmethod
    def _stable_id(text: str, author: str) -> int:
        """Deterministic id for tweets without a status URL.

        Uses sha1 (process-independent) so the same (text, author) yields
        the same id across restarts. With this, the (tweet_id, ts) ON CONFLICT
        idempotency in db.upsert_tweet actually works.
        """
        h = hashlib.sha1(f"{author}::{text}".encode()).hexdigest()
        # Take the first 10 hex chars, max 0xFFFFFFFFFF (just under 2^40)
        return int(h[:10], 16)

    @staticmethod
    def _parse_stat(item, selector: str) -> int:
        el = item.select_one(selector)
        if not el:
            return 0
        # Try data-count-* attribute
        for attr in ("data-count", "data-count-likes", "data-count-retweets", "data-count-replies"):
            v = el.get(attr)
            if v and str(v).isdigit():
                return int(v)
        txt = el.get_text(strip=True)
        if not txt:
            return 0
        # Nitter shows "1.2K" etc.
        txt = txt.replace(",", "").upper().strip()
        m = re.match(r"^([\d.]+)([KM]?)$", txt)
        if not m:
            return 0
        n, suffix = float(m.group(1)), m.group(2)
        if suffix == "K":
            n *= 1_000
        elif suffix == "M":
            n *= 1_000_000
        return int(n)

    @staticmethod
    def _parse_timestamp(item) -> datetime:
        # Look for <span title="..."> in date anchor
        date_el = item.select_one(".tweet-date a, .tweet-published")
        if date_el and date_el.has_attr("title"):
            from email.utils import parsedate_to_datetime
            try:
                return parsedate_to_datetime(date_el["title"])
            except (TypeError, ValueError):
                pass
        return datetime.now(UTC)
