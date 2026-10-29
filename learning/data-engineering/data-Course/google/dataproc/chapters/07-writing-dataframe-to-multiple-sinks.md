# 2.4 — Writing DataFrames to Multiple Sinks

> **Section 2 · Spark Fundamentals · Lecture 2.4 · 24:47**

## 🎯 What you will learn

- `DataFrameWriter` and the `df.write` object — the mirror image of `spark.read`
- Write modes (`overwrite`, `append`, `ignore`, `error`) and how each behaves per sink
- Writing to Cloud Storage: Parquet, CSV, JSON, Avro, ORC — with `partitionBy` and repartitioning
- Writing to BigQuery: `writeDisposition`, `createDisposition`, and **why `temporaryGcsBucket` is required**
- The BigQuery Storage Write API: `writeMethod="direct"` vs `"indirect"`
- Writing to Hive metastore tables with `saveAsTable` and `insertInto`
- Writing to JDBC, Pub/Sub, and Kafka — all via `foreachPartition` with native clients
- The fan-out pattern, the cost of recomputation, and when to `cache()`
- Idempotency, `partitionOverwriteMode`, and at-least-once vs exactly-once

---

## 🧠 Concept

Writing is the mirror of reading, and it is where pipelines become dangerous. Reading a
corrupt file gives you a wrong answer. Writing incorrectly gives you **wrong data in a
system of record** — and usually nobody notices for weeks.

```
   READ                                 WRITE
   ────                                 ─────
   df = spark.read...                   df.write...
       │                                     │
   "I got data from somewhere"          "I put data somewhere"

   Risk: bad input                   Risk: bad output + no undo
   Detection: row counts             Detection: ??? (usually none)
```

The core principle of this chapter: **a sink is a contract, not a function call.** Every
write asks the same six questions:

1. What happens if I write the same data twice?
2. What happens if I write half the data and then crash?
3. What happens if the schema drifts?
4. What happens if the sink is briefly unavailable?
5. Is the operation atomic?
6. Can I re-run the whole job safely?

---

### The writer API

```python
df.write                       # DataFrameWriter
df.write.mode("overwrite")     # returns a new DataFrameWriter (immutable)
df.write.option("compression", "snappy")
df.write.partitionBy("dt")
df.write.save("gs://bucket/path")
```

The full call shape:

```python
(
    df.write
    .mode("overwrite")                          # write mode
    .option("compression", "snappy")            # format-specific options
    .partitionBy("dt")                          # partition columns
    .format("parquet")                          # format
    .save("gs://bucket/path")                   # destination
)
```

`DataFrameWriter` is **immutable** — every method returns a new writer. `df.write.mode("append")`
does not mutate `df.write`; it returns a copy. This is a common source of confusion:

```python
df.write.mode("overwrite")          # ← discarded, does nothing
df.write.mode("overwrite").save(p)  # ← this is what actually writes
```

| Method | Purpose |
|--------|---------|
| `.format(fmt)` | Set the output format (`parquet`, `csv`, `json`, `avro`, `orc`, `bigquery`, `jdbc`, …) |
| `.mode(m)` | Write mode |
| `.option(k, v)` | Format-specific option |
| `.partitionBy(*cols)` | Hive-style partitioning |
| `.bucketBy(n, *cols)` | Bucketing (only for Hive tables) |
| `.sortBy(*cols)` | Sort within each partition |
| `.save(path)` | Write to a path |
| `.saveAsTable(name)` | Write to a Hive metastore table |
| `.insertInto(name, overwrite=False)` | Append/overwrite into an existing table |
| `.foreachPartition(f)` | Write with a custom function (JDBC, Pub/Sub, Kafka) |

💡 **Shortcuts exist for some formats** — `df.write.parquet(path)`, `df.write.csv(path)`,
`df.write.json(path)`, `df.write.orc(path)`. As with reads, the canonical
`.format(...).option(...).save(path)` form is better in shared code because it parameterises
cleanly.

---

### Write modes, and how they differ per sink

| Mode | Semantics | If the destination already exists |
|------|-----------|------------------------------------|
| `overwrite` | Replace everything | Deletes the existing data first |
| `append` | Add to what is there | Adds alongside |
| `ignore` | Write only if absent | **Silently does nothing** |
| `error` (default) | Write only if absent | **Throws `AnalysisException`** |
| `errorifexists` | Alias for `error` | Same |

```python
df.write.mode("overwrite").parquet(path)
df.write.mode("append").parquet(path)
df.write.mode("ignore").parquet(path)
df.write.mode("error").parquet(path)
```

⚠️ **The default mode is `error`, not `overwrite`.** A first-time pipeline developer writes
`df.write.parquet(path)` expecting a fresh file, and the second run fails with
`AnalysisException: path file:/... already exists`. Good default — it stops the "I thought I
overwrote it" class of bug.

⚠️ **`ignore` is the most dangerous mode.** It is the standard "create if not exists"
bootstrap pattern, but it means **a re-run silently writes nothing**. If your job is
"overwrite the day's partition", `ignore` means the second run is a no-op and your data is
stale, with no error and no log line. Use it only for genuinely idempotent one-time setup.

### How the modes behave on each sink

This is where the API abstraction leaks. The same mode name means different things.

| Sink | `overwrite` | `append` | `ignore` | `error` |
|------|-------------|----------|----------|---------|
| **GCS / HDFS (Parquet, CSV, JSON, ORC, Avro)** | Deletes the directory contents, then writes | Adds new files | Skips if the path exists | Throws if the path exists |
| **BigQuery** | Maps to `WRITE_TRUNCATE` | Maps to `WRITE_APPEND` | Skips if the table exists | Throws if the table exists |
| **Hive metastore table** (`saveAsTable`) | `DROP` + recreate (table metadata too) | Fails — `saveAsTable` overwrites | — | — |
| **JDBC** | Truncates the table, then inserts | Inserts | — | Inserts (JDBC has no native "exists" check) |
| **`foreachPartition` sinks** | **You implement it.** Nothing is automatic. | | | |

⚠️ **JDBC ignores `overwrite` in the way you'd hope.** Spark's JDBC writer implements
`overwrite` by running `TRUNCATE TABLE` on the target table before inserting. On a
transactional database with concurrent readers, that is a visible gap. And on a partitioned
JDBC target, it truncates the **whole** table, not just the partitions you wrote.

