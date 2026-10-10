---
l_id: L37
title: Working with rejected records
duration: "8:00"
prereqs: ["L36"]
downloads: []
---

# L37 — Working with Rejected Records

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 5 — Copy Options
> **Duration:** ~8:00

## Prereqs

L36 — Using the copy options. This lecture drills into
rejected records — the rows that fail to load — and how to
inspect and recover them.

## Key terms

- **Rejected record** — a row that failed to parse, cast, or
  satisfy a constraint during `COPY INTO`.
- **`VALIDATE` table function** — returns the list of rejected
  records for a previous load.
- **Rejection reason** — the human-readable error string
  (e.g. `Numeric value 'abc' is not recognized`).
- **Rejection column position** — which column in the source
  file caused the rejection.

## Lecture

A "rejected record" is a row that `COPY INTO` couldn't load —
bad data type, constraint violation, or parsing error. The
load may have completed with `ON_ERROR = 'CONTINUE'` (skipping
the bad rows) or `ON_ERROR = 'ABORT_STATEMENT'` (rolling back
everything). Either way, you need a way to **see the
rejections** and fix them.

### The `VALIDATE` function

```sql
SELECT *
FROM TABLE(VALIDATE(ORDERS, JOB_ID => '<query_id>'));
```

`VALIDATE` returns one row per rejected record:

- `REJECTED_RECORD` — the raw line as VARIANT
- `REJECT_REASON` — error message
- `ERROR_LINE` — the line number in the source file
- `ERROR_CHARACTER` — the position in the line
- `ERROR_COLUMN` — the column name in the target table
- `FILE_NAME` — the source file

### Workflow

```sql
-- 1. Run a tolerant load
COPY INTO ORDERS
  FROM @demo_stage/orders.csv
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  ON_ERROR = 'CONTINUE';
```

The result includes the query_id of this `COPY INTO`. Note it
(it shows up in the result panel: `... COPY INTO executed
as query id <id>`).

```sql
-- 2. Look at the rejections
SELECT
  REJECTED_RECORD,
  REJECT_REASON,
  ERROR_LINE,
  ERROR_COLUMN,
  FILE_NAME
FROM TABLE(VALIDATE(ORDERS, JOB_ID => '<id>'));
```

You can now see exactly which rows failed and why.

### Common rejection reasons

| Reason | Cause | Fix |
|---|---|---|
| `Numeric value 'abc' is not recognized` | Non-numeric in a NUMBER column | Clean source; use TRY_CAST |
| `Date '2024-13-01' is not recognized` | Invalid date | Fix source data; use TRY_CAST |
| `String 'X' is too long and would be truncated` | VARCHAR overflow | Use TRUNCATECOLUMNS = TRUE or widen the column |
| `Null value not allowed` | NOT NULL column violated | Clean source or relax constraint |
| `Duplicate key` | Primary key / unique constraint | Deduplicate source |

### The `TRUNCATECOLUMNS` option

For string overflow, the `TRUNCATECOLUMNS = TRUE` option
silently truncates instead of erroring:

```sql
COPY INTO ORDERS
  FROM @demo_stage/orders.csv
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  TRUNCATECOLUMNS = TRUE
  ON_ERROR = 'CONTINUE';
```

We'll cover `TRUNCATECOLUMNS` in L40.

### Building a rejections dashboard

A common production pattern: write rejections to a
"rejects" table and alert on count:

```sql
-- After a load
CREATE OR REPLACE TABLE DEMO.RAW.LOAD_REJECTS AS
SELECT
  CURRENT_TIMESTAMP()::TIMESTAMP_NTZ AS load_time,
  REJECTED_RECORD,
  REJECT_REASON,
  ERROR_LINE,
  ERROR_COLUMN,
  FILE_NAME
FROM TABLE(VALIDATE(ORDERS, JOB_ID => '<id>'));

-- Check the count
SELECT COUNT(*) FROM DEMO.RAW.LOAD_REJECTS;
```

### Recovery patterns

**Fix and reload.** Edit the source file, `TRUNCATE` the
table (or filter out the bad rows), and reload with
`FORCE = TRUE`.

**Load to a "quarantine" table.** Use `ON_ERROR = 'CONTINUE'`
and a separate process to fix the rejections out of band.

**Skip and log.** Use `ON_ERROR = 'SKIP_FILE'` and accept
that the file is corrupt; alert on the rejection.

## Hands-on

```sql
-- 1. Run a tolerant load
COPY INTO ORDERS
  FROM @demo_stage/orders.csv
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  ON_ERROR = 'CONTINUE';

-- 2. Capture the query id from the result panel
-- (or query LOAD_HISTORY to find it)
SELECT query_id
FROM DEMO.INFORMATION_SCHEMA.LOAD_HISTORY
WHERE table_name = 'ORDERS'
ORDER BY last_load_time DESC
LIMIT 1;

-- 3. Inspect rejections
SELECT *
FROM TABLE(VALIDATE(ORDERS, JOB_ID => '<query_id>'))
LIMIT 10;
```

## Quiz prep

- What does the `VALIDATE` table function return? (One row
  per rejected record, with reason and source location)
- What does `TRUNCATECOLUMNS = TRUE` do? (Silently truncates
  strings that exceed the column width instead of erroring)
- What are the most common rejection reasons? (Type cast
  failures, NOT NULL violations, string overflow, duplicate
  keys)

## What's next

Next up is **L38 — SIZE_LIMIT**, where we cover the option
that caps the bytes loaded per statement.
