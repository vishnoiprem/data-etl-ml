# Section 11 — Snowpipe

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Lectures:** L79–L85
> **Duration:** ~50 min

In this section we round out the loading story with **Snowpipe** —
Snowflake's serverless, event-driven auto-ingest service. So far in
this course every `COPY INTO` we've run has been **batch**: you or a
task schedules it, a warehouse spins up, files are loaded, the
warehouse suspends. That works for hourly or daily drops, but a lot of
modern pipelines want data inside Snowflake within **seconds** of a
file landing in S3, GCS, or Azure Blob — without anyone standing up a
warehouse.

Snowpipe is the answer. A **pipe** is a named Snowflake object that
encapsulates a `COPY INTO` statement, watches a stage, and reacts to
cloud-storage events (SQS, GCS Pub/Sub, Event Grid) by loading new
files automatically. The compute is a serverless Snowflake-managed
engine — you don't size a warehouse, you pay per file loaded.

By the end of this section you will have queried data we already loaded
from GCS (recap), unloaded data back out with `COPY INTO ... LOCATION=`,
and stood up a working Snowpipe on GCS that auto-loads new files
arriving in a bucket.

| L# | Title | Min |
|---|---|---|
| L79 | Query & load data (GCS) | 6:00 |
| L80 | Unload data (`COPY INTO ... LOCATION=`) | 7:00 |
| L81 | What is Snowpipe? | 6:30 |
| L82 | High-level steps (Snowpipe) | 6:00 |
| L83 | Creating stage (Snowpipe) | 7:00 |
| L84 | Create & configure pipe | 9:00 |
| L85 | Configure pipe & notifications | 8:30 |

## Key concepts you'll need later

- **Snowpipe** — serverless, event-driven auto-ingest. Listens to a
  cloud event source, loads new files within ~minutes, no warehouse
  to manage.
- **Pipe** — a named Snowflake object that wraps a `COPY INTO`
  statement and points at an external stage + notification
  integration.
- **Auto-ingest** — Snowflake creates the SQS queue (AWS) /
  Pub/Sub topic (GCS) / Event Grid subscription (Azure); your
  producer just drops files in the bucket.
- **`COPY INTO ... LOCATION=`** — the unload direction. Same syntax
  family as `COPY INTO <table>` but writes files out to a stage.
- **Serverless compute cost** — billed per file loaded, not per
  warehouse second. Best for steady small-file streams, not bulk
  backfills.

## What comes next

Section 12 is **Cortex AI & Machine Learning** — the modern
text-and-media AI surface in Snowflake. We start with Snowpipe error
handling, then jump into Cortex AI SQL functions, Cortex Search,
Cortex Analyst, and a hands-on AI scenario that ties most of it
together.
