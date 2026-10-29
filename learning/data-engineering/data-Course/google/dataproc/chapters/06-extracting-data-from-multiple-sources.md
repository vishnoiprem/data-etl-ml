# 2.3 — Extracting Data from Multiple Sources

> **Section 2 · Spark Fundamentals · Lecture 2.3 · 26:14**

## 🎯 What you will learn

- The unified `DataFrameReader` API: one `spark.read` object that reads every format Spark knows
- Reading Cloud Storage: CSV, JSON, Parquet, Avro, and ORC — and why Parquet is the default answer
- The GCS connector internals: `spark.hadoop.fs.gs.impl`, `fs.gs.connector.*` tuning, and globs
- BigQuery reads with the connector: `load()`, the `query` option, and how incremental reads work
- Streaming reads from Pub/Sub and Kafka via `readStream`
- JDBC reads, and when `dbtable` beats `query` (partition pushdown)
- Schema inference vs explicit schema, and the four error-handling modes
- Why "extract" is trivial and the **schema contract** is the hard part

---

## 🧠 Concept

Here is the thing almost nobody tells you when they say "data ingestion is simple": the
*reading* is simple. The **schema contract** is not.

```
   ╔══════════════════════════════════════════════════════════════╗
   ║   WHAT PEOPLE THINK INGESTION IS                           ║
   ║                                                            ║
   ║      spark.read.csv("gs://bucket/data/*.csv")               ║
   ║                                                              ║
   ║   WHAT IT ACTUALLY IS                                        ║
   ║                                                              ║
   ║      1. What is the contract for a missing column?          ║
   ║      2. What happens when the type changes?                 ║
   ║      3. What happens when a row is malformed?               ║
   ║      4. What happens when a file arrives 40% written?       ║
   ║      5. What happens when I re-run the job?                 ║
   ║      6. What happens when the upstream schema evolves?      ║
   ╚══════════════════════════════════════════════════════════════╝
```

Every one of those six questions is decided by *how* you call `spark.read`, not by Spark.
The API surface is uniform; the semantics underneath are wildly different per format, per
sink, per error mode.

---

### The unified reader API

Every read in Spark 3.x goes through `DataFrameReader`, obtained from `spark.read`.

```
                         spark.read
                             │
              ┌──────────────┼───────────────┐
              │              │               │
         .csv(...)      .format(...)     .load(...)
         .json(...)     .parquet(...)    .table(...)
         .avro(...)     .orc(...)        .sql(...)
         .jdbc(...)     .text(...)
```

The **shortcut methods** (`read.csv`, `read.json`, `read.parquet`, `read.avro`, `read.orc`,
`read.jdbc`, `read.text`, `read.format`) are sugar over the **canonical** three-step form:

```python
# These two are exactly equivalent
df = spark.read.csv("gs://bucket/orders.csv", header=True)
df = spark.read.format("csv").option("header", True).load("gs://bucket/orders.csv")
```

| Form | Use it when |
|------|-------------|
| `spark.read.csv(path)` | The format is known and fixed — terse, readable |
| `spark.read.format("csv").option(...).load(path)` | You build the reader dynamically, or want the `.option()` chain visible |
| `spark.read.format("bigquery").load(...)` | You need a source with no shortcut method (BigQuery, Kafka, Pub/Sub) |

💡 **Prefer `format(...).option(...).load(...)` in shared library code.** It makes it trivial
to parameterise the format, and it means every option you set appears in one place instead of
being scattered across positional arguments and keyword arguments.

⚠️ **`spark.read.format("csv")` and `spark.read.csv()` are not always the same.** The shortcut
methods have their own default option sets. For example `read.csv()` defaults to
`header=False` and `read.json()` handles multiline records differently depending on options.
When you switch a working job from the shortcut to the canonical form, re-check the defaults.

---

### The GCS connector: what is actually happening

On Dataproc, the GCS connector is **built into the image**. There is no extra JAR to add.
When Spark sees a `gs://` path, it delegates to Hadoop's `FileSystem` abstraction, which
resolves to `com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem`.

```
spark.read.csv("gs://bucket/data/*.csv")
        │
        ▼
   DataSource.resolveRelation()
        │
        ▼
   InMemoryFileIndex ──► lists matching paths
        │
        ▼
   FileScan (CSV)  ──► splits files into partitions
        │
        ▼
   Hadoop FileSystem.getFileStatus()  ──► GCS JSON API (list + metadata)
        │
        ▼
   GoogleHadoopFileSystem.open()      ──► GCS object GET (streamed)
```

The property that binds Hadoop's `FileSystem` SPI to the GCS implementation:

```text
spark.hadoop.fs.gs.impl = com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem
```

In practice you never set this on Dataproc — the image sets it for you. You set it when you
run Spark outside Dataproc (EMR, Databricks, plain EC2, your laptop) and must ship the
`gcs-connector` and `google-cloud-storage` JARs yourself.

💡 **The GCS connector is a shim, not a native Spark filesystem.** It speaks the Hadoop
`FileSystem` API, which means Spark still has to **list** files and **stat** them before it
can read them. On GCS, listing is a paginated JSON API call. This is why the
`fs.gs.connector.maximum-file-count` property exists — a directory with a million small files
will spend a long time just listing.

### The `fs.gs.connector.*` tuning properties

| Property | Default | What it controls |
|----------|---------|------------------|
| `fs.gs.connector.maximum-file-count` | `1000000` | Hard cap on files a single scan will list. Exceed it → `IllegalArgumentException: Maximum number of files exceeded`. |
| `fs.gs.connector.maximum-file-count` (raise) | — | Raise it for very wide directory trees |
| `fs.gs.connector.parallelism` | `64` | Threads used for parallel list/stat operations |
| `fs.gs.connector.maximum-buffer-size` | `104857600` (100 MB) | Buffer for write-ahead of large objects |
| `fs.gs.connector.use.internal.download` | `true` | Use the connector's own download path rather than the Hadoop stream |
| `fs.gs.connector.http.timeout` | `120000` (ms) | HTTP timeout for GCS calls |
| `fs.gs.connector.maximum-delete-files` | `10000` | Cap on deletes in a single delete call |
| `fs.gs.connector.marked-for-deletion-retention-period-ms` | `0` | Soft-delete marker retention (GCS soft delete) |

