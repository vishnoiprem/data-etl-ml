---
l_id: L25
title: Loading methods
duration: "7:00"
prereqs: ["L24"]
downloads: []
---

# L25 — Loading Methods

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 4 — Loading Data
> **Duration:** ~7:00

## Prereqs

L24 — Roles in Snowflake. The `LOADER` role from L24 will be
used in the hands-on.

## Key terms

- **Bulk loading** — `COPY INTO <table> FROM @<stage>`. The
  recommended pattern for batch loads.
- **Snowpipe** — serverless auto-ingest via `CREATE PIPE`.
- **Streaming ingestion** — Snowpipe Streaming (formerly
  Snowpipe Streaming SDK) for sub-minute latency.
- **Snowsight "Load data" wizard** — UI-driven one-off loads.
- **Snowpark** — programmatic DataFrame-style loading from
  Python / Java / Scala. Useful for transformations.

## Lecture

This lecture surveys the four primary ways to get data into
Snowflake. We'll drill into `COPY INTO` in L28 and Snowpipe
in section 11. Snowsight and Snowpark are mentioned for
completeness.

### The four methods

| Method | Latency | Use case | Cost model |
|---|---|---|---|
| `COPY INTO` (bulk) | Minutes | Periodic batch loads | Warehouse credits |
| Snowpipe | ~1 minute | New files arriving in S3 | Serverless per-file |
| Snowpipe Streaming | Seconds | Event streams, CDC | Serverless per-row |
| Snowsight wizard | Minutes | One-off, manual | Warehouse credits |
| Snowpark | Minutes | Programmatic, transformed | Warehouse credits |

### Bulk loading with `COPY INTO`

The recommended pattern for most batch loads:

```sql
COPY INTO my_table
FROM @my_s3_stage/path/to/files/
FILE_FORMAT = (TYPE = CSV)
ON_ERROR = 'ABORT_STATEMENT';
```

- Files are staged in S3/ADLS/GCS (or an internal stage).
- `COPY INTO` reads files in parallel, parses them, and
  inserts rows.
- One warehouse can load from thousands of files at once.
- The same file is not re-loaded twice (Snowflake tracks
  load history).

### Snowpipe — serverless auto-ingest

```sql
CREATE PIPE my_pipe AUTO_INGEST = TRUE AS
COPY INTO my_table
FROM @my_s3_stage
FILE_FORMAT = (TYPE = CSV);
```

- Snowpipe uses Snowflake-managed compute, not your
  warehouse.
- Billed per file processed.
- New files arriving in the stage are picked up within ~1
  minute.

Section 11 covers Snowpipe end-to-end.

### Snowsight "Load data" wizard

In the Snowsight UI:

1. Click **Data** → **Databases** → your database → **+ Table**.
2. Choose **Load data from a file**.
3. Pick a local file or a stage.
4. Pick a file format.
5. Snowsight generates the `CREATE TABLE` and `COPY INTO`
   statements and runs them.

This is the fastest way to load a small file once. It's
**not** for production pipelines.

### Snowpark (programmatic loading)

For transformed or filtered loads, use Snowpark:

```python
from snowflake.snowpark import Session

session = Session.builder.configs({
    "account": "abc12345",
    "user":    "loader_user",
    "password": "...",
    "role":    "LOADER",
    "warehouse": "LOADING_WH",
    "database":  "DEMO",
    "schema":    "RAW"
}).getOrCreate()

df = session.read.option("field_delimiter", ",") \
              .csv("@my_stage/sales.csv")
df = df.filter(df["amount"] > 0)
df.write.save_as_table("sales_clean", mode="append")
```

Useful when you need filtering, complex transformations, or
integration with Python ML libraries. We cover Snowpark in
section 12.

### Choosing the right method

A simple decision tree:

- **Files in S3, loaded periodically?** → `COPY INTO`.
- **Files arriving continuously in S3?** → Snowpipe.
- **Streaming data (Kafka, Kinesis)?** → Snowpipe Streaming
  or Kafka connector.
- **One-off small file?** → Snowsight wizard.
- **Heavy transformation in Python?** → Snowpark.

## Hands-on

For this orientation lecture, no new SQL is required. The
hands-on starts in L26 with stages.

## Quiz prep

- What is the recommended bulk-loading command? (`COPY INTO`)
- What is the difference between `COPY INTO` and Snowpipe?
  (`COPY INTO` is batch, uses your warehouse; Snowpipe is
  serverless, billed per file)
- Which method would you use for a 5 GB CSV uploaded to
  S3 once per day? (`COPY INTO`)

## What's next

Next up is **L26 — Understanding stages**, the foundation
for both `COPY INTO` and Snowpipe.
