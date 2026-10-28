# 6.5 — `bq` Loading Data & Exclusive Operations

> **Section 6 · Command Line Interface · Lecture 6.5 · 5:51**

## 🎯 What you will learn

- `bq load` in all its forms — CSV, JSON, Parquet, Avro
- `bq extract` vs `EXPORT DATA`
- `bq insert` for streaming
- Job management for long-running operations

---

## 🧠 Concept

Loading data into BigQuery is the entry point to every pipeline. The CLI gives you full control
over format, schema, and error handling.

---

## 🧠 `bq load` — bulk ingestion

```bash
bq load [flags] DESTINATION_TABLE SOURCE
```

### The core flags

| Flag | Purpose |
|------|---------|
| `--source_format` | `CSV`, `NEWLINE_DELIMITED_JSON`, `AVRO`, `PARQUET`, `ORC` |
| `--schema_file` | JSON schema file (recommended) |
| `--autodetect` | Infer the schema (use sparingly) |
| `--skip_leading_rows` | Skip header rows (CSV) |
| `--field_delimiter` | CSV delimiter |
| `--max_bad_records` | Skip up to N bad rows |
| `--replace` | Truncate and replace the destination |
| `--append` | Append to the destination |
| `--create_disposition` | `CREATE_IF_NEEDED` / `CREATE_NEVER` |
| `--write_disposition` | `WRITE_APPEND` / `WRITE_TRUNCATE` / `WRITE_EMPTY` |
| `--time_partitioning_type` | Partition the new table |
| `--time_partitioning_field` | Partition field |
| `--clustering_fields` | Cluster the new table |
| `--require_partition_filter` | Require partition filters on the new table |
| `--project_id` | Project |
| `--quiet` | Suppress job output |

### CSV loading

```bash
# With an explicit schema
bq load \
  --source_format=CSV \
  --schema_file=schemas/orders_schema.json \
  --skip_leading_rows=1 \
  --replace \
  YOUR_PROJECT_ID:curated.orders \
  gs://YOUR_PROJECT_ID-bq-course/staging/orders_2026-01-01.csv

# With auto-detection
bq load \
  --source_format=CSV \
  --autodetect \
  --skip_leading_rows=1 \
  --replace \
  YOUR_PROJECT_ID:curated.orders \
  gs://YOUR_PROJECT_ID-bq-course/staging/orders_2026-01-01.csv

# With schema relaxation
bq load \
  --source_format=CSV \
  --autodetect \
  --schema_update_options=ALLOW_FIELD_ADDITION,ALLOW_FIELD_RELAXATION \
  --ignore_unknown_values \
  --max_bad_records=10 \
  YOUR_PROJECT_ID:curated.orders \
  gs://YOUR_PROJECT_ID-bq-course/staging/orders_2026-01-01.csv
```

### Newline-delimited JSON

```bash
bq load \
  --source_format=NEWLINE_DELIMITED_JSON \
  --schema_file=schemas/events_schema.json \
  --replace \
  YOUR_PROJECT_ID:raw.events \
  gs://YOUR_PROJECT_ID-bq-course/staging/events.ndjson
```

### Parquet and Avro

```bash
# Parquet — the fastest path, no parsing
bq load \
  --source_format=PARQUET \
  --replace \
  YOUR_PROJECT_ID:curated.events \
  gs://YOUR_PROJECT_ID-bq-course/staging/events_*.parquet

# Avro
bq load \
  --source_format=AVRO \
  --replace \
  YOUR_PROJECT_ID:curated.events \
  gs://YOUR_PROJECT_ID-bq-course/staging/events.avro
```

💡 **Parquet and Avro load fastest** because the schema and structure are already in the file —
no parsing, no detection.

### Loading from a local file

```bash
bq load --source_format=CSV --autodetect --replace \
  YOUR_PROJECT_ID:curated.orders ./local_orders.csv
```

### Loading a wildcard of files

```bash
# All files in one load job
bq load \
  --source_format=PARQUET \
  --replace \
  YOUR_PROJECT_ID:curated.events \
  "gs://YOUR_PROJECT_ID-bq-course/staging/events_*.parquet"
```

