"""Tests for bot filter."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

import pytest
from bot_filter import filter_events, RateLimiter, _ua_matches_blocklist


def test_ua_signature_blocks_headless():
    assert _ua_matches_blocklist("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/91.0.4472.114 Safari/537.36")
    assert _ua_matches_blocklist("python-requests/2.31.0")
    assert _ua_matches_blocklist("curl/7.85.0")


def test_ua_signature_allows_normal():
    assert not _ua_matches_blocklist("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15")
    assert not _ua_matches_blocklist("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/118.0.0.0")


def test_rate_limiter_detects_burst():
    rl = RateLimiter(max_events_per_5s=50)
    # 100 events in 1 second = 500 events per 5s window
    base_ts = 1_000_000
    flagged = False
    for i in range(100):
        if rl.is_burst("user_1", base_ts + i * 10):
            flagged = True
            break
    assert flagged, "should detect burst"


def test_full_filter_runs():
    events = [
        {"user_id": "u1", "event_ts": "2026-09-26T10:00:00Z",
         "user_agent": "Mozilla/5.0 (iPhone)", "event_name": "page_view"},
        {"user_id": "u2", "event_ts": "2026-09-26T10:00:00Z",
         "user_agent": "python-requests/2.31", "event_name": "page_view"},
    ]
    res = filter_events(events)
    assert len(res.human) == 1
    assert len(res.bot) == 1
    assert res.stats["stage1_ua"] == 1
