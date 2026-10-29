---
l_id: L40
title: TRUNCATECOLUMNS + FORCE + Load history
duration: "7:00"
prereqs: ["L39"]
downloads: []
---

# L40 — TRUNCATECOLUMNS + FORCE + Load History

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 5 — Copy Options
> **Duration:** ~7:00

## Prereqs

L39 — RETURN_FAILED_ONLY. This is the last lecture in
section 5; we wrap up the `COPY INTO` options with
`TRUNCATECOLUMNS`, a deeper look at `FORCE`, and a recap of
load history.

## Key terms

- **`TRUNCATECOLUMNS = TRUE`** — silently truncate strings
  that exceed the column width instead of erroring.
- **`FORCE = TRUE`** — bypass load history; load files even
  if they were loaded before.
- **Load history** — Snowflake's record of every file loaded
  into every table. Default retention 64 days.

## Lecture

This lecture is the wrap-up of the `COPY INTO` options. We
cover `TRUNCATECOLUMNS` (the option that prevents string
overflow errors), a deeper look at `FORCE` (with practical
workflows), and a recap of load history (the 64-day window
that powers idempotent loads).

### `TRUNCATECOLUMNS`

```sql
COPY INTO ORDERS
  FROM @demo_stage/orders.csv
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  TRUNCATECOLUMNS = TRUE
  ON_ERROR = 'CONTINUE';
```

If a string value is wider than the column's
`VARCHAR(n)`, the value is truncated to `n` characters
instead of rejecting the row.

> **Use when.** Loading data with hard-to-control source
> width (e.g. user input, log lines). Truncation is silent —
> you may want to combine with a separate audit.

> **Anti-pattern.** Using `TRUNCATECOLUMNS = TRUE` to "fix" a
> schema mismatch. The right fix is to widen the column
> (`ALTER TABLE ... MODIFY COLUMN status VARCHAR(100)`).

### `FORCE` — deeper

```sql
COPY INTO ORDERS
  FROM @demo_stage/orders.csv
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  FORCE = TRUE;
```

`FORCE = TRUE` makes Snowflake treat the file as new — load
history is bypassed. Common patterns:

**Pattern 1 — Replay after a fix.** The source had a bug;
you fix the bug, then re-emit and reload the file with
`FORCE = TRUE`. The new data overwrites the old (the
table's existing rows are updated by primary key, or the
table is `TRUNCATE`d first).

**Pattern 2 — Schema change.** You added a column to the
target; existing rows need to be repopulated. `TRUNCATE`
then `COPY INTO ... FORCE = TRUE`.

**Pattern 3 — Disaster recovery.** A load was reversed (you
ran an undo script). You need to re-load from the source
files — `FORCE = TRUE`.

> **Warning.** `FORCE = TRUE` doesn't deduplicate. If you
> re-load without truncating, you may double-count rows. Use
> `MERGE` instead of plain `COPY INTO` for upserts.

### Load history — recap

The `INFORMATION_SCHEMA.LOAD_HISTORY` view (or the
`ACCOUNT_USAGE.LOAD_HISTORY` view for older history) tracks
every file ever loaded.

```sql
SELECT file_name,
       row_count,
       status,
       last_load_time,
       error_count,
       first_error_message
FROM DEMO.INFORMATION_SCHEMA.LOAD_HISTORY
WHERE table_name = 'ORDERS'
ORDER BY last_load_time DESC
LIMIT 20;
```

Key columns:

- `FILE_NAME` — the source file
- `ROW_COUNT` — rows successfully loaded
- `STATUS` — `LOADED`, `PARTIALLY_LOADED`, `LOAD_FAILED`,
  `LOAD_IN_PROGRESS`
- `ERROR_COUNT` — number of failed rows
- `FIRST_ERROR_MESSAGE` — first error
- `LAST_LOAD_TIME` — when the file was last processed

### 64-day retention

Load history is retained for **64 days** by default. After
that, the same file is considered "new" again — and a
`COPY INTO` without `FORCE` will re-load it.

For longer retention, copy the load history into your own
table periodically:

```sql
CREATE OR REPLACE TABLE DEMO.RAW.LOAD_HISTORY_ARCHIVE AS
SELECT * FROM DEMO.INFORMATION_SCHEMA.LOAD_HISTORY;
```

### Section 5 recap

You now know:

- Named file format objects (L33)
- The full `COPY INTO` pattern (L34)
- `VALIDATION_MODE` for dry-runs (L35)
- Combining options: `PATTERN`, `PURGE`, `FORCE` (L36)
- `VALIDATE` for inspecting rejections (L37)
- `SIZE_LIMIT` for cost guards (L38)
- `RETURN_FAILED_ONLY` for cleaner output (L39)
- `TRUNCATECOLUMNS` and `FORCE` deep-dive (L40)

## Hands-on

```sql
-- 1. Truncate-and-reload with FORCE
TRUNCATE TABLE ORDERS;
COPY INTO ORDERS
  FROM @demo_stage/orders.csv
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  FORCE = TRUE
  ON_ERROR = 'ABORT_STATEMENT';

-- 2. Truncate-on-overflow load
COPY INTO ORDERS
  FROM @demo_stage/orders_with_long_status.csv
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  TRUNCATECOLUMNS = TRUE
  ON_ERROR = 'CONTINUE';

-- 3. Inspect the full load history
SELECT file_name, row_count, status, error_count, last_load_time
FROM DEMO.INFORMATION_SCHEMA.LOAD_HISTORY
WHERE table_name = 'ORDERS'
ORDER BY last_load_time DESC
LIMIT 20;
```

## Quiz prep

- What does `TRUNCATECOLUMNS = TRUE` do? (Silently truncates
  strings that exceed the column width)
- What is the retention period of load history? (64 days
  default)
- When should you use `FORCE = TRUE`? (Replay after a fix;
  schema change; disaster recovery — and **after truncating
  the table** to avoid duplicates)

## Key takeaways

- **`TRUNCATECOLUMNS`** — silent truncation; use sparingly.
- **`FORCE`** — bypasses load history; always combine with
  `TRUNCATE` or `MERGE` to avoid duplicates.
- **Load history** — 64-day default retention; archive to
  your own table for longer history.
- Section 5 covers the full `COPY INTO` surface — you can
  now debug any production load.

## What's next

Next up is **L41 — High-level steps**, the first lecture in
section 6. We move from CSV/JSON loading into **unstructured
data** — semi-structured JSON with nested arrays, objects,
and the `LATERAL FLATTEN` pattern in depth.
