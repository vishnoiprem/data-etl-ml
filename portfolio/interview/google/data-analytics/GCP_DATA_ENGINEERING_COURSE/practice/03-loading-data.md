# 3 — Loading Data from Different Sources

> **Practice Module 3 · BigQuery · 45 minutes**

## 🎯 What you will learn

- Every route data can take into BigQuery, and the one question that picks between them.
- Batch load jobs versus the Storage Write API, and why the gRPC path is the one to prefer.
- What delivery guarantee you actually get, and what that forces you to build.
- Why a partially successful load is the most dangerous result in this module.
- How to load a file, verify it, and make the job idempotent — in that order.

---

## 🧠 Concept

### The routes in

| Route | Use it when | Latency |
|---|---|---|
| **Batch load job** | Files are already in Cloud Storage, arriving in batches | Minutes |
| **Storage Write API (gRPC)** | You need low latency, high throughput, or exactly-once | Sub-second |
| **Storage Write API (REST)** | Legacy path — `tabledata.insertAll` | Sub-second |
| **Data Transfer Service** | Scheduled or recurring loads from Cloud Storage and SaaS sources | Minutes |
| **Datastream (CDC)** | You need to replicate an operational database | Near real-time |
| **Dataflow** | Custom sources, or preprocessing before a high-throughput stream | Varies |
| **Federated query / external connection** | You want to query the data *without* loading it | Query time |

### The question that picks between them

> **Is the data arriving as files, as a stream of changes, or as a database you did not write?**

- **Files** → batch load job.
- **A stream of individual records** → Storage Write API.
- **Changes to rows in someone else's database** → Datastream CDC.
- **A recurring pull from a SaaS system** → Data Transfer Service.
- **You just want to read it once, occasionally** → federated query. Do not copy it at all.

The fourth route is the one people forget. If you need to query data once a month for a report,
loading it into BigQuery means you now own a copy, a refresh job, a staleness bug and a storage
bill — to answer one question. **Federated queries and external connections** read the source in
place, which is exactly right for occasional reads and exactly wrong for repeated ones.

### Batch load jobs

A load job reads from **Cloud Storage or a local file** and writes into a BigQuery table. You
create it programmatically, with the `LOAD DATA` SQL statement, or with `bq load`.

Supported formats: **Avro, CSV, JSON, ORC, Parquet.**

Two things about load jobs that bite people:

1. **The source file must be in Cloud Storage** (or local) — not a live database, not an S3
   bucket without a connection.
2. **A load job is not atomic with your table.** It writes into the table's destination, and if
   it fails halfway, the table holds partial data. This is why the load → verify → assert pattern
   in module 6 matters.

### Storage Write API: gRPC versus REST

The Storage Write API streams rows into an existing BigQuery table without a load job.
Acknowledged data is queryable in real time.

| | gRPC | REST |
|---|---|---|
| Status | **Recommended for new projects** | Legacy (`tabledata.insertAll`) |
| Pricing | Lower | Higher |
| Delivery | **Exactly-once** available | At-least-once |
| Extras | Iceberg managed-table streaming | — |

Google's own guidance for new projects is gRPC, for three reasons that all matter in production:
lower price, exactly-once delivery semantics, and Iceberg managed-table streaming.

### Delivery semantics — what it forces you to build

**At-least-once** means a row can arrive more than once. If your sink is not idempotent, you get
duplicate rows, and your totals are wrong in a way that is very hard to detect — because the
duplicates look like real data.

**Exactly-once** requires a stream configured with a **write stream ID**. The default stream is
the at-least-once path.

On the legacy REST path, the only dedupe is `insertId`, and it is **best-effort for about one
minute**. BigQuery may suppress repeated identical `insertId` values for up to a minute — but it
is not a guarantee, and rows sharing an ID are assumed identical. Omitting `insertId` disables
the behaviour entirely and is recommended for maximum throughput. So REST's dedupe is a
**performance hint, not a correctness mechanism**. If you need correctness, use gRPC with a write
stream ID.

