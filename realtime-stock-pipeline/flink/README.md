# Flink streaming layer

The SQL jobs that turn the raw Kafka tick stream into bars and signals, then land them in TimescaleDB. Four jobs, in order, all pure SQL — no Java/Scala, no JAR. The whole layer is four `.sql` files you can read in five minutes.

## Shape

```
   stock.ticks (Kafka)
        │
        ├─▶ 01_ticks_to_jdbc.sql  ──▶  ticks       (TimescaleDB, raw)
        │
        ├─▶ 02_bars_1m.sql        ──▶  bars_1m     (TimescaleDB, 1-min OHLCV)
        │
        ├─▶ 03_bars_5m.sql        ──▶  bars_5m     (TimescaleDB, 5-min OHLCV)
        │
        └─▶ 04_signals.sql        ──▶  signals     (TimescaleDB, rolling features
                                                  + classification, pure SQL)
```

## Layout

```
flink/
├── flink-conf.yaml        # Flink config (jobmanager / taskmanager slots)
├── jobs/
│   ├── 01_ticks_to_jdbc.sql   # raw ticks   ->  ticks      (JDBC -> TimescaleDB)
│   ├── 02_bars_1m.sql         # ticks       ->  bars_1m    (JDBC -> TimescaleDB)
│   ├── 03_bars_5m.sql         # ticks       ->  bars_5m    (JDBC -> TimescaleDB)
│   └── 04_signals.sql         # ticks       ->  signals    (JDBC -> TimescaleDB)
└── README.md
```

## Prerequisites

The Flink JobManager + TaskManager containers must mount:

* `./flink/jobs` → `/opt/flink/jobs` (read-only)

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
  by event-time — correct enough for single-partition Kafka topics at the
  tick rates we expect.
* `day_high` / `day_low` in 04 are approximated as MAX/MIN over a 6.5-hour
  HOP window (one US trading day). A proper session window would be more
  robust to late ticks.
* `current_price` is approximated as `MAX(price)` in the latest 1-min
  slide; for exact "last price" semantics a `LAST_VALUE` over an ordered
  window would be required (not supported cleanly in Flink 1.17 TUMBLE).

## Real numbers

- End-to-end latency (tick in Kafka → row in TimescaleDB): ~400–700 ms p50 at the toy tick rate.
- Job 04 (`signals`) is the most expensive: HOP windows over 6.5 h × N symbols. Add a `WHERE` partition filter if you scale beyond a few hundred symbols.
- All four jobs run forever; restart is "kill container, re-submit the four SQL files in order."
- TimescaleDB hypertable compression on `bars_1m` / `bars_5m` cuts disk ~10× after 7 days; enable with `ALTER TABLE ... SET (timescaledb.compress)` once the table is populated.

## What I learned the hard way

- **sql-client sessions are isolated.** Each `.sql` file must declare its own source + sink tables, even though they're identical across files. The first attempt to share a `CREATE TABLE` across files failed silently.
- **TUMBLE open/close via `ROW_NUMBER` is fine for single-partition topics.** It's wrong for multi-partition topics because the partition boundaries don't align with the bar boundaries. Real systems use `PROCTIME` ordering or a watermark-aware `LAST_VALUE`.
- **A 6.5-hour HOP is not a session window.** A session window would respect the lunch break (no ticks 12:00–13:00 ET). The HOP includes the gap. For an end-of-day report this doesn't matter; for a "max drawdown since open" it does.
- **Pure SQL Flink jobs are deployable in 4 minutes.** The win is not the SQL — it's that there's no JAR to build, no classpath to manage, no Maven. The whole layer is "copy 4 files into the container and run them."

## When to use

- The realtime-stock-pipeline is the *only* thing that uses this layer.
- You're streaming low-rate public market data (< 10K events/sec) and want a 4-file deployable.
- You want bar aggregation + signal features without standing up a Java build pipeline.

## When NOT to use

- High-rate (>100K events/sec) tick streams — pure SQL hits Flink's planner limits.
- You need exactly-once sink semantics across jobs — these jobs are at-least-once.
- You need event-time semantics with late-arrival handling beyond simple watermarks.

---

## What this is NOT

- **Not the producer side.** The Kafka producer is in
  [`../producer/`](../producer/) — this directory is *consume + transform + sink only*.
- **Not a Java/Scala Flink job.** The whole layer is four `.sql` files. There is no `pom.xml`, no `build.gradle`, no JAR. If you need a custom operator (a Python UDF, a stateful join), this is the wrong layer; write a JAR-based Flink job instead.
- **Not the storage layer.** TimescaleDB is the sink. Schema management, retention policies, and compression live in
  [`../db/`](../db/). The Flink layer writes rows; it doesn't own them.
- **Not the Grafana dashboard.** The dashboard reads from the same TimescaleDB tables this layer populates, but the two are decoupled. You can re-point Grafana at a different source without touching Flink, and you can change the bar / signal logic without redeploying the dashboard.

---

## Related directories

- [`../README.md`](../README.md) — the parent `realtime-stock-pipeline/` overview that lists every component in the stack.
- [`../producer/`](../producer/) — the Kafka producer that feeds `stock.ticks`, the input to every job here.
- [`../db/`](../db/) — the TimescaleDB schema, retention, and compression that this layer's jobs sink into.
- [`../grafana/`](../grafana/) — the dashboards that read the `bars_1m` / `bars_5m` / `signals` tables this layer populates.
- [`../trade-finder/`](../trade-finder/) — the downstream consumer that reads `signals` to surface trade opportunities.

---

**Last updated:** 2026-10-13  
**License:** MIT — use freely in your own courses, prototypes, and products.  
