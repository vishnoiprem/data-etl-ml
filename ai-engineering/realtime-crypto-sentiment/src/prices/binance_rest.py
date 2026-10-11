"""Binance REST backfill (1m klines).

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""
from __future__ import annotations

import time
from datetime import UTC, datetime

import requests
from loguru import logger

from src.config import settings

KLINES_URL = "https://api.binance.com/api/v3/klines"
MAX_KLINES_PER_CALL = 1000


def backfill_klines(
    symbol: str,
    interval: str = "1m",
    days: int = 7,
    base_url: str | None = None,
) -> list[dict]:
    """Fetch 1m klines for `symbol` going back `days` days.

    Returns a list of {ts, symbol, price_usd, volume_usd} dicts (using
    the close price as the price_usd; volume is quote-volume * close).
    """
    base = base_url or settings.binance_rest
    end = int(time.time() * 1000)
    start = end - days * 24 * 3600 * 1000
    out: list[dict] = []
    cursor = start

    while cursor < end:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": cursor,
            "endTime": end,
            "limit": MAX_KLINES_PER_CALL,
        }
        try:
            resp = requests.get(f"{base}/api/v3/klines", params=params, timeout=10)
            if resp.status_code == 429:
                logger.warning("binance 429; sleeping 5s")
                time.sleep(5)
                continue
            if resp.status_code != 200:
                logger.error(f"binance {resp.status_code} for {symbol}: {resp.text[:200]}")
                break
            rows = resp.json()
        except requests.RequestException as e:
            logger.error(f"binance request error: {e}")
            break

        if not rows:
            break

        for row in rows:
            ts_ms, _open, _high, _low, close, volume, *_ = row
            ts = datetime.fromtimestamp(ts_ms / 1000.0, tz=UTC)
            out.append({
                "ts": ts,
                "symbol": symbol,
                "price_usd": float(close),
                "volume_usd": float(volume) * float(close),
            })

        # Advance cursor past the last returned candle
        last_ts = rows[-1][0]
        if last_ts <= cursor:
            break
        cursor = last_ts + 1

    logger.info(f"backfill {symbol}: {len(out)} candles")
    return out
