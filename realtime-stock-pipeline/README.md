# Realtime US Stock Pipeline

A streaming pipeline that pulls US equity ticks, computes 1-minute OHLCV bars, runs
intraday-momentum rules, and surfaces BUY/WATCH signals in Grafana — end-to-end in
real time using Kafka, Flink, and TimescaleDB.

> **Disclaimer** — Educational project only. **Not financial advice.** No guarantee of
> accuracy, completeness, or profitability. Markets can lose money. Do your own research.

---

## Architecture

```
                +---------------------+
                |  stock-producer     |   yfinance → Kafka
                |  (Python, asyncio)  |   topic: stock.ticks
                +----------+----------+
                           |
                           v
                +---------------------+
                |       Kafka         |   stock.ticks
                |  (Confluent / KRaft)|
                +----------+----------+
                           |
                           v
                +---------------------+
                |   Flink JobManager  |
                |  +  TaskManager     |   SQL jobs (3 of 4 task slots):
                |                     |     - 02_bars_1m  -> bars_1m
                |                     |     - 03_bars_5m  -> bars_5m
                |                     |     - 04_signals  -> signals
                +----+-----------+----+
                     |           |
                     v           v
              +-----------------------+
              |       TimescaleDB     |   tables:
              |  bars_1m, bars_5m,    |     bars_1m, bars_5m, signals
              |  signals             |     + view latest_prices
              +----------+------------+
                         |
                         v
              +-----------------------+
              |        Grafana        |   dashboard:
              |   provisioning YAML   |     - US Stocks Live
              +-----------------------+
```

---

## Quick start

```bash
# from the project root
bash scripts/0_setup_env.sh         # copy .env, ensure producer/__init__.py, check Python
bash scripts/1_start_containers.sh  # docker compose up -d + healthcheck wait
bash scripts/2_init_db.sh           # apply db/02_views.sql (idempotent)
bash scripts/3_register_flink_jobs.sh # submit every flink/jobs/*.sql
bash scripts/4_start_producer.sh    # restart stock-producer + tail 10s
bash scripts/5_open_grafana.sh      # open dashboard in browser
```

Then in another terminal, follow producer logs:

```bash
docker compose logs -f stock-producer
```

---

## URLs

| Service     | URL                       | Credentials       |
|-------------|---------------------------|-------------------|
| Grafana     | http://localhost:3000     | admin / admin     |
| Flink UI    | http://localhost:8081     | (none)            |
| Kafka       | localhost:9092            | (PLAINTEXT)       |
| TimescaleDB | localhost:5432            | from `.env`       |

---

## Pipeline components

- **producer/** — Python service that polls yfinance for ~100 tickers, emits JSON ticks
  to the `stock.ticks` Kafka topic. Async + batching. Each tick is a tz-aware ISO 8601
  timestamp so Flink's `TO_TIMESTAMP` parses cleanly.
- **flink/jobs/** — SQL jobs that consume `stock.ticks` and write to TimescaleDB:
  - `02_bars_1m.sql` — TUMBLE 1-min OHLCV → `bars_1m`
  - `03_bars_5m.sql` — TUMBLE 5-min OHLCV → `bars_5m`
  - `04_signals.sql` — HOP 15-min features (momentum, volatility) + pure-SQL
    BUY/WATCH/HOLD classifier → `signals`
- **db/** — TimescaleDB schema: tables for `bars_1m`, `bars_5m`, `signals`, plus
  convenience views (`latest_prices` sources from `bars_1m` joined to the latest
  `signals` row per ticker for `previous_close`/`day_high`/`day_low`).
- **grafana/** — Auto-provisioned dashboards (this folder) plus datasource YAML.
- **scripts/** — The orchestration layer you're using now.

See `docs/signal-explanation.md` for the exact BUY/WATCH rules and confidence math.

---

## What's running

Three Flink jobs are intentionally kept alive (the cluster exposes 4 task slots,
so we run 3 long-lived sinks and submit the 4th slot for ad-hoc experiments):

| Job                       | Sink              | Notes                                     |
|---------------------------|-------------------|-------------------------------------------|
| `02_bars_1m_sink`         | `bars_1m`         | 1-min OHLCV per ticker.                   |
| `03_bars_5m_sink`         | `bars_5m`         | 5-min OHLCV per ticker.                   |
| `04_signals_jdbc_sink`    | `signals`         | BUY / WATCH / HOLD rows every ~minute.    |

`01_ticks_to_jdbc.sql` (raw-tick passthrough to the `ticks` table) is shipped in
the repo but is **not** submitted by default: the Flink 1.17 Kafka source has a
known consumer-hang issue against KRaft-mode brokers when used inside a parallel
source job that shares a TaskManager with other Kafka sources. The dashboard
sources everything from `bars_1m` / `bars_5m` / `signals` so the raw `ticks` table
isn't on the critical path.

---



## Caveats

- **yfinance has a ~15-minute quote delay** for most free endpoints. Numbers reflect
  delayed data, not live exchange prints.
- **Rate limits** — yfinance will throttle aggressive polling. The producer paces
  requests and backs off on errors.
- **Market hours** — Best signal-to-noise is 09:30–16:00 ET. Pre/post-market activity
  is included but sparser.
- **Data is illustrative** — Use a paid feed (Polygon, Alpaca, IEX) for production.

---

## Stopping the stack

```bash
bash scripts/stop_all.sh        # docker compose down (volumes preserved)
# nuclear option:
docker compose down -v           # WARNING: deletes all stored ticks/bars/signals
```

Restart any time with `bash scripts/1_start_containers.sh`.
