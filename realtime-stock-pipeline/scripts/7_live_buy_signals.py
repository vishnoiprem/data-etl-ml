#!/usr/bin/env python3
"""
7_live_buy_signals.py — terminal "tickers to buy today" dashboard.

Fetches live yfinance data for the ticker universe and runs the same BUY /
WATCH / HOLD signal logic that the Flink job ``flink/jobs/04_signals.sql``
applies in production. No Kafka, no Flink, no TimescaleDB required — pure
host-side Python, so it works even when the docker stack is down.

Signal model (mirror of ``04_signals.sql``)
-------------------------------------------
  range_pct         = (day_high - day_low) / day_low
  hours_remaining   = max(0, 16*60 - HHMM) / 60          # NY close = 16:00
  expected_move_pct = range_pct * sqrt(hours_remaining / 6.5)
  momentum_5m       = (last_close - first_close_in_last_5m) / first_close_in_last_5m

  confidence        = 0.30 * near_low
                    + 0.30 * LEAST(1, momentum_5m / 0.02)
                    + 0.25 * LEAST(1, expected_move_pct / 0.06)
                    + 0.15 * time_factor(hours_remaining)
  capped at 1.0.

  BUY    when:  price <= day_low * 1.01
                AND momentum_5m > 0
                AND expected_move_pct >= 0.04
                AND confidence >= 0.6
  WATCH  when:  price <= day_low * 1.01 AND momentum_5m > 0
  HOLD   otherwise.

Usage:
  python3 scripts/7_live_buy_signals.py
  python3 scripts/7_live_buy_signals.py --tickers AAPL,MSFT,NVDA
  python3 scripts/7_live_buy_signals.py --once
  python3 scripts/7_live_buy_signals.py --poll-seconds 60
  python3 scripts/7_live_buy_signals.py --json        # machine-readable
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import zoneinfo
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Iterable

# Repo-relative import (so this works when run as ``python3 scripts/7_...``)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from producer.ticker_universe import get_tickers, is_market_hours  # noqa: E402

import yfinance as yf  # noqa: E402
from pandas import MultiIndex  # noqa: E402


# --------------------------------------------------------------------------- #
# Signal model (mirror of 04_signals.sql)
# --------------------------------------------------------------------------- #

#: Weights — must match 04_signals.sql LEAST(1.0, ...) weights
W_NEAR_LOW = 0.30
W_MOMENTUM = 0.30
W_VOL = 0.25
W_TIME = 0.15

#: Cap for momentum (in raw return-pct units)
MOMENTUM_CAP = 0.02
#: Cap for expected_move_pct
VOL_CAP = 0.06
#: Confidence threshold for BUY
BUY_CONF_THRESHOLD = 0.60
#: BUY minimum expected move
BUY_MOVE_THRESHOLD = 0.04
#: "near day low" = price within 1% of day low
NEAR_LOW_PCT = 0.01
#: NY market close hour (24h) — used to compute hours_remaining
NY_CLOSE_HOUR = 16
NY_TZ = zoneinfo.ZoneInfo("America/New_York")


@dataclass
class Signal:
    ticker: str
    sector: str
    last: float | None
    prev_close: float | None
    day_high: float | None
    day_low: float | None
    day_open: float | None
    gap_pct: float | None
    momentum_5m: float | None
    range_pct: float | None
    expected_move_pct: float | None
    confidence: float | None
    action: str  # BUY | WATCH | HOLD | NA
    reasons: str

    def to_row(self) -> dict:
        return asdict(self)


def _safe_float(x) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if v != v:  # NaN
        return None
    return v


def _hours_remaining(now_et: datetime) -> float:
    """Hours until NY market close (16:00). Clamped to [0, 6.5]."""
    minutes_left = NY_CLOSE_HOUR * 60 - (now_et.hour * 60 + now_et.minute)
    hours = max(0.0, minutes_left / 60.0)
    return min(hours, 6.5)


def _time_factor(hours_remaining: float) -> float:
    """Same shape as the SQL CASE: full credit at >= 0.5h, scaled below."""
    if hours_remaining >= 0.5:
        return 1.0
    return max(0.0, hours_remaining / 0.5)


def _classify(
    *,
    last: float,
    day_low: float,
    momentum_5m: float,
    expected_move_pct: float,
    hours_remaining: float,
) -> tuple[str, float, str]:
    """Run the SQL CASE expression; return (action, confidence, reasons)."""
    near_low = 1.0 if last <= day_low * (1.0 + NEAR_LOW_PCT) else 0.0
    cond_mom = momentum_5m > 0

    # Weighted sum, identical to the SQL.
    conf = (
        W_NEAR_LOW * near_low
        + W_MOMENTUM * (min(1.0, momentum_5m / MOMENTUM_CAP) if cond_mom else 0.0)
        + W_VOL * min(1.0, expected_move_pct / VOL_CAP)
        + W_TIME * _time_factor(hours_remaining)
    )
    conf = min(1.0, max(0.0, conf))

    if near_low and cond_mom and expected_move_pct >= BUY_MOVE_THRESHOLD and conf >= BUY_CONF_THRESHOLD:
        action = "BUY"
        reasons = "near_day_low;positive_momentum;vol_above_4pct_target"
    elif near_low and cond_mom:
        action = "WATCH"
        reasons = "near_low_and_momentum;low_vol_or_short_time"
    else:
        action = "HOLD"
        reasons = "no_signal"

    return action, conf, reasons


# --------------------------------------------------------------------------- #
# Data fetch (batched, mirrors producer/stock_producer.py)
# --------------------------------------------------------------------------- #

def _fetch_snapshot(symbols: tuple[str, ...]) -> dict[str, dict]:
    """fast_info batch for prev_close, day_high/low, open, last price."""
    out: dict[str, dict] = {}
    if not symbols:
        return out
    try:
        tickers = yf.Tickers(" ".join(symbols))
    except Exception as exc:
        print(f"[warn] yf.Tickers construction failed: {exc}", file=sys.stderr)
        return out

    for sym in symbols:
        info: dict = {}
        try:
            fi = tickers.tickers[sym].fast_info
            info = {
                "last": _safe_float(getattr(fi, "last_price", None) or getattr(fi, "lastPrice", None)),
                "prev_close": _safe_float(getattr(fi, "previous_close", None) or getattr(fi, "previousClose", None)),
                "day_high": _safe_float(getattr(fi, "day_high", None) or getattr(fi, "dayHigh", None)),
                "day_low": _safe_float(getattr(fi, "day_low", None) or getattr(fi, "dayLow", None)),
                "day_open": _safe_float(getattr(fi, "open", None)),
            }
        except Exception as exc:
            print(f"[warn] fast_info failed for {sym}: {exc}", file=sys.stderr)
        # info() is sometimes more current — overlay when present.
        try:
            tk = tickers.tickers[sym]
            i = tk.info or {}
            for k, src in (
                ("last", "regularMarketPrice"),
                ("prev_close", "regularMarketPreviousClose"),
                ("day_high", "regularMarketDayHigh"),
                ("day_low", "regularMarketDayLow"),
                ("day_open", "regularMarketOpen"),
            ):
                v = _safe_float(i.get(src))
                if v is not None:
                    info[k] = v
        except Exception:
            pass
        out[sym] = info
    return out


def _fetch_momentum(symbols: tuple[str, ...]) -> dict[str, float | None]:
    """5m momentum: (last - first) / first over the last 5 minutes of 1m bars."""
    if not symbols:
        return {}
    try:
        data = yf.download(
            tickers=symbols,
            period="1d",
            interval="1m",
            group_by="ticker",
            progress=False,
            threads=True,
        )
    except Exception as exc:
        print(f"[warn] yf.download momentum failed: {exc}", file=sys.stderr)
        return {sym: None for sym in symbols}

    out: dict[str, float | None] = {}
    for sym in symbols:
        try:
            if isinstance(data.columns, MultiIndex):
                if sym not in data.columns.get_level_values(0):
                    out[sym] = None
                    continue
                sub = data[sym]
            else:
                sub = data
            sub = sub.dropna(how="all")
            if sub.empty or len(sub) < 2:
                out[sym] = None
                continue
            # Use the last 5 minutes of bars.
            tail = sub.tail(5)
            first_close = _safe_float(tail["Close"].iloc[0])
            last_close = _safe_float(tail["Close"].iloc[-1])
            if first_close is None or last_close is None or first_close == 0:
                out[sym] = None
                continue
            out[sym] = (last_close - first_close) / first_close
        except Exception:
            out[sym] = None
    return out


# --------------------------------------------------------------------------- #
# Computation
# --------------------------------------------------------------------------- #

def compute_signals(
    tickers: list[dict],
    *,
    now_et: datetime | None = None,
) -> list[Signal]:
    if now_et is None:
        now_et = datetime.now(NY_TZ)
    symbols = tuple(t["ticker"] for t in tickers)
    by_ticker = {t["ticker"]: t for t in tickers}

    snap = _fetch_snapshot(symbols)
    mom = _fetch_momentum(symbols)
    hours_remaining = _hours_remaining(now_et)

    signals: list[Signal] = []
    for sym in symbols:
        s = snap.get(sym, {})
        last = s.get("last")
        prev_close = s.get("prev_close")
        day_high = s.get("day_high")
        day_low = s.get("day_low")
        day_open = s.get("day_open")

        gap_pct: float | None = None
        if last is not None and prev_close not in (None, 0):
            gap_pct = (last - prev_close) / prev_close

        range_pct: float | None = None
        if day_high is not None and day_low not in (None, 0):
            range_pct = (day_high - day_low) / day_low

        expected_move_pct: float | None = None
        if range_pct is not None:
            expected_move_pct = range_pct * math.sqrt(hours_remaining / 6.5)

        momentum_5m = mom.get(sym)

        # Classification needs all four inputs — anything missing ⇒ HOLD/NA.
        if None in (last, day_low, momentum_5m, expected_move_pct):
            signals.append(Signal(
                ticker=sym,
                sector=by_ticker[sym].get("sector", ""),
                last=last,
                prev_close=prev_close,
                day_high=day_high,
                day_low=day_low,
                day_open=day_open,
                gap_pct=gap_pct,
                momentum_5m=momentum_5m,
                range_pct=range_pct,
                expected_move_pct=expected_move_pct,
                confidence=None,
                action="NA",
                reasons="missing_data",
            ))
            continue

        action, conf, reasons = _classify(
            last=last,  # type: ignore[arg-type]
            day_low=day_low,  # type: ignore[arg-type]
            momentum_5m=momentum_5m,  # type: ignore[arg-type]
            expected_move_pct=expected_move_pct,  # type: ignore[arg-type]
            hours_remaining=hours_remaining,
        )

        signals.append(Signal(
            ticker=sym,
            sector=by_ticker[sym].get("sector", ""),
            last=last,
            prev_close=prev_close,
            day_high=day_high,
            day_low=day_low,
            day_open=day_open,
            gap_pct=gap_pct,
            momentum_5m=momentum_5m,
            range_pct=range_pct,
            expected_move_pct=expected_move_pct,
            confidence=conf,
            action=action,
            reasons=reasons,
        ))

    # BUY first, then WATCH, then HOLD, then NA. Within each: confidence desc.
    order = {"BUY": 0, "WATCH": 1, "HOLD": 2, "NA": 3}
    signals.sort(key=lambda r: (order.get(r.action, 9), -(r.confidence or 0.0)))
    return signals


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

# Minimal ANSI color — disable with NO_COLOR or non-tty.
_USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _c(text: str, code: str) -> str:
    if not _USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def _green(s: str) -> str: return _c(s, "32")
def _yellow(s: str) -> str: return _c(s, "33")
def _red(s: str) -> str: return _c(s, "31")
def _dim(s: str) -> str: return _c(s, "2")
def _bold(s: str) -> str: return _c(s, "1")


def _fmt(x, places: int = 2, dash: str = "—") -> str:
    if x is None:
        return dash
    try:
        return f"{float(x):.{places}f}"
    except (TypeError, ValueError):
        return dash


def _pct(x, places: int = 2, dash: str = "—", signed: bool = True) -> str:
    if x is None:
        return dash
    fmt = f"{{:{'' if signed else ''}.{places}f}}"
    s = f"{x * 100:.{places}f}"
    if signed and not s.startswith("-"):
        s = "+" + s
    return s + "%"


def render_table(signals: list[Signal], now_et: datetime) -> str:
    buys = [s for s in signals if s.action == "BUY"]
    watches = [s for s in signals if s.action == "WATCH"]

    market_state = "OPEN" if is_market_hours() else "CLOSED"
    hours_left = _hours_remaining(now_et)
    header = _bold(
        f"=== Live BUY signals — {now_et.strftime('%Y-%m-%d %H:%M:%S ET')} "
        f"({market_state}, {hours_left:.1f}h left) ==="
    )
    subtitle = _dim(
        f"Universe: {len(signals)} tickers  |  "
        f"BUY: {len(buys)}  |  WATCH: {len(watches)}  |  "
        f"signal model: mirrors flink/jobs/04_signals.sql"
    )

    cols = [
        ("TICKER", 7, lambda s: s.ticker),
        ("ACTION", 6, lambda s: s.action),
        ("CONF", 5, lambda s: _fmt((s.confidence or 0) * 100, 0) + "%"),
        ("LAST", 8, lambda s: _fmt(s.last, 2)),
        ("GAP%", 7, lambda s: _pct(s.gap_pct, 2)),
        ("DAY-LOW", 8, lambda s: _fmt(s.day_low, 2)),
        ("DAY-HI", 8, lambda s: _fmt(s.day_high, 2)),
        ("RANGE%", 7, lambda s: _pct(s.range_pct, 2, signed=False)),
        ("MOM5M%", 7, lambda s: _pct(s.momentum_5m, 2)),
        ("EXP%", 7, lambda s: _pct(s.expected_move_pct, 2, signed=False)),
        ("SECTOR", 22, lambda s: s.sector),
    ]

    # Header row
    head = "  ".join(f"{name:<{w}}" for name, w, _ in cols)
    sep = _dim("  ".join("─" * w for _, w, _ in cols))

    rows: list[str] = [header, subtitle, "", head, sep]

    def _row_for(s: Signal) -> str:
        cells = []
        for i, (_, w, fn) in enumerate(cols):
            text = fn(s)
            if i == 1:  # action
                if s.action == "BUY":
                    text = _green(_bold(text))
                elif s.action == "WATCH":
                    text = _yellow(text)
                elif s.action == "HOLD":
                    text = _dim(text)
                else:
                    text = _red(text)
            elif i == 2 and s.confidence is not None and s.confidence >= 0.6:
                text = _green(text)
            cells.append(f"{text:<{w}}")
        return "  ".join(cells)

    for s in signals:
        rows.append(_row_for(s))
    return "\n".join(rows)


def render_buy_summary(signals: list[Signal]) -> str:
    """Short, scannable list — the 'what should I buy today?' view."""
    buys = [s for s in signals if s.action == "BUY"]
    watches = [s for s in signals if s.action == "WATCH"]
    if not buys and not watches:
        return _dim("  (no BUY/WATCH signals right now — try again at the open)")

    out: list[str] = []
    if buys:
        out.append(_green(_bold(f"  🟢 BUY ({len(buys)}):")))
        for s in sorted(buys, key=lambda x: -(x.confidence or 0)):
            out.append(
                f"    {s.ticker:<7} ${_fmt(s.last, 2):>8}   "
                f"conf={_fmt((s.confidence or 0) * 100, 0)}%   "
                f"mom5m={_pct(s.momentum_5m, 2)}   "
                f"exp%={_pct(s.expected_move_pct, 2, signed=False)}   "
                f"[{s.sector}]"
            )
    if watches:
        out.append("")
        out.append(_yellow(f"  🟡 WATCH ({len(watches)}):"))
        for s in sorted(watches, key=lambda x: -(x.confidence or 0))[:8]:
            out.append(
                f"    {s.ticker:<7} ${_fmt(s.last, 2):>8}   "
                f"conf={_fmt((s.confidence or 0) * 100, 0)}%   "
                f"mom5m={_pct(s.momentum_5m, 2)}   "
                f"[{s.sector}]"
            )
        if len(watches) > 8:
            out.append(_dim(f"    ... and {len(watches) - 8} more"))
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Show live BUY/WATCH/HOLD signals for the ticker universe.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--tickers",
        type=str,
        default=None,
        help="Comma-separated tickers (default: full universe from "
             "producer/ticker_universe.py).",
    )
    p.add_argument(
        "--once",
        action="store_true",
        help="Single snapshot, then exit.",
    )
    p.add_argument(
        "--poll-seconds",
        type=int,
        default=int(os.environ.get("POLL_SECONDS", "60")),
        help="Refresh interval in seconds (default: 60).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a table.",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        help="Show only the BUY/WATCH summary (skip the full table).",
    )
    p.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Append every snapshot to this CSV file (header written on first run).",
    )
    return p.parse_args(argv)


def _append_csv(path: str, now_et: datetime, signals: list[Signal]) -> None:
    import csv
    new_file = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow([
                "ts_et", "ticker", "action", "confidence", "last", "prev_close",
                "gap_pct", "day_open", "day_high", "day_low", "range_pct",
                "momentum_5m", "expected_move_pct", "sector", "reasons",
            ])
        for s in signals:
            w.writerow([
                now_et.isoformat(), s.ticker, s.action, s.confidence, s.last,
                s.prev_close, s.gap_pct, s.day_open, s.day_high, s.day_low,
                s.range_pct, s.momentum_5m, s.expected_move_pct, s.sector, s.reasons,
            ])


def _resolve_universe(args) -> list[dict]:
    """Build the list of ticker dicts to process.

    - If ``--tickers`` is given, those symbols are used *as-is* — the user is
      telling us exactly what they want to see, so we do not filter against
      the universe CSV (which may not contain the ticker at all).
    - Otherwise the full universe from ``ticker_universe.py`` is returned.
    """
    if args.tickers:
        wanted = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        # Look up sector info from the universe when possible; otherwise blank.
        by_symbol = {t["ticker"]: t for t in get_tickers()}
        return [
            by_symbol.get(
                sym,
                {"ticker": sym, "sector": "", "index_membership": ""},
            )
            for sym in wanted
        ]
    return list(get_tickers())


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    universe = _resolve_universe(args)
    if not universe:
        print("No tickers to process. Check --tickers spelling or CSV.", file=sys.stderr)
        return 2

    print(
        f"=== Live BUY/WATCH/HOLD signals — {len(universe)} tickers "
        f"(poll every {args.poll_seconds}s) — Ctrl-C to stop ===",
        flush=True,
    )
    if args.csv:
        print(f"CSV log: {args.csv}", flush=True)

    try:
        while True:
            now_et = datetime.now(NY_TZ)
            signals = compute_signals(universe, now_et=now_et)

            if args.json:
                payload = {
                    "ts_et": now_et.isoformat(),
                    "market_open": is_market_hours(),
                    "hours_remaining": _hours_remaining(now_et),
                    "n_buys": sum(1 for s in signals if s.action == "BUY"),
                    "n_watches": sum(1 for s in signals if s.action == "WATCH"),
                    "signals": [s.to_row() for s in signals],
                }
                print(json.dumps(payload, indent=2, default=str), flush=True)
            else:
                # Clear screen for a "live dashboard" feel (only when tty + once/poll).
                if sys.stdout.isatty() and not args.once:
                    sys.stdout.write("\033[2J\033[H")
                print(render_table(signals, now_et), flush=True)
                if not args.summary:
                    print("\n" + render_buy_summary(signals), flush=True)

            if args.csv:
                _append_csv(args.csv, now_et, signals)

            if args.once:
                return 0
            time.sleep(args.poll_seconds)
    except KeyboardInterrupt:
        print("\nstopped.", flush=True)
        return 0


if __name__ == "__main__":
    sys.exit(main())
