# 6.4 — `bq` Dataset & Table Commands

> **Section 6 · Command Line Interface · Lecture 6.4 · 3:05**

## 🎯 What you will learn

- Create datasets and every table type from the CLI
- The `--schema` flag, nested schemas, and schema files
- Partitioning, clustering, and expiration from the CLI
- When to use `bq mk` vs `bq query` for DDL

---

## 🧠 Concept

This chapter covers creating datasets and tables of every type from the command line.

---

## 🧠 Datasets

```bash
# Basic
bq mk --dataset --location=US YOUR_PROJECT_ID:curated

# With a description and labels
bq mk --dataset \
    --location=US \
    --description="Curated analytics models" \
    --labels=env=prod,tier=curated,owner=data-eng \
    YOUR_PROJECT_ID:curated

# Default table expiration (auto-expire tables created in this dataset)
bq mk --dataset \
    --location=US \
    --default_table_expiration_days=90 \
    --default_partition_expiration_days=60 \
    YOUR_PROJECT_ID:scratch

# Case-insensitive naming
bq mk --dataset \
    --location=US \
    --is_case_insensitive \
    YOUR_PROJECT_ID:case_insensitive_ds

# Delete (with contents)
bq rm --dataset --delete_contents YOUR_PROJECT_ID:scratch
```

---

## 🧠 Tables — every type

### 1. From a schema string

```bash
bq mk --table \
    --description="Orders with line items" \
    --time_partitioning_type=DAY \
    --time_partitioning_field=order_date \
    --require_partition_filter \
    --labels=tier=silver \
    YOUR_PROJECT_ID:curated.orders \
    order_id:STRING,customer_id:STRING,order_date:DATE,total_amount:NUMERIC,status:STRING
```

### 2. From a schema file (recommended for anything non-trivial)

```json
[
  { "name": "order_id",     "type": "STRING",    "mode": "REQUIRED", "description": "Unique order ID" },
  { "name": "customer_id",  "type": "STRING",    "mode": "REQUIRED" },
  { "name": "order_date",   "type": "DATE",      "mode": "REQUIRED" },
  { "name": "order_ts",     "type": "TIMESTAMP" },
  { "name": "total_amount", "type": "NUMERIC",   "mode": "REQUIRED" },
  { "name": "status",       "type": "STRING",    "mode": "REQUIRED" },
  { "name": "is_completed", "type": "BOOLEAN" },
  {
    "name": "line_items",
    "type": "RECORD",
    "mode": "REPEATED",
    "fields": [
      { "name": "product_id", "type": "STRING" },
      { "name": "quantity",   "type": "INTEGER" },
      { "name": "unit_price", "type": "NUMERIC" }
    ]
  }
]
```

```bash
bq mk --table \
    --schema_file=schemas/orders_schema.json \
    --time_partitioning_type=DAY \
    --time_partitioning_field=order_date \
    --require_partition_filter \
    YOUR_PROJECT_ID:curated.orders
```

💡 **Always use a schema file for nested or documented schemas.** The colon-delimited string
format cannot express `RECORD`/`REPEATED` structures, descriptions, or modes.

### 3. Clustered tables

```bash
bq mk --table \
    --time_partitioning_type=DAY \
    --time_partitioning_field=order_date \
    --clustering_fields=customer_id,status \
    --schema_file=schemas/orders_schema.json \
    YOUR_PROJECT_ID:curated.orders_clustered
```

### 4. External tables

```bash
# Parquet
bq mk --table \
    --source_format=PARQUET \
    --source_uris=gs://YOUR_PROJECT_ID-bq-course/raw/events_*.parquet \
    --description="Events in Parquet" \
    YOUR_PROJECT_ID:raw.events_external

# CSV with an explicit schema
bq mk --table \
    --source_format=CSV \
    --source_uris=gs://YOUR_PROJECT_ID-bq-course/staging/orders_*.csv \
    --skip_leading_rows=1 \
    --max_bad_records=10 \
    --schema_file=schemas/orders_schema.json \
    YOUR_PROJECT_ID:raw.orders_external

# Hive-partitioned
bq mk --table \
    --source_format=PARQUET \
    --source_uris=gs://YOUR_PROJECT_ID-bq-course/raw/events/* \
    --hive_partitioning_uri_prefix=gs://YOUR_PROJECT_ID-bq-course/raw/events/ \
    YOUR_PROJECT_ID:raw.events_hive
```

