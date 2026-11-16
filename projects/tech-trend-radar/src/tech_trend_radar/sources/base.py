"""The adapter protocol and the registry that resolves which sources to run.

Every platform is an adapter. An adapter knows how to fetch one platform's
items and how to turn them into `Post` objects. It does not know what a topic
is, how a burst is measured, or how anything is ranked — that all happens
upstream, over the flat `Post` list every adapter produces.

Two rules keep this honest:

1. An adapter that fails returns a `FetchResult` with `ok=False` and a reason.
   It never raises into the run. One dead source must not blind the radar.
2. An adapter that needs credentials is *absent* from the registry when those
   credentials are missing, not present-and-failing.
"""

from __future__ import annotations

import time
from typing import Protocol, runtime_checkable

from ..config import Settings
from ..http import HttpClient
from ..models import FetchResult


@runtime_checkable
class SourceAdapter(Protocol):
    """One platform's fetch-and-normalise logic."""

    #: The stable platform name, used in `Post.platform` and in the registry.
    name: str

    def available(self, settings: Settings) -> bool:
        """Whether this source can run in the current configuration."""
        ...

    def fetch(self, client: HttpClient, settings: Settings) -> list:
        """Fetch and return the platform's items as `Post` objects."""
        ...


class BaseAdapter:
    """Shared plumbing: timing, error capture and the availability check.

    Subclasses implement `fetch` and may raise. `run` catches, times, and
    converts the outcome into a `FetchResult`.
    """

    name = "base"

    #: Tags that identify the source rather than the subject of a post.
    #: `hackernews` or `techcrunch` are where a post came from, not what it
    #: is about, and they must never become topics. Platform markers added
    #: by the adapters themselves are listed here so the extractor can drop
    #: them without knowing each adapter's internals.
    source_markers: frozenset[str] = frozenset()

    def available(self, settings: Settings) -> bool:
        return True

    def fetch(self, client: HttpClient, settings: Settings) -> list:
        raise NotImplementedError

    def run(self, client: HttpClient, settings: Settings) -> FetchResult:
        started = time.perf_counter()
        try:
            posts = self.fetch(client, settings)
        except Exception as exc:  # noqa: BLE001 - a dead source must not kill the run
            return FetchResult(
                platform=self.name,
                ok=False,
                error=f"{type(exc).__name__}: {exc}",
                duration_ms=(time.perf_counter() - started) * 1000,
            )
        return FetchResult(
            platform=self.name,
            posts=posts,
            ok=True,
            duration_ms=(time.perf_counter() - started) * 1000,
        )


#: The markers every adapter uses to tag its own posts with its name. These
#: are the source identifiers, not topic labels.
PLATFORM_MARKERS: frozenset[str] = frozenset(
    {
        "hackernews",
        "github",
        "stackoverflow",
        "devto",
        "youtube",
        "rss",
        "reddit",
    }
)
