"""Tests for the Binance WebSocket parser.

Author: Prem Vishnoi <pvishnoi@pvishnoi.com>
"""
from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from src.prices.binance_ws import build_stream_url, parse_trade_frame

# ── build_stream_url ─────────────────────────────────────────────────────

def test_build_stream_url_default():
    url = build_stream_url(["BTCUSDT", "ETHUSDT"], base="wss://stream.binance.com:9443/stream")
    assert url == "wss://stream.binance.com:9443/stream?streams=btcusdt@trade/ethusdt@trade"


def test_build_stream_url_lowercases_symbols():
    url = build_stream_url(["SOLUSDT"], base="wss://x")
    assert "solusdt@trade" in url


# ── parse_trade_frame ────────────────────────────────────────────────────

def test_parse_trade_frame_valid():
    frame = json.dumps({
        "stream": "btcusdt@trade",
        "data": {
            "e": "trade", "E": 1700000000000,
            "s": "BTCUSDT", "t": 12345,
            "p": "67123.45", "q": "0.012", "T": 1700000000123, "m": False,
        },
    })
    tick = parse_trade_frame(frame)
    assert tick is not None
    assert tick["symbol"] == "BTCUSDT"
    assert tick["price_usd"] == pytest.approx(67123.45)
    assert tick["volume_usd"] == pytest.approx(67123.45 * 0.012)
    assert tick["ts"] == datetime.fromtimestamp(1700000000.123, tz=UTC)


def test_parse_trade_frame_uses_event_time_as_fallback():
    frame = json.dumps({
        "data": {
            "e": "trade", "E": 1700000000999,
            "s": "ETHUSDT", "p": "3000", "q": "0.5",
            # Note: no "T" — fallback to "E"
        },
    })
    tick = parse_trade_frame(frame)
    assert tick is not None
    assert tick["symbol"] == "ETHUSDT"
    assert tick["ts"] == datetime.fromtimestamp(1700000000.999, tz=UTC)


def test_parse_trade_frame_invalid_json():
    assert parse_trade_frame("not json") is None


def test_parse_trade_frame_missing_data_field():
    assert parse_trade_frame(json.dumps({"foo": "bar"})) is None


def test_parse_trade_frame_missing_required_fields():
    bad = json.dumps({"data": {"s": "BTCUSDT"}})  # no price, no ts
    assert parse_trade_frame(bad) is None


def test_parse_trade_frame_non_numeric_returns_none():
    bad = json.dumps({"data": {"s": "BTCUSDT", "p": "not-a-number", "T": 1700000000000}})
    assert parse_trade_frame(bad) is None


def test_parse_trade_frame_empty_string():
    assert parse_trade_frame("") is None
    assert parse_trade_frame("{}") is None


# ── Backoff semantics (smoke) ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stream_prices_respects_stop_event(monkeypatch):
    """If stop_event is set, the function returns promptly without connecting."""
    import asyncio

    from src.prices import binance_ws

    stop = asyncio.Event()
    stop.set()  # already stopped
    called = {"connect": 0}

    class _FakeWS:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False

    def _fake_connect(*a, **k):
        called["connect"] += 1
        return _FakeWS()

    monkeypatch.setattr(binance_ws.websockets, "connect", _fake_connect)
    await binance_ws.stream_prices(
        on_tick=lambda t: None,
        symbols_usdt=["BTCUSDT"],
        base_url="wss://example",
        stop_event=stop,
    )
    assert called["connect"] == 0  # never tried to connect