💡 **`mode` on a `foreachPartition` sink is meaningless.** When you write with
`foreachPartition`, Spark hands you an iterator and you decide what to do with it. If your
function inserts rows into Postgres, "append" and "overwrite" are things **you** implement —
usually by deleting the target partition range yourself inside the partition function.

---

### Writing to Cloud Storage

```python
# ---------- Parquet (the default answer) ----------
df.write.mode("overwrite").parquet("gs://my-bucket/warehouse/orders")

# ---------- CSV ----------
(
    df.write
    .option("header", True)
    .option("delimiter", ",")
    .option("nullValue", "")
    .option("dateFormat", "yyyy-MM-dd")
    .option("timestampFormat", "yyyy-MM-dd'T'HH:mm:ss")
    .mode("overwrite")
    .csv("gs://my-bucket/exports/orders")
)

# ---------- JSON ----------
df.write.mode("overwrite").json("gs://my-bucket/events/orders")

# ---------- ORC ----------
df.write.mode("overwrite").orc("gs://my-bucket/warehouse/orders_orc")

# ---------- Avro (requires spark-avro) ----------
df.write.mode("overwrite").avro("gs://my-bucket/warehouse/orders_avro")
```

**CSV and JSON output are directory writes, not file writes.** Spark writes many part files
in parallel:

```text
gs://my-bucket/exports/orders/
├── part-00000-<uuid>-c000.csv
├── part-00001-<uuid>-c000.csv
├── _SUCCESS
```

⚠️ **You cannot write a single CSV file with Spark.** For a single file, coalesce to one
partition *and* disable the directory semantics — which is rarely worth it. If you truly need
one file, write to a temp directory and concatenate on the client, or use Spark's
`coalesce(1)` and accept the `part-` filename.

⚠️ **The `_SUCCESS` marker file.** Spark writes `_SUCCESS` (and possibly `_committed_`,
`_started_`) into the output directory. A downstream reader that does a plain directory read
will try to parse `_SUCCESS` as data. This is why the extract chapter recommends
`recursiveFileLookup=true` (which skips underscore-prefixed files) or writing to a temp path
and renaming.

### Partitioning

```python
df.write.mode("overwrite").partitionBy("order_date").parquet("gs://my-bucket/warehouse/orders")
```

```text
gs://my-bucket/warehouse/orders/
├── order_date=2026-10-26/
│   └── part-00000-....parquet
├── order_date=2026-10-27/
│   └── part-00000-....parquet
└── order_date=2026-10-28/
    └── part-00000-....parquet
```

Partition columns are **removed from the data files** and encoded in the directory path.
On read, Spark reconstructs them.

| Consideration | Guidance |
|---------------|----------|
| **Cardinality** | Aim for **< 1,000 values** per partition column. High cardinality → tiny files. |
| **Number of columns** | More partition columns = deeper directory trees = more LIST operations on GCS. |
| **Ordering** | `partitionBy("year", "month", "day")` nests. Put the **coarsest** first. |
| **Type** | Partition values are cast to strings. Dates become `2026-10-28`. |
| **Filters** | Partition pruning only happens for **equality** and **IN** predicates. `BETWEEN` does prune in recent Spark, but a range on a non-partition column never will. |
| **Dynamic overwrite** | See `partitionOverwriteMode` below. |

💡 **Partition by a date column and overwrite per partition.** This is the single most
important pattern for idempotent pipelines — you get atomic per-day rewrites, cheap
backfills, and no need to rewrite the whole table.

⚠️ **`partitionBy` with `mode("overwrite")` and the default `STATIC` overwrite mode wipes
the *entire* table, not just the partitions you are writing.** If you write only
`order_date=2026-10-28` but the table has 365 days, `STATIC` deletes all 365 days and
leaves you with one. This is the classic "why did my history disappear" incident. Set
`spark.sql.sources.partitionOverwriteMode=DYNAMIC` for per-partition overwrites.

### `coalesce` vs `repartition`

```python
# coalesce: reduce the number of partitions WITHOUT a shuffle.
# Only works when reducing, never when increasing.
df.coalesce(1).write.mode("overwrite").parquet(path)

# repartition: change the number of partitions WITH a shuffle.
# Works for both increasing and reducing.
df.repartition(10).write.mode("overwrite").parquet(path)

# Repartition by column: groups data by key, co-locating all rows for a key.
df.repartition(10, "customer_id").write.mode("overwrite").parquet(path)

# Repartition by range: evenly sized output partitions.
df.repartitionByRange(10, "order_date").write.mode("overwrite").parquet(path)
```

| Method | Shuffle? | Direction | Use for |
|--------|----------|-----------|---------|
| `coalesce(n)` | ❌ No | Decrease only | Merging small files into fewer, larger files |
| `repartition(n)` | ✅ Yes (hash) | Any | Controlling output file count and distribution |
| `repartition(n, col)` | ✅ Yes (hash by col) | Any | Co-locating all rows of a key in one partition |
| `repartitionByRange(n, col)` | ✅ Yes (range) | Any | Evenly sized partitions over a sorted key |

💡 **Small files are the silent killer of GCS + Spark performance.** Each small file is a
separate task, a separate LIST entry, and a separate GCS GET. A table of 10 million
10 KB files is unreadable in practice. Aim for **128 MB – 1 GB per part file**.

```python
# The standard "fix small files" pattern
from pyspark.sql import functions as F

target_size = 256 * 1024 * 1024   # 256 MB

df.coalesce(1).write.mode("overwrite").parquet(path)   # quick single file — fine for small data
```

For larger data, compute the right partition count from the measured average row size:

```python
# Estimate bytes per row from a sample, then choose a target partition count
sample_bytes = df.sample(fraction=0.01, seed=42).rdd.map(lambda r: len(str(r))).sum()
avg_row_bytes = max(sample_bytes / max(df.count() * 0.01, 1), 1)
total_bytes = avg_row_bytes * df.count()
target_partitions = max(1, int(total_bytes / target_size))
```

⚠️ **`coalesce(1)` on a large dataset funnels everything through one task.** It is a
bottleneck and a single point of failure. Use it for small outputs only (a few hundred MB),
and use `repartition` for anything larger.

### Compression

```python
df.write.mode("overwrite") \
  .option("compression", "snappy") \
  .parquet("gs://my-bucket/warehouse/orders")
```

