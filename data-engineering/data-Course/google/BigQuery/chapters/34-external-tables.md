# 5.2 — Permanent External Tables

> **Section 5 · External Data, Views & Materialized Views · Lectures 5.2–5.3 · 4:48 + 2:18**

## 🎯 What you will learn

- Create permanent external tables over Cloud Storage
- All supported file formats and their trade-offs
- The full list of external table limitations
- When to use an external table vs a managed table

---

## 🧠 Concept

An **external table** is a schema defined in BigQuery that points at files in Cloud Storage.
BigQuery reads the files at query time — no data is copied into BigQuery.

### The core trade-off

| | External table | Managed table |
|---|---|---|
| **Storage cost** | GCS only (~$0.02/GB) | BigQuery only (~$0.02/GB) |
| **Query cost** | Same (per byte scanned) | Same (per byte scanned) |
| **Ingestion cost** | Zero | Load cost + time |
| **Query latency** | Slower (no columnar optimization, no caching) | Faster |
| **Clustering** | ❌ Not supported | ✅ |
| **Partitioning** | ✅ Via Hive URI or explicit | ✅ Native |
| **Materialized views** | ❌ Not supported on external | ✅ |
| **Time travel** | ❌ No | ✅ 7 days |
| **Streaming into it** | ❌ No | ✅ |
| **Data locality** | GCS only | BigQuery only |

💡 **The key insight:** an external table and a managed table cost the *same* to query. The
difference is ingestion cost and query speed. If you are going to query the data many times,
managed tables win on speed; if you query once, external tables win on total cost.

---

## 🧠 Supported File Formats

| Format | Extension | Schema | Nested | Compression | Best for |
|--------|-----------|--------|--------|-------------|----------|
| **CSV** | `.csv` | Explicit or auto | ❌ | None | Simple, human-readable |
| **Newline-delimited JSON** | `.json`, `.ndjson` | Explicit or auto | ✅ | None | Event data |
| **Avro** | `.avro` | In-file ✅ | ✅ | Yes | Schema in the file |
| **Parquet** | `.parquet`, `.pq` | In-file ✅ | ✅ | Yes | **The default choice** |
| **ORC** | `.orc` | In-file ✅ | ✅ | Yes | Hive ecosystem |
| **ORC + Avro** | — | In-file ✅ | ✅ | Yes | Mixed |
| **Google Sheets** | — | Auto | ❌ | — | Ad-hoc |
| **Bigtable** | — | In-table | ✅ | — | Live lookups |

💡 **Parquet is the right answer 90% of the time.** Columnar, compressed, schema-in-file, nested
support, and readable by Spark, Hive, DuckDB, and pandas.

---

## 🛠️ Hands-On

### 1. Create an external table over Parquet

```sql
CREATE OR REPLACE EXTERNAL TABLE `YOUR_PROJECT_ID.raw.events_parquet`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://YOUR_PROJECT_ID-bq-course/raw/events_*.parquet'],
  description = "Events stored as Parquet in Cloud Storage"
);
```

💡 **No schema needed for Parquet** — the schema is embedded in the file metadata.

```sql
-- Check the inferred schema
SELECT column_name, data_type, is_nullable
FROM `YOUR_PROJECT_ID.raw.events_parquet.INFORMATION_SCHEMA.COLUMNS`
ORDER BY ordinal_position;
```

### 2. Explicit schema (safer for production)

```sql
CREATE OR REPLACE EXTERNAL TABLE `YOUR_PROJECT_ID.raw.events_parquet_strict`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://YOUR_PROJECT_ID-bq-course/raw/events_*.parquet'],
  schema = (
    event_id   STRING,
    user_id    STRING,
    event_type STRING,
    event_ts   TIMESTAMP,
    amount     NUMERIC(10,2),
    properties JSON
  )
);
```

⚠️ **An explicit schema on an external table avoids a schema-detection scan on every query.** With
auto-detection, BigQuery may re-read the file metadata each time.

### 3. Hive-partitioned external table

```sql
CREATE OR REPLACE EXTERNAL TABLE `YOUR_PROJECT_ID.raw.events_hive`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://YOUR_PROJECT_ID-bq-course/raw/events/*'],
  hive_partition_uri_prefix = 'gs://YOUR_PROJECT_ID-bq-course/raw/events/',
  hive_partitioning_mode = 'AUTO'
);
```

```sql
-- The dt column comes from the URI path, not the file
SELECT column_name, data_type
FROM `YOUR_PROJECT_ID.raw.events_hive.INFORMATION_SCHEMA.COLUMNS`
ORDER BY ordinal_position;

-- And it prunes
SELECT dt, COUNT(*)
FROM `YOUR_PROJECT_ID.raw.events_hive`
WHERE dt >= '2026-01-01'
GROUP BY dt;
```

### 4. CSV external table

```sql
CREATE OR REPLACE EXTERNAL TABLE `YOUR_PROJECT_ID.raw.orders_csv`
OPTIONS (
  format = 'CSV',
  uris = ['gs://YOUR_PROJECT_ID-bq-course/staging/orders_*.csv'],
  skip_leading_rows = 1,
  field_delimiter = ',',
  quote = '"',
  null_markers = [''],
  max_bad_records = 10,
  schema = (
    order_id     STRING,
    customer_id  STRING,
    order_date   DATE,
    total_amount NUMERIC(12,2),
    status       STRING
  )
);
```

### 5. JSON external table

