# Postgres → Kafka → Delta — CDC Reference (single file)

> **The smallest end-to-end CDC pipeline that still does the right
> things.** One file. Postgres (via Debezium) → Kafka → Spark
> Structured Streaming → Delta Lake. Read it in five minutes; run it
> in fifteen.

This directory exists for the same reason a one-page cheat sheet
exists: when you need to remember "how does CDC actually wire up,"
the answer should fit on one screen. The file below is that screen.

It is **deliberately a single file** with no abstraction. When you
copy it into a real project, the first thing you'll do is split it
into a config layer, a schema module, and a sink module. That's
fine. The point of having it as one file is that you can see the
whole thing at once.

---

## What it does

```
Postgres logical replication
        │
        ▼
Debezium connector
        │
        ▼
Kafka topic: dbserver1.public.my_table
        │
        ▼  (this script)
Spark Structured Streaming
   - reads from Kafka
   - parses the JSON envelope
   - writes to Delta Lake (append)
        │
        ▼
/tmp/delta/tmp_retail
```

Same topology as [`../flink-cdc-dashboard/`](../flink-cdc-dashboard/),
but the streaming engine is Spark instead of Flink. The choice
between them is mostly a team-skill decision; both work.

---

## How to run it

```bash
# 1. Make sure Kafka is running with the Debezium connector for
#    the table you care about. The topic name should match the
#    one in the script: dbserver1.public.my_table

# 2. Make sure Postgres has logical replication enabled
#    (wal_level=logical, a publication, a replication slot)

# 3. Install the dependencies
pip install pyspark delta-spark==1.0.0

# 4. Run the script
python kafka_to_delta.py
```

The script will:

1. Create a Spark session with the Delta Lake extension enabled.
2. Subscribe to the Kafka topic `dbserver1.public.my_table`.
3. Parse each message as JSON using the Debezium envelope schema.
4. Write the parsed stream to Delta Lake at `/tmp/delta/tmp_retail`
   in append mode, with a checkpoint at `/tmp/delta/checkpoints`.

The stream runs until you `Ctrl-C` it.

---

## What the file shows, line by line

| Lines | What it does | Why it matters |
|-------|--------------|----------------|
| 1-3 | Imports | `pyspark.sql.functions` for the JSON parse, `pyspark.sql.types` for the schema |
| 5-9 | The Debezium envelope schema | `op` (c/u/d), `before`, `after` — the three things every CDC message has |
| 11-17 | Spark session with Delta | The `.config(...)` block is the minimum to enable Delta Lake on a Spark session |
| 19-24 | Kafka source | `subscribe` (not `assign`) for auto-discovery; `kafka.bootstrap.servers` is the only required option |
| 26-27 | Cast value to string | Kafka gives you bytes; you need to interpret them |
| 28 | Parse the JSON | The Debezium schema is the contract here |
| 30-34 | Delta sink | `outputMode("append")` because CDC is append-only; `checkpointLocation` is mandatory for any streaming sink |
| 36 | Block forever | The script never exits on its own; `Ctrl-C` to stop |

---

## What this script is NOT

- **Not production code.** No auth, no schema registry, no
  backpressure config, no error handling, no DLQ. It's a
  reference.
- **Not the latest Delta API.** Uses Delta 1.0.0, which is from
  2020. Modern Delta (3.x) is significantly different; this
  script is preserved as a historical reference of the
  minimum-viable CDC pattern.
- **Not a multi-table pipeline.** One Kafka topic, one Delta
  table. Multi-table CDC needs a routing layer; the pattern
  lives in [`../data-engineering/keystone-iceberg-ops/`](../data-engineering/keystone-iceberg-ops/).

---

## What to read next

After you understand this file:

1. **Flink SQL version:** [`../flink-cdc-dashboard/`](../flink-cdc-dashboard/)
   for the same topology but with SQL instead of code.
2. **Production reference:** [`../realtime-stock-pipeline/`](../realtime-stock-pipeline/)
   for the full Kafka + Flink + Postgres + Grafana build, with
   auth, monitoring, and persistence.
3. **Schema evolution:** [`../data-engineering/keystone-iceberg-ops/`](../data-engineering/keystone-iceberg-ops/)
   for the table-ops layer that comes after the pipeline: snapshot
   expiry, compaction, schema-evolution tests.
4. **dbt on top of the Delta table:** [`../data-engineering/financial-reporting-platform/`](../data-engineering/financial-reporting-platform/)
   for the dbt-pattern that turns the raw Delta table into a
   reporting layer.
