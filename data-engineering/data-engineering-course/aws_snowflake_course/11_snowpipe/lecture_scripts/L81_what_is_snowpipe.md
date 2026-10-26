---
l_id: L81
title: What is Snowpipe?
duration: "6:30"
prereqs: ["L80 - Unload data"]
---

# L81 — What is Snowpipe?

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 11 — Snowpipe
> **Duration:** 6:30

## Prereqs

You're comfortable with `COPY INTO <table>` and external stages on
S3 / GCS / Azure (covered earlier in this course).

## Lecture

### The 30-second definition

**Snowpipe** is a serverless, event-driven data-load service built
into Snowflake. You define a **pipe** (a named object) that wraps a
`COPY INTO` statement and points at an external stage. Snowflake
listens to cloud-storage events for that stage, and whenever a new
file lands, Snowflake loads it within ~1–2 minutes — with **no
warehouse to manage**.

### Snowpipe vs batch `COPY INTO`

| | Batch `COPY INTO` | Snowpipe |
|---|---|---|
| Trigger | You / a task runs it | Cloud event (file arrival) |
| Compute | Your warehouse (size + auto-suspend) | Snowflake-managed serverless |
| Latency | Minutes–hours | Seconds–1–2 minutes |
| Cost model | Warehouse seconds | Per file loaded (~0.04 credits/1000 files, varies) |
| Best for | Bulk backfills, hourly/daily drops | Continuous small-file streams |
| Backpressure | Warehouse queues the work | Snowflake throttles if you overwhelm it |

### The three Snowpipe flavors

1. **Auto-ingest Snowpipe** (this section) — cloud pushes an event
   notification. This is what 95% of people mean when they say
   "Snowpipe".
2. **Snowpipe Streaming** — client SDK writes row-by-row over a
   streaming API, bypassing files entirely. High-throughput,
   sub-second latency. Newer, different mental model.
3. **Snowpipe via the REST `insertFiles` endpoint** — you call the
   endpoint yourself from anywhere. Useful for ad-hoc loads from
   serverless functions.

We'll cover flavor #1 here. Flavor #2 is in the extra-topics
appendix; #3 is a niche tool you can read about when you need it.

### The pipe object

```sql
-- A pipe is just a name + a COPY INTO
CREATE OR REPLACE PIPE my_db.raw.orders_pipe
  AUTO_INGEST = TRUE
AS
COPY INTO my_db.raw.orders_gcs
FROM @my_db.raw.my_gcs_stage
FILE_FORMAT = (FORMAT_NAME = 'ff_csv_gcs');
```

- `AUTO_INGEST = TRUE` — Snowflake creates and manages the
  SQS queue (S3), Pub/Sub topic (GCS), or Event Grid subscription
  (Azure).
- The pipe *stores* the `COPY INTO` so Snowflake can replay it on
  each event.
- `SHOW PIPES` shows you the notification channel name — that's
  what you wire up to the cloud side.

### Cost intuition

- Auto-ingest Snowpipe charges per file loaded (roughly 0.04
  credits per 1,000 files on Standard edition — check the current
  rate card).
- The compute is fully serverless; you do not size or scale a
  warehouse.
- A Snowpipe that processes 100 files a day is essentially free
  in credits. A Snowpipe that processes 10 million files a day is
  an architecture conversation.

## Key takeaways

- Snowpipe = serverless `COPY INTO` triggered by cloud-storage
  events.
- Three flavors: auto-ingest (this section), streaming (SDK),
  REST `insertFiles`.
- Pricing is per-file, not per-warehouse-second.

## What's next

In **L82 — High-level steps (Snowpipe)** we walk through the five
clicks / commands you need to go from a bucket to a working pipe on
GCS.
