---
l_id: L43
title: "Creating stage & raw file"
duration: "7:00"
prereqs:
  - L42 (Understanding our data)
---

# L43 — Creating stage & raw table

> **Section:** 6 — Loading unstructured data
> **Duration:** 7:00

## Prereqs

- L42 — Understanding our data

## Key terms

- **Internal stage** — a Snowflake-managed storage location
  (S3/Azure/GCS) you `PUT` files into with the SnowSQL CLI.
- **External stage** — points at an existing S3 bucket / Azure
  container / GCS bucket via a storage integration. Used in
  Section 8+.
- **File format object** — `CREATE FILE FORMAT … TYPE = JSON` saves
  the parsing options once and reuses them across many `COPY INTO`s.
- **Raw landing table** — a one-column `VARIANT` table plus
  `METADATA$` columns. The schema is "the JSON itself".

## Lecture

Time to set up the **landing pad** for our JSON file. We need two
artifacts: a stage (the pointer to the file) and a `raw` table (the
landing pad inside Snowflake). The file format is optional but
**strongly recommended** so we never retype the options.

### Step 1 — create the database & schema

Use a sandbox you can blow away. We work in `demo_db.json_demo`:

```sql
CREATE DATABASE IF NOT EXISTS demo_db;
USE DATABASE demo_db;
CREATE SCHEMA IF NOT EXISTS json_demo;
USE SCHEMA json_demo;
```

### Step 2 — create a file format for JSON

```sql
CREATE OR REPLACE FILE FORMAT ff_json
    TYPE                = JSON
    STRIP_OUTER_ARRAY   = FALSE
    STRIP_NULL_VALUES   = FALSE
    IGNORE_UTF8_ERRORS  = FALSE;
```

A note on `STRIP_OUTER_ARRAY`:

- `FALSE` (default) — every line in the file is a **separate JSON
  object**. Use this for "JSON Lines" / `.jsonl` files, which is
  what we have.
- `TRUE` — Snowflake expects the file to be **one big array** like
  `[{…}, {…}, …]` and will strip the outer `[ ]`. Use this for
  files exported by APIs that always wrap collections.

### Step 3 — create an internal stage

Internal stages are free, scoped to the schema, and perfect for the
free-trial. The `PUT` command (SnowSQL) uploads a local file into
the stage.

```sql
CREATE OR REPLACE STAGE stg_orders_json
    FILE_FORMAT = ff_json
    DIRECTORY   = (ENABLE = TRUE);
```

`DIRECTORY = (ENABLE = TRUE)` lets us see the file list from SQL —
useful for debugging.

From a local terminal (SnowSQL):

```bash
snowsql -a <account> -u <user>
PUT file:///path/to/orders.json @demo_db.json_demo.public.stg_orders_json;
```

### Step 4 — verify the stage sees the file

```sql
LIST @stg_orders_json;
```

Expected: one row, `orders.json.gz` (Snowflake auto-gzips on `PUT`),
with a `size`, `md5`, and `last_modified`.

### Step 5 — create the `raw_orders` table

```sql
CREATE OR REPLACE TABLE raw_orders (
    raw         VARIANT,
    filename    VARCHAR   AS METADATA$FILENAME::VARCHAR,
    row_number  NUMBER    AS METADATA$FILE_ROW_NUMBER,
    loaded_at   TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);
```

The first three columns are populated by Snowflake during `COPY INTO`:

- `raw` — the parsed JSON object.
- `filename` — the source file, useful for lineage.
- `row_number` — the line number within the file, useful when a
  single row rejects.

`loaded_at` is a default column so you can answer "when did this
row land?" with `WHERE loaded_at > '2026-10-10'`.

### Why a `raw` table and not a typed table?

Three reasons:

1. **Failures are cheap.** If a downstream field is missing, the
   `COPY INTO` still succeeds and you find the bad row later with
   `WHERE raw:customer.email IS NULL`.
2. **Reparsing is free.** The data is already in Snowflake. If your
   `LATERAL FLATTEN` was wrong, you fix the SQL and rerun — no
   S3 round-trip.
3. **Schema is recorded.** Each `VARIANT` row is the exact bytes
   you loaded. Tomorrow's "can you also give me `customer.phone`?"
   request is a `SELECT`, not another pipeline.

### Common mistakes at this step

- **Forgetting the file format** and writing `FILE_FORMAT = (TYPE =
  JSON)` inline every time. Save it once as an object.
- **Pointing the stage at the wrong schema** — `PUT` requires
  `db.schema.stage` or `@~` (the user stage).
- **Making the `raw` table strongly-typed.** Resist. The whole point
  is that `raw` doesn't care about the shape.

## Hands-on

Run steps 1–5 in the Snowflake UI. You should be able to `LIST
@stg_orders_json` and see one row before continuing to L44.

## Quiz prep

- What is the difference between an internal and an external stage?
- What does `STRIP_OUTER_ARRAY = FALSE` mean?
- Why do we add a `filename` column to the `raw` table?

## Key takeaways

- Create a **file format object** (`ff_json`) once and reuse it.
- Use an **internal stage** for the free trial; you `PUT` files with
  SnowSQL.
- The `raw` table is a **single `VARIANT` column** plus file
  metadata (`METADATA$FILENAME`, `METADATA$FILE_ROW_NUMBER`).
- A `raw` table is your safety net — re-parsing is free, no S3
  round-trip needed.

## What's next

In **L44 — Load raw JSON** we run the actual `COPY INTO raw_orders
FROM @stg_orders_json` and verify that every JSON object becomes one
row.
