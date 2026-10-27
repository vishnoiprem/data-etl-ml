# BigQuery Cheat Sheet

> One page per topic. Keep it open in a tab.

---

## `bq` CLI — essentials

```bash
# Datasets
bq mk --dataset --location=US YOUR_PROJECT_ID:curated
bq ls --project_id=YOUR_PROJECT_ID --format="table(datasetId,location,lastModifiedTime)"
bq rm --dataset --delete_contents YOUR_PROJECT_ID:scratch
bq show --format=prettyjson YOUR_PROJECT_ID:curated

# Tables
bq mk --table --schema_file=schemas/orders.json YOUR_PROJECT_ID:curated.orders
bq ls --project_id=YOUR_PROJECT_ID --max_results=50
bq show --format=prettyjson YOUR_PROJECT_ID:curated.orders
bq rm --table --force YOUR_PROJECT_ID:curated.orders
bq head --max_rows=10 YOUR_PROJECT_ID:curated.orders

# Query
bq query --use_legacy_sql=false 'SELECT 1'
bq query --use_legacy_sql=false --dry_run 'SELECT ...'      # free cost check
bq query --use_legacy_sql=false --max_bytes_billed=1000000000 'SELECT ...'
bq query --use_legacy_sql=false --format=json 'SELECT ...'
bq query --use_legacy_sql=false --format="value(col)" 'SELECT ...'
bq query --use_legacy_sql=false --quiet 'SELECT ...'         # no job summary
bq query --use_legacy_sql=false --job_id=my_job_20260115 'SELECT ...'  # exactly-once

# Load
bq load --source_format=CSV --schema_file=s.json --skip_leading_rows=1 \
  --replace YOUR_PROJECT_ID:curated.orders gs://bucket/file.csv
bq load --source_format=PARQUET --replace \
  YOUR_PROJECT_ID:curated.orders "gs://bucket/files_*.parquet"
bq load --source_format=CSV --schema_file=s.json \
  YOUR_PROJECT_ID:curated.orders$20260115 gs://bucket/day.csv   # idempotent

# Extract / Export
bq extract --destination_format=CSV --compression=GZIP \
  YOUR_PROJECT_ID:curated.orders "gs://bucket/out_*.csv"

# Jobs
bq ls --project_id=YOUR_PROJECT_ID --jobs --max_results=20
bq show --format=prettyjson --job_id=bquxjob_abc123
bq cancel --job_id=bquxjob_abc123

# Undelete
bq undelete --dataset YOUR_PROJECT_ID:curated
bq undelete --table YOUR_PROJECT_ID:curated.orders
```

---

## SQL — DDL

```sql
-- Dataset
CREATE SCHEMA IF NOT EXISTS `p.ds`
OPTIONS(location="US", labels=[("tier","raw")]);

-- Table
CREATE OR REPLACE TABLE `p.ds.t` (
  id STRING NOT NULL,
  amount NUMERIC,
  items ARRAY<STRUCT<sku STRING, qty INT64>>,
  meta JSON
)
PARTITION BY order_date
CLUSTER BY customer_id, status
OPTIONS(
  description="...",
  require_partition_filter=TRUE,
  partition_expiration_days=730,
  labels=[("tier","silver")]
);

-- View
CREATE OR REPLACE VIEW `p.ds.v` AS SELECT ...;

-- Materialized view
CREATE MATERIALIZED VIEW `p.ds.mv`
PARTITION BY order_date
OPTIONS(enable_refresh=TRUE, max_staleness=INTERVAL 1 HOUR) AS
SELECT ... FROM `p.ds.t` GROUP BY 1;

-- Snapshot
CREATE OR REPLACE SNAPSHOT TABLE `p.ds.snap` AS
SELECT * FROM `p.ds.t` FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR);

-- External table
CREATE EXTERNAL TABLE `p.ds.ext`
WITH FORMAT OPTIONS(format='PARQUET', uris=['gs://b/*.parquet']);

-- Alter
ALTER TABLE `p.ds.t` ADD COLUMN c STRING DEFAULT 'x';
ALTER TABLE `p.ds.t` DROP COLUMN c;
ALTER TABLE `p.ds.t` SET OPTIONS(description='...', partition_expiration_days=90);
ALTER TABLE `p.ds.t` SET OPTIONS(clustering_fields=['a','b']);
ALTER TABLE `p.ds.t` ADD PARTITION DATE '20260115';
ALTER TABLE `p.ds.t` DROP PARTITION DATE '20260115';
```

---

## SQL — DML

```sql
INSERT INTO `p.ds.t` (a, b) VALUES (1, 'x');

UPDATE `p.ds.t` SET b = 'y' WHERE order_date = DATE '2026-01-15';

DELETE FROM `p.ds.t` WHERE order_date = DATE '2026-01-15';

MERGE `p.ds.t` AS t
USING `p.src.s` AS s
ON t.id = s.id AND t.order_date = s.order_date
WHEN MATCHED THEN UPDATE SET t.v = s.v
WHEN NOT MATCHED THEN INSERT (id, order_date, v) VALUES (s.id, s.order_date, s.v);

TRUNCATE TABLE `p.ds.t`;

-- Replace a whole partition (cheaper than UPDATE)
CREATE OR REPLACE TABLE `p.ds.t$20260115` AS SELECT * FROM `p.ds.t$20260115`;
```

