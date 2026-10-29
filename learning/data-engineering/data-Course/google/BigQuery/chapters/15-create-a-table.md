# 2.8 — Create a Table

> **Section 2 · BigQuery Fundamentals · Lecture 2.9 · 8:11**

## 🎯 What you will learn

- Every way to create a table in BigQuery, and when to use each
- The complete `CREATE TABLE` DDL reference
- Schema-first vs schema-inferred (`CREATE TABLE AS SELECT`)
- How to pick the right table type, partitioning, and clustering in one decision

---

## 🧠 Concept

There are six ways to create a table, and they differ in what they cost, how flexible they are,
and whether data moves.

| Method | Data source | Copies data? | Flexible? | Use when |
|--------|-------------|--------------|-----------|----------|
| `CREATE TABLE ... AS SELECT` | A query | Yes (writes results) | Schema fixed by query | Building a model from source data |
| `CREATE TABLE ... (schema)` | Nothing yet | No | Fully flexible | Empty table for a load pipeline |
| `CREATE EXTERNAL TABLE` | GCS/S3 files | No | Fully flexible | Querying the lake in place |
| `CREATE SNAPSHOT TABLE` | Existing table | Yes (copies) | Schema fixed | Point-in-time safety copy |
| `CREATE TABLE LIKE` | Existing table | No | Inherits schema, no data | Schema-only clone |
| `bq load` / load job | Files | Yes (loads) | Schema flexible | Bulk ingest |

💡 **The single most important decision is `CREATE TABLE AS SELECT` vs `CREATE TABLE` + load.**
`CTAS` is one operation, one cost, no intermediate files. A load pipeline is two operations and
costs GCS storage + egress for the files. Use `CTAS` unless you specifically need the table to be
empty first.

---

## 🛠️ Hands-On

### 1. Schema-first table (empty, ready for loads)

```sql
CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID.raw.orders` (
    order_id      STRING     NOT NULL,
    customer_id   STRING     NOT NULL,
    order_date    DATE       NOT NULL,
    order_ts      TIMESTAMP,
    total_amount  NUMERIC(12,2),
    status        STRING,
    is_completed  BOOL,
    line_items    ARRAY<STRUCT<
        product_id  STRING,
        quantity    INT64,
        unit_price  NUMERIC(10,2),
        discount    NUMERIC(10,2)
    >>,
    shipping_address STRUCT<
        street   STRING,
        city     STRING,
        country  STRING,
        postcode STRING
    >
)
PARTITION BY order_date
CLUSTER BY customer_id, status
OPTIONS (
  description = "Raw orders as received from the checkout service",
  labels = [('tier', 'raw'), ('source', 'checkout')],
  require_partition_filter = FALSE,
  partition_expiration_days = 365
);
```

### 2. CTAS — build a model directly

```sql
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.daily_order_summary`
PARTITION BY order_date
CLUSTER BY customer_id
OPTIONS (
  description = "Daily order rollup per customer",
  labels = [('tier', 'curated')],
  partition_expiration_days = 730
)
AS
SELECT
    order_date,
    customer_id,
    COUNT(*)                    AS order_count,
    COUNT(DISTINCT status)      AS distinct_statuses,
    SUM(total_amount)           AS gross_revenue,
    SUM(IF(status = 'completed', total_amount, 0)) AS recognized_revenue,
    MIN(order_ts)               AS first_order_ts,
    MAX(order_ts)               AS last_order_ts,
    ARRAY_AGG(STRUCT(product_id AS sku, quantity) ORDER BY order_ts) AS items
FROM `YOUR_PROJECT_ID.raw.orders`
WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 400 DAY)
GROUP BY order_date, customer_id;
```

### 3. Clone schema without data

```sql
-- Same schema, partitioning, clustering, labels — no rows
CREATE TABLE `YOUR_PROJECT_ID.curated.orders_v2`
LIKE `YOUR_PROJECT_ID.curated.orders`
OPTIONS (
  description = "Schema clone for migration",
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
);
```

### 4. Snapshot for safe table swaps

```sql
-- Point-in-time copy you can restore from
CREATE SNAPSHOT TABLE `YOUR_PROJECT_ID.curated.orders_backup`
FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY) AS
SELECT * FROM `YOUR_PROJECT_ID.curated.orders`;
```