### Loading into a partition

```bash
# Idempotent daily load — replaces only that day's partition
bq load \
  --source_format=CSV \
  --schema_file=schemas/orders_schema.json \
  --skip_leading_rows=1 \
  YOUR_PROJECT_ID:curated.orders$20260115 \
  gs://YOUR_PROJECT_ID-bq-course/staging/orders_2026-01-15.csv
```

💡 **This is the correct pattern for daily incremental loads.** Re-running replaces the same
partition rather than duplicating rows.

---

## 🧠 `bq extract` — exporting a table

```bash
# Extract to CSV
bq extract \
  --destination_format=CSV \
  --compression=GZIP \
  YOUR_PROJECT_ID:curated.orders \
  gs://YOUR_PROJECT_ID-bq-course/exports/orders_*.csv

# Extract to Parquet
bq extract \
  --destination_format=PARQUET \
  YOUR_PROJECT_ID:curated.orders \
  gs://YOUR_PROJECT_ID-bq-course/exports/orders_*.parquet
```

### `bq extract` vs `EXPORT DATA`

| | `bq extract` | `EXPORT DATA` |
|---|---|---|
| Mechanism | Copy job | Query job |
| Cost | Storage only | Query + storage |
| Parallelism | Limited | ✅ High (up to 100k files) |
| Compressed output | ✅ | ✅ |
| Multiple formats | CSV, JSON, Avro, Parquet | CSV, JSON, Avro, Parquet, ORC |
| Filter/transform | ❌ | ✅ |
| Can write to a table | ❌ | ❌ |

💡 **Prefer `EXPORT DATA`** for anything beyond a trivial table. It is a query, so you can filter
and transform, and it parallelizes far better.

```sql
-- EXPORT DATA with filtering and partitioning of the output
EXPORT DATA OPTIONS(
  uri = 'gs://YOUR_PROJECT_ID-bq-course/exports/orders_*.csv',
  format = 'CSV',
  overwrite = true
) AS
SELECT order_date, customer_id, total_amount
FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY);
```

---

## 🧠 `bq insert` — streaming inserts

```bash
# Insert a single row
bq insert --use_legacy_sql=false YOUR_PROJECT_ID:raw.events \
  '{"event_id": "e001", "user_id": "u001", "event_type": "click", "event_ts": "2026-01-01T10:00:00Z"}'

# Insert from a file
bq insert --use_legacy_sql=false YOUR_PROJECT_ID:raw.events < events.json

# Insert with a schema
bq insert --use_legacy_sql=false --schema_file=schemas/events_schema.json \
  YOUR_PROJECT_ID:raw.events < events.json
```

```python
# The Python equivalent — much faster for bulk streaming
from google.cloud import bigquery

client = bigquery.Client()
table = client.dataset("raw").table("events")

rows = [
    {"event_id": f"e{i:06d}", "user_id": "u001", "event_type": "click",
     "event_ts": "2026-01-01T10:00:00Z"}
    for i in range(1000)
]

errors = client.insert_rows_json(table, rows)
if errors:
    print(f"Failed rows: {errors}")
```

💡 **Streaming inserts have a specific cost profile:**
- The first 1 GB of data streamed into a table per day is **free**
- After that, $0.01 per 200 MB
- Streaming buffer data is billed at the **active storage** rate
- Streaming inserts are **not cached** — a query against the streaming buffer never hits the cache

⚠️ **Do not stream-insert millions of rows one at a time.** Use the batch API
(`insert_rows_json` with 500 rows per call) or, better, load in bulk.

---

## 🧠 Job management for long operations

```bash
# List jobs
bq ls --project_id=YOUR_PROJECT_ID --jobs --max_results=20 \
    --format="table(jobId,jobType,state,creationTime)"

# Watch a job
bq show --format=prettyjson --job_id=bquxjob_abc123

# Cancel a running job
bq cancel --job_id=bquxjob_abc123

# Show only failed jobs
bq ls --project_id=YOUR_PROJECT_ID --jobs --state=DONE \
    --format=json | jq -r '.[] | select(.status.errorResult != null) | .jobId'
```