| Codec | Compression | Speed | Use for |
|-------|-------------|-------|---------|
| `snappy` | Moderate | **Very fast** | Default for Parquet. The right default 99% of the time. |
| `gzip` | Moderate | Slow | Max compatibility |
| `zstd` | High | Fast | Best compression/speed ratio; great for Parquet |
| `lz4` | Low | Very fast | Fastest, but larger files |
| `none` | None | Fastest | Only for data you compress later |

💡 **`snappy` for Parquet, `zstd` if you want smaller files and have the CPU budget.**
Parquet already compresses column-wise with dictionary + RLE encodings; Snappy on top of
that gives excellent ratios with negligible CPU. Zstd often beats Gzip by 30–40% at similar
speed.

💡 **Compression is a column-store decision, not a file-format decision.** Because Parquet
is columnar, you can compress only the wide, cold columns and leave narrow hot columns
uncompressed — `ParquetOutputFormat` and the `compression` option apply per-column in
Spark 3.x via `spark.sql.parquet.compression.codec` (per-file) and the
`parquet.compression` column metadata for finer control.

---

### Writing to BigQuery

```python
df.write \
    .format("bigquery") \
    .option("writeDisposition", "WRITE_APPEND") \
    .option("createDisposition", "CREATE_IF_NEEDED") \
    .option("temporaryGcsBucket", "gs://my-bucket-bigquery-tmp") \
    .mode("append") \
    .save("my_project.sales.orders")
```

| Option | Values | Meaning |
|--------|--------|---------|
| `writeDisposition` | `WRITE_APPEND`, `WRITE_TRUNCATE`, `WRITE_EMPTY` | What to do with existing rows |
| `createDisposition` | `CREATE_IF_NEEDED`, `CREATE_NEVER` | Whether to create the table if missing |
| `temporaryGcsBucket` | `gs://...` | Staging bucket for the load job |
| `writeMethod` | `indirect`, `direct` | Which write API to use |
| `insertId` | a string | Idempotency token for the row batch |
| `allowFieldAddition` | `true`/`false` | Add new columns to the table automatically |
| `allowFieldRelaxation` | `true`/`false` | Widen existing column types |

| `writeDisposition` | Behaviour |
|-------------------|-----------|
| `WRITE_APPEND` | Add rows to the existing table |
| `WRITE_TRUNCATE` | **Replace all existing rows** — equivalent to `mode("overwrite")` |
| `WRITE_EMPTY` | Fail if the table already contains rows |

⚠️ **`WRITE_TRUNCATE` is destructive.** It deletes every row in the table and then writes
yours. If your job runs daily and appends, and someone flips the disposition to
`WRITE_TRUNCATE` for a "fresh rebuild", you have just deleted production history.

💡 **`mode("overwrite")` on BigQuery maps to `WRITE_TRUNCATE`; `mode("append")` maps to
`WRITE_APPEND`.** Setting the disposition explicitly is clearer and avoids ambiguity when
both are present.

---

#### Why `temporaryGcsBucket` is required

This is the question that trips up everyone the first time.

```
   THE LEGACY (INDIRECT) WRITE PATH
   ════════════════════════════════

   Spark DataFrame
        │
        ▼
   Serialize to Avro/Parquet
        │
        ▼
   Upload to a TEMPORARY location in GCS
        │
        ▼
   BigQuery LOAD JOB  ──► reads those objects ──► writes to your table
        │
        ▼
   Temporary objects are deleted

   WHY?
   BigQuery's bulk-load job is a server-side operation. It needs to read
   the data from somewhere GCS-native, and it needs a single, well-defined
   set of objects. Spark's executors are not directly addressable by the
   BigQuery load job. So Spark stages the bytes in GCS and hands BigQuery
   a list of URIs.
```

⚠️ **If you omit `temporaryGcsBucket`, the write fails** (or, depending on the connector
version and configuration, falls back to a default project that may not exist or may not be
writable). The connector needs *some* writable GCS location to stage the load. The
recommended practice is to point it at a **dedicated temporary bucket** in your project,
not at your data lake — because staged files are transient garbage that should never be
mixed with your curated data.

```python
.option("temporaryGcsBucket", "gs://my-project-bq-staging")
```

💡 **Give the staging bucket its own lifecycle rule.** A 90-day expiration on everything in
`gs://my-project-bq-staging` cleans up the residue from crashed jobs, which the connector
normally deletes for you but cannot when the job dies mid-write.

---

#### The Storage Write API: `writeMethod="direct"` vs `"indirect"`

The modern connector can bypass the GCS staging round-trip entirely.

```
   INDIRECT (the legacy/bulk-load path)
   ═════════════════════════════════════
   Spark ──serialize──► GCS (staging) ──► BigQuery LOAD JOB ──► Table
                          │
                          └── bytes make a round trip through GCS

   DIRECT (Storage Write API)
   ═════════════════════════════
   Spark ──row deltas──► BigQuery Storage Write API ──► Table
                          (streamed; no intermediate bucket)

   Benefits of direct:
     • No GCS staging bucket needed (temporaryGcsBucket becomes optional)
     • No temporary objects to clean up
     • Much faster — often 5–10x for large writes
     • Lower cost — you skip GCS write + read + delete round trips
     • Supports streaming writes
```

```python
# Direct write — no temporaryGcsBucket required
(
    df.write
    .format("bigquery")
    .option("writeMethod", "direct")
    .option("writeDisposition", "WRITE_APPEND")
    .option("createDisposition", "CREATE_IF_NEEDED")
    .save("my_project.sales.orders")
)
```

| `writeMethod` | Mechanism | Staging bucket | Relative speed | Notes |
|---------------|-----------|----------------|----------------|-------|
| `indirect` | BigQuery bulk-load job via GCS | **Required** | Baseline | Default in older connectors; robust; good for very large batch loads |
| `direct` | BigQuery Storage Write API | Not required | **Much faster** | Default in newer connectors; supports streaming |

⚠️ **`writeMethod` availability depends on the connector version.** The Storage Write API
support landed in connector versions around 0.42/1.x, and the option name and defaults have
shifted across releases. **Check the current version before relying on `direct`** — query the
bundled version from the image metadata (`SPARK_BQ_CONNECTOR_VERSION`) and confirm the
default `writeMethod` in that release's documentation.

💡 **Rule of thumb: use `direct` for anything interactive or latency-sensitive, and use
`indirect` for very large overnight bulk loads** where the bulk-load path's throughput
characteristics and lower per-row overhead are proven. In practice, `direct` now wins in the
majority of cases.