### 5. Load data from Cloud Storage

```bash
# Load a CSV with an explicit schema file
bq load \
  --source_format=CSV \
  --schema_file=schemas/orders_schema.json \
  --skip_leading_rows=1 \
  --replace \
  YOUR_PROJECT_ID:raw.orders \
  gs://YOUR_PROJECT_ID-bq-course/staging/orders_2026-01-01.csv
```

```bash
# Load with auto-detection
bq load \
  --source_format=CSV \
  --autodetect \
  --replace \
  YOUR_PROJECT_ID:raw.orders \
  gs://YOUR_PROJECT_ID-bq-course/staging/orders_2026-01-02.csv
```

💡 **`--replace` truncates and replaces the whole table.** If you are loading into a partitioned
table, you almost always want `--replace` so re-running the load does not duplicate rows. But
`--replace` also **destroys the partitioning** in some cases — check whether your load creates a
single partition or one partition per file.

### 6. Load with a schema — the JSON format

```json
[
  {
    "name": "order_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Unique order identifier"
  },
  {
    "name": "order_date",
    "type": "DATE",
    "mode": "REQUIRED"
  },
  {
    "name": "total_amount",
    "type": "NUMERIC",
    "mode": "NULLABLE"
  },
  {
    "name": "line_items",
    "type": "RECORD",
    "mode": "REPEATED",
    "fields": [
      { "name": "product_id", "type": "STRING", "mode": "NULLABLE" },
      { "name": "quantity",   "type": "INTEGER", "mode": "NULLABLE" }
    ]
  }
]
```

### 7. Create the table via the Python client

```python
from google.cloud import bigquery

client = bigquery.Client(project="YOUR_PROJECT_ID")

schema = [
    bigquery.SchemaField("order_id",     "STRING",    mode="REQUIRED", description="Unique order ID"),
    bigquery.SchemaField("customer_id",  "STRING",    mode="REQUIRED"),
    bigquery.SchemaField("order_date",   "DATE",      mode="REQUIRED"),
    bigquery.SchemaField("order_ts",     "TIMESTAMP"),
    bigquery.SchemaField("total_amount", "NUMERIC",   precision=12, scale=2),
    bigquery.SchemaField("status",       "STRING"),
    bigquery.SchemaField(
        "line_items", "RECORD", mode="REPEATED",
        fields=[
            bigquery.SchemaField("product_id", "STRING"),
            bigquery.SchemaField("quantity",   "INTEGER"),
            bigquery.SchemaField("unit_price", "NUMERIC", precision=10, scale=2),
        ],
    ),
]

table = bigquery.Table(
    f"YOUR_PROJECT_ID.raw.orders",
    schema=schema,
    description="Raw orders as received from the checkout service",
    labels={"tier": "raw", "source": "checkout"},
)

# Time partitioning by a DATE column
table.time_partitioning = bigquery.TimePartitioning(
    type_=bigquery.TimePartitioningType.DAY,
    field="order_date",
    expiration_ms=365 * 24 * 60 * 60 * 1000,   # 365 days
)

# Clustering
table.clustering_fields = ["customer_id", "status"]

table = client.create_table(table)
print(f"Created {table.full_table_id}")
```

---

## 🧠 The Complete `CREATE TABLE` DDL

```sql
CREATE [OR REPLACE] [TEMP | TEMPORARY] TABLE [IF NOT EXISTS] table_name
[(
  column_name column_schema[, ...]
  |
  LIKE other_table
  |
  AS query
)]
[PARTITION BY partition_expression]
[CLUSTER BY clustering_column_list]
[OPTIONS (table_option_list)]
```

### Column schema syntax

```
column_name [column_type] [NOT NULL] [DEFAULT default_value]
  [OPTIONS (column_option_list)]
```

### Column types

