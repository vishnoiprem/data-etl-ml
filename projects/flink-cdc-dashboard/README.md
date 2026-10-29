# Flink CDC Dashboard — Postgres → Kafka → Flink → Dashboard

> **A 6-step reference build for Change-Data-Capture with Flink SQL.**
> Postgres → Debezium → Kafka → Flink → Postgres (sink) → dashboard.
> The whole thing comes up in 5 minutes on a laptop.

This is the smallest, most readable end-to-end Flink CDC build I could
put together. Every step is a separate shell script. Each script is
~50 lines, every line is commented, and the result is a working CDC
pipeline with a live dashboard.

The point isn't to be production. The point is to give someone who's
heard of CDC a single afternoon's path from "I don't know how this
works" to "I have it running and I changed the SQL query."

---

## Architecture

```
                    ┌──────────────────────┐
                    │  Postgres (source)   │
                    │  public.orders       │
                    └──────────┬───────────┘
                               │  Debezium connector
                               ▼
                    ┌──────────────────────┐
                    │  Kafka (broker)      │
                    │  topic: cdc.orders   │
                    └──────────┬───────────┘
                               │  Flink SQL CDC source
                               ▼
                    ┌──────────────────────┐
                    │  Flink               │
                    │  - project           │
                    │  - filter            │
                    │  - aggregate         │
                    │  - window            │
                    └──────────┬───────────┘
                               │  JDBC sink
                               ▼
                    ┌──────────────────────┐
                    │  Postgres (sink)     │
                    │  public.orders_dw    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Streamlit dashboard │
                    │  p50 / p95 / GMV     │
                    └──────────────────────┘
```

---

## The 6 bring-up steps

```bash
cd flink-cdc-dashboard

# 1. Set up project (creates dirs + init.sql + the queries/ dir)
chmod +x 0_setup_project.sh && ./0_setup_project.sh

# 2. Start the containers (Zookeeper, Kafka, Postgres, Flink, dashboard)
chmod +x 1_start_containers.sh && ./1_start_containers.sh

# 3. Register the Debezium CDC connector in Kafka Connect
chmod +x 2_setup_cdc.sh && ./2_setup_cdc.sh

# 4. Submit the Flink SQL job (project → filter → window → sink)
chmod +x 3_run_flink_sql.sh && ./3_run_flink_sql.sh

# 5. Generate synthetic order events so the pipeline has data
chmod +x 4_run_data_generator.sh && ./4_run_data_generator.sh

# 6. Open the dashboard
chmod +x 5_run_dashboard.sh && ./5_run_dashboard.sh
```

The dashboard listens on `http://localhost:8501`. You should see
orders flowing through the pipeline within ~30 seconds of step 5.

---

## What you can play with

Once it's up, the parts worth poking at:

| File | What it does | Try changing |
|------|--------------|--------------|
| `queries/transform.sql` | The Flink SQL pipeline: source → project → window → sink | Switch the window from `TUMBLE(5s)` to `HOP(1m, 30s)` |
| `init.sql` | The source schema + seed data | Add a `category` column; CDC picks it up automatically |
| `data_generator.py` | Synthetic order emitter | Change the rate, the distribution, the schema |
| `dashboard.py` | Streamlit dashboard with p50/p95/GMV | Add a new chart; the SQL is a single SELECT |
| `event_time_process.py` | Watermarks + late-arrival handling | This is the file that matters once you have real data |

---

## What this build teaches

Five things, in order of importance:

1. **CDC is just "tail the WAL" in a typed wrapper.** Debezium reads
   Postgres' logical replication slot; the messages on the Kafka
   topic already have a schema. The Flink side is just SQL.
2. **Event time vs. processing time is the single most-important
   design choice.** The Flink job uses event time; the
   `event_time_process.py` file is where you set watermarks.
3. **At-least-once vs. exactly-once is a sink decision, not a
   pipeline decision.** The JDBC sink here is at-least-once. The
   pattern for exactly-once is a 2-phase commit sink + a
   transactional Kafka producer.
4. **Backpressure is the only health metric that matters.** Flink
   exposes it; the dashboard reads it. If backpressure goes red,
   the pipeline is sick even if everything else is green.
5. **Schema changes flow through CDC automatically.** Add a column
   to `orders`; Debezium picks it up; Flink sees the new field;
   you decide what to do with it in the SQL.

---

## What this build is NOT

- **Not a production CDC pipeline.** No auth, no TLS, no
  multi-broker Kafka, no Flink savepoints, no Kafka Connect
  restart policy. Production-grade streaming lives in
  [`../realtime-stock-pipeline/`](../realtime-stock-pipeline/) —
  Kafka + Flink + Postgres + Grafana, with the real configs.
- **Not multi-tenant.** One Postgres, one Kafka cluster, one
  Flink job. If you need isolation, look at
  [`../data-engineering/multi-tenant-isolation/`](../../learning/data-engineering/multi-tenant-isolation/).
- **Not a CDC-from-Oracle / MySQL demo.** Just Postgres. The
  Debezium pattern is the same for MySQL; for Oracle and SQL
  Server, the connector config changes but the topology doesn't.

---

## Prerequisites

- Docker + Docker Compose
- `curl` (used by `2_setup_cdc.sh` to register the connector)
- `python3` (the data generator and dashboard)
- A free port on `8501` (Streamlit), `8081` (Flink UI),
  `8083` (Kafka Connect), `9092` (Kafka), `5432` (Postgres)

If any of those ports are taken, edit the `docker-compose.yml`
and the affected `*.sh` script.

---

## Related directories

- [`../realtime-stock-pipeline/`](../realtime-stock-pipeline/) —
  The production-grade sibling: Kafka + Flink + Postgres +
  Grafana with the same topology, but with HA + monitoring
  + persistence.
- [`../data-engineering/keystone-iceberg-ops/`](../../learning/data-engineering/keystone-iceberg-ops/) —
  The Iceberg-table-ops angle on the same data. CDC into
  Iceberg instead of into a Postgres sink.
- [`../data-engineering/activity-volume-olap/`](../../learning/data-engineering/activity-volume-olap/) —
  The OLAP-on-top-of-CDC view: ClickHouse + Kafka + dbt.
