"""Tests for the Nitter mirror adapter.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""
from __future__ import annotations

import asyncio
import time

import pytest

from src.sources.nitter_mirror import NitterMirrorAdapter, TokenBucket
from src.sources.base import AdapterError, RawTweet


# ── HTML fixtures ────────────────────────────────────────────────────────

def _tweet_html(items: list[dict]) -> str:
    """Build a minimal Nitter-style HTML with the given tweet items."""
    parts = ['<html><body><div class="timeline">']
    for it in items:
        author = it.get("author", "alice")
        body = it.get("text", "hello world")
        tweet_id = it.get("id", 1234567890)
        likes = it.get("likes", 0)
        retweets = it.get("retweets", 0)
        url_path = f"/alice/status/{tweet_id}"
        parts.append(f'''
        <div class="timeline-item">
          <a class="fullname">{author}</a>
          <div class="tweet-content">{body}</div>
          <a class="tweet-date" href="{url_path}" title="Mon, 01 Jan 2026 12:00:00 +0000">
            <span>Jan 1, 2026 · 12:00</span>
          </a>
          <span class="icon-heart">{likes}</span>
          <span class="icon-retweet">{retweets}</span>
        </div>''')
    parts.append("</div></body></html>")
    return "".join(parts)


# ── Token bucket ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_token_bucket_initial_burst():
    b = TokenBucket(rate=1.0, burst=3)
    t0 = time.monotonic()
    # First 3 should be free
    for _ in range(3):
        await b.acquire()
    # 4th should wait
    await b.acquire()
    elapsed = time.monotonic() - t0
    assert elapsed >= 0.9  # waited at least ~1s for 4th token


@pytest.mark.asyncio
async def test_token_bucket_refill():
    b = TokenBucket(rate=2.0, burst=1)
    t0 = time.monotonic()
    await b.acquire()
    await b.acquire()  # should wait ~0.5s
    elapsed = time.monotonic() - t0
    assert 0.3 < elapsed < 1.5


# ── Parser ───────────────────────────────────────────────────────────────

def test_parse_html_extracts_tweets():
    a = NitterMirrorAdapter(mirrors=["example.test"], min_mirror_gap_sec=0)
    html = _tweet_html([
        {"id": 111, "text": "$BTC breakout confirmed", "author": "alice", "likes": 100, "retweets": 20},
        {"id": 222, "text": "$ETH volume drying up", "author": "bob", "likes": 5, "retweets": 1},
    ])
    tweets = a._parse(html, query="$BTC", max_results=10)
    assert len(tweets) == 2
    assert tweets[0].id == 111
    assert tweets[0].author == "alice"
    assert "BTC" in tweets[0].text
    assert tweets[0].likes == 100
    assert tweets[0].retweets == 20
    assert tweets[0].url.endswith("/alice/status/111")
    assert "BTC" in tweets[0].symbol_tags


def test_parse_html_handles_alternate_selectors():
    a = NitterMirrorAdapter(mirrors=["example.test"])
    html = '''
    <html><body>
      <div class="tweet">
        <div class="display-name">carol</div>
        <div class="tweet-body">SOL pump incoming</div>
        <a class="tweet-link" href="/carol/status/333">link</a>
      </div>
    </body></html>
    '''
    tweets = a._parse(html, query="$SOL", max_results=5)
    assert len(tweets) == 1
    assert tweets[0].author == "carol"
    assert "SOL" in tweets[0].text


def test_parse_stat_handles_k_m_suffixes():
    a = NitterMirrorAdapter(mirrors=["x"])
    html = '''
    <div class="timeline-item">
      <div class="fullname">x</div>
      <div class="tweet-content">hi</div>
      <a class="tweet-date" href="/x/status/1" title="x"></a>
      <span class="icon-heart">1.2K</span>
      <span class="icon-retweet">3.4M</span>
    </div>
    '''
    tweets = a._parse(html, query="x", max_results=5)
    assert tweets[0].likes == 1_200
    assert tweets[0].retweets == 3_400_000


# ── Denylist & rotation ──────────────────────────────────────────────────

def test_denylist_after_403(monkeypatch):
    """After a 403, the mirror is added to the denylist for 24h."""
    a = NitterMirrorAdapter(
        mirrors=["m1.test", "m2.test"], min_mirror_gap_sec=0,
        deny_duration_sec=3600,
    )
    # Simulate 403 by manually invoking the denylist side-effect
    a._mirror_denied_until["m1.test"] = time.monotonic() + 3600
    assert a._healthy_mirrors() == ["m2.test"]
    # After expiry, mirror is healthy again
    a._mirror_denied_until["m1.test"] = time.monotonic() - 1
    assert set(a._healthy_mirrors()) == {"m1.test", "m2.test"}


@pytest.mark.asyncio
async def test_rotate_mirror_on_failure(monkeypatch):
    """When mirror A returns 403, adapter rotates to mirror B."""
    a = NitterMirrorAdapter(
        mirrors=["a.test", "b.test"], min_mirror_gap_sec=0, deny_duration_sec=3600,
    )
    call_log = []

    async def fake_fetch_one(mirror, query):
        call_log.append(mirror)
        if mirror == "a.test":
            raise AdapterError("403 from a.test (denied for 24h)")
        return _tweet_html([{"id": 999, "text": "hello"}])

    monkeypatch.setattr(a, "_fetch_one", fake_fetch_one)
    tweets = await a.fetch(query="$BTC", max_results=5)
    assert call_log == ["a.test", "b.test"]
    assert len(tweets) == 1
    assert "a.test" not in a._healthy_mirrors()


@pytest.mark.asyncio
async def test_all_mirrors_down_raises(monkeypatch):
    a = NitterMirrorAdapter(mirrors=["a.test", "b.test"], min_mirror_gap_sec=0)

    async def fake_fetch_one(mirror, query):
        raise AdapterError(f"down: {mirror}")

    monkeypatch.setattr(a, "_fetch_one", fake_fetch_one)
    with pytest.raises(AdapterError) as exc_info:
        await a.fetch(query="x")
    assert "all mirrors failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_no_mirrors_configured_raises():
    a = NitterMirrorAdapter(mirrors=[])
    with pytest.raises(AdapterError):
        await a.fetch(query="x")


# ── Query normalization ──────────────────────────────────────────────────

def test_normalize_query_strips_cashtag():
    a = NitterMirrorAdapter(mirrors=["x"])
    assert a._normalize_query("$BTC") == "BTC"
    assert a._normalize_query("#memecoin") == "memecoin"
    assert a._normalize_query("ethereum") == "ethereum"