⚠️ **The default `maximum-file-count` of 1,000,000 is generous but not infinite.** Dataproc's
own metadata-server shim (`gs://.../google-cloud-dataproc-metainfo`) plus a date-partitioned
lake can exceed it. If you see `Maximum number of files exceeded`, raise it explicitly:

```python
spark.conf.set("fs.gs.connector.maximum-file-count", 10000000)
```

⚠️ **Raising the cap is not free.** Listing 10 million files takes real time and real API
quota. If your tree is that wide, the fix is usually a **narrower glob**, a **partitioned
layout**, or an **inventory table** — not a bigger number.

💡 **Prefer a narrow glob to a broad directory read.** `gs://bucket/sales/dt=2026-10-28/*.parquet`
lists one partition's worth of files. `gs://bucket/sales/` lists every file in the entire
lake and then throws most of them away. On a lake with years of history, the difference
between the two is minutes versus milliseconds.

---

### Reading files from Cloud Storage

#### The four core formats

```python
# ---------- CSV ----------
df_csv = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .option("delimiter", ",")
    .option("nullValue", "")
    .option("quote", '"')
    .option("escape", '"')
    .option("encoding", "UTF-8")
    .csv("gs://my-bucket/raw/orders/*.csv")
)

# ---------- JSON (one JSON object per line) ----------
df_json = (
    spark.read
    .option("multiLine", "false")      # default: one JSON object per line
    .json("gs://my-bucket/raw/events/*.json")
)

# ---------- Parquet ----------
df_parquet = spark.read.parquet("gs://my-bucket/warehouse/orders")

# ---------- ORC ----------
df_orc = spark.read.orc("gs://my-bucket/warehouse/orders_orc")

# ---------- Avro (requires the spark-avro package) ----------
df_avro = spark.read.avro("gs://my-bucket/raw/users.avro")
```

#### The Avro package

Avro is the one format here that is **not** bundled with Spark core. You need the
`spark-avro` package, which in turn depends on `spark-avro_2.12` and Avro itself.

```bash
# Download the matching package for Spark 3.5 / Scala 2.12
gsutil cp \
  gs://spark-packages/releases/com/spark/sql/spark-avro_2.12-3.5.3.jar \
  gs://my-bucket/libs/

gcloud dataproc clusters create course-dev \
  --region=us-central1 \
  --image-version=2.2-debian12 \
  --jars=gs://my-bucket/libs/spark-avro_2.12-3.5.3.jar \
  ...
```

Or, without a cluster-level JAR, at job submission time:

```bash
gcloud dataproc jobs submit pyspark main.py \
  --cluster=course-dev \
  --region=us-central1 \
  --jars=gs://my-bucket/libs/spark-avro_2.12-3.5.3.jar
```

💡 **Avro vs Parquet: pick one and be consistent.** Avro carries its schema *in the file*,
which makes it self-describing and excellent for schema evolution and event streams. Parquet
carries its schema in the *footer* and is dramatically faster to scan and much better at
predicate pushdown. The common pattern is Avro at the edge (Kafka schema registry, event
ingestion) and Parquet in the warehouse.

#### Format comparison

| Format | Schema in file | Read speed | Compression | Best use |
|--------|----------------|-----------|-------------|----------|
| **CSV** | No | Slowest (parse per row) | None by default | Interop, tiny files, human inspection |
| **JSON** | No (unless NDJSON) | Slow | None by default | Event payloads, API responses |
| **Parquet** | Footer | **Fastest** | Snappy default | Analytical warehouse tables |
| **ORC** | Footer | Fast | Snappy/Zstd | Hive ecosystem, ACID tables |
| **Avro** | Header (per file) | Fast | Deflate | Schema evolution, streaming ingest |

💡 **Write Parquet, read Parquet.** Every round-trip through CSV costs you type information,
compression, and scan speed. If a source system only gives you CSV, convert once at
ingestion and never touch CSV again.

---

### Globs, directories, `paths`, and `recursiveFileLookup`

This is where a lot of real-world ingestion bugs live.

```python
# ---------- A single file ----------
spark.read.parquet("gs://bucket/orders-2026-10-28.parquet")

# ---------- A glob: ONE level, matching files in that directory ----------
spark.read.parquet("gs://bucket/orders/part-*.parquet")

# ---------- A directory: ALL files directly inside, non-recursively ----------
spark.read.parquet("gs://bucket/orders/")

# ---------- A recursive glob: any depth ----------
spark.read.parquet("gs://bucket/orders/**/*.parquet")

# ---------- Multiple explicit paths ----------
spark.read.parquet("gs://bucket/a.parquet", "gs://bucket/b.parquet")

# ---------- Multiple paths as a list via .load(paths=...) ----------
spark.read.format("parquet").load(paths=["gs://bucket/a.parquet", "gs://bucket/b.parquet"])

# ---------- Recursive directory traversal ----------
(
    spark.read
    .option("recursiveFileLookup", "true")
    .parquet("gs://bucket/orders/")
)
```

| Form | Depth | Notes |
|------|-------|-------|
| `dir/` | 1 level only | `dir/sub/file.parquet` is **not** included |
| `dir/*.parquet` | 1 level only | Glob applies to the immediate children |
| `dir/**/*.parquet` | Any depth | `**` is the recursive wildcard |
| `.option("recursiveFileLookup","true")` + `dir/` | Any depth | Equivalent effect, different spelling |
| `.load(paths=[...])` | Explicit | The only way to read a heterogeneous list of paths |

⚠️ **`**` and `recursiveFileLookup` are not identical in all Spark versions.** In Spark 3.x
the Hadoop `GlobFilter` supports `**` as recursive, and `recursiveFileLookup` additionally
**suppresses `_SUCCESS` and hidden files** (those starting with `_` or `.`). If your lake has
`_temporary` folders from failed jobs, `recursiveFileLookup` is safer.

⚠️ **A directory read will happily pick up `_SUCCESS` marker files** and files left behind by
a failed write. This is a classic source of "one extra malformed record" bugs. Either use
`recursiveFileLookup`, or write to a temp path and rename on success (covered in the next
chapter).