---

## SQL — query patterns

```sql
-- Partition filters (pruning)
WHERE order_date = DATE '2026-01-15'
WHERE order_date BETWEEN DATE '2026-01-01' AND DATE '2026-01-31'
WHERE order_date >= DATE '2026-01-01' AND order_date < DATE '2026-02-01'  -- best

-- Partition decorators
`p.ds.t$20260115`
`p.ds.t$20260101:20260131`
`p.ds.t$*`

-- Wildcards
`p.ds.t_2026_01_1?`     -- one char
`p.ds.t_2026_*`         -- any chars
_TABLE_ID              -- pseudo-column

-- Nested
customer.name
UNNEST(line_items) AS item
JSON_VALUE(meta, '$.channel')
JSON_QUERY(meta, '$.items')
JSON_EXTRACT_SCALAR(meta, '$.channel')

-- Time travel
FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 HOUR)

-- Window functions
ROW_NUMBER() OVER (PARTITION BY c ORDER BY t DESC)
SUM(x) OVER (ORDER BY d RANGE BETWEEN INTERVAL 6 DAY PRECEDING AND CURRENT ROW)
```

---

## Python client

```python
from google.cloud import bigquery

client = bigquery.Client(project="YOUR_PROJECT_ID")

# Query
job = client.query(sql)
rows = job.result()
df = job.to_dataframe()
bytes_processed = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True)).total_bytes_processed

# Parameters
job_config = bigquery.QueryJobConfig(
    query_parameters=[bigquery.ScalarQueryParameter("d", "DATE", "2026-01-15")],
    maximum_bytes_billed=10 * 1024**4,
    labels={"env": "dev"},
)
client.query(sql, job_config=job_config).result()

# Dataset
ds = bigquery.Dataset("p.curated", location="US", description="...",
                       labels={"tier": "curated"})
client.create_dataset(ds, exists_ok=True)

# Table
schema = [bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
           bigquery.SchemaField("nested", "RECORD", mode="REPEATED",
                                 fields=[bigquery.SchemaField("x", "STRING")])]
t = bigquery.Table("p.curated.t", schema=schema)
t.time_partitioning = bigquery.TimePartitioning(
    type_=bigquery.TimePartitioningType.DAY, field="order_date")
t.clustering_fields = ["customer_id"]
client.create_table(t, exists_ok=True)

# Update
t = client.get_table("p.curated.t")
t.description = "new"
client.update_table(t, update_mode="update_fields")

# Load
job = client.load_table_from_uri(
    ["gs://b/*.parquet"], "p.curated.t",
    job_config=bigquery.LoadJobConfig(source_format="PARQUET",
                                       write_disposition="WRITE_APPEND"))
job.result()   # ALWAYS block on .result()

# Streaming
errors = client.insert_rows_json(client.dataset("raw").table("events"), rows)
```

---

## Pricing quick reference

| Item | Price |
|------|-------|
| Storage (active logical) | $0.02 / GiB / month |
| Storage (long-term logical) | $0.01 / GiB / month |
| Storage (capacity-optimized active) | $0.04 / GiB / month |
| On-demand queries | $6.25 / TiB scanned |
| Standard slot | $0.04 / slot-hour |
| Enterprise slot | $0.06 / slot-hour |
| DML modified | $0.01 / GiB |
| Streaming inserts (after 1 GB/day/table) | $0.01 / 200 MB |
| Free tier | 10 GB storage, 1 TiB queries/month, 1 GB/day streaming |

---

## Performance rules

| Rule | Why |
|------|-----|
| Always filter the partition column | Skips 99% of the data |
| `require_partition_filter = TRUE` | Turns a costly scan into an error |
| Never `SELECT *` | Column pruning is free |
| Cluster on frequently-filtered columns | Up to 70% fewer bytes |
| Materialize repeated aggregations | Pre-aggregated reads |
| `maximum_bytes_billed` on every job | Fails fast instead of billing |
| `REPLACE PARTITION` over `UPDATE` | Rewrites one partition, not the table |
| Parquet over CSV | 3–10× smaller, faster to load and query |
| Dry run every non-trivial query | Free, exact cost |

---

## Key limits

| Limit | Value |
|-------|-------|
| Partitions per table | 10,000 |
| Clustering columns | 4 |
| Materialized view base tables | 1 |
| Streaming rows per request | 1,000 |
| Streaming request size | 10 MB |
| Interactive query timeout | 6 hours |
| Max bytes per query | 5 TiB |
| Time travel window | 7 days |
| Undelete window | 30 days |
| Long-term storage transition | After 30 days |

---

## Common errors

| Error | Fix |
|-------|-----|
| `Not found: Table` | Check the dataset's region; use a fully qualified name |
| `Exceeded maximum bytes billed` | Add a partition filter |
| `Syntax error: Unexpected keyword` | GoogleSQL, not legacy SQL; use backticks |
| `Table name missing dataset` | Fully qualify `project.dataset.table` |
| `Access Denied` | Grant `roles/bigquery.jobUser` |
| `Duplicate name` | Use `IF NOT EXISTS` / `exists_ok=True` |
| `SchemaMismatchError` | Check `job.errors`; relax the schema |
| `Invalid schema: Field is_repeated` | Use `RECORD` + `REPEATED` |
| `Streaming buffer ... not cached` | Expected — the buffer is never cached |
