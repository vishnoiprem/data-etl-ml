---
l_id: L28
title: COPY command
duration: "10:00"
prereqs: ["L27"]
downloads: []
---

# L28 — COPY Command

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 4 — Loading Data
> **Duration:** ~10:00

## Prereqs

L27 — Creating stage. You should have a stage with a file
uploaded and a target table created.

## Key terms

- **`COPY INTO`** — the bulk-load command. Reads from a stage
  and inserts into a table.
- **`FROM @<stage>`** — the source. Can be a sub-path or a
  list of files.
- **`FILE_FORMAT`** — either an inline object
  (`FILE_FORMAT = (TYPE = CSV ...)`) or a named file format
  object.
- **`ON_ERROR`** — what to do on row errors. `ABORT_STATEMENT`
  (default), `CONTINUE`, or `SKIP_FILE`.
- **`FORCE`** — load files even if they were loaded before.
  Defaults to `FALSE` (skip already-loaded files).

## Lecture

`COPY INTO` is the workhorse command for bulk loading. This
lecture covers the full syntax, the most useful options, and
the load history that makes it idempotent.

### The canonical `COPY INTO`

```sql
COPY INTO DEMO.RAW.ORDERS
  FROM @DEMO.RAW.demo_stage
  FILE_FORMAT = (TYPE = CSV
                 FIELD_OPTIONALLY_ENCLOSED_BY = '"'
                 SKIP_HEADER = 1)
  ON_ERROR = 'ABORT_STATEMENT';
```

Components:

- **Target** — `DEMO.RAW.ORDERS` (or just `ORDERS` with the
  schema set).
- **Source** — `@DEMO.RAW.demo_stage` (the stage from L27).
- **FILE_FORMAT** — inline or named. We'll cover named file
  formats in section 5.
- **ON_ERROR** — behavior on row-level errors:
  - `ABORT_STATEMENT` (default) — entire load fails, no rows
    committed.
  - `CONTINUE` — load valid rows, log the rest.
  - `SKIP_FILE` — if any row in a file is bad, skip the file.

### Loading a sub-path

```sql
-- Only load January 2024 files
COPY INTO ORDERS
  FROM @demo_stage/2024/01/
  FILE_FORMAT = (TYPE = CSV SKIP_HEADER = 1);
```

### Loading a specific file list

```sql
COPY INTO ORDERS
  FROM (
    SELECT $1, $2, $3, $4, $5
    FROM @demo_stage/orders_2024-01-15.csv
  )
  FILE_FORMAT = (TYPE = CSV);
```

The `FROM (SELECT ...)` form lets you use a sub-query
against the stage, with column references like `$1`, `$2`.

### Load history — exactly-once semantics

`COPY INTO` records every file it loads. By default, a second
load of the same file is a no-op:

```sql
-- First load: 1000 rows loaded
COPY INTO ORDERS FROM @demo_stage FILE_FORMAT = (TYPE = CSV);

-- Second load: 0 rows loaded (already loaded)
COPY INTO ORDERS FROM @demo_stage FILE_FORMAT = (TYPE = CSV);

-- Force reload: 1000 rows loaded again
COPY INTO ORDERS FROM @demo_stage FILE_FORMAT = (TYPE = CSV) FORCE = TRUE;
```

The load history is held for **64 days** by default. After
that, the same file is considered "new" again.

### Inspecting load history

```sql
SELECT file_name,
       row_count,
       row_parsed,
       file_size,
       status,
       error_count,
       last_load_time
FROM DEMO.INFORMATION_SCHEMA.LOAD_HISTORY
WHERE schema_name = 'RAW'
  AND table_name = 'ORDERS'
ORDER BY last_load_time DESC;
```

`LOAD_HISTORY` is your debugging tool for failed loads.

### Common options

| Option | Default | What it does |
|---|---|---|
| `ON_ERROR` | `ABORT_STATEMENT` | Behavior on row errors |
| `FORCE` | `FALSE` | Reload already-loaded files |
| `PURGE` | `FALSE` | Delete files from stage after load |
| `PATTERN` | (none) | Regex filter on file names |
| `SIZE_LIMIT` | (none) | Cap on total bytes loaded per statement |
| `RETURN_FAILED_ONLY` | `FALSE` | Return only failed rows in the result |

We cover each in section 5.

### Performance notes

- `COPY INTO` parallelizes across files automatically.
- Larger files are slightly more efficient than many small
  ones (less overhead). Aim for 100–250 MB compressed per
  file.
- Snowflake recommends compressing CSV files with GZIP
  before loading.
- Parquet loads are typically 3–5× faster than CSV because
  the type information is preserved.

## Hands-on

```sql
USE ROLE LOADER;
USE WAREHOUSE LOADING_WH;
USE DATABASE DEMO;
USE SCHEMA RAW;

-- Load the file uploaded in L27
COPY INTO ORDERS
  FROM @demo_stage
  FILE_FORMAT = (TYPE = CSV
                 FIELD_OPTIONALLY_ENCLOSED_BY = '"'
                 SKIP_HEADER = 1)
  ON_ERROR = 'CONTINUE';

-- Verify
SELECT COUNT(*) FROM ORDERS;

-- Inspect load history
SELECT file_name, row_count, status
FROM DEMO.INFORMATION_SCHEMA.LOAD_HISTORY
WHERE table_name = 'ORDERS'
ORDER BY last_load_time DESC;
```

## Quiz prep

- What is the default `ON_ERROR` behavior? (`ABORT_STATEMENT`)
- How does Snowflake ensure files are not loaded twice?
  (Load history, 64-day default retention)
- What does `FORCE = TRUE` do? (Reload already-loaded files)

## What's next

Next up is **L29 — Create a stage & load data**, a hands-on
lab that puts L26–L28 together into a single end-to-end
workflow.
