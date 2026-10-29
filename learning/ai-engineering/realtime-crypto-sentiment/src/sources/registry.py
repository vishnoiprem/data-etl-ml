"""Source adapter registry with auto-fallback.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""
from __future__ import annotations

import time

from loguru import logger

from src.config import settings
from src.sources.apify_x import ApifyXAdapter
from src.sources.base import AdapterError, RawTweet
from src.sources.nitter_mirror import NitterMirrorAdapter
from src.sources.syndication import SyndicationAdapter


class SourceRegistry:
    """Resolves which adapter to use, in priority order:

    1. Apify (if `tweet_source=apify` or `auto` with `APIFY_TOKEN` set)
    2. Nitter mirrors (mostly dead since 2024)
    3. syndication.twitter.com fallback (rate-limited)

    Caches the working adapter for 10 minutes.
    """

    def __init__(
        self,
        apify: ApifyXAdapter | None,
        nitter: NitterMirrorAdapter,
        syndication: SyndicationAdapter,
    ):
        self.apify = apify
        self.nitter = nitter
        self.syndication = syndication
        self._active: str = "nitter"
        self._active_until: float = 0.0

    @classmethod
    def from_settings(cls) -> SourceRegistry:
        apify = None
        if settings.apify_token or settings.tweet_source in ("apify", "auto"):
            apify = ApifyXAdapter(
                token=settings.apify_token,
                actor=settings.apify_actor,
                max_wait_sec=settings.apify_max_wait_sec,
            )
        return cls(
            apify=apify,
            nitter=NitterMirrorAdapter(
                mirrors=settings.mirrors,
                user_agent=settings.user_agent,
            ),
            syndication=SyndicationAdapter(user_agent=settings.user_agent),
        )

    @property
    def active(self) -> str:
        if time.monotonic() > self._active_until:
            return "auto"
        return self._active

    def is_healthy(self) -> bool:
        """True if any configured adapter is reachable. Order checked:
        Apify (if configured) → Nitter → Syndication (always True).

        Used by healthcheck endpoints / CLI `--check` to surface the
        pipeline's data-source availability without doing a real fetch.
        """
        if self.apify and self.apify.is_healthy():
            return True
        if self.nitter.is_healthy():
            return True
        # Syndication always reports healthy (it doesn't rate-limit us
        # in practice); see SyndicationAdapter.is_healthy.
        return self.syndication.is_healthy()

    async def fetch(self, query: str, max_results: int = 30) -> list[RawTweet]:
        # 1) Apify (preferred when configured)
        if self.apify and self.apify.is_healthy():
            try:
                result = await self.apify.fetch(query, max_results)
                if result:
                    self._active = "apify"
                    self._active_until = time.monotonic() + 600
                    return result
                logger.debug(f"apify returned 0 tweets for {query!r}; trying next")
            except AdapterError as e:
                logger.warning(f"apify failed: {e}; trying nitter")

        # 2) Nitter mirrors
        if self.nitter.is_healthy():
            try:
                result = await self.nitter.fetch(query, max_results)
                if result:
                    self._active = "nitter"
                    self._active_until = time.monotonic() + 600
                    return result
            except AdapterError as e:
                logger.warning(f"nitter failed: {e}; falling back to syndication")

        # 3) Syndication
        try:
            result = await self.syndication.fetch(query, max_results)
            self._active = "syndication"
            self._active_until = time.monotonic() + 600
            return result
        except AdapterError as e:
            logger.error(f"all sources failed for query {query!r}: {e}")
            return []

    async def close(self) -> None:
        if self.apify:
            await self.apify.close()
        await self.nitter.close()
        await self.syndication.close()