---

## 🛠️ Hands-On: A Complete Load Pipeline

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-YOUR_PROJECT_ID}"
BUCKET="gs://${PROJECT_ID}-bq-course"
DATASET="curated"
DATE="${1:-$(date -u +%Y%m%d)}"

echo "=== Loading ${DATE} ==="

# 1. Verify the source exists
if ! gcloud storage ls "${BUCKET}/staging/orders_${DATE}.csv" >/dev/null 2>&1; then
    echo "ERROR: source file not found" >&2
    exit 1
fi

# 2. Dry run the load cost
bq load --source_format=CSV --schema_file=schemas/orders_schema.json \
    --skip_leading_rows=1 --dry_run \
    "${PROJECT_ID}:${DATASET}.orders" \
    "${BUCKET}/staging/orders_${DATE}.csv"

# 3. Load into the specific partition (idempotent)
bq load \
    --source_format=CSV \
    --schema_file=schemas/orders_schema.json \
    --skip_leading_rows=1 \
    --max_bad_records=100 \
    --quiet \
    "${PROJECT_ID}:${DATASET}.orders\$${DATE}" \
    "${BUCKET}/staging/orders_${DATE}.csv"

# 4. Verify
ROWS=$(bq query --use_legacy_sql=false --quiet --format="value(f0_)" \
    "SELECT COUNT(*) FROM \`${PROJECT_ID}.${DATASET}.orders\` WHERE order_date = DATE '${DATE:0:4}-${DATE:4:2}-${DATE:6:2}'")

echo "Loaded ${ROWS} rows for ${DATE}"
```

---

## 💡 Production Notes

- **Use `--schema_file` over `--autodetect` in production.** Auto-detection can promote types
  unexpectedly and silently change your schema.
- **Load into a specific partition** for daily jobs — it makes the load idempotent.
- **`--max_bad_records` prevents one corrupt row from failing a daily pipeline.** Set it to a
  small non-zero number and monitor the job log for skipped rows.
- **`--replace` on a partitioned table truncates the whole table.** This is the most common
  `bq load` bug.
- **Use `EXPORT DATA` rather than `bq extract`** for anything with filters or large row counts.
- **Streaming inserts are free for the first 1 GB/day per table** — use that for low-volume
  operational data.

---

## 🔑 Key Takeaways

- `bq load` handles CSV, NDJSON, Parquet, Avro, and ORC.
- **Prefer `--schema_file` over `--autodetect`** in production.
- **Load into a specific partition (`table$YYYYMMDD`) for idempotent daily jobs.**
- `--replace` truncates the entire table, not one partition.
- `EXPORT DATA` beats `bq extract` — it filters, transforms, and parallelizes.
- Streaming inserts: first 1 GB/day/table is free; use the batch API, not row-by-row.

---

## 📚 Practice Exercises

1. **Load matrix.** Load the same dataset into BigQuery in all four formats (CSV, NDJSON, Parquet,
   Avro). Measure load time, file size, and query cost. Write the recommendation.

2. **Idempotent loader.** Write a `bq load` wrapper that is fully idempotent: re-running it never
   duplicates data. Support both full-refresh and incremental modes.

3. **Error handling.** Write a loader that handles a corrupt source file: detect it, skip bad
   rows, report them to a dead-letter table, and alert. Include the verification query.

4. **Export design.** For an archival requirement (7 years of daily exports to Cloud Storage,
   Parquet, partitioned by date), write the export job and the lifecycle policy. Include the
   cost estimate.

5. **Streaming vs loading.** Compare streaming inserts and batch loads for an event pipeline
   producing 50M events/day. Include latency, cost, and operational complexity. Write the
   recommendation.

---

## 📖 Further Reading

- `bq load` — https://cloud.google.com/bigquery/docs/reference/bq-cli-reference#bq_load
- `bq insert` — https://cloud.google.com/bigquery/docs/reference/bq-cli-reference#bq_insert
- `EXPORT DATA` — https://cloud.google.com/bigquery/docs/reference/standard-sql/export-statements
- Streaming inserts — https://cloud.google.com/bigquery/streaming-data-into-bigquery
