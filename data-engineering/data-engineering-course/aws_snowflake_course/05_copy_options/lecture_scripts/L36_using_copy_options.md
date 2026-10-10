---
l_id: L36
title: Using the copy options
duration: "8:00"
prereqs: ["L35"]
downloads: []
---

# L36 — Using the Copy Options

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 5 — Copy Options
> **Duration:** ~8:00

## Prereqs

L35 — VALIDATION_MODE. This lecture combines the options
we've covered so far in real-world load patterns.

## Key terms

- **`PATTERN`** — a regex filter on file names. Only matching
  files are loaded.
- **`PURGE`** — delete files from the stage after a successful
  load. Useful for "move and load" patterns.
- **`FORCE`** — load files even if they were loaded before.

## Lecture

So far we've covered `FILE_FORMAT`, `ON_ERROR`, `FORCE`,
`PURGE`, `PATTERN`, `VALIDATION_MODE`, and column-level
transforms. This lecture shows how to combine them in
production-grade load patterns.

### Pattern 1 — Daily batch with file pattern

```sql
COPY INTO ORDERS
  FROM @demo_stage/landing/
  PATTERN = '.*orders_[0-9]{4}-[0-9]{2}-[0-9]{2}\.csv$'
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  ON_ERROR = 'ABORT_STATEMENT';
```

The `PATTERN` regex matches only files named like
`orders_2024-01-15.csv`, ignoring everything else in the
stage.

### Pattern 2 — Move-and-load with PURGE

```sql
COPY INTO ORDERS
  FROM @demo_stage/staging/orders.csv
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  ON_ERROR = 'ABORT_STATEMENT'
  PURGE = TRUE;
```

After the load succeeds, the file is deleted from the stage.
Useful when the stage is a transient landing zone.

> **Warning.** `PURGE` deletes files **permanently**. Only use
> it when the stage is ephemeral or you have a backup.

### Pattern 3 — Force-reload after a fix

```sql
-- Schema changed; need to reload everything
TRUNCATE TABLE ORDERS;
COPY INTO ORDERS
  FROM @demo_stage
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  ON_ERROR = 'ABORT_STATEMENT'
  FORCE = TRUE;
```

`FORCE = TRUE` bypasses load history. Combined with
`TRUNCATE` (or a recreate), it gives you a clean reload.

### Pattern 4 — Multi-source union

```sql
COPY INTO ORDERS
  FROM (
    SELECT $1::NUMBER, $2::NUMBER, $3::DATE, $4::NUMBER(10,2), $5::VARCHAR
    FROM @demo_stage/orders/*.csv
    UNION ALL
    SELECT $1::NUMBER, $2::NUMBER, $3::DATE, $4::NUMBER(10,2), $5::VARCHAR
    FROM @s3_stage/orders_legacy/*.csv
  )
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  ON_ERROR = 'ABORT_STATEMENT';
```

The `SELECT ... FROM @stage1 UNION ALL SELECT ... FROM @stage2`
form lets you combine multiple sources in one load.

### Pattern 5 — Conditional column transform

```sql
COPY INTO ORDERS
  FROM (
    SELECT
      $1::NUMBER AS order_id,
      $2::NUMBER AS customer_id,
      CASE
        WHEN $3 = '' THEN NULL
        ELSE $3::DATE
      END AS order_date,
      $4::NUMBER(10,2) AS amount,
      UPPER(TRIM($5)) AS status
    FROM @demo_stage/orders.csv
  )
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  ON_ERROR = 'ABORT_STATEMENT';
```

Handle empty strings by converting them to NULL.

### Pattern 6 — Load + post-process in a task

A common pattern is to use a `COPY INTO` in a Snowflake task
(scheduled query):

```sql
-- Inside a CREATE TASK body
COPY INTO ORDERS
  FROM @demo_stage/landing/
  PATTERN = '.*orders_.*\.csv$'
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  ON_ERROR = 'ABORT_STATEMENT';

-- Then run downstream transformations
MERGE INTO ORDERS_CLEAN
USING ORDERS
  ON ORDERS.order_id = ORDERS_CLEAN.order_id
WHEN MATCHED THEN UPDATE SET ...
WHEN NOT MATCHED THEN INSERT ...;
```

We cover tasks in section 20.

## Hands-on

```sql
-- Force-reload a single file
COPY INTO ORDERS
  FROM @demo_stage/orders.csv
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  ON_ERROR = 'ABORT_STATEMENT'
  FORCE = TRUE;

-- Verify load history shows it
SELECT file_name, row_count, status, last_load_time
FROM DEMO.INFORMATION_SCHEMA.LOAD_HISTORY
WHERE table_name = 'ORDERS'
ORDER BY last_load_time DESC
LIMIT 5;
```

## Quiz prep

- What does `PURGE = TRUE` do? (Deletes files from the stage
  after a successful load)
- What does `PATTERN` match against? (The file name in the
  stage)
- How do you force a re-load of already-loaded files?
  (`FORCE = TRUE`)

## What's next

Next up is **L37 — Working with rejected records**, where
we cover `VALIDATE` and how to recover from partial failures.
