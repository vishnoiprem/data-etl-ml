"""Tests for the SourceRegistry auto-fallback chain.

These tests stub out the underlying adapters so we can exercise the
registry's `is_healthy()` and `fetch()` ordering without hitting the
network.
"""
from __future__ import annotations

import pytest

from src.sources.base import AdapterError, RawTweet
from src.sources.registry import SourceRegistry


class _HealthyAdapter:
    name = "healthy"

    def __init__(self):
        self.calls = 0
        self._healthy = True

    def is_healthy(self) -> bool:
        return self._healthy

    async def fetch(self, query, max_results=30):
        self.calls += 1
        return [RawTweet(
            id=1, ts=None, author="x", text="ok",  # type: ignore[arg-type]
            likes=0, retweets=0, url="u",
        )]

    async def close(self):
        pass


class _UnhealthyAdapter:
    name = "unhealthy"

    def __init__(self):
        self._healthy = False
        self.calls = 0

    def is_healthy(self) -> bool:
        return self._healthy

    async def fetch(self, query, max_results=30):
        self.calls += 1
        raise AdapterError("should not be called")

    async def close(self):
        pass


class _ErroringAdapter:
    """Reports healthy but raises on every fetch — used to test fallback."""

    name = "errors"

    def __init__(self):
        self.calls = 0

    def is_healthy(self) -> bool:
        return True

    async def fetch(self, query, max_results=30):
        self.calls += 1
        raise AdapterError("simulated upstream failure")

    async def close(self):
        pass


def _make_registry(apify, nitter, syndication) -> SourceRegistry:
    return SourceRegistry(apify=apify, nitter=nitter, syndication=syndication)


# ── is_healthy() ─────────────────────────────────────────────────────────


def test_registry_is_healthy_false_when_all_adapters_unhealthy():
    r = _make_registry(None, _UnhealthyAdapter(), _UnhealthyAdapter())
    assert r.is_healthy() is False


def test_registry_is_healthy_true_when_nitter_alive():
    r = _make_registry(None, _HealthyAdapter(), _UnhealthyAdapter())
    assert r.is_healthy() is True


def test_registry_is_healthy_prefers_apify_when_configured():
    apify = _HealthyAdapter()
    nitter = _HealthyAdapter()
    r = _make_registry(apify, nitter, _UnhealthyAdapter())
    assert r.is_healthy() is True


def test_registry_is_healthy_true_with_only_syndication():
    """SyndicationAdapter always reports healthy; check the registry
    surfaces that even when Nitter is denylisted."""
    r = _make_registry(None, _UnhealthyAdapter(), _HealthyAdapter())
    assert r.is_healthy() is True


# ── fetch() fallback ordering ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_registry_fetch_uses_apify_first():
    """When apify is healthy, it should be tried before nitter/syndication."""
    apify = _HealthyAdapter()
    nitter = _HealthyAdapter()
    synd = _HealthyAdapter()
    r = _make_registry(apify, nitter, synd)
    tweets = await r.fetch("AI")
    assert len(tweets) == 1
    assert apify.calls == 1
    assert nitter.calls == 0
    assert synd.calls == 0
    # `active` should have been recorded as apify
    assert r.active == "apify"


@pytest.mark.asyncio
async def test_registry_fetch_falls_through_to_nitter_when_apify_unhealthy():
    apify = _UnhealthyAdapter()
    nitter = _HealthyAdapter()
    synd = _HealthyAdapter()
    r = _make_registry(apify, nitter, synd)
    await r.fetch("AI")
    assert apify.calls == 0
    assert nitter.calls == 1
    assert synd.calls == 0
    assert r.active == "nitter"


@pytest.mark.asyncio
async def test_registry_fetch_falls_through_to_syndication_after_nitter_error():
    apify = _UnhealthyAdapter()
    nitter = _ErroringAdapter()  # healthy=True but errors
    synd = _HealthyAdapter()
    r = _make_registry(apify, nitter, synd)
    tweets = await r.fetch("AI")
    assert nitter.calls == 1
    assert synd.calls == 1
    assert len(tweets) == 1
    assert r.active == "syndication"


@pytest.mark.asyncio
async def test_registry_fetch_returns_empty_when_all_fail():
    apify = _UnhealthyAdapter()
    nitter = _ErroringAdapter()
    synd = _ErroringAdapter()
    r = _make_registry(apify, nitter, synd)
    tweets = await r.fetch("AI")
    assert tweets == []
    assert synd.calls == 1


@pytest.mark.asyncio
async def test_registry_fetch_falls_through_on_empty_apify_result():
    """Some Apify runs return 0 tweets (legitimate but useless). The
    registry should fall through to the next adapter rather than
    returning an empty list as 'apify is broken'."""
    class _EmptyApify:
        name = "empty-apify"

        def is_healthy(self) -> bool:
            return True

        async def fetch(self, query, max_results=30):
            return []

        async def close(self):
            pass
    apify = _EmptyApify()
    nitter = _HealthyAdapter()
    r = _make_registry(apify, nitter, _HealthyAdapter())
    await r.fetch("AI")
    assert nitter.calls == 1
