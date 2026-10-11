"""Tests for the Binance WebSocket parser.

Author: Prem Vishnoi <pvishnoi@pvishnoi.com>
"""
from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
import websockets

from src.prices.binance_ws import build_stream_url, parse_trade_frame

# ── build_stream_url ─────────────────────────────────────────────────────

def test_build_stream_url_default():
    url = build_stream_url(["BTCUSDT", "ETHUSDT"], base="wss://stream.binance.com:9443/stream")
    assert url == "wss://stream.binance.com:9443/stream?streams=btcusdt@trade/ethusdt@trade"


def test_build_stream_url_lowercases_symbols():
    url = build_stream_url(["SOLUSDT"], base="wss://x")
    assert "solusdt@trade" in url


def test_build_stream_url_preserves_order():
    """Symbol order in the URL must match input order — Binance rejects
    streams that are out of expected order in some cases."""
    url = build_stream_url(["ETHUSDT", "BTCUSDT", "SOLUSDT"], base="wss://x")
    # streams=ethusdt@trade/btcusdt@trade/solusdt@trade
    streams_part = url.split("streams=", 1)[1]
    streams = streams_part.split("/")
    assert streams == ["ethusdt@trade", "btcusdt@trade", "solusdt@trade"]


def test_build_stream_url_single_symbol():
    url = build_stream_url(["DOGEUSDT"], base="wss://x")
    assert url.endswith("?streams=dogeusdt@trade")


def test_build_stream_url_handles_10_symbols():
    symbols = [f"COIN{i}USDT" for i in range(10)]
    url = build_stream_url(symbols, base="wss://x")
    # 10 streams joined with /
    assert url.count("@trade") == 10
    assert url.split("streams=", 1)[1].count("/") == 9  # n-1 separators


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


def test_parse_trade_frame_default_volume_when_qty_missing():
    """If 'q' (quantity) is missing, volume_usd should default to 0.0,
    not crash on a KeyError."""
    frame = json.dumps({
        "data": {
            "e": "trade", "E": 1700000000000,
            "s": "BTCUSDT", "p": "67123.45", "T": 1700000000000,
            # no "q" field
        },
    })
    tick = parse_trade_frame(frame)
    assert tick is not None
    assert tick["volume_usd"] == 0.0


def test_parse_trade_frame_preserves_symbol_case():
    """Symbol comes through as Binance sends it (uppercase). Downstream
    code joins with settings.symbols_by mapping, so case matters."""
    frame = json.dumps({
        "data": {"s": "btcusdt", "p": "100.0", "T": 1700000000000},
    })
    tick = parse_trade_frame(frame)
    assert tick is not None
    assert tick["symbol"] == "btcusdt"  # raw passthrough


# ── Backoff semantics (smoke) ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stream_prices_respects_stop_event(monkeypatch):
    """If stop_event is set BEFORE the call, the function returns without
    ever trying to connect."""
    import asyncio

    from src.prices import binance_ws

    stop = asyncio.Event()
    stop.set()
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


@pytest.mark.asyncio
async def test_stream_prices_processes_received_ticks(monkeypatch):
    """End-to-end: synthetic recv() frames flow through to on_tick."""
    import asyncio
    from src.prices import binance_ws

    received: list[dict] = []

    async def _on_tick(tick):
        received.append(tick)

    frames = [
        json.dumps({"data": {"s": "BTCUSDT", "p": "100.0", "q": "0.5", "T": 1700000000000}}),
        json.dumps({"data": {"s": "BTCUSDT", "p": "101.0", "q": "0.3", "T": 1700000001000}}),
        json.dumps({"data": {"s": "BTCUSDT", "p": "99.0",  "q": "0.2", "T": 1700000002000}}),
    ]
    stop = asyncio.Event()
    iter_frames = iter(frames)

    class _FakeWS:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def recv(self):
            try:
                f = next(iter_frames)
            except StopIteration:
                stop.set()
                raise websockets.ConnectionClosed(None, None)
            return f

    def _fake_connect(*a, **k):
        return _FakeWS()

    monkeypatch.setattr(binance_ws.websockets, "connect", _fake_connect)
    await binance_ws.stream_prices(
        on_tick=_on_tick,
        symbols_usdt=["BTCUSDT"],
        base_url="wss://example",
        stop_event=stop,
    )
    assert len(received) == 3
    assert [t["price_usd"] for t in received] == [100.0, 101.0, 99.0]
    assert received[0]["volume_usd"] == pytest.approx(50.0)
    assert received[1]["volume_usd"] == pytest.approx(30.3)
    assert received[2]["volume_usd"] == pytest.approx(19.8)


@pytest.mark.asyncio
async def test_stream_prices_skips_malformed_frames_silently(monkeypatch):
    """A bad frame (missing required fields) is skipped, not raised."""
    import asyncio
    from src.prices import binance_ws

    received: list[dict] = []

    async def _on_tick(tick):
        received.append(tick)

    frames = [
        json.dumps({"data": {"s": "BTCUSDT", "p": "100.0", "T": 1700000000000}}),  # good
        "not-json",                                                                  # skipped
        json.dumps({"foo": "bar"}),                                                  # skipped (no .data)
        json.dumps({"data": {"s": "BTCUSDT", "p": "101.0", "T": 1700000001000}}),  # good
    ]
    stop = asyncio.Event()
    iter_frames = iter(frames)

    class _FakeWS:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def recv(self):
            try:
                return next(iter_frames)
            except StopIteration:
                stop.set()
                raise websockets.ConnectionClosed(None, None)

    def _fake_connect(*a, **k):
        return _FakeWS()

    monkeypatch.setattr(binance_ws.websockets, "connect", _fake_connect)
    await binance_ws.stream_prices(
        on_tick=_on_tick,
        symbols_usdt=["BTCUSDT"],
        base_url="wss://example",
        stop_event=stop,
    )
    assert len(received) == 2
    assert [t["price_usd"] for t in received] == [100.0, 101.0]
