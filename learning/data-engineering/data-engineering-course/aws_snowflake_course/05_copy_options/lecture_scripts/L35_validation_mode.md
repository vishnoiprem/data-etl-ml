---
l_id: L35
title: VALIDATION_MODE
duration: "8:00"
prereqs: ["L34"]
downloads: []
---

# L35 — VALIDATION_MODE

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 5 — Copy Options
> **Duration:** ~8:00

## Prereqs

L34 — Summary. This lecture drills into `VALIDATION_MODE`, the
dry-run option for `COPY INTO`.

## Key terms

- **`VALIDATION_MODE`** — runs the load without inserting any
  rows. Returns the count of rows that would be loaded plus
  the list of errors.
- **`RETURN_ALL_ERRORS`** — return every error found.
- **`RETURN_ERRORS`** — return only the first error per file
  (cheaper).
- **`RETURN_N_ROWS`** — return the first N rows that would be
  inserted. Useful for spot-checking.

## Lecture

`VALIDATION_MODE` is the most important debugging tool for
`COPY INTO`. It runs the full load logic — parsing, casting,
constraint checks — but commits **no rows**. The result is
the count of rows that would be loaded plus the list of
errors.

### Basic usage

```sql
COPY INTO ORDERS
  FROM @demo_stage/orders.csv
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  VALIDATION_MODE = 'RETURN_ALL_ERRORS';
```

The statement returns:

- A row count summary.
- A detailed error list (file, row number, column, error).
- A status column (`LOADED` / `PARTIALLY_LOADED` /
  `LOAD_FAILED`).

### The validation modes

| Mode | Returns |
|---|---|
| `RETURN_ERRORS` | First error per file |
| `RETURN_ALL_ERRORS` | All errors |
| `RETURN_N_ROWS` | First 1000 rows that would be loaded |

Use `RETURN_ERRORS` for a quick sanity check; `RETURN_ALL_ERRORS`
for a thorough audit; `RETURN_N_ROWS` to spot-check the
content.

### Workflow

A common production pattern:

```sql
-- 1. Validate first
COPY INTO ORDERS
  FROM @demo_stage/orders.csv
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  VALIDATION_MODE = 'RETURN_ALL_ERRORS';

-- 2. If clean, run the real load
COPY INTO ORDERS
  FROM @demo_stage/orders.csv
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  ON_ERROR = 'ABORT_STATEMENT';
```

This two-step pattern is the standard for nightly batch loads.

### Saving the result

The validation result isn't directly returned as rows — it's
in the result set of the `COPY INTO`. To capture it for
later use, use the `VALIDATE` table function:

```sql
SELECT *
FROM TABLE(VALIDATE(ORDERS, JOB_ID => '<query_id_of_last_copy>'));
```

`VALIDATE` returns one row per error with the rejected
record as a VARIANT.

### Forcing a re-validation

By default, load history tracks files. To re-validate files
that have already been loaded, add `FORCE = TRUE`:

```sql
COPY INTO ORDERS
  FROM @demo_stage/orders.csv
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  VALIDATION_MODE = 'RETURN_ALL_ERRORS'
  FORCE = TRUE;
```

`FORCE` here is harmless because `VALIDATION_MODE` doesn't
insert.

### Combining with `ON_ERROR`

`VALIDATION_MODE` ignores `ON_ERROR` — it always returns
errors, regardless of what the load would have done.

### Common use cases

- **Pre-flight check** before a scheduled load.
- **Diffing source and target** — re-validate and compare to
  load history.
- **Auditing a new file format** — validate a sample before
  committing the format to production.
- **CI/CD** — include validation in your pipeline tests.

## Hands-on

```sql
-- Validate (no rows inserted)
COPY INTO ORDERS
  FROM @demo_stage/orders.csv
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  VALIDATION_MODE = 'RETURN_ALL_ERRORS';

-- Spot-check
COPY INTO ORDERS
  FROM @demo_stage/orders.csv
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  VALIDATION_MODE = 'RETURN_N_ROWS';
```

If `VALIDATION_MODE = 'RETURN_ALL_ERRORS'` returns errors,
inspect the source file and fix the data or the format. If
clean, run the real load.

## Quiz prep

- What does `VALIDATION_MODE = 'RETURN_ALL_ERRORS'` do?
  (Validates without inserting; returns all errors)
- What is the difference between `RETURN_ERRORS` and
  `RETURN_ALL_ERRORS`? (`RETURN_ERRORS` = first error per
  file; `RETURN_ALL_ERRORS` = all errors)
- How do you retrieve the detailed error list?
  (`SELECT * FROM TABLE(VALIDATE(<table>, JOB_ID =>
  '<query_id>'))`)

## What's next

Next up is **L36 — Using the copy options**, where we
combine multiple `COPY INTO` options together in real
scenarios.