```sql
CREATE OR REPLACE EXTERNAL TABLE `YOUR_PROJECT_ID.raw.events_json`
OPTIONS (
  format = 'NEWLINE_DELIMITED_JSON',
  uris = ['gs://YOUR_PROJECT_ID-bq-course/raw/events_*.json'],
  json_extension = 'json',
  schema = (
    event_id   STRING,
    user_id    STRING,
    event_type STRING,
    event_ts   TIMESTAMP,
    amount     NUMERIC(10,2),
    properties JSON
  )
);
```

### 6. Wildcard over many files

```sql
-- One table, thousands of files
CREATE OR REPLACE EXTERNAL TABLE `YOUR_PROJECT_ID.raw.all_logs`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://YOUR_PROJECT_ID-bq-course/logs/**/*.parquet']
);
```

```bash
# Query without creating a table at all — federated
bq query --use_legacy_sql=false '
  SELECT COUNT(*) FROM `gs://YOUR_PROJECT_ID-bq-course/logs/**/*.parquet`'
```

### 7. Compare external vs managed

```sql
-- Create the managed equivalent
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.events_managed`
PARTITION BY DATE(event_ts)
CLUSTER BY event_type
AS SELECT * FROM `YOUR_PROJECT_ID.raw.events_parquet`;

-- Compare sizes and query costs
SELECT
    table_name,
    ROUND(size_bytes / POW(1024, 3), 3) AS size_gb,
    partition_count,
    clustering_fields
FROM `YOUR_PROJECT_ID.INFORMATION_SCHEMA.TABLES`
WHERE table_name IN ('events_parquet', 'events_managed');
```

---

## ⚠️ All External Table Limitations

| Limitation | Detail |
|------------|--------|
| **No clustering** | ❌ Cannot cluster an external table |
| **No materialized views** | ❌ Cannot create an MV on an external table |
| **No time travel** | ❌ No `FOR SYSTEM_TIME` |
| **No streaming writes** | ❌ Cannot insert into an external table |
| **No DML** | ❌ Cannot UPDATE/DELETE/MERGE |
| **No table constraints** | ❌ No `NOT NULL`, no `REQUIRED` enforcement |
| **No automatic schema evolution** | Schema changes need manual intervention |
| **No partition expiration** | ❌ Lifecycle rules are managed at the GCS layer |
| **No `require_partition_filter`** | ❌ Not applicable |
| **No policy tag inheritance** | ⚠️ Limited |
| **Query performance** | Slower — no BigQuery-specific columnar optimizations |

💡 **The practical rule:** use an external table as a **landing zone** — a cheap place to land raw
data — and then transform it into a managed table for anything that gets queried repeatedly.

---

## 💡 The Lakehouse Pattern

```sql
-- 1. Land raw data in GCS (Parquet, Hive-partitioned)
--    gs://bucket/raw/events/dt=2026-01-01/*.parquet

-- 2. External table for exploration (zero cost, zero latency to set up)
CREATE EXTERNAL TABLE `YOUR_PROJECT_ID.raw.events_external`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://YOUR_PROJECT_ID-bq-course/raw/events/*'],
  hive_partition_uri_prefix = 'gs://YOUR_PROJECT_ID-bq-course/raw/events/'
);

-- 3. Promote to a managed table once the data is worth optimizing
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.events`
PARTITION BY DATE(event_ts)
CLUSTER BY event_type, user_id
OPTIONS (
  partition_expiration_days = 400,
  require_partition_filter = TRUE
)
AS SELECT * FROM `YOUR_PROJECT_ID.raw.events_external`
WHERE event_ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY);
```

---

## 💡 Production Notes

- **External tables cost nothing to create** — no data movement, no load job, no wait.
- **The first query against an external table is slow** (metadata reads), subsequent ones are
  faster (filesystem metadata caching).
- **Use `hive_partition_uri_prefix`** whenever the data is Hive-partitioned. It is the single
  biggest external-table performance lever.
- **External tables cannot be materialized views' source** — plan to promote to managed tables for
  the hot paths.
- **Watch GCS retrieval fees** — Archive and Coldline classes add per-GB read costs on every
  scan.

---

## 🔑 Key Takeaways

- External tables query files in place: **zero ingestion cost, same per-byte query cost, slower
  queries**.
- **Parquet is the default format** — columnar, compressed, schema-in-file, nested-capable.
- Hive-style `key=value/` URI paths with `hive_partition_uri_prefix` enable pruning.
- **External tables support no clustering, no MVs, no time travel, no DML, no streaming.**
- Use them as a **landing zone**, then promote hot data to managed tables with partitioning and
  clustering.

---

## 📚 Practice Exercises

1. **External vs managed.** Compare the total cost of a 10 TB Parquet dataset that is (a) queried
   once, (b) queried daily by 20 analysts, (c) queried by a daily pipeline. Include storage,
   ingestion, and query costs.

2. **Hive partitioning.** Create a Hive-partitioned dataset with `dt=` and `region=` segments.
   Prove pruning for `dt` and measure the bytes difference with and without the prefix option.

3. **Format comparison.** Create the same 1 GB dataset in CSV, JSON, Avro, and Parquet. Measure
   file size, query time, and query cost for each. Write the recommendation.

4. **Limitation workarounds.** For each limitation (no clustering, no MVs, no DML, no time travel),
   describe the workaround. Include: how to do a partitioned refresh, how to build a summary, and
   how to recover a corrupted file.

5. **Lakehouse promotion.** Design a promotion policy: when does a dataset move from external to
   managed? Give concrete thresholds (query frequency, data size, latency requirement).

---

## 📖 Further Reading

- BigQuery external tables — https://cloud.google.com/bigquery/docs/external-tables
- Hive partitioning — https://cloud.google.com/bigquery/docs/external-tables-hive-partitioned-tables
- File format support — https://cloud.google.com/bigquery/docs/external-tables#formats
