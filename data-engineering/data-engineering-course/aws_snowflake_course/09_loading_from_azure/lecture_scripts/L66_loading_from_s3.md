---
l_id: L66
title: "Loading from S3"
duration: "7:00"
prereqs:
  - L65 (Creating integration object)
---

# L66 — Loading from S3

> **Section:** 9 — Loading from Azure
> **Duration:** 7:00

## Prereqs

- L65 — Creating integration object

## Key terms

- **`COPY INTO … FROM @external_stage`** — the canonical
  pattern for loading from S3 / Azure / GCS via a storage
  integration.
- **`STORAGE_INTEGRATION`** — the bridge object created in
  L65. The `COPY INTO` references it transparently through
  the stage.
- **End-to-end pipeline** — the full path:
  `S3 bucket → stage → raw table → curated table → BI`.

## Lecture

In L65 we created the storage integration. This lecture
exercises the **end-to-end** load: `COPY INTO` from the
S3 stage into a raw Parquet table, parse the JSON
sidecar, and verify the result counts match the source.

### Step 1 — set up the warehouse and database

```sql
USE WAREHOUSE loading_wh;
USE DATABASE demo_db;
USE SCHEMA json_demo;
```

### Step 2 — `COPY INTO` the Parquet file

```sql
CREATE OR REPLACE TABLE raw_orders_parquet (
    raw         VARIANT,
    filename    VARCHAR   AS METADATA$FILENAME::VARCHAR,
    row_number  NUMBER    AS METADATA$FILE_ROW_NUMBER,
    loaded_at   TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

COPY INTO raw_orders_parquet (raw, filename, row_number)
FROM (
    SELECT
        $1                          AS raw,
        METADATA$FILENAME           AS filename,
        METADATA$FILE_ROW_NUMBER    AS row_number
    FROM @stg_orders_s3
)
FILE_FORMAT = (FORMAT_NAME = ff_parquet)
ON_ERROR    = CONTINUE;
```

This is the same statement from L51, with **one** difference:
the stage is `@stg_orders_s3` (an external S3 stage), not
`@stg_orders_parquet` (an internal stage). The `COPY INTO`
syntax doesn't change; Snowflake resolves the credentials
from the storage integration.

### Step 3 — verify the row count

```sql
SELECT
    COUNT(*)        AS n_rows,
    COUNT(DISTINCT filename) AS n_files
FROM raw_orders_parquet;
```

Expected: `n_rows` matches the number of rows in the source
Parquet file; `n_files` is 1 (or 2 if both Parquet and JSON
were loaded).

### Step 4 — peek at the data

```sql
SELECT
    raw:order_id::STRING                       AS order_id,
    raw:customer.name::STRING                  AS customer_name,
    raw:total::NUMBER(10, 2)                   AS total,
    filename,
    loaded_at
FROM raw_orders_parquet
ORDER BY loaded_at DESC
LIMIT 5;
```

The `filename` column shows the S3 path:
`s3://pv-snowflake-course-2026/raw/orders/2026-10-01/orders.parquet`.

### Step 5 — check load history

```sql
SELECT
    file_name,
    row_count,
    row_parsed,
    error_count,
    first_load_time
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
    TABLE_NAME => 'raw_orders_parquet',
    START_TIME => DATEADD('hour', -1, CURRENT_TIMESTAMP())
));
```

If `error_count > 0`, the most common cause is a Parquet
schema mismatch — e.g. a column that was `INT64` in the file
but you tried to `::STRING` it.

### Step 6 — re-run for idempotency

```sql
COPY INTO raw_orders_parquet (raw, filename, row_number)
FROM (
    SELECT $1, METADATA$FILENAME, METADATA$FILE_ROW_NUMBER
    FROM @stg_orders_s3
)
FILE_FORMAT = (FORMAT_NAME = ff_parquet);
-- "0 files processed, 0 rows loaded"
```

`FORCE = FALSE` (default) makes the second run a no-op. To
re-load after a schema change, use `FORCE = TRUE` or
`TRUNCATE` the table first.

### Pattern: dual ingest (Parquet + JSON)

If you maintain both formats, define two stages:

```sql
CREATE OR REPLACE STAGE stg_orders_json_s3
    STORAGE_INTEGRATION = s3_orders_int
    URL = 's3://pv-snowflake-course-2026/raw/orders/'
    FILE_FORMAT = (FORMAT_NAME = ff_json);
```

Then `COPY INTO` from the JSON stage into a separate raw
table. In production, the two are usually not both loaded
— pick one as the source of truth.

### Cost tracking for S3 loads

The cost components of an S3 → Snowflake load:

| Component | Billed by | Approx cost |
|---|---|---|
| S3 storage | AWS | ~$0.023/GB/mo |
| S3 GET requests | AWS | ~$0.0004 per 1k |
| Snowflake compute (loading_wh) | Snowflake | per-second credits |
| Result cache fills | Snowflake | free |

For a 1 GB daily load, the S3-side cost is negligible;
the loading warehouse dominates.

### Operational checklist

- [ ] Storage integration exists and is enabled.
- [ ] External stage lists at least one file.
- [ ] `COPY INTO` returns the expected row count.
- [ ] `COPY_HISTORY` shows zero errors.
- [ ] Spot-check 5 rows in the raw table.
- [ ] Repeat `COPY INTO` — should be a no-op.

## Hands-on

Run the `COPY INTO`, then run the spot-check `SELECT`.
Compare your output with the screenshot in this lecture;
if any column is `NULL`, the JSON path is wrong.

## Quiz prep

- How is the `COPY INTO` syntax different for an internal vs
  external stage?
- What does `FORCE = FALSE` (default) do on a re-run?
- Where do you find the load history?

## Key takeaways

- The `COPY INTO` syntax is identical for internal and
  external stages; only the **stage** changes.
- The storage integration handles the AWS credentials
  transparently.
- Always verify with `COPY_HISTORY` and a spot-check
  `SELECT`.
- The re-run is a no-op thanks to file-load tracking.

## What's next

In **L67 — Handle JSON (S3)** we extend the pipeline to
JSON files in the same S3 prefix and build a unified
`raw_orders` table that holds both formats.