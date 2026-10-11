"""Source adapter base class + shared types.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


class AdapterError(RuntimeError):
    """Raised when a source adapter cannot fetch."""


@dataclass
class RawTweet:
    id: int
    ts: datetime
    author: str
    text: str
    likes: int = 0
    retweets: int = 0
    followers: int = 0
    url: str = ""
    symbol_tags: List[str] = field(default_factory=list)

    def matches(self, symbols: List[str]) -> List[str]:
        """Return the subset of `symbols` mentioned in `text` (case-insensitive)."""
        lower = self.text.lower()
        return [s for s in symbols if s.lower() in lower]


class SourceAdapter(ABC):
    """Pluggable interface for tweet sources.

    Implementations: NitterMirrorAdapter, SyndicationAdapter.
    """

    name: str = "abstract"

    @abstractmethod
    async def fetch(self, query: str, max_results: int = 30) -> List[RawTweet]:
        """Return up to `max_results` tweets matching `query`."""
        raise NotImplementedError

    @abstractmethod
    def is_healthy(self) -> bool:
        """Return True if the adapter is in a usable state."""
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """Release any open resources (sessions, sockets)."""
        raise NotImplementedError
