---
l_id: L16
title: Loading data in Snowflake (intro)
duration: "6:00"
prereqs: ["L15"]
downloads: []
---

# L16 — Loading Data in Snowflake (Intro)

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 3 — Snowflake Architecture
> **Duration:** ~6:00

## Prereqs

L15 — Exploring tables & databases. This is a short orientation
lecture before the deep dive in section 4.

## Key terms

- **Bulk loading** — Snowflake's recommended pattern. Use the
  `COPY INTO` command to load files from a stage.
- **Stage** — a location where data files live, either
  internal (Snowflake-managed) or external (S3, Azure Blob, GCS).
- **Snowpipe** — a serverless auto-ingest service that loads
  files as they arrive in a stage.
- **Continuous loading** — Snowpipe and streaming ingestion
  are continuous; `COPY INTO` is batch.

## Lecture

This lecture is a quick orientation before we go hands-on with
loading in section 4. There are three primary ways to get data
into Snowflake, and picking the right one is the first design
decision in any pipeline.

### The three loading patterns

| Pattern | Command | When to use |
|---|---|---|
| Bulk batch | `COPY INTO <table> FROM @<stage>` | Periodic loads, files in S3/ADLS/GCS |
| Continuous auto-ingest | `CREATE PIPE ... AUTO_INGEST=TRUE` | New files arrive continuously; serverless |
| Manual one-off | Snowsight UI "Load data" wizard | Ad-hoc, first-time setup |

### Bulk batch — `COPY INTO`

The recommended pattern. Stage files in S3/Azure/GCS, then run
`COPY INTO` to load them into a table. A `COPY INTO` command can
process thousands of files in parallel and is the most cost-
efficient way to load large data volumes.

```sql
COPY INTO my_table
FROM @my_s3_stage/orders/2024/01/
FILE_FORMAT = (TYPE = CSV COMPRESSION = GZIP)
ON_ERROR = 'ABORT_STATEMENT';
```

### Continuous auto-ingest — Snowpipe

Snowpipe is the **serverless** version of `COPY INTO`. You
define a `PIPE` that points at a stage; when a new file
arrives, Snowflake auto-loads it within minutes. No warehouse
required — Snowpipe uses Snowflake-managed compute billed per
file.

```sql
CREATE PIPE my_pipe
  AUTO_INGEST = TRUE
AS
COPY INTO my_table
FROM @my_s3_stage
FILE_FORMAT = (TYPE = CSV);
```

Section 11 covers Snowpipe in depth.

### Choosing between bulk and Snowpipe

| Workload | Recommendation |
|---|---|
| Daily batch load from S3 | `COPY INTO` on a schedule |
| Hourly micro-batches from S3 | `COPY INTO` on a cron |
| Streaming data (sub-minute) | Snowpipe or Kafka connector |
| One-off CSV upload from browser | Snowsight "Load data" wizard |

### Data formats

Snowflake can load:

- **CSV** — comma-separated, with optional header
- **JSON** — newline-delimited JSON (NDJSON) is the standard
- **Parquet** — columnar, compressed, fastest to load
- **Avro** — schema-based, common in Kafka pipelines
- **ORC** — Hive-style columnar
- **XML** — parsed via `XMLGET` after loading

Most production pipelines standardize on **Parquet** for
bulk loads and **JSON** for event streams.

## Hands-on

No lab in this orientation lecture. The hands-on starts in
section 4 with L24.

## Quiz prep

- What is the recommended bulk-loading command? (`COPY INTO`)
- What is the difference between `COPY INTO` and Snowpipe?
  (`COPY INTO` is batch and uses your warehouse; Snowpipe is
  serverless and billed per file)
- Which format is fastest to bulk load? (Parquet)

## What's next

Next up is **L17 — What is a data warehouse?**, a short
context lecture for readers new to the data warehousing
concept.
