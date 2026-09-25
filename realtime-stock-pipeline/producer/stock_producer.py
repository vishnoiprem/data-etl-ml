"""Real-time US stock producer.

Polls Yahoo Finance in batched ``yf.download`` calls (single HTTP round-trip per
batch — avoids yfinance rate limits) and publishes per-ticker JSON ticks to
Kafka topic ``stock.ticks``. Cadence: 5s during US market hours, 60s otherwise.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import pandas as pd
import yfinance as yf
from confluent_kafka import KafkaError, KafkaException, Producer

from producer.ticker_universe import get_tickers, is_market_hours

logger = logging.getLogger("stock_producer")

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "localhost:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "stock.ticks")
POLL_FAST_SECONDS = 5
POLL_SLOW_SECONDS = 60
INITIAL_BACKOFF_SECONDS = 2.0
MAX_BACKOFF_SECONDS = 60.0


@dataclass
class ProducerStats:
    """Run-level counters, useful for observability."""
    batches: int = 0
    messages_sent: int = 0
    errors: int = 0
    started_at: datetime = datetime.utcnow()


def _delivery_report(err: KafkaError | None, msg) -> None:
    """confluent-kafka per-message callback. Logs but does not raise."""
    if err is not None:
        logger.error("Delivery failed for %s: %s", msg.key(), err)
    # Successful deliveries are noisy at high rate; debug-level only.
    else:
        logger.debug("Delivered %s [%d] @ offset %d", msg.key(), msg.partition(), msg.offset())


def _build_producer(bootstrap: str) -> Producer:
    """Construct a confluent-kafka Producer tuned for low-latency batching."""
    conf = {
        "bootstrap.servers": bootstrap,
        "client.id": "stock-producer",
        # Low-latency: send promptly, don't sit on batches forever.
        "linger.ms": 50,
        "compression.type": "lz4",
        "acks": "1",
        # Reasonable retries for transient broker hiccups.
        "retries": 5,
        "retry.backoff.ms": 200,
    }
    return Producer(conf)


def _fetch_batch(symbols: tuple[str, ...]) -> pd.DataFrame:
    """One batched yfinance download covering all symbols."""
    logger.debug("yfinance.download: %d tickers", len(symbols))
    data = yf.download(
        tickers=symbols,
        period="1d",
        interval="1m",
        group_by="ticker",
        progress=False,
        threads=True,
    )
    return data


def _extract_latest(data: pd.DataFrame, symbol: str) -> dict | None:
    """Pull the most recent 1-minute bar for a single symbol from a batched frame.

    Returns ``None`` if there is no data for the symbol (e.g. delisted, halted,
    or no trades yet today).
    """
    try:
        if isinstance(data.columns, pd.MultiIndex):
            if symbol not in data.columns.get_level_values(0):
                return None
            sub = data[symbol]
        else:
            # Single-symbol case: yfinance returns a flat frame.
            sub = data
        sub = sub.dropna(how="all")
        if sub.empty:
            return None
        row = sub.iloc[-1]
    except (KeyError, IndexError, ValueError) as exc:
        logger.debug("No data for %s: %s", symbol, exc)
        return None

    def _f(val) -> float | None:
        try:
            f = float(val)
        except (TypeError, ValueError):
            return None
        if pd.isna(f):
            return None
        return round(f, 4)

    price = _f(row.get("Close"))
    if price is None:
        return None

    ts = sub.index[-1]
    # Normalize to ISO-8601 with NY offset so downstream Flink can parse it.
    if isinstance(ts, pd.Timestamp):
        ts_str = ts.tz_convert("America/New_York").isoformat() if ts.tz is not None \
            else ts.isoformat()
    else:
        ts_str = datetime.utcnow().isoformat()

    return {
        "ticker": symbol,
        "ts": ts_str,
        "price": price,
        "open": _f(row.get("Open")),
        "high": _f(row.get("High")),
        "low": _f(row.get("Low")),
        "volume": int(row.get("Volume") or 0),
        "day_high": _f(row.get("High")),
        "day_low": _f(row.get("Low")),
        "day_open": _f(row.get("Open")),
        "previous_close": None,  # yfinance intraday 1m doesn't include prev close; leave None
    }


def _fetch_day_metadata(symbols: tuple[str, ...]) -> dict[str, dict]:
    """Fetch previous_close (and friends) for each symbol via batched Tickers call.

    ``yf.download`` intraday 1m data does not include prior-close, so we need a
    second call. We batch with ``yf.Tickers`` so all symbols come back in one
    HTTP round-trip — keeps us well under yfinance's rate limit.
    """
    try:
        tickers = yf.Tickers(" ".join(symbols))
    except Exception as exc:
        logger.debug("yf.Tickers construction failed: %s", exc)
        return {}

    meta: dict[str, dict] = {}
    for sym in symbols:
        try:
            info = tickers.tickers[sym].fast_info
            meta[sym] = {
                "previous_close": _safe_float(getattr(info, "previous_close", None)),
                "day_high": _safe_float(getattr(info, "day_high", None)),
                "day_low": _safe_float(getattr(info, "day_low", None)),
                "day_open": _safe_float(getattr(info, "open", None)),
            }
        except Exception as exc:  # network / parse / rate-limit — keep going
            logger.debug("fast_info failed for %s: %s", sym, exc)
            meta[sym] = {}
    return meta


def _safe_float(val) -> float | None:
    try:
        f = float(val)
    except (TypeError, ValueError):
        return None
    if pd.isna(f):
        return None
    return round(f, 4)


def _publish_batch(producer: Producer, messages: Iterable[dict]) -> int:
    """Produce a sequence of tick dicts; returns the count queued."""
    count = 0
    for msg in messages:
        try:
            producer.produce(
                topic=KAFKA_TOPIC,
                key=msg["ticker"].encode("utf-8"),
                value=json.dumps(msg, default=str).encode("utf-8"),
                on_delivery=_delivery_report,
            )
            count += 1
        except BufferError:
            # Local queue full: poll to drain callbacks then retry once.
            producer.poll(1.0)
            try:
                producer.produce(
                    topic=KAFKA_TOPIC,
                    key=msg["ticker"].encode("utf-8"),
                    value=json.dumps(msg, default=str).encode("utf-8"),
                    on_delivery=_delivery_report,
                )
                count += 1
            except Exception as exc:
                logger.error("produce() failed for %s: %s", msg.get("ticker"), exc)
        except KafkaException as exc:
            logger.error("KafkaException for %s: %s", msg.get("ticker"), exc)
    producer.poll(0)
    return count


def _run_loop(
    symbols: tuple[str, ...],
    producer: Producer,
    stats: ProducerStats,
    once: bool,
) -> None:
    """Main poll loop. ``once=True`` exits after a single batch."""
    backoff = INITIAL_BACKOFF_SECONDS
    last_market_state: bool | None = None

    while True:
        market_open = is_market_hours()
        if market_open != last_market_state:
            logger.info("Market state change: %s", "OPEN" if market_open else "CLOSED")
            last_market_state = market_open

        try:
            data = _fetch_batch(symbols)
            meta = _fetch_day_metadata(symbols) if not once else {}

            messages: list[dict] = []
            for sym in symbols:
                tick = _extract_latest(data, sym)
                if tick is None:
                    continue
                m = meta.get(sym) or {}
                # Overlay richer day-level metadata when we have it.
                if m.get("day_high") is not None:
                    tick["day_high"] = m["day_high"]
                if m.get("day_low") is not None:
                    tick["day_low"] = m["day_low"]
                if m.get("day_open") is not None:
                    tick["day_open"] = m["day_open"]
                if m.get("previous_close") is not None:
                    tick["previous_close"] = m["previous_close"]
                messages.append(tick)

            sent = _publish_batch(producer, messages)
            stats.batches += 1
            stats.messages_sent += sent
            logger.info(
                "batch=%d published=%d tickers=%d market_open=%s",
                stats.batches, sent, len(symbols), market_open,
            )
            backoff = INITIAL_BACKOFF_SECONDS  # success — reset backoff

            if once:
                producer.flush(10)
                return

            interval = POLL_FAST_SECONDS if market_open else POLL_SLOW_SECONDS
            time.sleep(interval)

        except KeyboardInterrupt:
            raise
        except Exception as exc:
            stats.errors += 1
            logger.exception("Batch failed (will retry in %.1fs): %s", backoff, exc)
            time.sleep(backoff)
            backoff = min(backoff * 2.0, MAX_BACKOFF_SECONDS)


def _install_signal_handlers(producer: Producer, stats: ProducerStats) -> None:
    """Best-effort graceful shutdown on SIGINT / SIGTERM."""
    stop = {"flag": False}

    def _handle(signum, _frame):
        if stop["flag"]:
            logger.warning("Second signal received — forcing exit")
            sys.exit(1)
        stop["flag"] = True
        logger.info(
            "Signal %s received — flushing producer (batches=%d messages=%d)",
            signum, stats.batches, stats.messages_sent,
        )
        try:
            producer.flush(10)
        finally:
            logger.info("Producer flushed. Exiting.")
            sys.exit(0)

    signal.signal(signal.SIGINT, _handle)
    signal.signal(signal.SIGTERM, _handle)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Real-time US stock Kafka producer")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Fetch exactly one batch and exit (useful for smoke tests).",
    )
    parser.add_argument(
        "--tickers",
        type=str,
        default=None,
        help="Comma-separated tickers to fetch (overrides the universe). "
             "Example: --tickers AAPL,MSFT,NVDA",
    )
    parser.add_argument(
        "--bootstrap",
        type=str,
        default=KAFKA_BOOTSTRAP,
        help="Kafka bootstrap servers (default: $KAFKA_BOOTSTRAP or localhost:9092).",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    universe = get_tickers()
    if args.tickers:
        wanted = {t.strip().upper() for t in args.tickers.split(",") if t.strip()}
        symbols = tuple(t["ticker"] for t in universe if t["ticker"] in wanted)
        if not symbols:
            logger.error("--tickers produced an empty set; check spelling")
            return 2
    else:
        symbols = tuple(t["ticker"] for t in universe)

    logger.info(
        "Starting producer: bootstrap=%s topic=%s tickers=%d once=%s",
        args.bootstrap, KAFKA_TOPIC, len(symbols), args.once,
    )

    producer = _build_producer(args.bootstrap)
    stats = ProducerStats()
    _install_signal_handlers(producer, stats)

    try:
        _run_loop(symbols, producer, stats, once=args.once)
    except KeyboardInterrupt:
        logger.info("Interrupted — flushing producer")
    finally:
        producer.flush(10)
        logger.info(
            "Shutdown complete: batches=%d messages=%d errors=%d elapsed=%.1fs",
            stats.batches, stats.messages_sent, stats.errors,
            (datetime.utcnow() - stats.started_at).total_seconds(),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