---

### Writing to Hive metastore tables

Dataproc can use a GCS-backed Hive metastore, so `saveAsTable` works without running a
separate metastore service.

```python
# Create a table and write into it (replaces the table if it exists)
df.write.mode("overwrite").saveAsTable("sales.orders")

# Append into an existing table
df.write.mode("append").insertInto("sales.orders")

# Overwrite only the matching partitions
df.write.mode("overwrite").insertInto("sales.orders")

# Create the table explicitly, then insert
spark.sql("""
  CREATE TABLE IF NOT EXISTS sales.orders (
    order_id STRING,
    customer_id STRING,
    amount DOUBLE,
    created_at TIMESTAMP
  ) USING parquet
  PARTITIONED BY (order_date DATE)
  STORED AS PARQUET
  LOCATION 'gs://my-bucket/warehouse/orders'
""")
df.write.mode("append").insertInto("sales.orders")
```

| Method | Table exists? | Table missing? | Behaviour |
|--------|---------------|----------------|-----------|
| `saveAsTable` | ❌ Error (unless `mode="overwrite"`) | ✅ Creates | Replaces the **table metadata** too |
| `insertInto` | ✅ Writes | ❌ Error | Writes into the existing table's schema |

⚠️ **`saveAsTable` and `insertInto` use **different** schema-resolution rules.**
`saveAsTable` uses the DataFrame's schema (creating or replacing the table definition).
`insertInto` uses the **existing table's** schema and **matches by position**, not by name.
If your DataFrame's column order differs from the table's column order, `insertInto` will
happily write your values into the wrong columns.

💡 **Prefer `insertInto` when the table already exists** (it preserves external table
configuration and location), and be very careful about column ordering. When in doubt,
explicitly reorder with `.select("col_a", "col_b", ...)` to match the table definition.

⚠️ **Writing to a Hive table that is also an external table over a GCS path creates two
sources of truth.** The metastore says the table lives at `gs://.../warehouse/orders`, and
the path also exists on disk. If a job writes to the path directly while another writes via
the table, they can disagree. Pick one write path per table.

---

### Writing to JDBC — `foreachPartition` and batching

**Spark's native JDBC writer is single-partition.** This is the single most important fact
about JDBC writes:

```python
# ⚠️ THIS IS SINGLE-PARTITION AND SLOW
df.write \
    .format("jdbc") \
    .option("url", "jdbc:postgresql://host:5432/mydb") \
    .option("dbtable", "public.orders") \
    .option("user", "readonly") \
    .option("password", "secret") \
    .mode("append") \
    .save()
```

All the data goes through **one partition, one JDBC connection, one INSERT at a time**.
Writing a million rows this way is painfully slow and will time out.

The standard production idiom is `foreachPartition` with a **batched** insert:

```python
from pyspark.sql import functions as F
import psycopg2

def write_partition(rows, jdbc_url, user, password, table, batch_size=1000):
    """
    Insert one Spark partition into Postgres using executemany batching.
    Called once per partition, on the executor.
    """
    conn = psycopg2.connect(
        host=jdbc_url["host"],
        port=jdbc_url["port"],
        dbname=jdbc_url["dbname"],
        user=user,
        password=password,
    )
    try:
        with conn:
            with conn.cursor() as cur:
                batch = []
                for row in rows:
                    batch.append((
                        row["order_id"],
                        row["customer_id"],
                        float(row["amount"]),
                        row["created_at"],
                    ))
                    if len(batch) >= batch_size:
                        cur.executemany(
                            "INSERT INTO public.orders "
                            "(order_id, customer_id, amount, created_at) "
                            "VALUES (%s, %s, %s, %s)",
                            batch,
                        )
                        batch.clear()
                if batch:
                    cur.executemany(
                        "INSERT INTO public.orders "
                        "(order_id, customer_id, amount, created_at) "
                        "VALUES (%s, %s, %s, %s)",
                        batch,
                    )
    finally:
        conn.close()


def write_to_postgres(df, jdbc_config, table, batch_size=1000):
    """Fan out over partitions; each partition opens its own DB connection."""
    def writer(iterator):
        write_partition(
            iterator, jdbc_config["url"], jdbc_config["user"],
            jdbc_config["password"], table, batch_size
        )

    df.foreachPartition(writer)
```

```
   Spark partition 0 ──► connection #1 ──► executemany(batch of 1000) ──┐
   Spark partition 1 ──► connection #2 ──► executemany(batch of 1000) ──┼──► Postgres
   Spark partition 2 ──► connection #3 ──► executemany(batch of 1000) ──┘
        ...
   Spark partition N ──► connection #N+1
```

💡 **`executemany` with a batch of 1000 is the sweet spot.** One INSERT per row is death
by a thousand round trips. `executemany` collapses a thousand rows into a single
parameterised multi-row INSERT (or a batched protocol message). Batches of 500–5000 are
typical; tune by measuring.

⚠️ **Each partition opens its own connection.** With `numPartitions=200` you will open 200
database connections. Check your Postgres `max_connections` and your Dataproc worker count
before scaling this up. Repartition to match your connection budget:

```python
df.repartition(20).foreachPartition(writer)   # 20 connections, not 200
```

⚠️ **`foreachPartition` gives you NO automatic transactional semantics across partitions.**
If partition 7 of 20 fails, partitions 0–6 are already committed and you have a partial
write. Re-running the job without first cleaning up will duplicate those rows.

💡 **Make the JDBC write idempotent.** The cleanest pattern is a staging table plus a
merge, or a delete-then-insert scoped to the partition you are writing:

```python
def writer(iterator):
    conn = psycopg2.connect(...)
    try:
        with conn:
            with conn.cursor() as cur:
                # Scope the delete to the same range this partition owns
                cur.execute("DELETE FROM public.orders WHERE batch_date = %s", (batch_date,))
                cur.executemany("INSERT INTO public.orders ...", batch)
    finally:
        conn.close()
```

⚠️ **The `foreachPartition` function must be picklable.** It is serialized and shipped to
the executors. It cannot close over a live DB connection, a SparkSession, or an open file
handle. Define it at module level and pass only serializable configuration (strings,
dicts, numbers).

⚠️ **Credentials in `foreachPartition` closures are serialized to every executor** and may
appear in the Spark UI and in the serialized task description. Use Secret Manager, IAM
authentication, or environment variables from the executor environment rather than literals.

