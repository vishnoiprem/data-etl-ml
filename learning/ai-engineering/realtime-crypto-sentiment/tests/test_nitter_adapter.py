"""Tests for the Nitter mirror adapter.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""
from __future__ import annotations

import time

import pytest

from src.sources.base import AdapterError
from src.sources.nitter_mirror import NitterMirrorAdapter, TokenBucket

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
          <span class="tweet-date">
            <a href="{url_path}" title="Mon, 01 Jan 2026 12:00:00 +0000">Jan 1, 2026 · 12:00</a>
          </span>
          <span class="icon-heart">{likes}</span>
          <span class="icon-retweet">{retweets}</span>
        </div>''')
    parts.append("</div></body></html>")
    return "".join(parts)


# ── Token bucket ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_token_bucket_initial_burst():
    """The first `burst` acquires are immediate; only the (burst+1)-th waits."""
    b = TokenBucket(rate=1.0, burst=3)
    t0 = time.monotonic()
    # First 3 should be free
    for _ in range(3):
        await b.acquire()
    burst_elapsed = time.monotonic() - t0
    # Burst phase must complete in well under the refill interval
    assert burst_elapsed < 0.5, f"burst should be instant, took {burst_elapsed:.3f}s"
    # The 4th must wait ~1s (rate=1.0/sec)
    await b.acquire()
    total_elapsed = time.monotonic() - t0
    # Total = ~1s for the 4th token to refill
    assert 0.9 <= total_elapsed <= 1.6, f"4th token wait unexpected: {total_elapsed:.3f}s"


@pytest.mark.asyncio
async def test_token_bucket_refill():
    """rate=2/sec means ~0.5s between tokens after the burst is exhausted."""
    b = TokenBucket(rate=2.0, burst=1)
    t0 = time.monotonic()
    await b.acquire()  # burst=1, instant
    burst_elapsed = time.monotonic() - t0
    assert burst_elapsed < 0.3
    await b.acquire()  # must wait ~0.5s for refill at rate=2/sec
    refill_elapsed = time.monotonic() - t0
    assert 0.4 <= refill_elapsed <= 1.0, f"refill rate wrong: {refill_elapsed:.3f}s"


@pytest.mark.asyncio
async def test_token_bucket_concurrent_acquires_serialize_correctly():
    """10 concurrent acquires on burst=3 + rate=10/sec must finish in
    ~0.7s (7 tokens needed after the burst). If the lock is broken,
    multiple acquires may pass the check and over-grant tokens."""
    import asyncio as _asyncio
    b = TokenBucket(rate=10.0, burst=3)
    t0 = time.monotonic()
    await _asyncio.gather(*[b.acquire() for _ in range(10)])
    elapsed = time.monotonic() - t0
    # Need 10 - 3 = 7 refills at 10/sec = 0.7s
    assert 0.6 <= elapsed <= 1.2, f"concurrent acquire timing wrong: {elapsed:.3f}s"


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
    assert "BTC" in tweets[0].symbol_tags or "$BTC" in tweets[0].symbol_tags


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
      <span class="tweet-date">
        <a href="/x/status/1" title="Mon, 01 Jan 2026 12:00:00 +0000">link</a>
      </span>
      <span class="icon-heart">1.2K</span>
      <span class="icon-retweet">3.4M</span>
    </div>
    '''
    tweets = a._parse(html, query="x", max_results=5)
    assert tweets[0].likes == 1_200
    assert tweets[0].retweets == 3_400_000


@pytest.mark.parametrize("raw,expected", [
    ("42", 42),
    ("1,234", 1234),       # comma-separated
    ("0", 0),
    ("1.5K", 1_500),       # decimal with K
    ("2.7M", 2_700_000),   # decimal with M
    ("100k", 100_000),     # lowercase k (the regex uppercases)
    ("5B", 0),             # B is NOT supported → returns 0 (not 5e9)
    ("", 0),               # empty
    ("not-a-number", 0),   # garbage
    ("  100  ", 100),      # get_text(strip=True) already trims whitespace
])
def test_parse_stat_edge_cases(raw, expected):
    a = NitterMirrorAdapter(mirrors=["x"])
    assert a._parse_stat(_stat_item(raw), ".stat") == expected


def _stat_item(text):
    """Build a parent element with a `.stat` child containing the given text.
    parse_stat(item, selector) does item.select_one(selector)."""
    from bs4 import BeautifulSoup
    return BeautifulSoup(f'<div class="item"><span class="stat">{text}</span></div>', "lxml").select_one(".item")


def test_parse_html_url_uses_active_mirror_not_first_configured():
    """Pre-fix this used mirrors[0] even when the response came from
    mirrors[1]. Now the URL must reference the mirror that actually served
    the response (so the link is a real tweet, not a 404)."""
    a = NitterMirrorAdapter(mirrors=["primary.test", "fallback.test"], min_mirror_gap_sec=0)
    a._active_mirror = "fallback.test"
    html = _tweet_html([{"id": 555, "text": "hi", "author": "a"}])
    tweets = a._parse(html, query="x", max_results=5)
    assert "fallback.test" in tweets[0].url
    assert "primary.test" not in tweets[0].url


def test_parse_html_respects_max_results():
    """If the page has 20 timeline-items and max_results=3, only 3 are returned."""
    a = NitterMirrorAdapter(mirrors=["x"])
    items = [{"id": i, "text": f"t{i}", "author": "a"} for i in range(20)]
    tweets = a._parse(_tweet_html(items), query="x", max_results=3)
    assert len(tweets) == 3
    assert [t.id for t in tweets] == [0, 1, 2]


def test_parse_html_does_not_crash_on_garbage_items():
    """The parser is tolerant by design — items with no author/text/link
    are returned as RawTweet('unknown', '', '', ...) rather than raising.
    What matters is that valid items around them still come through."""
    a = NitterMirrorAdapter(mirrors=["x"])
    html = '''
    <html><body>
      <div class="timeline-item">
        <a class="fullname">good</a>
        <div class="tweet-content">valid tweet</div>
        <span class="tweet-date">
          <a href="/good/status/1" title="Mon, 01 Jan 2026 12:00:00 +0000">link</a>
        </span>
      </div>
      <div class="timeline-item">
        <!-- no content, no link, no author → empty tweet -->
      </div>
      <div class="timeline-item">
        <a class="fullname">good2</a>
        <div class="tweet-content">another valid tweet</div>
        <span class="tweet-date">
          <a href="/good2/status/2" title="Mon, 01 Jan 2026 12:00:00 +0000">link</a>
        </span>
      </div>
    </body></html>
    '''
    tweets = a._parse(html, query="x", max_results=10)
    # No exception, all 3 items parsed (the empty one as an empty tweet)
    assert len(tweets) == 3
    # The two valid ones have the expected content
    assert tweets[0].text == "valid tweet"
    assert tweets[0].id == 1
    assert tweets[2].text == "another valid tweet"
    assert tweets[2].id == 2


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
    """When mirror A errors, adapter rotates to mirror B."""
    a = NitterMirrorAdapter(
        mirrors=["a.test", "b.test"], min_mirror_gap_sec=0, deny_duration_sec=3600,
    )
    call_log = []

    async def fake_fetch_one(mirror, query):
        call_log.append(mirror)
        if mirror == "a.test":
            # Simulate the real-world denylist side-effect
            a._mirror_denied_until[mirror] = time.monotonic() + 3600
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


@pytest.mark.parametrize("raw,expected", [
    ("$BTC", "BTC"),
    ("$$BTC", "BTC"),       # lstrip strips all leading $
    ("$btc", "btc"),        # case preserved (search is case-insensitive upstream)
    ("#BTC", "BTC"),
    ("##hashtag", "hashtag"),  # lstrip strips all leading #
    ("  $ETH  ", "ETH"),     # whitespace is stripped
    ("Solana", "Solana"),
    ("", ""),                # empty stays empty
])
def test_normalize_query_edge_cases(raw, expected):
    a = NitterMirrorAdapter(mirrors=["x"])
    assert a._normalize_query(raw) == expected


def test_extract_id_from_various_url_formats():
    """Tweet id extraction must work on Nitter (/user/status/ID), bare
    Twitter (twitter.com/user/status/ID), and bare ID-in-string fallback."""
    a = NitterMirrorAdapter(mirrors=["x"])
    assert a._extract_id("https://nitter.net/alice/status/1234567890") == 1234567890
    assert a._extract_id("https://twitter.com/alice/status/9876543210") == 9876543210
    # Falls back to a 10+ digit number anywhere in the string
    assert a._extract_id("garbage/1234567890/more") == 1234567890
    # No digits → None
    assert a._extract_id("https://example.com/no-id") is None
    assert a._extract_id("") is None


def test_stable_id_is_deterministic_across_runs():
    """The sha1 fallback must yield the same id on every process start,
    otherwise (tweet_id, ts) idempotency in db.upsert_tweet is broken."""
    a1 = NitterMirrorAdapter(mirrors=["x"])
    a2 = NitterMirrorAdapter(mirrors=["x"])
    id1 = a1._stable_id("hello world", "alice")
    id2 = a2._stable_id("hello world", "alice")
    assert id1 == id2
    # Different content → different id
    id3 = a1._stable_id("hello world", "bob")
    assert id1 != id3


def test_stable_id_falls_back_when_no_url():
    """When a tweet has no status URL, _parse should call _stable_id and still
    produce a deterministic id."""
    a = NitterMirrorAdapter(mirrors=["x.test"])
    html = '''
    <div class="timeline-item">
      <div class="fullname">alice</div>
      <div class="tweet-content">no url here</div>
      <!-- no .tweet-date at all -->
      <span class="icon-heart">5</span>
    </div>
    '''
    tweets = a._parse(html, query="x", max_results=5)
    assert len(tweets) == 1
    # Id is the sha1 of (author::text) → deterministic
    expected = a._stable_id("no url here", "alice")
    assert tweets[0].id == expected