This is exactly the same lesson as Pub/Sub in module 4 of the `interview/` bank: **derive your
idempotency key from the data, never from arrival time.** The course's `dedup_key(event_id,
partition)` returns `"20260115:evt-0001"` — a retry produces the same identity, so it is safe.

### Partial success — the most dangerous result here

REST streaming responses can be **partially successful**. That means the HTTP request succeeded,
some rows landed, and some did not.

**A successful HTTP status does not prove every row was inserted.** You must inspect
`insertErrors` in the response and handle the rows that failed.

Every code path that writes to BigQuery must check for this. A pipeline that ignores
`insertErrors` will eventually produce a report that is silently missing rows — and nothing will
alert you, because every log line says "success".

### Data Transfer Service

The **Data Transfer Service** is the scheduled-load tool. It supports **scheduled, one-time, or
recurring** transfers, and it is the right answer for "every night, pull these files into
BigQuery" and for SaaS sources like Google Ads, YouTube Analytics, Cloud Storage, and Google
Sheets.

Its advantage over a hand-rolled load job is operational, not technical: it is managed, it has
its own retry and alerting, and it shows up in a console you can hand to someone who is not you.

### Datastream — CDC

**Datastream** replicates changes from an operational database into BigQuery. It is the right
route when the source of truth is a running database and you need the warehouse to reflect it.

The trade-off, stated plainly: **CDC captures state changes, including updates to rows nobody
cared about.** Event streaming captures *intent*. A CDC stream will faithfully deliver that a
customer's address changed — even if your warehouse never uses addresses — and a `DELETE` in the
log is harder to interpret than a `deleted` event carrying a reason.

The other constraint: **CDC inherits the source's log retention.** Fall behind past the log's
lifetime and you have a gap you cannot fill. That is the number to negotiate with the database
team: *how long do we keep the binlog?*

---

## 🛠️ Hands-On

### 💻 Runs locally — idempotency, the thing you must get right

```python
import sys
sys.path.insert(0, "../project/core")
from pipeline_logic import dedup_key, deduplicate

# A batch arrives twice because the retry fired.
batch = [
    {"event_id": "evt-0001", "event_dt": "2026-01-15", "amount_eur": 10.0},
    {"event_id": "evt-0002", "event_dt": "2026-01-15", "amount_eur": 20.0},
    {"event_id": "evt-0001", "event_dt": "2026-01-15", "amount_eur": 10.0},
]

key = dedup_key("evt-0001", "20260115")
print(f"idempotency key: {key}")

unique = deduplicate(batch, partition="20260115")
print(f"in:  {len(batch)} rows")
print(f"out: {len(unique)} rows  -> duplicate removed")
```

Expected output:

```text
idempotency key: 20260115:evt-0001
in:  3 rows
out: 2 rows  -> duplicate removed
```

The key is derived from **the data** — the event id and its partition — so a retry produces the
same key and the duplicate collapses. Had the key included a load timestamp, the retry would have
produced a *different* key and both rows would have survived.

### 💻 Runs locally — the cost of a streaming ingest

```python
import sys
sys.path.insert(0, "../project/core")
from cost_model import estimate

# Streaming 1 GB a day into BigQuery, and reading it back once a day.
DAYS = 30
ingest = estimate("pubsub", pubsub_gb=1.0 * DAYS, apply_free_tier=False).total
scan = estimate("bigquery", scanned_tb=0.01 * DAYS, apply_free_tier=False).total

print(f"ingest, 1 GB/day for {DAYS} days: ${ingest:,.4f}")
print(f"scan back once a day:              ${scan:,.4f}")
```

Expected output:

```text
ingest, 1 GB/day for 30 days: $12.0000
scan back once a day:              $1.8750
```

Note the shape: the ingest cost scales with **volume**, and the read cost scales with **how much
you read**. Streaming into BigQuery is not expensive. Reading it badly is.

### 🌐 Needs a BigQuery project — load a CSV

```bash
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --autodetect=true \
  --replace=true \
  --maximum_bytes_billed=10000000000 \
  YOUR_PROJECT_ID:YOUR_DATASET.sales \
  gs://YOUR_BUCKET/sales.csv
```

Each flag earns its place:

| Flag | Why |
|---|---|
| `--source_format=CSV` | Required. Without it the load job cannot parse the file. |
| `--skip_leading_rows=1` | The header is not data. |
| `--autodetect=true` | Infers the schema from the first rows. Convenient for exploration, **dangerous in production** — see below. |
| `--replace=true` | Overwrites the destination table's data and schema. Makes the load idempotent. |
| `--maximum_bytes_billed` | Fails the load rather than billing you without limit. |

**`--autodetect` deserves a warning.** Autodetect samples the first rows and infers types. If the
first 100 rows happen to contain no `NULL`s, a column that is nullable in reality gets inferred
as `REQUIRED`, and every subsequent load with a null fails. In production, **declare the schema
explicitly** and treat the table definition as code.

With an explicit schema:

```bash
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --schema=transaction_id:STRING,store_id:STRING,sale_date:DATE,customer_id:STRING,sales_amount:NUMERIC \
  --replace=true \
  YOUR_PROJECT_ID:YOUR_DATASET.sales \
  gs://YOUR_BUCKET/sales.csv