---

### Writing to Pub/Sub

Spark has **no native `df.write.format("pubsub")`**. Pub/Sub writes go through
`foreachPartition` and the official Google Cloud Pub/Sub client library.

```python
import json
from google.cloud import pubsub_v1

PROJECT_ID = "my_project"
TOPIC_ID = "orders-out"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)


def publish_partition(rows, topic_path, publisher, batch_size=100):
    """Publish one Spark partition to Pub/Sub, batching up to 100 messages per request."""
    from google.cloud.pubsub_v1.types import types as pubsub_types

    batch = []
    futures = []
    for row in rows:
        payload = json.dumps({
            "order_id": row["order_id"],
            "customer_id": row["customer_id"],
            "amount": float(row["amount"]),
            "created_at": row["created_at"],
        }).encode("utf-8")

        future = publisher.publish(
            topic_path,
            payload,
            order_id=row["order_id"],          # attributes for downstream filtering
            source="dataproc-etl",
        )
        futures.append(future)
        batch.append(future)

        if len(batch) >= batch_size:
            # Wait for the batch to be confirmed before moving on
            for f in batch:
                f.result(timeout=60)
            batch.clear()

    if batch:
        for f in batch:
            f.result(timeout=60)


def write_to_pubsub(df):
    def writer(iterator):
        publish_partition(iterator, topic_path, publisher)

    df.foreachPartition(writer)
```

⚠️ **Pub/Sub has a 100 MB message size limit and a 10 MB attribute limit.** A single row
that serializes to more than 100 MB will fail the publish. For large records, write to GCS
and publish the GCS URI instead — a very common and correct pattern.

💡 **Publish the URI, not the payload, for anything large.** The consumer then reads from
GCS. This is the standard "reference architecture" for moving big records through Pub/Sub,
and it keeps your message size well under the limit.

⚠️ **Pub/Sub delivery is at-least-once.** Your consumer must be idempotent. If you write to
Pub/Sub from an idempotent Spark pipeline, you may still get duplicates downstream.

---

### Writing to Kafka

Same pattern — `foreachPartition` plus the `kafka-python` (or `confluent-kafka`) producer.

```python
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers="broker1:9092,broker2:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8") if k else None,
    acks="all",              # wait for all in-sync replicas
    retries=5,
    linger_ms=20,            # batch a little for throughput
    batch_size=65536,
    compression_type="snappy",
)


def publish_partition(rows, producer, topic, batch_size=1000):
    """Publish one Spark partition to Kafka."""
    for row in rows:
        record = {
            "order_id": row["order_id"],
            "customer_id": row["customer_id"],
            "amount": float(row["amount"]),
            "created_at": row["created_at"],
        }
        producer.send(
            topic,
            key=row["customer_id"],     # key controls partition assignment
            value=record,
        )
    # Flush this partition's buffered messages and surface any errors
    producer.flush(timeout=60)


def write_to_kafka(df, topic="orders-out"):
    def writer(iterator):
        publish_partition(iterator, producer, topic)

    df.foreachPartition(writer)
```

| Kafka producer option | Why it matters |
|----------------------|----------------|
| `acks="all"` | Wait for all in-sync replicas. `acks=0` can silently lose data. |
| `retries` | Retry on transient failures. |
| `linger_ms` | Delay send slightly to batch messages. Higher = better throughput, more latency. |
| `batch_size` | Bytes per batch. |
| `compression_type` | `snappy`, `gzip`, or `lz4` — reduces network cost. |
| `max_in_flight_requests_per_connection` | >1 with retries can reorder messages. Set to `1` if ordering matters. |
| `enable_idempotence` | Kafka ≥ 0.11 producer-level exactly-once. Set `acks=all` and it is implied. |

💡 **The key controls partitioning.** Sending with `key=customer_id` guarantees all events
for one customer land on one Kafka partition, which preserves per-key ordering. Sending with
`key=None` round-robins and destroys ordering.

⚠️ **Kafka and Pub/Sub are not natively supported as `df.write` sinks.** If you find a
tutorial claiming `df.write.format("kafka")`, it is either describing a third-party
connector or it is wrong. The `foreachPartition` + native client pattern is the standard
production approach.

⚠️ **Neither Pub/Sub nor Kafka provides exactly-once delivery with Spark.** Both are
at-least-once. Design the consumer to be idempotent.

---

### Writing to local disk

```python
df.write.mode("overwrite").parquet("/tmp/output/orders")
```

⚠️ **A local path is local to *each executor*.** If you write to `/tmp/output` from a
100-executor cluster, you get 100 separate `/tmp/output` directories on 100 different
machines, and the driver cannot see any of them. Local paths are only useful for:
- Small outputs that you then collect to the driver
- Scratch/intermediate data used within the same job
- `local[*]` development on a laptop

For anything that must survive the job, write to `gs://`.

---

### The fan-out pattern

Writing one DataFrame to multiple sinks is the "publish many views of the same data"
requirement, and it has a hidden cost.

```python
# ── BROKEN: three full recomputations ──
df.write.mode("overwrite").parquet("gs://bucket/warehouse/full")     # recompute #1
df.write.mode("overwrite").parquet("gs://bucket/warehouse/summary")  # recompute #2
df.write.mode("overwrite").parquet("gs://bucket/audit/full")         # recompute #3
```

```
   ┌─────────────────────────────────────────────────────────────────┐
   │  WITHOUT CACHE — the source is read THREE times                │
   │                                                                 │
   │   GCS source ──scan──► transform ──► write A                   │
   │           ──scan──► transform ──► write B                       │
   │           ──scan──► transform ──► write C                       │
   │                                                                 │
   │   Cost: 3× the I/O, 3× the CPU, 3× the shuffle                 │
   └─────────────────────────────────────────────────────────────────┘
```

```python
# ── CORRECT: cache once, write many ──
from pyspark.sql import StorageLevel

df = df.cache(StorageLevel.MEMORY_AND_DISK)
df.count()                      # ← materialise the cache NOW (an action)

df.write.mode("overwrite").parquet("gs://bucket/warehouse/full")
df.write.mode("overwrite").parquet("gs://bucket/warehouse/summary")
df.write.mode("overwrite").parquet("gs://bucket/audit/full")

df.unpersist()                  # ← free the cache when you are done
```

