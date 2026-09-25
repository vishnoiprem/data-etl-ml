# Architecture

A prose companion to the ASCII diagram in `README.md`. Each stage has a single
responsibility and a single well-defined output.

## 1. Producer (`producer/`)

**Responsibility:** turn the public US equity market into a stream of normalized JSON
ticks on a Kafka topic.

- **Input:** yfinance (or similar) quote fetches for a configurable ticker list.
- **Output:** Kafka topic `ticks.raw` — one JSON message per tick:
  ```json
  {
    "ts": "2026-09-25T13:42:11.123Z",
    "ticker": "AAPL",
    "price": 190.12,
    "volume": 12,
    "previous_close": 188.74
  }
  ```
- **Notes:** asyncio + batching; honors yfinance rate limits with exponential backoff.
  Idempotent at the topic level — replaying produces the same downstream state.

## 2. Kafka (`kafka`)

**Responsibility:** durable, ordered, partitioned transport for ticks.

- Single broker for the dev stack; KRaft mode (no Zookeeper).
- Topic `ticks.raw` partitioned by ticker for in-order processing per symbol.
- Retention short (hours) — TimescaleDB is the system of record.

## 3. Flink (`flink/`)

**Responsibility:** transform the raw stream into analytics-ready tables.

- **Job A — `bars_1m`**: Tumbling 1-minute window over `ticks.raw` keyed by ticker.
  Computes `open`, `high`, `low`, `close`, `volume` per bar and writes to TimescaleDB.
- **Job B — `signals`**: Continuous query over `bars_1m` computing intraday_return_5m,
  vol_15m, range_pct, expected_move_pct, confidence, target_price, and action
  (BUY/WATCH/HOLD). Writes to the `signals` hypertable.
- **UDFs** (`flink/udf/`) for any feature not expressible in pure SQL.

The SQL Client submits jobs declared in `flink/jobs/*.sql` — see `3_register_flink_jobs.sh`.

## 4. TimescaleDB (`db/`)

**Responsibility:** persistent time-series storage with SQL access for Grafana.

- Hypertables: `ticks`, `bars_1m`, `signals` — partitioned on `ts`.
- Convenience views: `latest_prices`, plus aggregates used by the dashboard.
- Schema files live in `db/01_schema.sql` and `db/02_views.sql` (idempotent).

## 5. Grafana (`grafana/`)

**Responsibility:** human-facing visualization.

- Provisioned datasource: TimescaleDB (uid `timescaledb`).
- Provisioned dashboards:
  - `US Stocks Live` (`stock-overview`) — five panels covering live prices, intraday
    OHLCV for a selected ticker, momentum/vol heatmap, target projection, and recent
    signals.
  - `Buy Signals` (`signals-alerts`) — focused BUY counter, per-minute rate, and
    latest signals table.
- Refresh: 10 seconds. Time window default: last 6 hours.

## 6. Orchestration (`scripts/`)

**Responsibility:** give a single human a single command sequence to bring the whole
system up — and another to tear it down.

- `0_setup_env.sh` — copy `.env.example` → `.env`, ensure `producer/__init__.py`, verify
  Python 3.11+.
- `1_start_containers.sh` — `docker compose up -d`, wait for healthchecks (180s).
- `2_init_db.sh` — wait for TimescaleDB, apply views SQL.
- `3_register_flink_jobs.sh` — submit every `flink/jobs/*.sql` via the sql-client.
- `4_start_producer.sh` — restart the producer container and tail logs briefly.
- `5_open_grafana.sh` — open `http://localhost:3000` in the default browser.
- `stop_all.sh` — `docker compose down` (volumes preserved).

## Data flow at a glance

```
yfinance ──► producer ──► Kafka ──► Flink (bars_1m, signals) ──► TimescaleDB ──► Grafana
                                                  │
                                                  └─► writes back to TimescaleDB
```

## Failure model

- **Producer dies** — `4_start_producer.sh` (or `docker compose restart stock-producer`)
  restarts it; Kafka retains the topic, downstream catches up.
- **Flink TaskManager dies** — JobManager re-schedules; in-flight windows recompute
  deterministically from Kafka offsets.
- **TimescaleDB dies** — Kafka retains ticks; replay on restart (see `db/` for retention
  policies). Production setups would use a continuous backup / WAL archive.
- **Grafana dies** — stateless; just restart. Dashboards auto-reload from provisioning.

## What's intentionally out of scope

- Authentication / multi-tenant Grafana.
- TLS between services.
- Exactly-once sinks (we rely on idempotent view creation and row-level inserts keyed
  on `(ts, ticker)`).
- Backfill from historical sources.
