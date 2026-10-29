# DB — TimescaleDB schema and views

> **The Postgres + TimescaleDB storage layer of the
> realtime stock pipeline.** Two SQL files: `01_init_timescale.sql`
> creates the schema (raw ticks + 1m/5m/1h bars as hypertables);
> `02_views.sql` creates the convenience views the Grafana
> dashboards query.

This directory is the data plane. Everything the user sees in
Grafana is a query against a view in this directory.

---

## Files

| File | What it does |
|------|--------------|
| `01_init_timescale.sql` | Creates the TimescaleDB extension, the `ticks` hypertable, the `bars_1m/5m/1h` continuous aggregates, and the indexes. Runs on first start of the TimescaleDB container. |
| `02_views.sql` | Creates the convenience views: `latest_prices`, `latest_signals`, intraday movers, etc. The Grafana dashboards query these, not the hypertables directly. |

The split is deliberate: `01_init_timescale.sql` is the data
contract (schema, hypertables, retention policies); `02_views.sql`
is the read model (what the dashboards need). If you change the
schema, you change the contract. If you change the read model,
nothing else has to.

---

## The schema

```
ticks           — raw tick stream (hypertable, partitioned by ts)
                   retention: 7 days raw, then continuous aggregates
                   PK: (ticker, ts)

bars_1m         — 1-minute OHLCV bars (continuous aggregate)
                   retention: 90 days
                   source: ticks via time_bucket('1 minute', ts)

bars_5m         — 5-minute bars (continuous aggregate)
                   retention: 1 year

bars_1h         — 1-hour bars (continuous aggregate)
                   retention: 5 years

signals         — AI-generated trade signals (hypertable, partitioned by ts)
                   retention: 1 year
                   FK: ticker (no enforced FK; signals can lead ticks)

decisions       — strategy decisions (BUY/SELL/HOLD, with rationale)
                   retention: 1 year

trades          — paper-trading fills
                   retention: 1 year
```

`create_hypertable('ticks', 'ts', ...)` is the magic call. It
turns a regular Postgres table into a chunk-partitioned
hypertable, which is what gives TimescaleDB its time-series
performance. The continuous aggregates (`bars_1m`, `bars_5m`,
`bars_1h`) are materialized views that Timescale auto-refreshes
on a schedule; querying them is O(chunk-count), not O(row-count).

---

## The read model (views)

| View | What it returns | Used by |
|------|-----------------|---------|
| `latest_prices` | Most recent price per ticker, with day_open / day_high / day_low / volume / day_change_pct | Grafana: Live Prices panel |
| `latest_signals` | Most recent signal per ticker, with model name + confidence + rationale | Grafana: AI Signals panel |
| `intraday_movers` | Top N tickers by abs(change_pct) since market open | Grafana: Movers panel |
| `signal_accuracy` | Per-model, per-ticker hit rate over the last N signals | Grafana: Model accuracy panel |
| `kpi_summary` | One row with today's GMV-ish KPIs (signals generated, fills, hit rate) | Grafana: KPI strip |

All views are `CREATE OR REPLACE VIEW` so re-running `02_views.sql`
is safe and idempotent.

---

## How the Flink job writes here

The Flink JDBC sink writes to `ticks` with `ON CONFLICT
(ticker, ts) DO UPDATE`. The conflict target comes from a unique
index that's created as part of `01_init_timescale.sql`. This
pattern gives at-least-once delivery with exactly-once observable
state: a re-run from the Kafka offset produces the same rows,
just with the same values.

The continuous aggregates auto-refresh on a 1-minute lag. So a
tick at `T+0` shows up in `bars_1m` around `T+1m`. If you need
a fresh read for backtesting or signal eval, query `ticks`
directly.

---

## Retention and storage math

A single ticker at 5s cadence during US market hours (6.5h) =
~4,680 ticks/day. With 100 tickers = 468,000 ticks/day = ~25 MB
uncompressed / ~5 MB compressed Parquet-style. TimescaleDB's
internal compression gets it to ~2 MB. So 100 tickers, 7 days
of raw retention = ~14 MB on disk. The continuous aggregates
are O(tickers × bars), negligible.

If you bump to 1,000 tickers: ~140 MB. 10,000 tickers: ~1.4 GB.
The pipeline scales linearly until you run out of disk; then
you tune `retention` on the raw hypertable.

---

## What this is NOT

- **Not the trade-strategy state.** The strategy's working set
  is in memory in the trade-finder process and in `signals` /
  `decisions` / `trades`. The DB stores it; the strategy is
  in code.
- **Not OLAP.** For analytical queries (cross-ticker backtests,
  factor analysis), use the Parquet exports in
  `ai_signals/backtest_report.json` or extract to ClickHouse /
  DuckDB.
- **Not a market-data archival store.** 7 days of raw ticks
  is enough for the live system. For multi-year archives,
  use S3 + Parquet + Iceberg (the pattern in
  [`../../data-engineering/keystone-iceberg-ops/`](../../data-engineering/keystone-iceberg-ops/)).

---

## Related directories

- [`../`](../) — the parent `realtime-stock-pipeline/`. Start
  there for the full architecture.
- [`../flink/`](../flink/) — the Flink jobs that write to
  `ticks` and read from `bars_*`.
- [`../producer/`](../producer/) — the producer that publishes
  the ticks that this DB stores.
- [`../grafana/`](../grafana/) — the dashboards that query the
  views in this directory.
- [`../ai_signals/`](../ai_signals/) — the ML signal layer
  that writes to `signals` / `decisions` / `trades`.