💡 **`paths=` vs `path=`.** `DataFrameReader.load(path)` takes one path. `load(paths=[...])`
takes a list. This is what you want when your inputs come from a configuration-driven
manifest rather than a fixed prefix.

---

### Schema inference vs explicit schema

```python
# ---------- Inference (the default) ----------
df = spark.read.option("header", True).option("inferSchema", True).csv(path)
```

Inference samples the data (default `spark.sql.sources.inferColumnTypes` sampling behaviour,
plus `spark.sql.sources.defaultSizeInBytes` for the initial file listing) and guesses types.

| Problem | Consequence |
|---------|-------------|
| Inference samples only the first files | A column that is `null` in the first 1 MB is inferred as `string` or `null` type |
| Type inference is per-file, then merged | Integer columns become `double` if one file has a decimal |
| Inference costs an extra scan | The file is read once to infer and again to parse |
| `null` type columns cannot be written to Parquet | `AnalysisException: Can't write incompatible data` |
| Inference is **not stable** across runs | Same schema today, different schema tomorrow |

```python
# ---------- Explicit schema (the production answer) ----------
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    DoubleType, TimestampType, DateType,
)

orders_schema = StructType([
    StructField("order_id",    StringType(),    True),
    StructField("customer_id", StringType(),    True),
    StructField("amount",      DoubleType(),    True),
    StructField("quantity",    IntegerType(),   True),
    StructField("status",      StringType(),    True),
    StructField("created_at",  TimestampType(), True),
    StructField("order_date",  DateType(),      True),
])

df = (
    spark.read
    .option("header", True)
    .schema(orders_schema)
    .csv("gs://my-bucket/raw/orders/*.csv")
)
```

💡 **Use explicit schemas for anything you do not own.** If the source is a partner's SFTP
drop or a third-party API, their schema will change without notice, and inference means your
pipeline breaks on a Tuesday because a currency symbol appeared in an amount column.

For data **you** produce, a better pattern is to keep the schema in a registry (a JSON file
in GCS, a BigQuery table, a Git repository) and load it at runtime:

```python
import json
from pyspark.sql.types import StructType

def load_schema_from_gcs(spark, path):
    """Read a schema definition stored as a JSON dict of column -> type string."""
    raw = spark.read.text(path).collect()
    text = "".join(r["value"] for r in raw)
    return StructType.fromJson(json.loads(text))

schema = load_schema_from_gcs(spark, "gs://my-bucket/schemas/orders.json")
df = spark.read.schema(schema).option("header", True).csv("gs://my-bucket/raw/orders/")
```

---

### Error handling modes: `FAILFAST`, `PERMISSIVE`, `DROPMALFORMED`, `EXCEPTION`

This is the single most consequential option on a CSV read, and the naming has a trap in it.

| Mode | Behaviour | Use when |
|------|-----------|----------|
| `FAILFAST` | Abort the job on the first malformed record | Data must be perfect; you want to know immediately |
| `PERMISSIVE` | *(CSV default)* Malformed rows are dropped, **all other rows load** | Never use on financial/audit data |
| `DROPMALFORMED` | Malformed rows are dropped, **valid rows load** | Same as PERMISSIVE for CSV but clearer intent |
| `EXCEPTION` | **Renamed to `FAILFAST` in Spark 3.0** | Legacy name only |

```python
# Spark 3.5 — use FAILFAST
df = (
    spark.read
    .option("mode", "FAILFAST")
    .option("header", True)
    .schema(schema)
    .csv("gs://my-bucket/raw/orders/*.csv")
)
```

⚠️ **`EXCEPTION` was renamed to `FAILFAST` in Spark 3.0.** If you see `EXCEPTION` in a blog
post or an LLM-generated tutorial, it is pre-3.0 code. In Spark 3.5, passing `EXCEPTION` does
**not** fail fast — it is silently treated as the default `PERMISSIVE` mode. This is one of the
most dangerous silent behaviour changes in the Spark ecosystem: a pipeline that used to halt
on bad data will now quietly skip rows.

⚠️ **CSV `PERMISSIVE` mode drops the entire row, not just the bad field.** If a single row
has 12 columns instead of 11, that row disappears entirely. You get no indication in the logs
that it happened. This is how 3% of your revenue data vanishes without anyone noticing.

### The `_corrupt_record` column (JSON)

For JSON, `PERMISSIVE` mode is smarter: instead of dropping the bad record, Spark keeps it
and puts the raw text in a `_corrupt_record` column.

```python
df = (
    spark.read
    .option("mode", "PERMISSIVE")
    .option("columnNameOfCorruptRecord", "_corrupt_record")
    .json("gs://my-bucket/raw/events/*.json")
)

# Split good from bad
good = df.filter(F.col("_corrupt_record").isNull())
bad  = df.filter(F.col("_corrupt_record").isNotNull())

# Quarantine the bad records — never just drop them
bad.select("_corrupt_record").write.mode("append").json("gs://my-bucket/quarantine/events/")
```

```
   events.json (one bad line)
   ────────────────────────────
   {"user_id": "u1", "event": "click"}          → normal row, _corrupt_record = null
   {"user_id": "u2", "event":  "click", "ts":}  → BROKEN
   {"user_id": "u3", "event": "view"}            → normal row
```

With `_corrupt_record` enabled, Spark produces **three** rows in one DataFrame: the two good
ones and the broken one (with all typed columns null and the raw text in `_corrupt_record`).
Filter on it.

💡 **Always quarantine, never silently drop.** A row you dropped is a business incident you
will never see. A row you quarantined is a ticket you can triage. Write the corrupt records
to a dead-letter path and alert on the count.

---

### Reading from BigQuery

The BigQuery connector is **bundled with Dataproc**, but it is versioned **separately** from
the Spark runtime. The image's `SPARK_BQ_CONNECTOR_VERSION` metadata attribute tells you
exactly which version is on the classpath.

```bash
# Check what is bundled
gcloud compute ssh course-dev-m --zone=us-central1-a --command="
  curl -s -H 'Metadata-Flavor: Google' \
  http://metadata.google.internal/computeMetadata/v1/instance/attributes/SPARK_BQ_CONNECTOR_VERSION"
```

