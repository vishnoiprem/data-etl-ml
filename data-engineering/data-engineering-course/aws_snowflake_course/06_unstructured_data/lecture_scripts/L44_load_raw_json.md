---
l_id: L44
title: "Load raw JSON"
duration: "7:00"
prereqs:
  - L43 (Creating stage & raw table)
---

# L44 — Load raw JSON

> **Section:** 6 — Loading unstructured data
> **Duration:** 7:00

## Prereqs

- L43 — Creating stage & raw table

## Key terms

- **`COPY INTO`** — the bulk-load command. Reads from a stage, parses
  with the file format, and inserts into a target table.
- **`ON_ERROR = CONTINUE`** — load what you can, log the rejects,
  don't fail the whole batch.
- **`FORCE = FALSE`** — the default. Snowflake tracks loaded file
  names and skips files it has already loaded in the last 64 days.
- **Load history** — `SELECT * FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(...))`
  shows you which files loaded, when, and how many rows rejected.

## Lecture

This is the lecture where JSON goes from "a file in a stage" to
"rows in a table". One `COPY INTO` statement, then a `SELECT *` to
verify.

### The actual `COPY INTO`

```sql
COPY INTO raw_orders (raw, filename, row_number)
FROM (
    SELECT
        $1                              AS raw,
        METADATA$FILENAME               AS filename,
        METADATA$FILE_ROW_NUMBER        AS row_number
    FROM @stg_orders_json
)
FILE_FORMAT = (FORMAT_NAME = ff_json)
ON_ERROR    = CONTINUE
FORCE       = FALSE;
```

Three things to notice:

1. **We select from the stage** in the inner `SELECT`. `$1` is the
   first (and only) column Snowflake parses from the JSON line; we
   alias it `raw`. The other `$1` candidates (`$2`, …) are
   meaningless for JSON — you only have one logical column.
2. **`METADATA$…`** columns are virtual columns Snowflake attaches
   to every file load.
3. **`ON_ERROR = CONTINUE`** is the production default for raw
   loads. The `raw` table should never fail because of one bad
   line; bad lines are visible in load history.

### Verify the row count

```sql
SELECT COUNT(*) AS rows_loaded FROM raw_orders;
```

You should see **one row per JSON object** in `orders.json`. If
the count is 0, your file format is wrong. If the count is 1 and
the file has 1000 lines, you forgot `STRIP_OUTER_ARRAY = FALSE` is
the right setting and Snowflake is treating the file as a single
object.

### Spot-check a single row

```sql
SELECT
    raw:order_id::STRING       AS order_id,
    raw:total::NUMBER(10, 2)   AS total,
    raw:customer.name::STRING  AS customer_name,
    filename
FROM raw_orders
LIMIT 5;
```

This is the moment of truth — if `order_id` shows `ORD-1001`,
`total` shows `149.97`, and `customer_name` shows `Ada Lovelace`,
the path operators and the load are both correct.

### Check load history

```sql
SELECT
    file_name,
    row_count,
    row_parsed,
    error_count,
    first_load_time
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
    TABLE_NAME => 'raw_orders',
    START_TIME => DATEADD('hour', -1, CURRENT_TIMESTAMP())
));
```

Expected:

- `row_count` = `row_parsed` (no rejects).
- `error_count` = 0.
- `first_load_time` is the time you ran the `COPY INTO`.

If `error_count > 0`, query `VALIDATE_PIPELINE_LOAD` or the
rejected-records table to see what was wrong.

### Re-running the same load

```sql
COPY INTO raw_orders (raw, filename, row_number)
FROM @stg_orders_json
FILE_FORMAT = (FORMAT_NAME = ff_json);
-- 0 files processed, 0 rows loaded
```

Because `FORCE = FALSE` (the default) and Snowflake remembers
file names in its load history for 64 days, the second run is a
**no-op**. That is the safety guarantee you want.

To force a reload — for example, after you changed the file
format — use `FORCE = TRUE`:

```sql
COPY INTO raw_orders (raw, filename, row_number)
FROM @stg_orders_json
FILE_FORMAT = (FORMAT_NAME = ff_json)
FORCE = TRUE;
```

### What to do with bad rows

If `ON_ERROR = CONTINUE` lets a few rows through with errors, you
have two options:

1. **Inspect them** with `SELECT * FROM TABLE(VALIDATE_ORDERS(...))`
   or by querying `raw_orders` for `NULL` fields.
2. **Reject them to a separate table** with `ON_ERROR = ABORT_STATEMENT`
   and a `VALIDATION_MODE = RETURN_ERRORS` dry run.

For our `raw` table we always use `ON_ERROR = CONTINUE` — we want
**every byte** of the source file, bad or not, so the next person
can debug it.

## Hands-on

Run the `COPY INTO` from L44, then run the spot-check `SELECT`.
You should see real order IDs, real totals, and real customer
names. If you see `NULL` instead of a string, your JSON path is
wrong — go back to L42 and re-check the field name.

## Quiz prep

- What does `ON_ERROR = CONTINUE` do?
- Why is `FORCE = FALSE` the safe default?
- How do you find the load history of a table?

## Key takeaways

- One `COPY INTO` statement with a `FROM (SELECT $1 … FROM
  @stage)` subquery ingests the whole file.
- `ON_ERROR = CONTINUE` is the right default for `raw` tables.
- `FORCE = FALSE` makes the load **idempotent** — re-running loads
  zero new rows.
- `COPY_HISTORY` tells you what loaded, when, and how many rows
  rejected.

## What's next

In **L45 — Parsing JSON** we cover the `:` / `:.` operators in
depth, including arrays with the `[]` indexer.
