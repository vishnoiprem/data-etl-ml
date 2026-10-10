---
l_id: L67
title: "Handle JSON (S3)"
duration: "7:00"
prereqs:
  - L66 (Loading from S3)
---

# L67 — Handle JSON (S3)

> **Section:** 9 — Loading from Azure
> **Duration:** 7:00

## Prereqs

- L66 — Loading from S3

## Key terms

- **`TYPE = JSON`** — file format setting for JSON files.
- **Path filter on a stage** — restrict the `COPY INTO` to
  files matching a prefix or pattern.
- **Unified raw table** — one `raw_orders` table that holds
  both Parquet and JSON rows, distinguishable by `filename`.

## Lecture

Section 8 covered Parquet; this lecture extends the same
S3 pipeline to JSON. The pattern is identical: another
stage, another `COPY INTO`, the same `raw_orders` `VARIANT`
table.

### Step 1 — verify the JSON file is in S3

```bash
aws s3 ls s3://pv-snowflake-course-2026/raw/orders/2026-10-01/ \
    --recursive --human-readable
```

Expected: `orders.json` and `orders.parquet`.

### Step 2 — create a JSON-format stage (or reuse)

The existing stage `stg_orders_s3` uses `ff_parquet`. Two
options:

- **Reuse the stage** with `FILE_FORMAT = (FORMAT_NAME =
  ff_json)` in the `COPY INTO` clause.
- **Create a dedicated stage** for JSON.

For clarity we use a dedicated stage:

```sql
CREATE OR REPLACE STAGE stg_orders_json_s3
    STORAGE_INTEGRATION = s3_orders_int
    URL = 's3://pv-snowflake-course-2026/raw/orders/'
    FILE_FORMAT = (FORMAT_NAME = ff_json)
    DIRECTORY = (ENABLE = TRUE);
```

### Step 3 — `COPY INTO` JSON

```sql
COPY INTO raw_orders (raw, filename, row_number)
FROM (
    SELECT
        $1                              AS raw,
        METADATA$FILENAME               AS filename,
        METADATA$FILE_ROW_NUMBER        AS row_number
    FROM @stg_orders_json_s3/2026-10-01/orders.json
)
FILE_FORMAT = (FORMAT_NAME = ff_json)
ON_ERROR    = CONTINUE;
```

The `@stg_orders_json_s3/2026-10-01/orders.json` form is a
**path filter on the stage** — the `COPY INTO` reads only
the file at that path. Useful for one-off loads.

### Step 4 — alternative: load a whole prefix

```sql
COPY INTO raw_orders (raw, filename, row_number)
FROM (
    SELECT $1, METADATA$FILENAME, METADATA$FILE_ROW_NUMBER
    FROM @stg_orders_json_s3
)
FILE_FORMAT = (FORMAT_NAME = ff_json)
ON_ERROR    = CONTINUE
PATTERN     = '.*orders.*[.]json';
```

`PATTERN` is a regex matched against the file name. Use it
when the prefix contains both Parquet and JSON files and
you only want the JSON.

### Step 5 — verify

```sql
SELECT
    filename,
    COUNT(*) AS n_rows
FROM raw_orders
GROUP BY filename;
```

Expected: one row per file (`orders.json`, `orders.parquet`)
with the correct row count each.

### Step 6 — handle missing JSON fields

The `orders.json` file might have orders missing the
`customer.email` field. Spot-check the impact:

```sql
SELECT
    COUNT(*)                                            AS total,
    COUNT(raw:customer.email::STRING)                   AS with_email,
    COUNT(*) - COUNT(raw:customer.email::STRING)        AS without_email
FROM raw_orders
WHERE filename LIKE '%orders.json';
```

`COUNT(raw:customer.email::STRING)` counts only the rows
where the cast is non-null. The difference is your "missing
email" count.

In production, a `WHERE raw:customer.email IS NULL` check
in the curated insert prevents the bad rows from leaking
downstream.

### Step 7 — incremental loads with the watermark

Combine the JSON path filter with the watermark pattern:

```sql
INSERT INTO curated_orders (order_id, order_ts, …)
SELECT
    raw:order_id::STRING,
    raw:order_ts::TIMESTAMP_LTZ,
    …
FROM raw_orders
WHERE loaded_at > (SELECT COALESCE(MAX(loaded_at), '1900-01-01'::TIMESTAMP_LTZ)
                   FROM curated_orders);
```

This loads only the rows that arrived after the last curated
insert — the production pattern for "ingest yesterday's
JSON drops" without re-parsing old files.

### Common JSON-on-S3 errors

- **`STRIP_OUTER_ARRAY` mismatch** — if the file is one big
  array `[{…}, {…}]`, set `STRIP_OUTER_ARRAY = TRUE` on the
  file format.
- **Path typo** — a missing colon (`raw:customer.email`)
  silently produces `NULL`. Always `LIMIT 5` after a
  `COPY INTO`.
- **Encoding** — UTF-8 is the default. If your JSON has
  non-UTF-8 bytes, set `IGNORE_UTF8_ERRORS = TRUE` on the
  file format (with caution).

## Hands-on

Run the JSON `COPY INTO`, then run the `GROUP BY filename`
verification. Confirm both `orders.json` and `orders.parquet`
are present in `raw_orders`.

## Quiz prep

- What does the path filter `@stage/2026-10-01/orders.json`
  do?
- How do you load only the JSON files from a mixed prefix?
- How do you count "missing email" rows in a JSON load?

## Key takeaways

- JSON and Parquet can share the same `raw_orders` table;
  distinguish them by `filename`.
- A **path filter** (`@stage/path`) or a **PATTERN** regex
  selects which files to load.
- A `COUNT(col::TYPE)` counts only the non-null casts; the
  difference from `COUNT(*)` is the missing-field count.
- The watermark pattern handles incremental JSON loads
  cleanly.

## What's next

In **L68 — Sign up for free trial (Azure)** we set up an
Azure account so we can switch from S3 to **Azure Blob
Storage** for the rest of the section.