To override it, you can ship a newer JAR:

```text
com.google.cloud.spark:bigquery-spark-sql_2.12:2.37.0
```

or, in newer artifact naming:

```text
com.google.cloud.spark:bigquery-spark-connector_2.12:2.37.0
```

```bash
# Check the current version before pinning — this changes regularly
gs://spark-packages/releases/com/google/cloud/spark/3.5/bigquery-spark-sql_2.12-2.37.0.jar

gcloud dataproc jobs submit pyspark main.py \
  --cluster=course-dev \
  --region=us-central1 \
  --jars=gs://my-bucket/libs/bigquery-spark-sql_2.12-2.37.0.jar
```

💡 **The `_2.12` suffix is the Scala binary version.** Spark 3.5 on Dataproc 2.2 uses Scala
2.12. If you download a `_2.13` jar you will get `NoSuchMethodError` or
`ClassNotFoundException` at runtime, not at submit time.

#### The three read shapes

```python
# ---------- 1. Read a whole table ----------
df = (
    spark.read
    .format("bigquery")
    .option("dataset", "my_project.sales")
    .option("table", "orders")
    .load()
)

# ---------- 2. Read via a query ----------
df = (
    spark.read
    .format("bigquery")
    .option("query", """
        SELECT order_id, customer_id, amount, created_at
        FROM `my_project.sales.orders`
        WHERE created_at >= '2026-10-01'
          AND created_at <  '2026-11-01'
    """)
    .load()
)

# ---------- 3. Read a specific table by path ----------
df = spark.read.format("bigquery").load("my_project.sales.orders")
```

| Form | How it reaches BigQuery | Cost |
|------|-------------------------|------|
| `dataset` + `table` | `extract` / direct table read | Billed per byte extracted |
| `query` | BigQuery runs the query, Spark pulls the result | **Query bytes billed** — a `SELECT *` from a huge table costs real money |
| `load("project.dataset.table")` | Same as dataset+table | Same as dataset+table |

⚠️ **The `query` option bills for the bytes the *query* returns, not the bytes you read.**
A `SELECT *` from a 1 TB partitioned table with a filter that matches 1% still extracts the
matching 10 GB, but a badly written query with a cross join can extract far more than you
expect. Always project only the columns you need and always check the query plan in the
BigQuery console first.

#### Incremental reads

The BigQuery connector supports several strategies for reading incrementally.

```python
# ---------- 1. Partitioned table with a partition filter ----------
df = (
    spark.read
    .format("bigquery")
    .option("query", """
        SELECT * FROM `my_project.sales.orders`
        WHERE order_date BETWEEN '2026-10-01' AND '2026-10-28'
    """)
    .load()
)
```

```python
# ---------- 2. Range predicate on a timestamp column ----------
df = (
    spark.read
    .format("bigquery")
    .option("readAll", False)
    .option("watermark", "2026-10-28T00:00:00Z")
    .option("partitionField", "order_date")
    .option("partitionExpirationMs", "86400000")   # 1 day
    .format("bigquery")
    .load("my_project.sales.orders")
)
```

```python
# ---------- 3. The simplest, most robust incremental read: push a range into the query ----------
from datetime import datetime, timedelta, timezone

def read_incremental(spark, project, table, days_back=1):
    """Read only rows newer than the lookback window, using an explicit UTC range."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days_back)
    query = f"""
        SELECT * FROM `{project}.{table}`
        WHERE updated_at >= TIMESTAMP('{start.isoformat()}')
          AND updated_at <  TIMESTAMP('{end.isoformat()}')
    """
    return spark.read.format("bigquery").option("query", query).load()
```

💡 **Overlapping windows are the standard pattern for correctness.** Read the last N hours
rather than "since the last run" — a run that starts at 10:59 and reads "since 10:00" will
miss nothing, but a run that crashes and restarts will need a checkpoint anyway. Use an
overlap window plus idempotent downstream writes, and you get at-least-once semantics without
data loss. (Exactly-once is discussed in the next chapter.)

#### `materialization` and `maxReadParallelism`

Two options that control *how* the connector moves data, not *what* it reads.

| Option | Default | Effect |
|--------|---------|--------|
| `materialization` | `true` (for `query` reads) | The connector **materializes** the query result into a temporary table in a **temporary project** (or the default project), then reads it in parallel. This is what makes parallel reads possible at all — BigQuery's `jobs.getQueryResults` returns a single result stream. |
| `materialization.project` | — | Which project holds the materialized table. Set this to a dedicated **temporary** project you control. |
| `materialization.dataset` | — | Dataset for the materialization table. |
| `maxReadParallelism` | `1` | How many BigQuery read streams are opened in parallel. `1` = sequential. Raising it to `8` or `16` gives large speedups on wide tables. |
| `maxReadParallelism` (config) | — | Also settable globally as `spark.datasource.bigquery.maxReadParallelism` |

```python
df = (
    spark.read
    .format("bigquery")
    .option("query", "SELECT * FROM `my_project.sales.orders`")
    .option("materialization", "true")
    .option("materialization.project", "my_project_tmp")
    .option("materialization.dataset", "bq_materialization")
    .option("maxReadParallelism", 8)
    .load()
)
```

💡 **`maxReadParallelism` is one of the highest-leverage knobs in BigQuery reads.** The
default of `1` means the connector pulls the result set in a single stream. Raising it to
`8`–`16` on a multi-terabyte table routinely cuts read time by an order of magnitude.

⚠️ **Materialization creates a temporary table, and it costs money and leaves residue.**
The connector creates a table in `materialization.project`, reads it, and (by default) drops
it afterward. If the job crashes, the table survives and you accumulate garbage tables that
you are billed storage for. Point `materialization.project` at a dedicated project with a
lifecycle policy that deletes tables after a few hours.

⚠️ **Materialization is only supported for `query` reads, not for direct table reads.**
Direct table reads (`dataset` + `table`) use the BigQuery Storage Read API directly and do
not materialize.

#### Storage Read API vs Storage Write API vs the legacy connector

This is the performance story that matters most for BigQuery in Spark.

