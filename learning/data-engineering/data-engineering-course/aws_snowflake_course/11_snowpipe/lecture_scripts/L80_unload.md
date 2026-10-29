---
l_id: L80
title: Unload data
duration: "7:00"
prereqs: ["L79 - Query & load data (GCS)"]
---

# L80 — Unload data

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 11 — Snowpipe
> **Duration:** 7:00

## Prereqs

A working GCS stage and a populated table (L73–L79). You have
`USAGE` on the stage and `SELECT` on the source table.

## Lecture

`COPY INTO` has a second mode most people miss: **unload**. Instead of
reading files *from* a stage and writing rows *into* a table, you
read rows from a query and write files *to* a stage. Same command,
opposite direction.

### Why unload at all?

- Hand processed data to a downstream consumer (a partner,
  a non-Snowflake warehouse, a data lake).
- Snapshot a table for backup before a risky change.
- Export ML scoring results back to object storage for an external
  service to pick up.
- Move data between regions or accounts without `CREATE TABLE AS
  SELECT` round-trips.

### Unload a query to a GCS stage

```sql
-- Simple unload — one file per thread, default name like data_0_0_0.csv
COPY INTO @my_gcs_stage/unload/orders_2024/
FROM (
  SELECT order_id, customer_id, order_date, amount
  FROM raw.orders_gcs
  WHERE order_date BETWEEN '2024-01-01' AND '2024-01-31'
)
FILE_FORMAT = (TYPE = CSV FIELD_DELIMITER = ',' COMPRESSION = GZIP)
HEADER = TRUE
PARTITION BY ('year=' || YEAR(order_date) || '/month=' || LPAD(MONTH(order_date), 2, '0') || '/')
OVERWRITE = TRUE;
```

The `PARTITION BY` clause is the killer feature — it produces a
hive-style directory tree (`year=2024/month=01/data_0_0_0.csv.gz`)
that most downstream engines (Spark, BigQuery, Athena) can read
natively without you doing path math.

### Useful unload options

| Option | What it does |
|---|---|
| `FILE_FORMAT = (...)` | Same `FILE_FORMAT` you use for `COPY INTO <table>`. |
| `HEADER = TRUE` | Writes a header row in each file (CSV only). |
| `COMPRESSION = GZIP \| ZSTD \| SNAPPY` | Shrinks the output. |
| `PARTITION BY '<expr>'` | Hive-style directory layout. |
| `OVERWRITE = TRUE` | Replaces existing files at the same path. |
| `MAX_FILE_SIZE = ...` | Soft cap per file (default 16 MB compressed). |
| `INCLUDE_QUERY_ID = TRUE` | Tags output files with the query that produced them. |

### Common gotchas

- **File format must allow write.** `PARQUET` works, but `JSON` only
  works when you also specify `STRIP_OUTER_ARRAY = TRUE`.
- **You cannot unload into a *named* stage that is itself a table
  stage.** Use a regular external or user stage.
- **You need a warehouse.** Unlike Snowpipe, unload is a normal
  warehouse-driven operation.

### Verify what landed

```sql
LIST @my_gcs_stage/unload/orders_2024/;
```

The output will show your partition tree, file size, and md5.

## Key takeaways

- `COPY INTO @<stage>/path FROM (<query>)` is the unload form.
- `PARTITION BY` produces hive-style layouts for downstream engines.
- Unload is warehouse-driven; Snowpipe is serverless. They are
  different beasts.

## What's next

In **L81 — What is Snowpipe?** we introduce the auto-ingest service
and explain when to pick it over batch `COPY INTO`.
