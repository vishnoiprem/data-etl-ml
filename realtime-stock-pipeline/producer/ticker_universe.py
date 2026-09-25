"""Ticker universe loader for the real-time US stock pipeline.

Loads the universe of tickers from ``config/tickers_top100.csv`` and exposes a
``get_tickers()`` helper. If the CSV is missing or malformed (e.g. running in
a stripped-down dev environment), falls back to a hardcoded top-10 list so the
producer can still demonstrate end-to-end flow.
"""
from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from datetime import datetime, time
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# Project root is two levels up from this file: producer/ticker_universe.py -> <root>
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CSV_PATH = _PROJECT_ROOT / "config" / "tickers_top100.csv"
_NY_TZ = ZoneInfo("America/New_York")

# Hardcoded fallback: the major tickers a demo cannot be without.
_FALLBACK_TICKERS = [
    {"ticker": "AAPL", "sector": "Technology", "index_membership": "S&P 500,NASDAQ 100"},
    {"ticker": "MSFT", "sector": "Technology", "index_membership": "S&P 500,NASDAQ 100"},
    {"ticker": "GOOGL", "sector": "Communication Services", "index_membership": "S&P 500,NASDAQ 100"},
    {"ticker": "AMZN", "sector": "Consumer Cyclical", "index_membership": "S&P 500,NASDAQ 100"},
    {"ticker": "NVDA", "sector": "Technology", "index_membership": "S&P 500,NASDAQ 100"},
    {"ticker": "META", "sector": "Communication Services", "index_membership": "S&P 500,NASDAQ 100"},
    {"ticker": "TSLA", "sector": "Consumer Cyclical", "index_membership": "S&P 500,NASDAQ 100"},
    {"ticker": "BRK-B", "sector": "Financial Services", "index_membership": "S&P 500"},
    {"ticker": "JPM", "sector": "Financial Services", "index_membership": "S&P 500"},
    {"ticker": "V", "sector": "Financial Services", "index_membership": "S&P 500,NASDAQ 100"},
    {"ticker": "MA", "sector": "Financial Services", "index_membership": "S&P 500,NASDAQ 100"},
]


@dataclass(frozen=True)
class Ticker:
    """One row of the ticker universe."""
    ticker: str
    sector: str
    index_membership: str

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "sector": self.sector,
            "index_membership": self.index_membership,
        }


def _load_from_csv(path: Path) -> list[dict]:
    """Parse the CSV into a list of plain dicts."""
    rows: list[dict] = []
    with path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        required = {"ticker", "sector", "index_membership"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"CSV missing required columns: {required}")
        seen: set[str] = set()
        for raw in reader:
            symbol = (raw.get("ticker") or "").strip().upper()
            if not symbol or symbol in seen:
                continue
            seen.add(symbol)
            rows.append({
                "ticker": symbol,
                "sector": (raw.get("sector") or "").strip(),
                "index_membership": (raw.get("index_membership") or "").strip(),
            })
    if not rows:
        raise ValueError("CSV produced zero rows")
    return rows


@lru_cache(maxsize=1)
def get_tickers() -> list[dict]:
    """Return the ticker universe as a list of dicts.

    Reads from ``config/tickers_top100.csv`` relative to the project root.
    Falls back to a small hardcoded list if the file is missing or unparsable,
    so the demo pipeline can still produce *some* ticks in dev environments.
    """
    try:
        if not _CSV_PATH.exists():
            raise FileNotFoundError(f"Ticker CSV not found at {_CSV_PATH}")
        tickers = _load_from_csv(_CSV_PATH)
        logger.info("Loaded %d tickers from %s", len(tickers), _CSV_PATH)
        return tickers
    except Exception as exc:  # broad: we want any failure to fall back
        logger.warning(
            "Falling back to hardcoded ticker list (%d tickers): %s",
            len(_FALLBACK_TICKERS),
            exc,
        )
        return list(_FALLBACK_TICKERS)


def is_market_hours(now: datetime | None = None) -> bool:
    """Return True if ``now`` (default: current time) is within US regular
    trading hours (Mon-Fri, 09:30-16:00 America/New_York). Weekends are
    treated as closed regardless of clock time.
    """
    if now is None:
        now = datetime.now(_NY_TZ)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=_NY_TZ)
    else:
        now = now.astimezone(_NY_TZ)

    if now.weekday() >= 5:  # Sat=5, Sun=6
        return False

    market_open = time(9, 30)
    market_close = time(16, 0)
    return market_open <= now.time().replace(microsecond=0) < market_close


if __name__ == "__main__":  # quick manual smoke test
    logging.basicConfig(level=logging.INFO)
    tickers = get_tickers()
    print(f"{len(tickers)} tickers loaded; first 5: {[t['ticker'] for t in tickers[:5]]}")
    print(f"market_hours: {is_market_hours()}")
