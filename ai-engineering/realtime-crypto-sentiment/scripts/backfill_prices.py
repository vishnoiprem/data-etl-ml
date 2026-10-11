#!/usr/bin/env python3
"""Backfill Binance 1m klines for all configured symbols.

Author: Prem Vishnoi <pvishnoi@avilx.com>

Usage:
    python scripts/backfill_prices.py             # default: 7d, 10 symbols
    python scripts/backfill_prices.py --days 30   # 30-day backfill
    python scripts/backfill_prices.py --symbols BTC ETH
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from loguru import logger

from src.config import settings
from src.prices.binance_rest import backfill_klines
from src.store import db


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=settings.backfill_days, help="Days to backfill (default: 7)")
    p.add_argument("--symbols", nargs="+", default=settings.symbols, help="Symbols (default: from .env)")
    p.add_argument("--interval", default="1m", help="Kline interval (default: 1m)")
    args = p.parse_args()

    logger.info(f"backfill: {len(args.symbols)} symbols × {args.days}d × {args.interval}")
    logger.info(f"database: {settings.database_url.split('@')[-1]}")
    db.init_schema()  # idempotent

    total = 0
    t0 = time.monotonic()
    for sym in args.symbols:
        logger.info(f"→ {sym}USDT")
        rows = backfill_klines(f"{sym}USDT", interval=args.interval, days=args.days)
        n = db.bulk_upsert_prices(rows)
        total += n
        logger.info(f"  {n:,} rows inserted for {sym}")
    elapsed = time.monotonic() - t0
    logger.info(f"done: {total:,} rows total in {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
