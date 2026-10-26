---
l_id: L38
title: SIZE_LIMIT
duration: "6:00"
prereqs: ["L37"]
downloads: []
---

# L38 — SIZE_LIMIT

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 5 — Copy Options
> **Duration:** ~6:00

## Prereqs

L37 — Working with rejected records. This lecture covers
`SIZE_LIMIT`, a way to cap the bytes loaded per `COPY INTO`
statement.

## Key terms

- **`SIZE_LIMIT`** — a byte cap on the total amount of data
  loaded by a single `COPY INTO` statement.
- **Units** — bytes. Use `SIZE_LIMIT = 50000000` for 50 MB.

## Lecture

`SIZE_LIMIT` lets you cap the **total bytes loaded** by a
single `COPY INTO` statement. Files exceeding the limit are
skipped (or the statement aborts, depending on
`ON_ERROR`).

### Why use `SIZE_LIMIT`

Three common reasons:

1. **Cost control.** A misbehaving pipeline that suddenly
   sees a 10 TB file shouldn't trigger an unbounded load.
2. **Throttling.** A nightly window with a budget of 100 GB
   per hour can use `SIZE_LIMIT` to cap each statement.
3. **Concurrency control.** When many parallel `COPY INTO`
   statements compete for the same warehouse, `SIZE_LIMIT`
   can prevent any one statement from monopolizing.

### Basic usage

```sql
COPY INTO ORDERS
  FROM @demo_stage/landing/
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  SIZE_LIMIT = 50000000  -- 50 MB
  ON_ERROR = 'CONTINUE';
```

If the total bytes from files in the path exceed 50 MB, the
excess files are skipped.

### Behavior with `ON_ERROR`

| `ON_ERROR` | Behavior when `SIZE_LIMIT` exceeded |
|---|---|
| `ABORT_STATEMENT` | The whole statement fails; no rows loaded |
| `CONTINUE` | Excess files are skipped; valid files load |
| `SKIP_FILE` | Excess files are skipped individually |

### Snowpipe and `SIZE_LIMIT`

`SIZE_LIMIT` works for both `COPY INTO` and Snowpipe. In
Snowpipe, it caps the bytes per pipe run; a file exceeding
the limit is skipped.

### Alternative — `PATTERN` for control

If you want to limit by **which files** load, use `PATTERN`:

```sql
COPY INTO ORDERS
  FROM @demo_stage/landing/
  PATTERN = '.*small_.*\.csv$'   -- only "small_*" files
  FILE_FORMAT = (FORMAT_NAME = 'csv_format');
```

This is more explicit than `SIZE_LIMIT` for many use cases.

### When to use `SIZE_LIMIT`

- **Cost caps** in CI/CD or scheduled jobs.
- **Defensive limits** on stages shared with many users.
- **Production safety nets** alongside other guards (resource
  monitors, role grants).

> **Anti-pattern.** Using `SIZE_LIMIT` to "fix" a misbehaving
> pipeline. Better to investigate the root cause.

## Hands-on

```sql
-- Load with a 1 MB cap
COPY INTO ORDERS
  FROM @demo_stage/landing/
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  SIZE_LIMIT = 1000000
  ON_ERROR = 'CONTINUE';

-- Inspect the load history to see what was skipped
SELECT file_name, file_size, status, last_load_time
FROM DEMO.INFORMATION_SCHEMA.LOAD_HISTORY
WHERE table_name = 'ORDERS'
ORDER BY last_load_time DESC
LIMIT 10;
```

## Quiz prep

- What does `SIZE_LIMIT` cap? (Total bytes loaded per
  statement)
- What happens to files that exceed the limit? (They are
  skipped, with the load succeeding or failing per
  `ON_ERROR`)
- What's the alternative to `SIZE_LIMIT` for per-file
  control? (`PATTERN`)

## What's next

Next up is **L39 — RETURN_FAILED_ONLY**, a small but useful
option for diagnosing partial loads.
