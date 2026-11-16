"""Shared fixtures.

Every test in this suite is hermetic: no network, no API key, no Docker.
The fixtures build synthetic corpora rather than reading the live snapshot,
so the tests are deterministic and do not depend on what happened to be
trending on the day they run.
"""

from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone

import pytest

from tech_trend_radar.config import Settings
from tech_trend_radar.models import FetchResult, Post

#: A fixed reference time. Every test that needs "now" uses this, so the
#: time windows are deterministic.
NOW = datetime(2026, 11, 15, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def now() -> datetime:
    return NOW


@pytest.fixture
def settings() -> Settings:
    """Settings with the default windows."""
    return Settings()


def make_post(
    native_id: str,
    title: str,
    platform: str = "hackernews",
    hours_ago: float = 1.0,
    weight: float = 1.0,
    tags: tuple[str, ...] = (),
    url: str = "",
    reference: datetime | None = None,
) -> Post:
    """A synthetic post."""
    base = reference or NOW
    return Post(
        platform=platform,
        native_id=native_id,
        title=title,
        published=base - timedelta(hours=hours_ago),
        weight=weight,
        raw_engagement=100.0,
        url=url or f"https://example.invalid/{native_id}",
        tags=tags,
    )


@pytest.fixture
def post_factory():
    """A factory for synthetic posts."""
    return make_post


@pytest.fixture
def accelerating_corpus(post_factory):
    """A corpus with two accelerating topics and two steady ones.

    The accelerating topics get 9 recent mentions and 1 in the baseline.
    The steady topics get 4 recent and 4 in the baseline — the same rate,
    so no acceleration.
    """
    posts = []
    platforms = ("hackernews", "devto", "stackoverflow")

    for topic in ("rust", "kubernetes"):
        for n in range(9):
            posts.append(
                post_factory(
                    f"acc-{topic}-{n}",
                    f"Everything about {topic} you need to know",
                    platform=platforms[n % 3],
                    hours_ago=2 + n,
                )
            )
        posts.append(
            post_factory(
                f"acc-{topic}-old",
                f"Older post about {topic}",
                hours_ago=24 * 5,
            )
        )

    for topic in ("python", "docker"):
        for n in range(4):
            posts.append(
                post_factory(
                    f"steady-{topic}-{n}",
                    f"Working with {topic} today",
                    platform=platforms[n % 3],
                    hours_ago=6 + n * 4,
                )
            )
            posts.append(
                post_factory(
                    f"steady-{topic}-old-{n}",
                    f"Older work with {topic}",
                    platform=platforms[n % 3],
                    hours_ago=24 * 3 + n,
                )
            )

    return posts


@pytest.fixture
def fetch_result() -> FetchResult:
    """A FetchResult with a couple of posts."""
    return FetchResult(
        platform="hackernews",
        posts=[
            make_post("1", "Rust 1.90 is out", hours_ago=1),
            make_post("2", "Postgres 18 released", hours_ago=2),
        ],
        ok=True,
    )


@pytest.fixture
def semantic_matcher():
    """A real semantic matcher, or None when the model is not installed.

    The tests that use it are skipped when it is None, so the suite still
    runs on a machine without `sentence-transformers`.
    """
    from tech_trend_radar.semantic import SemanticMatcher

    if not _model_installed():
        return None
    matcher = SemanticMatcher()
    return matcher if matcher.available else None


def _model_installed() -> bool:
    """Whether `sentence-transformers` can be imported.

    The check is defensive: a broken install raises rather than returning
    None, and a broken install must not stop the suite from collecting.
    """
    try:
        return importlib.util.find_spec("sentence_transformers") is not None
    except (ImportError, ValueError):
        return False
