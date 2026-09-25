#!/usr/bin/env python3
"""
6_watch_googl.py — poll GOOGL from yfinance through the pre-market and into the
US regular session, and print a clean status line each minute.

Behavior:
  * Pulls yfinance fast_info + 1m history every POLL_SECONDS (default 60s).
  * Detects session phase: CLOSED | PRE-MARKET | REGULAR | AFTER-HOURS.
  * Tracks the first non-None pre-market price and reports the gap vs yesterday's close.
  * Saves a CSV log to /tmp/googl_watch.csv for later analysis.

Usage:
  python3 scripts/6_watch_googl.py
  POLL_SECONDS=30 TICKER=NVDA python3 scripts/6_watch_googl.py
  python3 scripts/6_watch_googl.py --once   # one shot, no loop

This is a host-side script — does not depend on the docker stack being up.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import sys
import time
import zoneinfo

import yfinance as yf


ET = zoneinfo.ZoneInfo("America/New_York")
CSV_PATH = "/tmp/googl_watch.csv"


def phase(now_et: dt.datetime) -> str:
    """Return the current US market session phase for `now_et` (a tz-aware ET datetime)."""
    minutes = now_et.hour * 60 + now_et.minute
    if 4 * 60 <= minutes < 9 * 60 + 30:
        return "PRE-MARKET"
    if 9 * 60 + 30 <= minutes < 16 * 60:
        return "REGULAR"
    if 16 * 60 <= minutes < 20 * 60:
        return "AFTER-HOURS"
    return "CLOSED"


def fmt(x, places: int = 2, dash: str = "—") -> str:
    if x is None:
        return dash
    try:
        return f"{float(x):.{places}f}"
    except (TypeError, ValueError):
        return dash


def gap_pct(price: float | None, prev_close: float | None) -> str:
    if price is None or prev_close is None or prev_close == 0:
        return "—"
    return f"{(price - prev_close) / prev_close * 100:+.2f}%"


def snapshot(ticker: str) -> dict:
    """Pull a single yfinance snapshot. Returns a dict with safe defaults."""
    t = yf.Ticker(ticker)
    fi = {}
    info = {}
    try:
        fi = t.fast_info or {}
    except Exception:
        pass
    try:
        info = t.info or {}
    except Exception:
        pass

    # Prefer ticker.info prices (sometimes more current than fast_info).
    last = info.get("regularMarketPrice") or fi.get("last_price") or fi.get("lastPrice")
    prev_close = info.get("regularMarketPreviousClose") or fi.get("previous_close") or fi.get("previousClose")
    pre_mkt = info.get("preMarketPrice")
    pre_chg = info.get("preMarketChange")
    pre_pct = info.get("preMarketChangePercent")
    day_high = info.get("regularMarketDayHigh") or fi.get("day_high") or fi.get("dayHigh")
    day_low = info.get("regularMarketDayLow") or fi.get("day_low") or fi.get("dayLow")
    day_open = info.get("regularMarketOpen") or info.get("open") or fi.get("open")

    return {
        "last": last,
        "prev_close": prev_close,
        "pre_mkt": pre_mkt,
        "pre_chg": pre_chg,
        "pre_pct": pre_pct,
        "day_high": day_high,
        "day_low": day_low,
        "day_open": day_open,
    }


def render(ticker: str, now_et: dt.datetime, s: dict) -> str:
    ph = phase(now_et)
    last = s["last"]
    prev = s["prev_close"]
    pre = s["pre_mkt"]
    parts = [
        f"[{now_et.strftime('%H:%M:%S')} ET] {ticker}  phase={ph}",
        f"last={fmt(last)}",
        f"prev_close={fmt(prev)}",
        f"gap={gap_pct(last, prev)}",
        f"pre_mkt={fmt(pre)}",
        f"day_range=[{fmt(s['day_low'])} .. {fmt(s['day_high'])}]",
    ]
    if s["pre_pct"] is not None:
        parts.append(f"pre%={s['pre_pct']:+.2f}")
    return "  ".join(parts)


def append_csv(path: str, now_et: dt.datetime, ticker: str, s: dict, ph: str) -> None:
    new_file = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow([
                "ts_et", "ticker", "phase", "last", "prev_close", "gap_pct",
                "pre_mkt", "pre_chg", "pre_pct", "day_open", "day_high", "day_low",
            ])
        last = s["last"]
        gap = (last - s["prev_close"]) / s["prev_close"] * 100 if last and s["prev_close"] else None
        w.writerow([
            now_et.isoformat(),
            ticker,
            ph,
            s["last"],
            s["prev_close"],
            f"{gap:.4f}" if gap is not None else "",
            s["pre_mkt"],
            s["pre_chg"],
            s["pre_pct"],
            s["day_open"],
            s["day_high"],
            s["day_low"],
        ])


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Poll a ticker through the US market open.")
    p.add_argument("--ticker", default=os.environ.get("TICKER", "GOOGL"))
    p.add_argument("--poll-seconds", type=int, default=int(os.environ.get("POLL_SECONDS", "60")))
    p.add_argument("--once", action="store_true", help="Take a single snapshot and exit.")
    p.add_argument("--csv", default=CSV_PATH)
    args = p.parse_args(argv)

    print(f"=== Watching {args.ticker} (poll every {args.poll_seconds}s) — Ctrl-C to stop ===")
    print(f"Log: {args.csv}")
    print()

    if args.once:
        now_et = dt.datetime.now(ET)
        s = snapshot(args.ticker)
        print(render(args.ticker, now_et, s))
        append_csv(args.csv, now_et, args.ticker, s, phase(now_et))
        return 0

    try:
        while True:
            now_et = dt.datetime.now(ET)
            try:
                s = snapshot(args.ticker)
                print(render(args.ticker, now_et, s), flush=True)
                append_csv(args.csv, now_et, args.ticker, s, phase(now_et))
            except Exception as e:
                print(f"[{now_et.strftime('%H:%M:%S')} ET] error: {e}", file=sys.stderr, flush=True)
            time.sleep(args.poll_seconds)
    except KeyboardInterrupt:
        print("\nstopped.")
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
