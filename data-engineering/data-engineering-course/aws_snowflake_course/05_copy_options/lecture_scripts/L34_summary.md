---
l_id: L34
title: Summary
duration: "5:00"
prereqs: ["L33"]
downloads: []
---

# L34 — Summary

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 5 — Copy Options
> **Duration:** ~5:00

## Prereqs

L33 — File format object. This is a short recap of L28–L33
to consolidate the `COPY INTO` patterns.

## Key terms

- **Recap** — no new terms. This is a consolidation lecture.

## Lecture

In the last six lectures we built up the full `COPY INTO`
pattern: roles, stages, file formats, the command itself,
transforms, and `ON_ERROR`. This lecture is a one-page
reference.

### The canonical `COPY INTO` pattern

```sql
-- 1. Define the format once
CREATE FILE FORMAT csv_format
  TYPE = CSV
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  SKIP_HEADER = 1;

-- 2. Stage the file (internal or external)
LIST @demo_stage;

-- 3. Define the target table
CREATE TABLE ORDERS (order_id NUMBER, customer_id NUMBER, order_date DATE, amount NUMBER(10,2), status VARCHAR);

-- 4. Run the load
COPY INTO ORDERS
  FROM (
    SELECT
      TRY_CAST($1 AS NUMBER)         AS order_id,
      TRY_CAST($2 AS NUMBER)         AS customer_id,
      TRY_CAST($3 AS DATE)           AS order_date,
      TRY_CAST($4 AS NUMBER(10,2))   AS amount,
      UPPER(TRIM($5))                AS status
    FROM @demo_stage/orders.csv
  )
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  ON_ERROR = 'ABORT_STATEMENT';

-- 5. Inspect
SELECT COUNT(*) FROM ORDERS;
SELECT * FROM DEMO.INFORMATION_SCHEMA.LOAD_HISTORY
WHERE table_name = 'ORDERS' ORDER BY last_load_time DESC;
```

### Decision cheat-sheet

| Question | Answer |
|---|---|
| File format? | CSV, JSON, Parquet, Avro, ORC, XML |
| Stage? | Internal (small files) or external (S3/ADLS/GCS) |
| File format object? | Named for production, inline for one-off |
| `ON_ERROR`? | `ABORT_STATEMENT` (safe default); `CONTINUE` for tolerant |
| `FORCE`? | `FALSE` (default); `TRUE` to reload files |
| Validation? | `VALIDATION_MODE = 'RETURN_ALL_ERRORS'` |
| Transforms? | `SELECT` in `FROM` with `$1`, casts, regex, `LATERAL FLATTEN` |

### Common pitfalls

1. **Wrong schema on the target table.** `COPY INTO` doesn't
   create the table; you must `CREATE TABLE` first.
2. **Wrong file format options.** `FIELD_OPTIONALLY_ENCLOSED_BY`
   matters; missing it makes quoted CSV fail.
3. **Missing warehouse.** You must be using a warehouse to
   run `COPY INTO` (Snowpipe doesn't need one).
4. **Missing privileges.** The role needs `READ` on the
   stage and `INSERT` on the target table.
5. **Wrong sub-path.** `COPY INTO` reads only the path you
   specify; check the file list with `LIST @stage/path/`.

### Performance tips

- **Compress files** with GZIP before loading CSV.
- **Use Parquet** when possible — 3–5× faster.
- **Right-size files** to 100–250 MB compressed.
- **Drop indexes** — Snowflake doesn't have indexes.
- **Cluster large tables** by the most common filter column.

### What's left in this section

We still have:

- L35: `VALIDATION_MODE`
- L36: combining copy options
- L37: working with rejected records
- L38: `SIZE_LIMIT`
- L39: `RETURN_FAILED_ONLY`
- L40: `TRUNCATECOLUMNS`, `FORCE`, load history

By L40 you'll have the complete reference for `COPY INTO`.

## Hands-on

No new lab. Re-run the canonical pattern from L33 with one
variation: try `ON_ERROR = 'CONTINUE'` and see how the
behavior changes.

```sql
COPY INTO ORDERS
  FROM @demo_stage/orders.csv
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  ON_ERROR = 'CONTINUE';
```

## Quiz prep

- What is the recommended `ON_ERROR` default for production
  data? (`ABORT_STATEMENT`)
- What's the difference between named and inline file
  formats? (Named = reusable; inline = one-off)
- Why use Parquet over CSV for bulk loads? (3–5× faster;
  schema preserved)

## What's next

Next up is **L35 — VALIDATION_MODE**, where we learn to
dry-run a `COPY INTO` before committing.
