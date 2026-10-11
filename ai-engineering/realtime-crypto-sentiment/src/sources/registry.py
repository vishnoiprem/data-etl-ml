"""Source adapter registry with auto-fallback.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""
from __future__ import annotations

import asyncio
import time
from typing import List, Optional

from loguru import logger

from src.config import settings
from src.sources.base import AdapterError, RawTweet, SourceAdapter
from src.sources.nitter_mirror import NitterMirrorAdapter
from src.sources.syndication import SyndicationAdapter


class SourceRegistry:
    """Tries Nitter mirrors first; falls back to syndication.pub on AdapterError.

    Caches the working adapter for 10 minutes.
    """

    def __init__(self, nitter: NitterMirrorAdapter, syndication: SyndicationAdapter):
        self.nitter = nitter
        self.syndication = syndication
        self._active: str = "nitter"
        self._active_until: float = 0.0

    @classmethod
    def from_settings(cls) -> "SourceRegistry":
        return cls(
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

    async def fetch(self, query: str, max_results: int = 30) -> List[RawTweet]:
        if self._active == "nitter" and self.nitter.is_healthy():
            try:
                result = await self.nitter.fetch(query, max_results)
                self._active_until = time.monotonic() + 600  # 10 min
                return result
            except AdapterError as e:
                logger.warning(f"nitter failed: {e}; falling back to syndication")

        # Fallback path
        try:
            result = await self.syndication.fetch(query, max_results)
            self._active = "syndication"
            self._active_until = time.monotonic() + 600
            return result
        except AdapterError as e:
            logger.error(f"all sources failed for query {query!r}: {e}")
            return []

    async def close(self) -> None:
        await self.nitter.close()
        await self.syndication.close()
