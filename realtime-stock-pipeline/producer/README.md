# Producer — Kafka tick publisher

> **A small, clean Python service that polls Yahoo Finance and
> publishes per-ticker JSON ticks to Kafka.** Cadence: 5s during
> US market hours, 60s otherwise. The producer is the entry point
> of the streaming pipeline — everything downstream (Flink,
> TimescaleDB, Grafana, AI signals) consumes the Kafka topic.

This directory contains exactly two Python files and a Dockerfile.
The intent is to be the smallest correct reference for "polling a
real-time data source and publishing to Kafka." The pattern is
identical for any other source you'd want to stream: rates, FX,
weather, IoT, clickstream.

---

## Files

| File | What it does |
|------|--------------|
| `stock_producer.py` | The producer. Polls Yahoo Finance, publishes JSON ticks to Kafka. Handles backpressure, reconnection, market-hours-aware cadence, and graceful shutdown. |
| `ticker_universe.py` | Loads the universe of tickers from `config/tickers_top100.csv` with a hardcoded top-10 fallback. Also exposes `is_market_hours()` so the producer can switch cadences. |
| `Dockerfile` | Containerize the producer so it can run alongside the rest of the stack in `docker compose up`. |

The full Kafka topic is `stock.ticks`. Each message is a JSON
envelope:

```json
{
  "ticker": "AAPL",
  "ts": "2026-10-13T01:23:45.123Z",
  "price": 187.43,
  "volume": 12345678,
  "day_high": 188.10,
  "day_low": 186.92,
  "day_open": 187.20,
  "previous_close": 186.55
}
```

---

## How it works

```
            ┌──────────────────┐
            │  Yahoo Finance   │
            │  (free, no key)  │
            └────────┬─────────┘
                     │  yf.download (batched, every 5s/60s)
                     ▼
            ┌──────────────────┐
            │  stock_producer  │
            │  - parse + check │
            │  - market hours? │
            │  - backpressure  │
            └────────┬─────────┘
                     │  JSON per ticker
                     ▼
            ┌──────────────────┐
            │  Kafka           │
            │  topic: stock.ticks│
            └────────┬─────────┘
                     │
                     ▼
            (Flink consumes → TimescaleDB → Grafana + AI signals)
```

The producer is the **only** component that talks to Yahoo Finance.
Downstream services consume the Kafka topic; they never hit Yahoo
directly. That decoupling is the whole point of putting Kafka in
the middle.

---

## How to run it

```bash
# Local Python
pip install -r requirements.txt
KAFKA_BOOTSTRAP=localhost:9092 python -m producer.stock_producer

# Or via Docker
docker build -t rts-producer .
docker run --rm --network host \
  -e KAFKA_BOOTSTRAP=localhost:9092 \
  rts-producer
```

The producer will:

1. Load the ticker universe (CSV, with top-10 fallback).
2. Check market hours; switch cadence to 5s or 60s.
3. Poll Yahoo Finance in batches (single HTTP round-trip per
   batch — avoids `yfinance` rate limits).
4. Publish one JSON message per ticker to Kafka.
5. Back off on Kafka backpressure; reconnect on broker drops.
6. Handle SIGTERM gracefully (drain in-flight, close producer).

---

## The 3 things this producer gets right

1. **Single HTTP round-trip per batch.** `yf.download(symbols)`
   returns a wide DataFrame; the producer iterates rows, not
   symbols. With 100 tickers, that's 1 request per cadence, not
   100.
2. **Market-hours-aware cadence.** 5s during US market hours,
   60s otherwise. Halves the data volume (and the Yahoo
   politeness budget) outside of trading hours.
3. **No silent loss on broker drop.** The producer tracks
   delivery callbacks via `confluent-kafka`'s `Producer`,
   logs every failed delivery, and exits non-zero on persistent
   failure so the orchestrator (`docker compose`, systemd,
   k8s) can restart it.

---

## What this is NOT

- **Not a low-latency HFT producer.** Yahoo's free API has ~1-3s
  of skew vs. the real tape. If you need sub-second latency,
  pay for a real market data feed (Polygon, Alpaca, IEX Cloud).
- **Not multi-exchange.** US equities only. Adding a separate
  producer for LSE or JPX is the right move; the pattern is
  the same but the universe + market-hours logic need to be
  per-exchange.
- **Not the trading strategy.** The producer only publishes
  the tape. The strategy lives in
  [`../trade-finder/`](../trade-finder/) — the
  always-on opportunity engine that consumes the same tape.
- **Not the AI signal generator.** That lives in
  [`../ai_signals/`](../ai_signals/) and is a separate
  service that consumes Kafka.

---

## Related directories

- [`../`](../) — the parent `realtime-stock-pipeline/`. Start
  there for the full architecture.
- [`../flink/`](../flink/) — the Flink SQL jobs that consume
  this topic and write to TimescaleDB.
- [`../db/`](../db/) — the TimescaleDB schema and views.
- [`../grafana/`](../grafana/) — the Grafana dashboards
  backed by the views.
- [`../ai_signals/`](../ai_signals/) — the ML signal layer
  that consumes the same topic.
- [`../trade-finder/`](../trade-finder/) — the always-on
  trade opportunity engine (a separate process on the same
  machine).