| Type | Notes | Use for |
|------|-------|---------|
| `INT64` | 64-bit signed integer | Counts, IDs |
| `FLOAT64` | 64-bit IEEE float | Scientific values, ratios |
| `NUMERIC(p,s)` | Exact decimal | **Money** — always, never FLOAT64 |
| `BIGNUMERIC` | Larger precision | Extreme-precision money |
| `BOOL` | True/False | Flags |
| `STRING` | Variable-length Unicode | Names, IDs, categories |
| `BYTES` | Raw bytes | Binary blobs |
| `DATE` | Calendar date | `order_date` |
| `DATETIME` | Date + time, no TZ | Local business timestamps |
| `TIME` | Time only | Times of day |
| `TIMESTAMP` | Absolute instant, UTC | **Event times** — use this |
| `GEOGRAPHY` | Lat/lng + spatial ops | Locations |
| `INTERVAL` | Duration | Time deltas |
| `JSON` | Native JSON | Semi-structured |
| `RANGE` | Start/end range | Time-series |

⚠️ **Never store money as `FLOAT64`.** `0.1 + 0.2 != 0.3` in binary floating point. Use `NUMERIC`.

💡 **Use `TIMESTAMP` for event time, `DATE` for calendar dates, `DATETIME` for local wall-clock
times with no timezone.** Mixing these up causes subtle off-by-one-day bugs in date partitioning.

### Modes

| Mode | Meaning |
|------|---------|
| `NULLABLE` | Column may be NULL (default) |
| `REQUIRED` | Column must be present and non-NULL |
| `REPEATED` | Column is an array of the given type |

### Table options

| Option | Purpose |
|--------|---------|
| `description` | Documentation shown in the catalog |
| `labels` | Key/value tags for governance and cost |
| `expiration_timestamp` | Delete the table at a specific time |
| `partition_expiration_days` | Drop partitions older than N days |
| `require_partition_filter` | Reject queries without a partition filter |
| `friendly_name` | Display name |
| `storage_billing_model` | `PHYSICAL` / `LOGICAL` / `STORAGE_OPTIMIZED` / `CAPACITY_OPTIMIZED` |
| `max_staleness` | For MVs |

---

## 💡 Production Notes

- **`CREATE OR REPLACE` is atomic.** The old table is dropped only after the new one is
  successfully written — no gap. This is why it is safe in a pipeline.
- **`CREATE OR REPLACE` drops the old table's grants.** Permissions must be re-granted. For
  production tables, use a snapshot + `RENAME` swap if you need to preserve grants.
- **`TEMP` tables** (`CREATE TEMP TABLE`) live for the duration of the session and are **free** for
  storage — perfect for multi-statement pipeline scripts.
- **`EXTERNAL` tables cost nothing to store** but the underlying GCS files still cost money, and
  query scans of files cost the same as managed tables.
- **Set `require_partition_filter = TRUE`** on any partitioned table where a full scan would be
  genuinely expensive.

---

## 🔑 Key Takeaways

- Six table-creation methods; `CTAS` is usually the right one.
- `PARTITION BY` + `CLUSTER BY` should be decided at creation time — adding them later requires a
  full table rewrite.
- **Use `NUMERIC` for money, `TIMESTAMP` for event times, `DATE` for calendar dates.**
- `CREATE OR REPLACE` is atomic but drops grants — use snapshot + rename when grants matter.
- `TEMP` tables are free and session-scoped — ideal for pipeline scripts.
- `storage_billing_model` can cut scan cost substantially — evaluate per table.

---

## 📚 Practice Exercises

1. **Table design.** Design the table for a `page_views` event: `user_id`, `session_id`,
   `page_path`, `referrer`, `viewed_at`, `duration_ms`, `viewport` (w/h/device type). Include
   partitioning, clustering, and reasoning for each.

2. **Schema evolution.** You created `orders` without a `discount` column. Write the exact
   `ALTER TABLE` to add it, the query to backfill it, and the query to verify it.

3. **CTAS vs load.** Compare the cost and operational profile of:
   (a) `CTAS` from a source table, (b) exporting to GCS then loading, (c) streaming insert. For a
   daily 50 GB refresh.

4. **Python table creation.** Write a full Python script that creates a partitioned, clustered,
   storage-optimized table with nested schema and labels. Include error handling for
   `AlreadyExists`.

5. **Atomic swap.** Write a stored-procedure-style script that atomically replaces a table while
   preserving grants, using snapshot + rename.

---

## 📖 Further Reading

- BigQuery DDL reference — https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language
- Table types — https://cloud.google.com/bigquery/docs/table-types
- Storage billing models — https://cloud.google.com/bigquery/docs/storage-optimization