### 5. Views and materialized views

```bash
# Logical view
bq mk --use_legacy_sql=false \
    YOUR_PROJECT_ID:curated.v_active_orders \
    "SELECT order_id, customer_id, total_amount
     FROM \`YOUR_PROJECT_ID.curated.orders\`
     WHERE status = 'active'"

# Materialized view
bq mk --use_legacy_sql=false \
    --time_partitioning_type=DAY \
    --time_partitioning_field=order_date \
    --clustering_fields=customer_id \
    YOUR_PROJECT_ID:mart.mv_daily_revenue \
    "SELECT order_date, customer_id, SUM(total_amount) AS revenue, COUNT(*) AS n
     FROM \`YOUR_PROJECT_ID.curated.orders\`
     GROUP BY 1, 2"

# Create a snapshot
bq mk --use_legacy_sql=false \
    YOUR_PROJECT_ID:backup.orders_snapshot \
    "SELECT * FROM \`YOUR_PROJECT_ID.curated.orders\`
     FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)"
```

---

## 🧠 The `--schema` string format

```
column_name:type, column_name:type, ...
```

| Type | CLI syntax |
|------|-----------|
| String | `STRING` |
| Integer | `INTEGER` / `INT64` |
| Float | `FLOAT` / `FLOAT64` |
| Numeric | `NUMERIC` |
| Boolean | `BOOLEAN` / `BOOL` |
| Date | `DATE` |
| Datetime | `DATETIME` |
| Timestamp | `TIMESTAMP` |
| Bytes | `BYTES` |
| Geography | `GEOGRAPHY` |
| JSON | `JSON` |
| Record | `RECORD` — **requires a schema file** |
| Repeated | `REPEATED` — **requires a schema file** |

💡 **Any nested structure requires a schema file.** The colon format cannot express it.

---

## 🧠 `bq mk` vs `bq query` for DDL

| Use | When |
|-----|------|
| `bq mk` | Simple table with a flat schema; simple dataset; simple view |
| `bq query` | Nested schemas, `DEFAULT` values, policy tags, `LIKE`, `COPY`, `SNAPSHOT`, `MERGE`, `ALTER`, anything with `OPTIONS` you cannot express |

```bash
# For complex DDL, use bq query
bq query --use_legacy_sql=false --quiet '
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders_v2` (
  order_id     STRING NOT NULL,
  order_date   DATE   NOT NULL,
  discount     NUMERIC(10,2) DEFAULT 0,
  line_items   ARRAY<STRUCT<product_id STRING, qty INT64>>,
  metadata     JSON
)
PARTITION BY order_date
CLUSTER BY customer_id
OPTIONS (
  description = "Version 2 orders",
  require_partition_filter = TRUE,
  partition_expiration_days = 730,
  labels = [("tier", "gold"), ("owner", "data-eng")]
)'
```

💡 **When in doubt, use `bq query` with DDL.** It supports the complete SQL surface; `bq mk` is a
convenience wrapper with a narrower flag set.

---

## 🛠️ Hands-On: A Complete Table Lifecycle

```bash
# 1. Create the dataset
bq mk --dataset --location=US --description="Course dataset" \
  YOUR_PROJECT_ID:cli_course