```
   LEGACY CONNECTOR (the old "jobs.getQueryResults" path)
   ┌──────────────────────────────────────────────────────────────┐
   │  Spark  ──► BigQuery job  ──►  single result stream         │
   │            (getQueryResults)                                 │
   │                                                              │
   │  Throughput: one stream, one HTTP connection. Slow.          │
   └──────────────────────────────────────────────────────────────┘

   STORAGE READ API  (read path of the modern connector)
   ┌──────────────────────────────────────────────────────────────┐
   │  Spark  ──► BigQuery Storage Read API                       │
   │            ──► parallel streams (maxReadParallelism)        │
   │            ──► bytes land in GCS, Spark reads from there    │
   │                                                              │
   │  Throughput: many parallel streams. Much faster.             │
   └──────────────────────────────────────────────────────────────┘

   STORAGE WRITE API (write path of the modern connector)
   ┌──────────────────────────────────────────────────────────────┐
   │  Spark  ──► BigQuery Storage Write API                      │
   │            ──► row deltas streamed directly into BQ         │
   │                                                              │
   │  No GCS staging. No temporary files. Much faster.           │
   └──────────────────────────────────────────────────────────────┘
```

| Path | Legacy (BigQuery jobs API) | Storage Read API / Storage Write API |
|------|---------------------------|--------------------------------------|
| Direction | Read | Read and write |
| Staging | Query result → temporary GCS location | **None** for direct writes; bytes stage for reads |
| Parallelism | Low | High (`maxReadParallelism`) |
| Throughput | Baseline | Several times faster; the write path is dramatically faster |
| Streaming | No | Yes (Storage Write API supports streaming inserts) |

💡 **Use the Storage Write API for writes** (see the next chapter) and the Storage Read API
for reads on large tables. The connector version matters — older connector versions fall back
to the legacy path. Bump the connector JAR if reads feel slow.

---

### Reading from Pub/Sub and Kafka (streaming)

Both are **streaming** sources and both use `spark.readStream`, not `spark.read`.

```python
# ---------- Pub/Sub ----------
df_pubsub = (
    spark.readStream
    .format("pubsub")
    .option("projectId", "my_project")
    .option("subscription", "orders-sub")
    .option("maxFilesPerTrigger", 1000)
    .load()
)
```

```python
# ---------- Kafka ----------
df_kafka = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "broker1:9092,broker2:9092")
    .option("subscribe", "orders-topic")
    .option("startingOffsets", "earliest")
    .option("failOnDataLoss", "false")
    .option("maxOffsetsPerTrigger", 100000)
    .load()
)

# Kafka messages arrive as a binary `value` — decode them
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

df_kafka = (
    df_kafka
    .withColumn("payload", F.col("value").cast(StringType()))
    .selectExpr("CAST(key AS STRING) AS key", "payload", "topic", "partition", "offset", "timestamp")
)
```

| Source | Key concepts |
|--------|--------------|
| **Pub/Sub** | Uses the **subscription** model — the subscription tracks a cursor. Spark's checkpoint stores the offset. `maxFilesPerTrigger` bounds the batch size. |
| **Kafka** | Uses **offsets** and consumer groups. Spark stores offsets in its checkpoint. `startingOffsets` only applies on the *first* start. `maxOffsetsPerTrigger` bounds the batch size. |

⚠️ **Both sources need a checkpoint location for exactly-once-ish semantics.** Without a
checkpoint, restarting the stream reprocesses everything from `earliest`/`latest` depending
on configuration, and you get duplicates.

```python
df_pubsub.writeStream \
    .format("parquet") \
    .option("checkpointLocation", "gs://my-bucket/checkpoints/orders_pubsub") \
    .option("path", "gs://my-bucket/stream/orders") \
    .trigger(processingTime="2 minutes") \
    .start()
```

💡 **The Pub/Sub connector is built into Dataproc.** Kafka's connector is also bundled in
recent Dataproc images, but you may need `--jars` with `spark-sql-kafka-0-10_2.12` if your
image does not include it. Check `ls /opt/spark/jars | grep kafka` on the master before
shipping a JAR you do not need.

⚠️ **The Kafka connector's `startingOffsets` only matters on the very first run.** Once a
checkpoint exists, Spark resumes from the checkpointed offsets. If you delete the checkpoint
to "start fresh," you are replaying the entire topic.

---

### Reading from JDBC databases

```python
# ---------- Simple: one table ----------
df = (
    spark.read
    .format("jdbc")
    .option("url", "jdbc:postgresql://db-host:5432/mydb")
    .option("dbtable", "public.orders")
    .option("user", "readonly")
    .option("password", "secret")
    .option("fetchsize", 10000)
    .load()
)

# ---------- With partition pushdown (the right way for big tables) ----------
df = (
    spark.read
    .format("jdbc")
    .option("url", "jdbc:postgresql://db-host:5432/mydb")
    .option("dbtable", """
        SELECT order_id, customer_id, amount, created_at
        FROM public.orders
        WHERE created_at >= '2026-10-01' AND created_at < '2026-11-01'
    """)
    .option("partitionColumn", "order_id")
    .option("lowerBound", "1")
    .option("upperBound", "1000000")
    .option("numPartitions", 10)
    .option("fetchsize", 10000)
    .load()
)
```

| Option | Effect |
|--------|--------|
| `url` | JDBC URL. `jdbc:<driver>://host:port/database` |
| `dbtable` | A table name **or** a subquery in parentheses. The connector wraps it in `SELECT * FROM (subquery) WHERE ...` when partitioning. |
| `query` | An alternative to `dbtable` that takes a full SQL query directly. **Cannot be combined with `partitionColumn`.** |
| `partitionColumn` | The column to partition on. Must be numeric, timestamp, or date — and **strictly increasing** for good pruning. |
| `lowerBound` / `upperBound` | The range to split. Spark divides it into `numPartitions` ranges. If wrong, you read too much or too little. |
| `numPartitions` | How many JDBC connections to open. Each is a parallel query. |
| `fetchsize` | Rows fetched per network round trip. The default of `0` means "use the driver default" and is often terrible. Set it to `10000`. |
| `query` + `partitionColumn` | ❌ **Mutually exclusive.** Spark throws `IllegalArgumentException`. |