```

### 🌐 Needs a BigQuery project — the same load, from Parquet

```bash
bq load \
  --source_format=PARQUET \
  --replace=true \
  YOUR_PROJECT_ID:YOUR_DATASET.sales_parquet \
  gs://YOUR_BUCKET/sales.parquet
```

Compare the bytes billed on each job in `INFORMATION_SCHEMA.JOBS_BY_PROJECT`. The Parquet load
reads far fewer bytes, because Parquet is columnar and compressed and the CSV is neither.

### 🌐 Needs a BigQuery project — verify the load landed correctly

Never trust a load job's exit code alone. Check the invariants:

```sql
SELECT
  COUNT(*)                        AS rows_loaded,
  COUNT(DISTINCT transaction_id)  AS distinct_transactions,
  MIN(sale_date)                  AS first_sale,
  MAX(sale_date)                  AS last_sale,
  SUM(sales_amount)               AS total_revenue
FROM `YOUR_PROJECT_ID.YOUR_DATASET.sales`;
```

The assertion that catches real problems: **`COUNT(*)` must equal `COUNT(DISTINCT
transaction_id)`.** If it does not, you have duplicates — which means either a non-idempotent
load or a double-delivered stream. This one query catches the single most common data defect in
this module.

---

## 🛠️ Common Errors and Fixes

**"Could not parse 'gs://…/sales.csv' as CSV: Could not parse '2026-01-15' as DATE for field
sale_date (position 2) starting at location 13."**

The file's date format does not match what BigQuery expects. BigQuery's `DATE` parsing accepts
`YYYY-MM-DD`. If your file has `15/01/2026` or `2026-01-15T00:00:00Z`, it will not coerce
silently — it fails. Fix the source, or load as `STRING` and cast in the query:

```sql
SELECT DATE(CAST(raw_date AS STRING)) AS sale_date FROM ...
```

**"Error while reading data, error message: CSV table encountered too many errors, giving up.
Rows: 12; errors: 1."**

BigQuery found a malformed row and gave up. Two controls:

```bash
-- Tolerate a few bad rows, record them in a log table.
--max_bad_records=10 --bad_field_delimiter=NULL
```

But understand what you are doing: `--max_bad_records` **silently discards** the bad rows. That
is acceptable for a scratch table and unacceptable for a financial ledger. For anything that
must be complete, load with a strict schema and route failures to a dead-letter path — exactly
what the course's `ingest_events` does with its ten reject reason codes.

**"The load job succeeded but the table has half the rows."**

Almost always one of two things:

1. **A previous load is still running** and interleaved with this one. Load jobs against the
   same destination table are not serialised by default. Use a different destination table per
   load, or `--replace=true` plus a `CREATE OR REPLACE TABLE` boundary.
2. **The source file was still being written** when the job read it. Load only closed files, or
   write to a temporary path and rename on completion.

**"Streaming insert returns HTTP 200 but rows are missing."**

Partial success. You must inspect the response body's `insertErrors` array and re-queue those
rows. This is not optional — a 200 means "the request was processed", not "every row was
stored".

**"Datastream fell behind and now there is a gap."**

The source's log retention expired before the stream caught up. There is no backfill: the
changes are gone. This is a conversation to have with the database team *before* it happens —
retention must exceed your worst-case catch-up time, with margin.

---

## 💡 Production Notes

### The load → verify → assert pattern

Never finish a load job with "the command exited 0". The pattern is:

1. **Load** into a temporary destination.
2. **Verify** the row count, the distinct-key count, and the row-count delta against the source.
3. **Assert** the invariants (unique keys, non-null required fields, value ranges).
4. **Promote** — swap the temporary table into place, or load with `--replace=true` only after
   the assertions pass.

This is the same discipline as the course's pipeline, where `ingest_events` returns both
`accepted` and `rejected` and the job fails when the counts do not match expectations.

### Make the load idempotent, in this order

1. **Derive the key from the data.** `dedup_key(event_id, partition)` — never a timestamp.
2. **Use `--replace=true`** for a full reload into a staging table.
3. **Use the gRPC Storage Write API with a write stream ID** if you need exactly-once and are
   streaming.
4. **Assert uniqueness after the load.** `COUNT(*) = COUNT(DISTINCT key)`.

### Batch versus stream — pick by latency requirement, not by modernity

| Requirement | Use |
|---|---|
| Daily or hourly, files in Cloud Storage | Batch load job |
| Scheduled pull from a SaaS source | Data Transfer Service |
| Sub-second freshness for new events | Storage Write API (gRPC) |
| Replicating an operational database | Datastream CDC |
| One-off report on external data | Federated query |
| High throughput with heavy preprocessing | Dataflow → BigQuery |

### The thing to put in the runbook

Write down, for each load: **the source, the schedule, the schema, the idempotency key, the
maximum bytes billed, and what happens on partial failure.** If any of those six is missing from
the runbook, it is missing from your understanding too — and it will be discovered during an
incident rather than before one.

---

## 🔑 Key Takeaways

- Choose the route by asking: **files, individual records, database changes, or a recurring
  pull?**
- Batch load jobs read **Cloud Storage or a local file**; formats are **Avro, CSV, JSON, ORC,
  Parquet**.
- **gRPC Storage Write API** is the recommended path for new projects: lower price, exactly-once
  with a write stream ID, Iceberg streaming. **REST** is legacy and at-least-once.
- REST's `insertId` dedupe is **best-effort for about a minute** — a performance hint, not a
  correctness mechanism.
- **Partial success is real.** HTTP 200 does not mean every row landed. Check `insertErrors`.
- **Datastream CDC** captures state changes, not intent, and inherits the source's log retention.
  Negotiate that retention *before* you need it.
- **Federated queries** avoid a copy entirely — right for occasional reads, wrong for constant
  ones.
- Verify every load with `COUNT(*) = COUNT(DISTINCT key)`. It catches the most common defect in
  this module.

---

## 📚 Practice Exercises

1. Write a decision table mapping each of these requirements to a loading route, and justify each
   choice in one sentence: (a) nightly CSV files from a partner SFTP drop, (b) clickstream events
   needing 5-second freshness, (c) a monthly finance report over a third-party warehouse, (d)
   keeping a warehouse in sync with a production Postgres that we do not own.

2. Explain the difference between at-least-once and exactly-once delivery to a colleague, and then
   state which of the two the legacy REST streaming path provides, which one the gRPC path can
   provide and under what condition, and what you would build if you had to stay on REST.

3. Explain why `insertId` is a performance hint rather than a correctness mechanism. Your answer
   must include the roughly one-minute window and the fact that rows sharing an ID are assumed
   identical.

4. Build the idempotency key for a load of order events into a table partitioned by order date.
   Then explain, in detail, what breaks if the key is instead derived from the load timestamp, and
   construct a scenario with two retries that silently produces double-counted revenue.

5. A load job exits successfully, and a subsequent `COUNT(*)` on the destination table returns
   fewer rows than the source file. List every plausible cause in the order you would investigate
   them, and state the query you would run at each step to distinguish between them.

6. Using `estimate` from `project/core/cost_model.py`, model the monthly cost of ingesting 500 GB
   a day via Pub/Sub and reading the whole dataset back once a week. Print each figure, and
   identify which term dominates and what you would change to move it.

7. A Datastream stream fell behind and hit the source database's log retention limit. Explain
   precisely what is lost, why it cannot be recovered, and write the two sentences you would
   send to the database team to renegotiate the retention period — including the number you would
   ask for and how you would derive it.

8. Explain why `--autodetect=true` is acceptable for exploration and dangerous in production.
   Name a specific schema inference that would break a production load, state the error the
   failing load would produce, and describe the mitigation.

---

## 📖 Further Reading

- [Introduction to loading data](https://docs.cloud.google.com/bigquery/docs/loading-data)
- [Streaming data into BigQuery](https://docs.cloud.google.com/bigquery/docs/streaming-data-into-bigquery)
- [BigQuery Data Transfer Service](https://docs.cloud.google.com/bigquery/docs/dts-introduction)
- [Loading CSV data from Cloud Storage](https://docs.cloud.google.com/bigquery/docs/loading-data-cloud-storage-csv)
- [Exporting table data](https://docs.cloud.google.com/bigquery/docs/exporting-data)
- [Querying external data sources](https://docs.cloud.google.com/bigquery/external-data-sources)
- [Using the bq command-line tool](https://docs.cloud.google.com/bigquery/docs/bq-command-line-tool)
- [Course interview bank: Streaming and Ingestion](../interview/04-streaming-and-ingestion.md)