```
   ┌─────────────────────────────────────────────────────────────────┐
   │  WITH CACHE — the source is read ONCE                          │
   │                                                                 │
   │   GCS source ──scan──► transform ──► CACHE ──┬──► write A       │
   │                              │                ├──► write B      │
   │                              │                └──► write C      │
   │                         (one scan)                              │
   └─────────────────────────────────────────────────────────────────┘
```

💡 **`cache()` is lazy — you must trigger it with an action.** `df.cache()` alone does
nothing. `df.count()` (or `df.write...` as the first action) materialises it. And
`unpersist()` when you are done, or you hold the data in memory for the rest of the job.

⚠️ **`cache()` is a memory gamble.** If the cached DataFrame does not fit in memory, Spark
spills to disk (with `MEMORY_AND_DISK`) and you may end up slower than recomputing. Measure
before you cache a 2 TB DataFrame.

💡 **A better pattern than caching for heavy fan-out: write once, read many.** Persist the
transformed DataFrame to Parquet in GCS, then run each sink as a separate job that reads
that Parquet. This makes the sinks independently restartable, independently scalable, and
independently observable — and it costs one extra read/write cycle.

⚠️ **`cache()` and `foreachPartition` sinks interact badly.** The `foreachPartition` function
receives rows as Python objects, which means the DataFrame must be deserialized into the
Python worker. Caching helps if the data fits; but if the sink is a database, you are
usually better off writing to Parquet and loading the database with an external tool.

---

### Idempotency and the write-exactly-once problem

| Guarantee | Meaning | How to get it |
|-----------|---------|---------------|
| **At-most-once** | The data is written once, possibly not at all | Truncate-then-write with no retries. Data loss on failure. |
| **At-least-once** | The data is written one or more times | Retry on failure; duplicates possible. **The practical default.** |
| **Exactly-once** | The data is written exactly once | Requires an atomic transaction between the source, the processing, and the sink. |

```
   THE CLASSIC DOUBLE-WRITE PROBLEM
   ═════════════════════════════════

   t0: Read source
   t1: Write to sink          ← SUCCEEDS
   t2: Commit the job metadata ← FAILS (network blip)

   Spark retries the job.
   t3: Read source
   t4: Write to sink          ← SUCCEEDS AGAIN
                              ← DUPLICATE DATA

   The job "failed" but the sink has two copies.
```

**Idempotent writes** are the practical answer. Make the write produce the same result
whether it happens once or many times.

| Technique | How |
|-----------|-----|
| **Partition by date and overwrite per partition** | Re-running rewrites the same day → same result. The gold standard. |
| **`partitionOverwriteMode=DYNAMIC`** | Only the partitions present in the data get overwritten; others survive. |
| **Use a deterministic output path** | `gs://bucket/dt=2026-10-28/` — a re-run replaces it wholesale. |
| **BigQuery `insertId`** | The connector can use a hash of the row as the insert ID, and BigQuery de-duplicates on it. |
| **Staging table + MERGE** | Load into a staging table, then `MERGE` into the target. Atomic in BigQuery. |
| **Transactional DB + `MERGE`/`ON CONFLICT`** | Upsert semantics in the database. |
| **Idempotent consumer** | Downstream systems de-duplicate by a business key. |

#### `partitionOverwriteMode`

```python
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "DYNAMIC")
```

| Mode | Behaviour | Use when |
|------|-----------|----------|
| `STATIC` (default) | `overwrite` wipes **the entire table**, then writes | You always rewrite the whole table |
| `DYNAMIC` | `overwrite` wipes **only the partitions present in the data being written** | You write one partition at a time |

```python
# With DYNAMIC, this touches only order_date=2026-10-28
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "DYNAMIC")
df.write.mode("overwrite").partitionBy("order_date").parquet("gs://bucket/warehouse/orders")
```

⚠️ **`DYNAMIC` is the setting you want for daily incremental pipelines, and forgetting it
is how you delete a year of history.** Set it deliberately, and put it in your run
configuration rather than relying on someone remembering it.

💡 **Partition by a date column for backfills.** A backfill for 2026-09-14 then writes to
exactly `order_date=2026-09-14/` and replaces it. Re-running the backfill is safe, and
running it twice does not double the data. This is the combination that makes a pipeline
operable by humans.

---

### The sink-side checklist

Before a sink goes into production, every item on this list should have an answer:

| # | Check | Question |
|---|-------|----------|
| 1 | **Schema match** | Does the sink's schema match the DataFrame? What happens when a column is added, removed, or retyped? |
| 2 | **Partitioning** | Is the data partitioned sensibly? Is the partition count in a reasonable range (hundreds, not millions)? |
| 3 | **Compression** | Is compression enabled? Snappy for Parquet, Zstd if you need smaller files? |
| 4 | **Atomicity** | If the job fails halfway, is the destination left in a partial state? Can a reader see a half-written dataset? |
| 5 | **Idempotency** | Can this write be safely repeated? What exactly makes it idempotent — partition overwrite, an `insertId`, a `MERGE`? |
| 6 | **File size** | Are the output part files in the 128 MB – 1 GB range? |
| 7 | **Small-file hygiene** | Will repeated runs accumulate small files? Is there a compaction step? |
| 8 | **Retry safety** | If the sink returns a transient error, does the write retry, and does the retry duplicate? |
| 9 | **Concurrency** | Can two instances of this job write to the same destination simultaneously? What happens if they do? |
| 10 | **Cost** | Does this write path involve GCS staging, extra scans, or an expensive BigQuery operation? |

---

## 🛠️ Hands-On: Write to Multiple Sinks

### Step 1 — Cluster and the source data

```bash
gcloud dataproc clusters create course-dev \
  --region=us-central1 \
  --image-version=2.2-debian12 \
  --master-machine-type=n2-standard-4 \
  --worker-machine-type=n2-standard-4 \
  --num-workers=2 \
  --optional-components=JUPYTER \
  --enable-component-gateway \
  --delete-max-idle=1h

gcloud storage mb -l us-central1 gs://my-bucket
gcloud storage mb -l us-central1 gs://my-bucket-bq-staging
```

### Step 2 — Generate source data

