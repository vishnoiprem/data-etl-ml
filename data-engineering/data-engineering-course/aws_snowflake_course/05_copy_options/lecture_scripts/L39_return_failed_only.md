---
l_id: L39
title: RETURN_FAILED_ONLY
duration: "6:00"
prereqs: ["L38"]
downloads: []
---

# L39 — RETURN_FAILED_ONLY

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 5 — Copy Options
> **Duration:** ~6:00

## Prereqs

L38 — SIZE_LIMIT. This lecture covers `RETURN_FAILED_ONLY`,
an option that controls the result of a `COPY INTO`.

## Key terms

- **`RETURN_FAILED_ONLY`** — when `TRUE`, the `COPY INTO`
  result only includes failed files; when `FALSE` (default),
  it includes all files.

## Lecture

By default, a `COPY INTO` statement returns one row per
file processed, regardless of whether the file loaded
successfully. For large stages with thousands of files, that
output is noisy. `RETURN_FAILED_ONLY = TRUE` trims it to
just the failures.

### Default behavior

```sql
COPY INTO ORDERS
  FROM @demo_stage/landing/
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  ON_ERROR = 'CONTINUE';
```

Result: one row per file in the path. For a 1000-file load,
you get 1000 rows back, even if 999 succeeded.

### With `RETURN_FAILED_ONLY = TRUE`

```sql
COPY INTO ORDERS
  FROM @demo_stage/landing/
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  ON_ERROR = 'CONTINUE'
  RETURN_FAILED_ONLY = TRUE;
```

Result: one row per **failed** file. If 999 succeeded and 1
failed, you get 1 row.

### When to use

`RETURN_FAILED_ONLY = TRUE` is most useful for:

- **Diagnostic queries** — you want to see only the failures
  without scrolling through thousands of success rows.
- **Programmatic monitoring** — easier to assert "no rows
  returned" means "all succeeded".
- **CI/CD tests** — assert on failure count.

### A monitoring pattern

```sql
-- Capture failed loads to a table
CREATE OR REPLACE TABLE DEMO.RAW.LOAD_FAILURES AS
SELECT *
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()));
```

Combined with a `TASK` that runs after each load, this
builds an alert-ready failures log.

### Snowpipe variant

Snowpipe also supports `RETURN_FAILED_ONLY` in the
`SYSTEM$PIPE_STATUS(...)` function and the
`PIPE_USAGE_HISTORY` view.

### Caveats

- `RETURN_FAILED_ONLY` doesn't change which files load — it
  only filters the result.
- The result row includes `FILE_NAME`, `STATUS`, `ROW_COUNT`,
  `ERROR_COUNT`, and `FIRST_ERROR_MESSAGE`.
- The result is per **file**, not per **row**. For per-row
  rejections, use `VALIDATE` (L37).

## Hands-on

```sql
-- Default: returns all files
COPY INTO ORDERS
  FROM @demo_stage/landing/
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  ON_ERROR = 'CONTINUE';

-- Failed only
COPY INTO ORDERS
  FROM @demo_stage/landing/
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  ON_ERROR = 'CONTINUE'
  RETURN_FAILED_ONLY = TRUE;
```

The first statement returns ~all files; the second returns
only the failures (likely 0 rows in our clean dataset).

## Quiz prep

- What does `RETURN_FAILED_ONLY = TRUE` do? (Returns only
  failed files in the result)
- Does `RETURN_FAILED_ONLY` change which files load? (No,
  only the result set)
- What is the related function for per-row rejections?
  (`VALIDATE`)

## What's next

Next up is **L40 — TRUNCATECOLUMNS + FORCE + Load history**,
the last lecture in section 5.
