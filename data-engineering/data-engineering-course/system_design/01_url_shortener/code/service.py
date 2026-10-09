"""URL shortener — core service.

The URLShortener class is the heart of the system. It implements:

  * Deterministic short-key generation (SHA-256 + base62).
  * Custom-alias support with reserved-word check.
  * An idempotent collision loop.
  * A read-through TTL cache (Redis in prod, TTLCache here).
  * Click counters.

This module has no HTTP layer; the Flask app in `app.py` is a thin
wrapper around it. That makes the service trivially testable.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field, asdict
from typing import Optional
from urllib.parse import urlparse

from common.cache import TTLCache
from common.hashing import short_hash
from common.storage import KeyValueStore

# Reserved short keys we never hand out as custom aliases.
RESERVED_ALIASES = frozenset({
    "api", "admin", "login", "logout", "signup", "settings", "health",
    "metrics", "static", "docs", "help", "about", "terms", "privacy",
    "favicon.ico", "robots.txt",
})

# Basic URL validator. Not bulletproof, but enough for a course.
URL_RE = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)
MAX_URL_LENGTH = 2048


@dataclass
class URLRecord:
    key: str
    long_url: str
    created_at: float
    clicks: int = 0
    is_alias: bool = False
    last_clicked_at: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


class URLShortener:
    """A working URL shortener.

    >>> svc = URLShortener()
    >>> rec = svc.shorten("https://example.com/long/path")
    >>> rec.key == short_hash("https://example.com/long/path")
    True
    >>> svc.resolve(rec.key) is not None
    True
    """

    def __init__(
        self,
        store: Optional[KeyValueStore] = None,
        cache: Optional[TTLCache] = None,
        cache_ttl_seconds: float = 24 * 3600,
    ):
        self.store = store or KeyValueStore("url_shortener")
        self.cache = cache or TTLCache(ttl_seconds=cache_ttl_seconds)
        self.cache_ttl = cache_ttl_seconds

    # ---- validation ---------------------------------------------------

    @staticmethod
    def validate_url(url: str) -> None:
        if not isinstance(url, str):
            raise ValueError("url must be a string")
        if len(url) == 0:
            raise ValueError("url is empty")
        if len(url) > MAX_URL_LENGTH:
            raise ValueError(f"url too long (>{MAX_URL_LENGTH})")
        if not URL_RE.match(url):
            raise ValueError("url must be http(s) and well-formed")
        parsed = urlparse(url)
        if not parsed.netloc:
            raise ValueError("url missing host")

    @staticmethod
    def validate_alias(alias: str) -> None:
        if not isinstance(alias, str):
            raise ValueError("alias must be a string")
        if not 1 <= len(alias) <= 32:
            raise ValueError("alias length must be in [1, 32]")
        if not re.fullmatch(r"[A-Za-z0-9_\-]+", alias):
            raise ValueError("alias may only contain [A-Za-z0-9_-]")
        if alias in RESERVED_ALIASES:
            raise ValueError(f"alias '{alias}' is reserved")

    # ---- writes --------------------------------------------------------

    def shorten(self, long_url: str, alias: Optional[str] = None) -> URLRecord:
        """Shorten ``long_url``.

        Idempotent for the same long URL when no alias is supplied.
        """
        self.validate_url(long_url)

        # Branch 1: custom alias path.
        if alias is not None:
            self.validate_alias(alias)
            key = alias
            if self.store.exists(self._k(key)):
                raise ValueError(f"alias '{alias}' is already taken")
            rec = URLRecord(
                key=key,
                long_url=long_url,
                created_at=time.time(),
                is_alias=True,
            )
            self._persist(rec)
            return rec

        # Branch 2: deterministic hash path. Same URL -> same key.
        candidate = short_hash(long_url)
        existing_key = self.store.get(f"hash:{long_url}")
        if existing_key and self.store.exists(self._k(existing_key)):
            return self._load(existing_key)

        # First time we see this URL. Try a few times in case of hash collision.
        for attempt in range(5):
            key = candidate if attempt == 0 else short_hash(
                long_url + str(attempt)
            )
            if self.store.exists(self._k(key)):
                continue  # collision — try again
            rec = URLRecord(key=key, long_url=long_url, created_at=time.time())
            self._persist(rec)
            # Backwards index for idempotency.
            self.store.set(f"hash:{long_url}", key)
            return rec
        raise RuntimeError("could not generate unique short key after 5 tries")

    def _persist(self, rec: URLRecord) -> None:
        self.store.set(self._k(rec.key), rec.to_dict())
        # Write-through cache.
        self.cache.set(self._k(rec.key), rec.to_dict(), self.cache_ttl)

    # ---- reads ---------------------------------------------------------

    def resolve(self, key: str) -> Optional[URLRecord]:
        """Resolve a short key to its record, populating the cache."""
        cache_key = self._k(key)
        cached = self.cache.get(cache_key)
        if cached:
            return URLRecord(**cached)
        if not self.store.exists(cache_key):
            return None
        rec = self._load(key)
        if rec:
            self.cache.set(cache_key, rec.to_dict(), self.cache_ttl)
        return rec

    def record_click(self, key: str) -> None:
        """Increment the click counter for ``key``."""
        rec = self.resolve(key)
        if not rec:
            return
        rec.clicks += 1
        rec.last_clicked_at = time.time()
        self._persist(rec)

    # ---- stats ---------------------------------------------------------

    def stats(self, key: str) -> Optional[dict]:
        rec = self.resolve(key)
        return rec.to_dict() if rec else None

    def total(self) -> int:
        return sum(1 for k, _ in self.store.scan("url:") if k.startswith("url:"))

    def cache_stats(self) -> dict:
        return self.cache.stats()

    # ---- internals -----------------------------------------------------

    @staticmethod
    def _k(key: str) -> str:
        return f"url:{key}"

    def _load(self, key: str) -> Optional[URLRecord]:
        data = self.store.get(self._k(key))
        if not data:
            return None
        return URLRecord(**data)