```python
# generate_data.py
from pyspark.sql import SparkSession, functions as F
from datetime import date, timedelta

spark = SparkSession.builder.appName("generate").getOrCreate()

start = date(2026, 10, 26)
rows = []
for d in range(3):
    day = start + timedelta(days=d)
    for i in range(500):
        rows.append((
            f"o-{d}-{i:05d}",
            f"c-{i % 50:04d}",
            float((i * 37 % 1000) + 0.99),
            i % 5 + 1,
            ["pending", "shipped", "delivered"][i % 3],
            f"{day.isoformat()}T{(i % 24):02d}:{(i % 60):02d}:00Z",
            day.isoformat(),
        ))

df = spark.createDataFrame(rows, [
    "order_id", "customer_id", "amount", "quantity",
    "status", "created_at", "order_date",
])

df.write.mode("overwrite").parquet("gs://my-bucket/source/orders")
print(f"wrote {df.count()} rows")
spark.stop()
```

```bash
gcloud dataproc jobs submit pyspark generate_data.py \
  --cluster=course-dev --region=us-central1
```

### Step 3 — The write job

```python
# write_job.py
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import TimestampType
import sys

RAW = "gs://my-bucket/source/orders"
WAREHOUSE = "gs://my-bucket/warehouse"
PROJECT = "your-project-id"

spark = (SparkSession.builder
         .appName("multi-sink-writer")
         .getOrCreate())

# DYNAMIC means we overwrite only the partitions present in the data
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "DYNAMIC")

df = (spark.read
      .parquet(RAW)
      .withColumn("created_at", F.col("created_at").cast(TimestampType()))
      .withColumn("order_date", F.col("order_date").cast("date")))

# ---------- Sink 1: full table, partitioned by date, Snappy ----------
full = (df.write
        .mode("overwrite")
        .option("compression", "snappy")
        .partitionBy("order_date")
        .parquet(f"{WAREHOUSE}/orders"))
print("sink 1 (parquet partitioned) done")

# ---------- Sink 2: a flat CSV export ----------
(df.write
 .mode("overwrite")
 .option("header", True)
 .option("compression", "gzip")
 .csv(f"{WAREHOUSE}/exports/orders_csv"))
print("sink 2 (csv export) done")

# ---------- Sink 3: a compact aggregate ----------
(df.groupBy("order_date", "status")
   .agg(F.count("*").alias("orders"),
        F.sum("amount").alias("total_amount"))
 .write
 .mode("overwrite")
 .parquet(f"{WAREHOUSE}/summary"))
print("sink 3 (summary) done")

# ---------- Fan-out with cache ----------
from pyspark.sql import StorageLevel

fanout = df.cache(StorageLevel.MEMORY_AND_DISK)
fanout.count()          # materialise the cache

fanout.write.mode("overwrite").parquet(f"{WAREHOUSE}/fanout/a")
fanout.write.mode("overwrite").parquet(f"{WAREHOUSE}/fanout/b")
fanout.unpersist()
print("fan-out done")

# ---------- BigQuery sink ----------
try:
    (df.write
     .format("bigquery")
     .option("writeDisposition", "WRITE_APPEND")
     .option("createDisposition", "CREATE_IF_NEEDED")
     .option("temporaryGcsBucket", "gs://my-bucket-bq-staging")
     .option("writeMethod", "direct")
     .mode("append")
     .save(f"{PROJECT}.sales.orders"))
    print("sink 4 (bigquery) done")
except Exception as e:
    print(f"bigquery sink skipped: {e}")

spark.stop()
```

### Step 4 — Submit and watch

```bash
gcloud dataproc jobs submit pyspark write_job.py \
  --cluster=course-dev \
  --region=us-central1 \
  --properties="spark.executor.instances=4,spark.executor.cores=2,spark.executor.memory=4g"
```

### Step 5 — Verify the output

```bash
# See the partitioned layout
gcloud storage ls gs://my-bucket/warehouse/orders/
gcloud storage ls gs://my-bucket/warehouse/orders/order_date=2026-10-28/

# Check part-file sizes — aim for 128 MB - 1 GB
gcloud storage ls -l gs://my-bucket/warehouse/orders/order_date=2026-10-28/

# Confirm the summary
gcloud dataproc jobs submit spark-sql \
  --cluster=course-dev --region=us-central1 \
  --execute="SELECT * FROM parquet.\`gs://my-bucket/warehouse/summary\` ORDER BY order_date, status"
```

### Step 6 — Prove the idempotency

Run the job **twice** and check the row count did not double:

```bash
gcloud dataproc jobs submit spark-sql \
  --cluster=course-dev --region=us-central1 \
  --execute="SELECT count(*) AS n FROM parquet.\`gs://my-bucket/warehouse/orders\`"
```

With `mode("overwrite")` + `DYNAMIC` partition overwrite, the second run replaces
`order_date=2026-10-26/27/28` and the count stays at 1500.

### Step 7 — Experiment with `STATIC` to see the danger

```python
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "STATIC")
df.write.mode("overwrite").partitionBy("order_date").parquet(f"{WAREHOUSE}/orders")
```

Run this and the previous day's partitions vanish. This is the behaviour that eats
production history — see it once in a lab so you never ship it.

### Step 8 — Write to Kafka or Pub/Sub

```python
# kafka_write.py — run only if you have a Kafka cluster
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8") if k else None,
    acks="all",
    retries=5,
    linger_ms=20,
)

def writer(iterator):
    for row in iterator:
        producer.send(
            "orders-out",
            key=row["customer_id"],
            value={
                "order_id": row["order_id"],
                "customer_id": row["customer_id"],
                "amount": float(row["amount"]),
            },
        )
    producer.flush(timeout=60)

df.foreachPartition(writer)
producer.close()
```

### Step 9 — Clean up

```bash
gcloud dataproc clusters delete course-dev --region=us-central1
```

---

## 🔑 Key Takeaways

- **`df.write` is a `DataFrameWriter`, and it is immutable.** `df.write.mode("append")` does
  not mutate `df.write` — you must chain the result.
- **Write modes: `overwrite`, `append`, `ignore`, `error` (default).** The default is
  `error`, not `overwrite` — a missing-`mode` write fails if the destination exists.
- **`ignore` is the dangerous one**: it makes a re-run a silent no-op.
- **Modes mean different things per sink.** On BigQuery, `overwrite` → `WRITE_TRUNCATE`.
  On JDBC, `overwrite` → `TRUNCATE TABLE`. With `foreachPartition`, the mode means
  **nothing** — you implement it.
- **CSV and JSON writes produce directories of part files, not single files.** `_SUCCESS`
  markers are written alongside and will be picked up by naive directory readers.