💡 **`dbtable` + `partitionColumn` beats `query` for big tables.** The connector generates
the range predicates for you, one per partition, and pushes them into the source database.
The database can then use an index. With the `query` option, Spark runs your query **once per
partition** (rewriting the partition predicates where possible) — which is a classic way to
accidentally run the same expensive query eight times.

⚠️ **`lowerBound`/`upperBound` are not "the min and max of the data" — they are the range
you want covered.** If the real values fall outside them, you silently get wrong or missing
data. And with `partitionColumn` on a **non-monotonic** column (like `updated_at` with
backdated updates, or a UUID), the range splitting produces wildly unbalanced partitions —
one partition reads 90% of the table and the job takes forever.

💡 **Partition JDBC reads on a monotonically increasing integer or a timestamp.** If your
source has no such column, add one at write time on the source side — or materialize to
Parquet in GCS first and read Parquet from then on. Polling a production OLTP database with
a full-table scan is a good way to get an incident ticket.

⚠️ **Credentials.** Never hardcode passwords. On Dataproc, use the cluster's service account
and **IAM authentication** for Cloud SQL, or store secrets in **Secret Manager** and read
them at runtime. If you must use a password, inject it via an environment variable from a
Secret Manager accessor, not from source code.

---

### Reading from HDFS, S3, and elsewhere

The path scheme determines the filesystem; the API does not change.

```python
# HDFS (needs an HDFS client on the classpath — not present on standard Dataproc images)
spark.read.parquet("hdfs://namenode:8020/data/orders")

# S3 (needs the AWS Hadoop bundle)
spark.read.parquet("s3a://my-bucket/data/orders")

# Local disk (on every executor — the path must exist on all of them!)
spark.read.parquet("/data/orders")

# Windows / SMB
spark.read.parquet("file:///mnt/data/orders")
```

| Scheme | Connector needed on Dataproc |
|--------|------------------------------|
| `gs://` | ✅ Built in |
| `hdfs://` | ❌ Requires Hadoop HDFS client jars |
| `s3a://` | ❌ Requires the AWS Hadoop bundle and AWS credentials |
| `abfss://` / `wasbs://` | ❌ Requires the Azure filesystem connector |
| `file://` | ✅ Always available |

💡 **Dataproc is a GCS-first platform.** S3 and HDFS connectors are not pre-installed, and
adding them means shipping JARs and solving cross-cloud IAM. If you have data on S3, the
usual answer is a one-time transfer to GCS using Storage Transfer Service, then work natively
from there.

---

### The full multi-source extract

Here is the complete shape of a real extraction job: three sources, one unified DataFrame.

```
   gs://raw/orders/*.csv  ──┐
                            ├──►  orders_df  ──┐
   gs://raw/events/*.json ──┘                  │
                                               ├──►  unified_df
   bigquery:sales.customers ───────────────────┘
```

```python
# extract.py
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    IntegerType, TimestampType, DateType,
)

RAW = "gs://my-bucket/raw"
BQ_PROJECT = "my_project"

orders_schema = StructType([
    StructField("order_id",    StringType(),    True),
    StructField("customer_id", StringType(),    True),
    StructField("amount",      DoubleType(),    True),
    StructField("quantity",    IntegerType(),   True),
    StructField("status",      StringType(),    True),
    StructField("created_at",  TimestampType(), True),
])

events_schema = StructType([
    StructField("event_id",   StringType(),    True),
    StructField("event_type", StringType(),    True),
    StructField("user_id",    StringType(),    True),
    StructField("event_ts",   TimestampType(), True),
])

customers_schema = StructType([
    StructField("customer_id", StringType(),  True),
    StructField("name",        StringType(),  True),
    StructField("country",     StringType(),  True),
    StructField("signed_up_at", DateType(),   True),
])


def read_orders(spark):
    """CSV from Cloud Storage, explicit schema, fail fast on malformed rows."""
    return (
        spark.read
        .option("header", True)
        .option("mode", "FAILFAST")
        .schema(orders_schema)
        .csv(f"{RAW}/orders/*.csv")
        .withColumn("source_system", F.lit("orders_csv"))
    )


def read_events(spark):
    """JSON from Cloud Storage, permissive mode with a quarantine column."""
    return (
        spark.read
        .option("mode", "PERMISSIVE")
        .option("columnNameOfCorruptRecord", "_corrupt_record")
        .schema(events_schema)
        .json(f"{RAW}/events/*.json")
        .filter(F.col("_corrupt_record").isNull())
        .drop("_corrupt_record")
        .withColumn("source_system", F.lit("events_json"))
    )


def read_customers(spark):
    """BigQuery via the bundled connector, read with a bounded query."""
    return (
        spark.read
        .format("bigquery")
        .option("query", f"""
            SELECT customer_id, name, country, signed_up_at
            FROM `{BQ_PROJECT}.sales.customers`
            WHERE signed_up_at >= '2020-01-01'
        """)
        .option("maxReadParallelism", 8)
        .load()
        .withColumn("source_system", F.lit("bq_customers"))
    )


def main():
    spark = (SparkSession.builder
             .appName("multi-source-extract")
             .getOrCreate())

    orders = read_orders(spark)
    events = read_events(spark)
    customers = read_customers(spark)

    # A union requires a common schema. Rename + project to align.
    orders_aligned = orders.select(
        F.col("order_id").alias("id"),
        F.lit("order").alias("entity_type"),
        F.col("customer_id").alias("entity_key"),
        F.col("amount").cast(DoubleType()).alias("value"),
        F.col("created_at").alias("event_ts"),
        F.col("source_system"),
    )

    events_aligned = events.select(
        F.col("event_id").alias("id"),
        F.lit("event").alias("entity_type"),
        F.col("user_id").alias("entity_key"),
        F.lit(None).cast(DoubleType()).alias("value"),
        F.col("event_ts"),
        F.col("source_system"),
    )

    customers_aligned = customers.select(
        F.lit(None).cast(StringType()).alias("id"),
        F.lit("customer").alias("entity_type"),
        F.col("customer_id").alias("entity_key"),
        F.lit(None).cast(DoubleType()).alias("value"),
        F.col("signed_up_at").cast(TimestampType()).alias("event_ts"),
        F.col("source_system"),
    )

    unified = orders_aligned.unionByName(events_aligned).unionByName(customers_aligned)

    print(f"orders={orders.count()} events={events.count()} customers={customers.count()}")
    unified.groupBy("entity_type", "source_system").count().show()
    unified.show(10, truncate=False)

    spark.stop()


if __name__ == "__main__":
    main()
```

