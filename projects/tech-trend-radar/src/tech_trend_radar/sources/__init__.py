"""The source registry.

`build_adapters` returns the adapters that can actually run right now. A
source that needs credentials and does not have them is left out entirely, so
`/sources` reports what is live rather than what is configured.

Every adapter is wrapped in `BaseAdapter.run`, which times it and converts a
failure into a `FetchResult` with `ok=False`. One dead source costs that
source's data, not the whole run.
"""

from __future__ import annotations

from ..config import Settings
from .base import BaseAdapter, SourceAdapter
from .devto import DevToAdapter
from .github import GitHubAdapter
from .hackernews import HackerNewsAdapter
from .reddit import RedditAdapter
from .rss import RSSAdapter, YouTubeAdapter
from .stackoverflow import StackOverflowAdapter

__all__ = [
    "BaseAdapter",
    "DevToAdapter",
    "GitHubAdapter",
    "HackerNewsAdapter",
    "RedditAdapter",
    "RSSAdapter",
    "SourceAdapter",
    "StackOverflowAdapter",
    "YouTubeAdapter",
    "build_adapters",
]


def build_adapters(settings: Settings | None = None) -> list[BaseAdapter]:
    """The adapters that can run under this configuration."""
    settings = settings or Settings()
    disabled = {s.lower() for s in settings.disabled_sources}

    candidates: list[BaseAdapter] = [
        HackerNewsAdapter(),
        GitHubAdapter(),
        StackOverflowAdapter(),
        DevToAdapter(),
        YouTubeAdapter(),
        RSSAdapter(),
        RedditAdapter(),
    ]

    return [
        adapter
        for adapter in candidates
        if adapter.name not in disabled and adapter.available(settings)
    ]