- **`partitionBy` + `mode("overwrite")` + `STATIC` (the default) wipes the entire table**,
  not just the partitions you wrote. Set
  `spark.sql.sources.partitionOverwriteMode=DYNAMIC` for per-partition overwrites.
- **`coalesce` reduces partitions without a shuffle; `repartition` uses one.** Target
  128 MB–1 GB per part file — small files are the silent killer of GCS + Spark performance.
- **Compression: `snappy` is the right default for Parquet**; `zstd` if you want smaller
  files and have CPU headroom.
- **BigQuery `writeDisposition`: `WRITE_APPEND`, `WRITE_TRUNCATE`, `WRITE_EMPTY`.
  `createDisposition`: `CREATE_IF_NEEDED`, `CREATE_NEVER`.**
- **`temporaryGcsBucket` is required for the indirect write path** because BigQuery bulk
  loads read from GCS — Spark stages the bytes there and hands BigQuery a list of URIs.
  Point it at a dedicated staging bucket with a lifecycle rule.
- **`writeMethod="direct"` uses the BigQuery Storage Write API** — no GCS staging, much
  faster, and the staging bucket becomes optional. Check your connector version; the
  default and the option's availability have changed across releases.
- **`saveAsTable` creates/replaces the table; `insertInto` writes into an existing table's
  schema, matching by position.** Always align column order before `insertInto`.
- **Spark's native JDBC writer is single-partition.** The production idiom is
  `foreachPartition` with a **batched `executemany`** insert (~1000 rows per batch).
  Repartition to match your database's `max_connections`.
- **Pub/Sub and Kafka have no native `df.write` sink.** Both are
  `foreachPartition` + the native client library.
- **`foreachPartition` has no cross-partition transactionality** — a failure leaves a
  partial write. Make the write idempotent (delete-then-insert, upsert, or `MERGE`).
- **Fan-out recomputes the source once per sink.** `cache()` + an explicit action
  (`df.count()`) materialises it once; `unpersist()` when done. Often, "write Parquet once,
  then run each sink as a separate job" is better.
- **At-least-once is the practical default.** Exactly-once requires an atomic transaction
  across source, processing, and sink — which, for batch ETL, you get by making the write
  idempotent: partition-by-date + dynamic overwrite, BigQuery `insertId`, or a staging
  table + `MERGE`.

---

## 📚 Practice Exercises

1. **Idempotency under retry.** Build a job that writes a partitioned Parquet dataset to
   GCS. Run it three times and prove the row count is stable. Then flip
   `partitionOverwriteMode` to `STATIC` and run it once more — show which partitions
   disappeared. Finally, simulate a crash: kill the job midway (use a long-running
   `sleep` transformation and `gcloud dataproc jobs kill`) and demonstrate that
   `DYNAMIC` leaves the previous day's partition intact while the in-progress day is
   incomplete. Write the runbook for "how do I safely re-run yesterday's partition?"

2. **The JDBC performance comparison.** Write the same 5 million-row dataset three ways:
   (a) `df.write.format("jdbc")...save()`, (b) `foreachPartition` with `executemany` in
   batches of 100, (c) `foreachPartition` with `executemany` in batches of 5000. Measure
   wall-clock time and the Postgres log of statement durations. Explain the difference in
   round trips. Then deliberately set `numPartitions` high enough to exhaust
   `max_connections` and record the exact error.

3. **BigQuery write method.** Write 200 MB to BigQuery twice — once with
   `writeMethod="indirect"` and a `temporaryGcsBucket`, once with `writeMethod="direct"`.
   Compare wall-clock time and check the BigQuery job history for the query plan each one
   produced. Then deliberately omit `temporaryGcsBucket` on an indirect write and capture
   the exact error. Finally, look in the staging bucket before and after each run and
   explain what the leftover objects are.

4. **Fan-out cost.** Build a DataFrame with a heavy shuffle and write it to three sinks
   (a) without caching, (b) with `cache()`. Compare the Spark UI stage view: total input
   bytes read, total shuffle bytes, and total job duration. Then implement the
   "write Parquet once, read many" alternative and compare all three on cost and
   operational complexity. Which would you choose for a pipeline with 8 sinks, and why?

5. **The sink checklist.** Take a real sink from your own environment (or one of the
   chapter's examples) and write out all ten items from the sink-side checklist. Be
   specific: not "compression is enabled" but "snappy on Parquet, chosen over zstd because
   the downstream reader is Trino and Trino reads snappy natively." Identify the two
   weakest items and write the code changes that would fix them.

---

## 📖 Further Reading

- Spark SQL programming guide: data sources — https://spark.apache.org/docs/latest/sql-programming-guide/data-sources.html
- Spark SQL programming guide: tables and partitions — https://spark.apache.org/docs/latest/sql-programming-guide/sql-data-sources-load-save-functions.html
- Spark configuration reference (`partitionOverwriteMode`) — https://spark.apache.org/docs/latest/configuration.html
- `DataFrameWriter` API (Scala) — https://spark.apache.org/docs/latest/api/scala/org/apache/spark/sql/DataFrameWriter.html
- BigQuery connector documentation — https://cloud.google.com/bigquery/docs/connector-overview
- BigQuery connector write optimization — https://cloud.google.com/bigquery/docs/connector-optimization
- BigQuery connector properties — https://cloud.google.com/bigquery/docs/connector-properties
- BigQuery Storage Write API — https://cloud.google.com/bigquery/docs/storage-write-api
- BigQuery write dispositions — https://cloud.google.com/bigquery/docs/writing-data
- Dataproc BigQuery connector — https://cloud.google.com/dataproc/docs/guides/bigquery-connector
- Dataproc metastore (Hive on GCS) — https://cloud.google.com/dataproc/docs/guides/metastore
- Spark SQL: JDBC data source — https://spark.apache.org/docs/latest/sql-data-sources-jdbc.html
- `foreachPartition` in the Spark programming guide — https://spark.apache.org/docs/latest/rdd-programming-guide.html#rdd-actions
- Google Cloud Pub/Sub publish — https://cloud.google.com/pubsub/docs/publisher
- Kafka producer semantics — https://kafka.apache.org/documentation/#producerconfigs
- Small file problem in Spark — https://spark.apache.org/docs/latest/sql-performance-tuning.html
- Dataproc image versions — https://cloud.google.com/dataproc/docs/concepts/versioning/dataproc-image-versions