⚠️ **`union` vs `unionByName` matters enormously here.** `union` is **positional** — it zips
columns by position and **ignores names**. `unionByName` matches by name and is
**schema-tolerant** about missing columns (they become null), which is exactly what you want
when aligning heterogeneous sources.

```python
# POSITIONAL — if the column order differs, you get silently WRONG data
a.union(b)          # a.col1 → b.col1, a.col2 → b.col2, regardless of name

# BY NAME — safe against reordering and additive schema changes
a.unionByName(b)    # a.col1 → b.col1, etc.
```

⚠️ **`union` with mismatched column counts does not error.** It truncates to the shorter
side, or errors depending on the version. `unionByName` with mismatched *names* errors
clearly. Use `unionByName` by default; use positional `union` only when you are certain the
schemas are byte-identical and you want the performance of a pure schema match.

💡 **Normalise to a canonical schema at the boundary.** Every source gets mapped into a
common shape — `id`, `entity_type`, `entity_key`, `value`, `event_ts`, `source_system` —
and then unioned. This is the **converged/canonical model** pattern from data engineering,
and it is what makes adding a fourth source a ten-line change instead of a rewrite.

---

## 🛠️ Hands-On: Build and Run the Extract

### Step 1 — Create the cluster and the data

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

# Staging bucket
gcloud storage mb -l us-central1 gs://my-bucket --project=YOUR_PROJECT_ID

# Raw landing zone
gcloud storage mkdir gs://my-bucket/raw/orders
gcloud storage mkdir gs://my-bucket/raw/events
```

### Step 2 — Put sample data in GCS

```bash
cat > orders-2026-10-28.csv <<'CSV'
order_id,customer_id,amount,quantity,status,created_at
o-1001,c-001,120.50,2,shipped,2026-10-28T10:15:00Z
o-1002,c-002,89.99,1,pending,2026-10-28T11:02:11Z
o-1003,c-001,45.00,5,shipped,2026-10-28T12:44:09Z
o-1004,c-003,310.75,3,delivered,2026-10-28T13:20:41Z
CSV

cat > events-2026-10-28.json <<'JSON'
{"event_id":"e-1","event_type":"click","user_id":"u-101","event_ts":"2026-10-28T10:00:00Z"}
{"event_id":"e-2","event_type":"view","user_id":"u-102","event_ts":"2026-10-28T10:05:12Z"}
{"event_id":"e-3","event_type":"purchase","user_id":"u-101","event_ts":"2026-10-28T10:07:44Z"}
JSON

gcloud storage cp orders-2026-10-28.csv gs://my-bucket/raw/orders/
gcloud storage cp events-2026-10-28.json gs://my-bucket/raw/events/
```

### Step 3 — Explore interactively first

In Jupyter (or `pyspark` over SSH), start with a quick look:

```python
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("explore").getOrCreate()

# What does the CSV actually look like?
raw = spark.read.option("header", True).csv("gs://my-bucket/raw/orders/*.csv")
raw.printSchema()
raw.show(truncate=False)

# Inference got the timestamp as a string — inspect the raw value
raw.select("created_at").distinct().show(truncate=False)

# Read with an explicit schema instead
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType

schema = StructType([
    StructField("order_id", StringType(), True),
    StructField("customer_id", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("quantity", IntegerType(), True),
    StructField("status", StringType(), True),
    StructField("created_at", TimestampType(), True),
])

typed = spark.read.option("header", True).schema(schema).csv("gs://my-bucket/raw/orders/*.csv")
typed.show(truncate=False)
```

### Step 4 — Run the extract job

```bash
gcloud dataproc jobs submit pyspark extract.py \
  --cluster=course-dev \
  --region=us-central1 \
  --properties="spark.executor.instances=4,spark.executor.cores=2,spark.executor.memory=4g" \
  --jars=gs://my-bucket/libs/spark-avro_2.12-3.5.3.jar
```

### Step 5 — Verify

```bash
JOB_ID=$(gcloud dataproc jobs list --region=us-central1 --limit=1 --format="value(jobId)")
gcloud dataproc jobs wait "$JOB_ID" --region=us-central1

# Inspect the output files
gcloud storage ls gs://my-bucket/raw/
gcloud storage cat gs://my-bucket/raw/orders/orders-2026-10-28.csv
```

### Step 6 — Test the failure modes deliberately

```bash
cat > bad-orders.csv <<'CSV'
order_id,customer_id,amount,quantity,status,created_at
o-2001,c-001,100.00,1,shipped,2026-10-28T10:00:00Z
o-2002,c-002,NOT_A_NUMBER,1,shipped,2026-10-28T10:01:00Z
CSV

gcloud storage cp bad-orders.csv gs://my-bucket/raw/orders/
```

Now re-run the job. With `mode=FAILFAST` it **fails**. Change to `PERMISSIVE` and it
**succeeds with 1 row instead of 2**. Feel that difference — it is the difference between
"we noticed" and "we quietly lost a row."

### Step 7 — Add Avro and exercise the schema contract

```python
from pyspark.sql import AvroFile
# Requires the spark-avro package on the classpath
```

Or in SQL:

```sql
CREATE TABLE orders_avro USING avro
OPTIONS (path 'gs://my-bucket/raw/orders_avro');

SELECT * FROM orders_avro LIMIT 10;
```

### Step 8 — Clean up

```bash
gcloud dataproc clusters delete course-dev --region=us-central1
```

---

## 🔑 Key Takeaways

- **Every read goes through `DataFrameReader`** — `spark.read`. The shortcut methods
  (`read.csv`, `read.json`, `read.parquet`) are sugar over `format(...).option(...).load(...)`.
- **Extraction is the easy part; the schema contract is the hard part.** Missing columns,
  type drift, malformed rows, partial files, and re-runs are all decided by your options.
- **The GCS connector is built into Dataproc** — no extra JAR. `spark.hadoop.fs.gs.impl` is
  set for you. `fs.gs.connector.maximum-file-count` (default 1,000,000) caps how many files a
  single scan may list.
- **Prefer narrow globs over broad directory reads.** `gs://bucket/dt=2026-10-28/*.parquet`
  lists one partition; `gs://bucket/` lists the entire lake.
- **`recursiveFileLookup=true` traverses subdirectories and skips `_SUCCESS`/hidden files.**
  A plain directory read does not recurse and does pick up `_SUCCESS`.
- **`load(paths=[...])` is the only way to read a heterogeneous list of paths.**
- **Use explicit schemas for data you don't control.** Inference samples, can infer `null`
  types, costs an extra scan, and is not stable across runs.
- **Error modes: `FAILFAST`, `PERMISSIVE`, `DROPMALFORMED`.** `EXCEPTION` was renamed to
  `FAILFAST` in Spark 3.0 — passing `EXCEPTION` today silently means `PERMISSIVE`.
- **CSV `PERMISSIVE` drops the whole row.** JSON `PERMISSIVE` keeps it in `_corrupt_record`.
  Quarantine the corrupt records; never just drop them.
- **BigQuery connector is bundled but versioned separately.** The artifact is
  `com.google.cloud.spark:bigquery-spark-sql_2.12:<version>` (or the newer
  `bigquery-spark-connector_2.12` naming). The `_2.12` suffix matters.
- **BigQuery `query` reads materialize the result into a temporary table** so they can be
  read in parallel; `maxReadParallelism` (default `1`) is a big performance lever. Point
  `materialization.project` at a dedicated temp project with a cleanup lifecycle.
- **The Storage Read API and Storage Write API are far faster than the legacy BigQuery
  path** — no single-stream bottleneck, no GCS staging for direct writes.
- **JDBC: `dbtable` + `partitionColumn` pushes predicates down. `query` and
  `partitionColumn` are mutually exclusive**, and `query` re-runs per partition.
- **`union` is positional; `unionByName` matches by name.** Align heterogeneous sources to
  a canonical schema and use `unionByName`.

---

## 📚 Practice Exercises

1. **Error-mode autopsy.** Using the bad-orders.csv from the hands-on lab, run the read
   four ways: default (PERMISSIVE), explicit `PERMISSIVE`, `DROPMALFORMED`, and `FAILFAST`.
   Record the row count for each. Then explain precisely *why* CSV PERMISSIVE dropped the
   entire `o-2002` row rather than nulling only the `amount` field, and write a version that
   quarantines the bad row instead. Add a count assertion to the job that fails the pipeline
   when the quarantine count exceeds zero.

2. **BigQuery read performance.** Create a partitioned BigQuery table with at least 100 MB of
   data. Read it (a) with `dataset`+`table`, (b) with `query` and default
   `maxReadParallelism=1`, (c) with `query` and `maxReadParallelism=8`, (d) with
   `materialization=false` on the query read. Time each, and use the Spark UI's stage view to
   explain the difference in task count and read throughput. Then find the materialized
   table left in `materialization.project` and write a lifecycle policy (or a scheduled
   cleanup query) that removes it.

3. **Schema contract.** Write a schema registry stored as JSON in GCS. Load it at runtime and
   apply it to the CSV read. Then simulate upstream drift: add a column to the CSV, change a
   string column to contain a number, and produce a row with too many fields. Show what
   happens with explicit schema + FAILFAST versus inference + PERMISSIVE. Conclude with a
   written policy for which columns are allowed to change and which require a deploy.

4. **JDBC partition pushdown.** Point the JDBC reader at a Cloud SQL Postgres instance with a
   `BIGSERIAL` primary key and an index on `created_at`. Populate it with 5 million rows.
   Compare: (a) `dbtable` with no partitioning, (b) `dbtable` with `partitionColumn`,
   `lowerBound`, `upperBound`, `numPartitions=10`, (c) the `query` option. Capture the
   Postgres query log to prove which approach pushed the predicate down and which ran the
   full scan — and explain why `query` + `partitionColumn` raises an exception.

5. **The four-source extract.** Extend the multi-source extract to add a fourth source: an
   ORC dataset in GCS. Write the code so the new source needs only (a) a reader function and
   (b) an alignment function. Prove the claim by showing that the union logic is untouched.
   Then switch every `unionByName` to positional `union` and deliberately reorder one
   source's columns to show the silent data corruption that `unionByName` prevents.

---

## 📖 Further Reading

- Spark SQL programming guide: loading data — https://spark.apache.org/docs/latest/sql-programming-guide/loading-data.html
- Spark SQL programming guide: data sources — https://spark.apache.org/docs/latest/sql-programming-guide/data-sources.html
- Spark configuration reference — https://spark.apache.org/docs/latest/configuration.html
- `DataFrameReader` API (Scala) — https://spark.apache.org/docs/latest/api/scala/org/apache/spark/sql/DataFrameReader.html
- BigQuery connector documentation — https://cloud.google.com/bigquery/docs/connector-overview
- BigQuery connector read optimization — https://cloud.google.com/bigquery/docs/connector-optimization
- BigQuery connector properties — https://cloud.google.com/bigquery/docs/connector-properties
- BigQuery Storage Write API — https://cloud.google.com/bigquery/docs/storage-write-api
- BigQuery Storage Read API — https://cloud.google.com/bigquery/docs/storage-read-api
- Dataproc BigQuery connector — https://cloud.google.com/dataproc/docs/guides/bigquery-connector
- Cloud Storage connector configuration — https://cloud.google.com/dataproc/docs/guides/connectors/configure-connectors
- GCS connector properties (Hadoop) — https://github.com/GoogleCloudDataproc/gcs-connector
- Spark Avro package — https://github.com/databricks/spark-avro
- Structured Streaming: Kafka — https://spark.apache.org/docs/latest/structured-streaming-kafka-integration.html
- Structured Streaming: Pub/Sub — https://spark.apache.org/docs/latest/structured-streaming-pubsub-integration.html
- JDBC data source — https://spark.apache.org/docs/latest/sql-data-sources-jdbc.html
- Google Cloud Dataproc image versions — https://cloud.google.com/dataproc/docs/concepts/versioning/dataproc-image-versions