# 2. Create the schema file
mkdir -p schemas
cat > schemas/events.json <<'EOF'
[
  { "name": "event_id",   "type": "STRING",    "mode": "REQUIRED" },
  { "name": "user_id",    "type": "STRING",    "mode": "REQUIRED" },
  { "name": "event_type", "type": "STRING",    "mode": "REQUIRED" },
  { "name": "event_ts",   "type": "TIMESTAMP", "mode": "REQUIRED" },
  { "name": "event_date", "type": "DATE",      "mode": "REQUIRED" },
  { "name": "amount",     "type": "NUMERIC" },
  { "name": "props",      "type": "JSON" }
]
EOF

# 3. Create the partitioned, clustered table
bq mk --table \
    --schema_file=schemas/events.json \
    --time_partitioning_type=DAY \
    --time_partitioning_field=event_date \
    --clustering_fields=user_id,event_type \
    --require_partition_filter \
    --description="Events partitioned by date, clustered by user" \
    --labels=tier=bronze,owner=data-eng \
    YOUR_PROJECT_ID:cli_course.events

# 4. Verify
bq show --format=prettyjson YOUR_PROJECT_ID:cli_course.events

# 5. Load data
bq load --source_format=CSV --autodetect --replace \
  YOUR_PROJECT_ID:cli_course.events \
  gs://YOUR_PROJECT_ID-bq-course/staging/events_2026-01-01.csv

# 6. Query
bq query --use_legacy_sql=false --max_bytes_billed=1000000000 \
  "SELECT event_type, COUNT(*) AS n
   FROM \`YOUR_PROJECT_ID.cli_course.events\`
   WHERE event_date = DATE '2026-01-01'
   GROUP BY 1 ORDER BY 2 DESC"

# 7. Add a column
bq query --use_legacy_sql=false --quiet \
  "ALTER TABLE \`YOUR_PROJECT_ID.cli_course.events\`
   ADD COLUMN source_channel STRING DEFAULT 'unknown'"

# 8. Drop it
bq rm --table --force YOUR_PROJECT_ID:cli_course.events
```

---

## 💡 Production Notes

- **Store schema files in version control.** They are the source of truth for your table
  definitions, and they are reusable for load jobs.
- **`bq show --schema --format=json` exports a table's schema** — use it to regenerate schema
  files after a change.
- **Always set `--description` and `--labels`** at creation. Retrofitting them means finding every
  table later.
- **Use `bq query` for anything with nested schemas** — `bq mk` cannot express it.
- **Test DDL with `--dry_run` first** on a `CREATE OR REPLACE` to see the byte cost.

---

## 🔑 Key Takeaways

- `bq mk --dataset` for datasets, `bq mk --table` for flat tables, `bq query` for complex DDL.
- **Schema files are required for nested/repeated structures** and are worth version-controlling.
- Partitioning flags: `--time_partitioning_type`, `--time_partitioning_field`,
  `--require_partition_filter`.
- Clustering: `--clustering_fields`.
- External tables: `--source_format`, `--source_uris`, `--hive_partitioning_uri_prefix`.
- Always set `--description` and `--labels` at creation time.

---

## 📚 Practice Exercises

1. **Schema library.** Create a `schemas/` directory with schema files for six table types:
   flat, nested, repeated, array-of-struct, JSON, and geo. Verify each with `bq mk`.

2. **DDL via CLI vs SQL.** Write the same table definition twice — once with `bq mk`, once with
   `bq query` DDL. Document where each is better.

3. **Schema export.** Write a script that exports every table's schema in a project to JSON
   schema files, suitable for version control.

4. **Lifecycle script.** Write a complete bash script that creates a dataset, table, view, and
   materialized view, loads data, verifies it, and cleans up. Make it idempotent.

5. **Table type matrix.** Create one table of each type (managed, external, view, MV, snapshot,
   clustering, partitioned, unpartitioned) and produce a comparison table of their properties.

---

## 📖 Further Reading

- `bq mk` reference — https://cloud.google.com/bigquery/docs/reference/bq-cli-reference#bq_mk
- Table schemas — https://cloud.google.com/bigquery/docs/schemas
- BigQuery DDL — https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language
