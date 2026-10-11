"""Binance public WebSocket price stream.

Author: Prem Vishnoi <pvishnoi@avilx.com>

Subscribes to `<symbol>@trade` streams for all configured symbols and
invokes `on_tick` for each trade event. Reconnects with exponential
backoff (1→60s) on disconnect.
"""
from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import websockets
from loguru import logger

from src.config import settings

# Trade-stream frame: {"stream":"btcusdt@trade","data":{"e":"trade","E":...,
# "s":"BTCUSDT","t":..., "p":"67123.45","q":"0.012","T":...,"m":...}}

OnTick = Callable[[dict], Awaitable[None]]


def build_stream_url(symbols_usdt: list[str], base: str | None = None) -> str:
    base = base or settings.binance_ws
    streams = "/".join(f"{s.lower()}@trade" for s in symbols_usdt)
    return f"{base}?streams={streams}"


def parse_trade_frame(payload: str) -> dict | None:
    """Parse a Binance trade frame; return a PriceTick dict or None on error."""
    try:
        msg = json.loads(payload)
    except (ValueError, TypeError):
        return None
    if "data" not in msg:
        return None
    d = msg["data"]
    sym = d.get("s")
    price = d.get("p")
    qty = d.get("q", "0")
    ts_ms = d.get("T") or d.get("E")
    if not (sym and price and ts_ms):
        return None
    try:
        return {
            "ts": datetime.fromtimestamp(ts_ms / 1000.0, tz=UTC),
            "symbol": sym,
            "price_usd": float(price),
            "volume_usd": float(price) * float(qty),
        }
    except (ValueError, TypeError):
        return None


async def stream_prices(
    on_tick: OnTick,
    symbols_usdt: list[str] | None = None,
    base_url: str | None = None,
    stop_event: asyncio.Event | None = None,
) -> None:
    """Forever-stream Binance trade ticks; calls on_tick(tick_dict) per trade.

    Reconnects on disconnect with exponential backoff capped at 60s.
    """
    symbols = symbols_usdt or settings.symbols_with_usdt
    url = build_stream_url(symbols, base_url)
    backoff = 1.0

    while True:
        if stop_event is not None and stop_event.is_set():
            return
        try:
            logger.info(f"binance-ws connecting to {url[:80]}…")
            async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                logger.info("binance-ws connected")
                backoff = 1.0
                while True:
                    if stop_event is not None and stop_event.is_set():
                        return
                    raw = await ws.recv()
                    tick = parse_trade_frame(raw)
                    if tick is None:
                        continue
                    try:
                        await on_tick(tick)
                    except Exception as e:
                        logger.error(f"binance-ws on_tick error: {e}")
        except (
            websockets.ConnectionClosed,
            websockets.WebSocketException,
            ConnectionError,
            OSError,
        ) as e:
            logger.warning(f"binance-ws disconnect: {e}; reconnect in {backoff:.1f}s")
            await asyncio.sleep(backoff)
            backoff = min(60.0, backoff * 2)
        except asyncio.CancelledError:
            return
