---
l_id: L51
title: "Loading PARQUET data"
duration: "8:00"
prereqs:
  - L50 (Querying PARQUET data)
---

# L51 — Loading PARQUET data

> **Section:** 7 — Performance optimization
> **Duration:** 8:00

## Prereqs

- L50 — Querying PARQUET data

## Key terms

- **`COPY INTO … FROM (SELECT $1:col, … FROM @stage)`** — the
  canonical Parquet load pattern.
- **Column pruning on load** — Snowflake reads only the columns
  you reference in the inner `SELECT`, not every column in the
  file.
- **Auto-compression** — Snowflake re-compresses ingested
  Parquet with its own columnar codec on write.

## Lecture

The `SELECT $1:… FROM @stage` query from L50 is one-shot. To make
the data persist (and benefit from caching, micro-partition
pruning, and Time Travel), we `COPY INTO` it into a real table.

### The minimal Parquet load

```sql
CREATE OR REPLACE TABLE raw_orders_parquet (
    raw         VARIANT,
    filename    VARCHAR   AS METADATA$FILENAME::VARCHAR,
    row_number  NUMBER    AS METADATA$FILE_ROW_NUMBER,
    loaded_at   TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

COPY INTO raw_orders_parquet (raw, filename, row_number)
FROM (
    SELECT
        $1                          AS raw,
        METADATA$FILENAME           AS filename,
        METADATA$FILE_ROW_NUMBER    AS row_number
    FROM @stg_orders_parquet
)
FILE_FORMAT = (FORMAT_NAME = ff_parquet)
ON_ERROR    = CONTINUE;
```

The structure is identical to the JSON load from L44 — `$1` is the
row group, `METADATA$…` columns are the file metadata, and
`ON_ERROR = CONTINUE` is the production default.

### Load **only** the columns you need

This is the performance trick of Parquet. The inner `SELECT` is
**column-pruning** — Snowflake reads only those columns from
disk:

```sql
COPY INTO curated_orders_parquet (order_id, customer_name, total)
FROM (
    SELECT
        $1:order_id::STRING         AS order_id,
        $1:customer.name::STRING    AS customer_name,
        $1:total::NUMBER(10, 2)     AS total
    FROM @stg_orders_parquet
)
FILE_FORMAT = (FORMAT_NAME = ff_parquet);
```

If the Parquet file has 30 columns but you only reference 3, the
ingest reads **only those 3** from disk. JSON can't do this
because the JSON reader has to parse the whole line. That's
typically the **5–10× speedup** people see when they switch from
JSON to Parquet.

### Cast on the way in

The same `::TYPE` cast we used for JSON works here. Casting
**during** the `COPY INTO` is the right place — it means the
curated table holds typed columns, not a `VARIANT`.

### Compare JSON vs Parquet performance

The honest answer is "your mileage will vary", but the typical
pattern is:

| Operation | JSON | Parquet |
|---|---|---|
| Read 3 of 30 columns | Reads whole line | Reads only 3 columns |
| Compression ratio | ~3:1 | ~10:1 |
| Schema enforcement | None (everything is `VARIANT`) | Strong (file header) |
| Type casting | At query time | At load time |

For a 10 GB file, expect Parquet to be **3–5× faster** to load
and **5–10× faster** to query when most queries touch only a
subset of columns.

### Inspect what got loaded

```sql
SELECT COUNT(*) FROM raw_orders_parquet;
-- should match the number of rows in the source Parquet file

SELECT *
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
    TABLE_NAME => 'raw_orders_parquet',
    START_TIME => DATEADD('hour', -1, CURRENT_TIMESTAMP())
));
```

If `error_count > 0`, the most common cause is a path typo —
Parquet is strictly typed, and `$1:foo.bar` on a non-nested
column throws a runtime error.

### Reload safely

```sql
TRUNCATE TABLE raw_orders_parquet;

COPY INTO raw_orders_parquet (raw, filename, row_number)
FROM (
    SELECT $1, METADATA$FILENAME, METADATA$FILE_ROW_NUMBER
    FROM @stg_orders_parquet
)
FILE_FORMAT = (FORMAT_NAME = ff_parquet)
FORCE = TRUE;
```

`TRUNCATE` + `FORCE = TRUE` is the **clean rebuild** pattern
when you change the file format object or the column list.

### When to use Parquet vs JSON

- **Parquet** — when you control the source (e.g. an upstream
  pipeline that already produces Parquet). Best for analytics
  workloads.
- **JSON** — when the source is an API or a third-party feed
  that ships JSON. Use the `raw` + `curated` two-step pattern.

In this course we'll use both. The pattern is identical
(`COPY INTO` with `$1:…` in the inner select); only the file
format object changes.

## Hands-on

Run the `COPY INTO raw_orders_parquet`, then the column-pruning
`COPY INTO curated_orders_parquet`. Compare the load times in
the Query History tab — Parquet should be markedly faster than
the JSON load from L44.

## Quiz prep

- What is column pruning, and how does Parquet benefit from it?
- Why is `::TYPE` cast during `COPY INTO` better than casting
  later?
- When would you choose JSON over Parquet?

## Key takeaways

- Parquet loads use the same `COPY INTO … FROM (SELECT $1, …
  FROM @stage)` pattern as JSON.
- Snowflake **column-prunes** on load: only referenced columns
  are read.
- The same `::TYPE` cast works — cast during load, not later.
- Parquet is typically **3–10× faster** than JSON for analytics
  workloads.

## What's next

In **L52 — Performance Considerations in Snowflake** we zoom
out and look at the **big-picture knobs**: warehouse size, scale
up vs scale out, and the three caches that make a query faster
the second time.