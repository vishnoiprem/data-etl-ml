---
l_id: L50
title: "Querying PARQUET data"
duration: "7:00"
prereqs:
  - L49 (Insert final data)
---

# L50 — Querying PARQUET data

> **Section:** 7 — Performance optimization
> **Duration:** 7:00

## Prereqs

- L49 — Insert final data

## Key terms

- **Parquet** — columnar binary file format. Reads only the
  columns a query references, not the whole file.
- **Micro-partition pruning** — Snowflake's columnar metadata
  index. Parquet ingestion preserves the file's column order, so
  pruning is even more effective than for CSV/JSON.
- **File format `TYPE = PARQUET`** — tells Snowflake to use the
  Parquet reader instead of the JSON one.
- **`$1:col_name`** — the Parquet field accessor (a colon-prefixed
  identifier, just like JSON).

## Lecture

In section 6 we loaded JSON. In this section we load **Parquet** —
the same logical data, but a columnar binary format. Parquet is
faster to scan, smaller on disk, and Snowflake's column-pruning
gets more efficient because the column order is preserved end-to-end.

### What Parquet is

A Parquet file is **columnar**: instead of storing rows together
(`order_1, order_2, order_3, …`), it stores columns together
(`all order_ids, all totals, all line_items, …`). Three
consequences:

1. **Reads are column-aware.** A query that asks for `total`
   reads only the `total` column, not the entire row.
2. **Compression is better.** All `total` values look similar
   (numbers), so column-wise compression is much smaller than
   row-wise.
3. **Schema is in the file.** Parquet has a header with the
   schema, so Snowflake knows every column's type up front.

### Set up a Parquet file format

```sql
CREATE OR REPLACE FILE FORMAT ff_parquet
    TYPE = PARQUET
    COMPRESSION = SNAPPY;
```

That's it. Snowflake's Parquet reader handles schema, compression
(we accept the default `SNAPPY`), and `null` encoding for you.

### Stage a Parquet file

The stage itself doesn't change — only the file format:

```sql
CREATE OR REPLACE STAGE stg_orders_parquet
    FILE_FORMAT = ff_parquet
    DIRECTORY   = (ENABLE = TRUE);
```

From a local terminal:

```bash
snowsql -a <account> -u <user>
PUT file:///path/to/orders.parquet @demo_db.json_demo.public.stg_orders_parquet;
LIST @stg_orders_parquet;
```

### Query Parquet **without loading it**

The killer feature: Snowflake can query Parquet files **in place**
from a stage. No table needed. This is how you preview a file
before committing to a `COPY INTO`:

```sql
SELECT
    $1:order_id::STRING                       AS order_id,
    $1:customer.name::STRING                  AS customer_name,
    $1:total::NUMBER(10, 2)                   AS total
FROM @stg_orders_parquet
LIMIT 5;
```

Three things to notice:

- `$1` is the **first (and only) row group** Snowflake reads
  from the Parquet file. The path navigation works the same way
  as for `VARIANT`.
- We **didn't create a table**. This is a one-shot query against
  the staged file.
- The same path operators (`:` and `::`) work — Parquet's
  schema becomes a `VARIANT` in the result.

### Why query-before-loading?

Three reasons:

1. **Sanity-check the file.** "Is this the right file? Are the
   columns what I expected?"
2. **Get a quick performance read.** Parquet reads in seconds;
   loading a 50 GB file into a table takes minutes.
3. **Prototype the SQL.** Once `$1:customer.name::STRING` is
   working, you can copy the expression into a real `COPY INTO
   … SELECT …` and only the `FROM` clause changes.

### Inspect Parquet metadata

You can also peek at the file's column list and types:

```sql
SELECT *
FROM TABLE(
    INFER_SCHEMA(
        LOCATION => '@stg_orders_parquet',
        FILE_FORMAT => 'ff_parquet'
    )
);
```

Returns one row per column with `COLUMN_NAME`, `TYPE`, `NULLABLE`,
`EXPRESSION` — the schema Snowflake will use if you load this
file.

### Limits of the in-place query

- **No joins across files** without loading first.
- **No aggregations persisted** — every run re-reads the file.
- **Performance is OK, not great** — for one-shot "what's in this
  file?" questions, not for dashboarding.

The answer for those is `COPY INTO … STAGE` into a real table —
which is L51.

## Hands-on

`PUT` the `orders.parquet` from `code/`, list the stage, then run
the `SELECT $1:…` preview. Confirm the column names match what
you saw in the JSON file.

## Quiz prep

- What is the difference between row-oriented and column-oriented
  storage?
- What does `$1` mean in a Parquet query?
- Why is querying a Parquet file in place useful before a full
  load?

## Key takeaways

- Parquet is **columnar** — only referenced columns are read.
- `TYPE = PARQUET` is the file format setting; `$1:col` is the
  path accessor.
- Snowflake can **query Parquet in place** from a stage — no
  table required — using the same `:` / `::` operators as JSON.
- `INFER_SCHEMA` returns the Parquet file's column types without
  loading it.

## What's next

In **L51 — Loading PARQUET data** we'll `COPY INTO` the file into
a real `raw_orders_parquet` table and compare performance with
the JSON version.