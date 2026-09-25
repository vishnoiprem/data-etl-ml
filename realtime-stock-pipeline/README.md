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
                |  (Python, asyncio)  |   topic: ticks.raw
                +----------+----------+
                           |
                           v
                +---------------------+
                |       Kafka         |   ticks.raw
                |  (Confluent / KRaft)|
                +----------+----------+
                           |
                           v
                +---------------------+
                |   Flink JobManager  |
                |  +  TaskManager     |   SQL jobs:
                |                     |     - tumble 1m -> bars_1m
                |                     |     - signal rules -> signals
                +----+-----------+----+
                     |           |
                     v           v
              +-----------------------+
              |       TimescaleDB     |   hypertables:
              |  ticks, bars_1m,      |     ticks, bars_1m, signals
              |  signals             |
              +----------+------------+
                         |
                         v
              +-----------------------+
              |        Grafana        |   dashboards:
              |   provisioning YAML   |     - US Stocks Live
              |                       |     - Buy Signals
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
  to the `ticks.raw` Kafka topic. Async + batching.
- **flink/jobs/** — SQL jobs that read `ticks.raw`, build 1-minute OHLCV bars
  (`bars_1m`), and emit `signals` rows (BUY / WATCH / HOLD) using intraday rules.
- **db/** — TimescaleDB schema: hypertables for `ticks`, `bars_1m`, `signals`, plus
  convenience views (`latest_prices`, etc.).
- **grafana/** — Auto-provisioned dashboards (this folder) plus datasource YAML.
- **scripts/** — The orchestration layer you're using now.

See `docs/signal-explanation.md` for the exact BUY/WATCH rules and confidence math.

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
