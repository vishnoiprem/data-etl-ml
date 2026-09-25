# Flink Streaming Layer

This directory contains the SQL jobs that power the real-time US stock
pipeline. Jobs are submitted to a sql-client session running inside the
Flink JobManager container; data flows through Kafka topics and lands in
TimescaleDB.

## Layout

```
flink/
├── jobs/
│   ├── 01_ticks_to_jdbc.sql   # raw ticks   ->  ticks      (JDBC -> TimescaleDB)
│   ├── 02_bars_1m.sql         # ticks       ->  bars_1m    (JDBC -> TimescaleDB)
│   ├── 03_bars_5m.sql         # ticks       ->  bars_5m    (JDBC -> TimescaleDB)
│   └── 04_signals.sql         # ticks       ->  signals    (JDBC -> TimescaleDB)
```

## Prerequisites

The Flink JobManager + TaskManager containers must mount:

* `./flink/jobs` -> `/opt/flink/jobs` (read-only)

The Kafka and TimescaleDB services must be reachable on the docker-compose
network at:

* `kafka:9092`
* `timescaledb:5432`

## Submitting a job

Each `.sql` file is self-contained (declares its own source/sink tables),
because sql-client sessions are isolated. Submit a job with:

```bash
docker exec -it <jobmanager> /opt/flink/bin/sql-client.sh \
    -f /opt/flink/jobs/01_ticks_to_jdbc.sql
```

Replace `<jobmanager>` with the actual container name (e.g.
`realtime-stock-pipeline-jobmanager-1`). Submit the bar / signal jobs the
same way, in this order so the `ticks` table is populated first:

1. `01_ticks_to_jdbc.sql`  (raw tick landing)
2. `02_bars_1m.sql`        (1-minute OHLCV)
3. `03_bars_5m.sql`        (5-minute OHLCV)
4. `04_signals.sql`        (rolling features + classification; pure SQL)

## Outputs

| Job          | Source (Kafka) | Sink (TimescaleDB) | Sink (Kafka)    |
|--------------|----------------|--------------------|-----------------|
| 01 ticks     | `stock.ticks`  | `ticks`            | --              |
| 02 bars 1m   | `stock.ticks`  | `bars_1m`          | --              |
| 03 bars 5m   | `stock.ticks`  | `bars_5m`          | --              |
| 04 signals   | `stock.ticks`  | `signals`          | --              |

## Notes / known approximations

* Open / close in 02/03 use `ROW_NUMBER` over the TUMBLE partition ordered
  by event-time -- correct enough for single-partition Kafka topics at the
  tick rates we expect.
* `day_high` / `day_low` in 04 are approximated as MAX/MIN over a 6.5-hour
  HOP window (one US trading day). A proper session window would be more
  robust to late ticks.
* `current_price` is approximated as `MAX(price)` in the latest 1-min
  slide; for exact "last price" semantics a `LAST_VALUE` over an ordered
  window would be required (not supported cleanly in Flink 1.17 TUMBLE).
