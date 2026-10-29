---
l_id: L82
title: High-level steps (Snowpipe)
duration: "6:00"
prereqs: ["L81 - What is Snowpipe?"]
---

# L82 — High-level steps (Snowpipe)

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 11 — Snowpipe
> **Duration:** 6:00

## Prereqs

You have a GCS bucket (L76), a storage integration (L77), and an
external stage pointing at it (L78). You have a working
`COPY INTO` that loads from that stage (L79).

## Lecture

The whole Snowpipe setup is five steps. Don't memorize the SQL —
internalize the **shape**: cloud side first, then Snowflake side,
then you point cloud at Snowflake.

### Step 1 — Confirm the cloud side

You need a bucket, a service account Snowflake can assume, and
permission to grant that service account `roles/storage.objectCreator`
on the bucket. We did all of this in L76–L78. If you can run
`LIST @my_gcs_stage` and see files, you're done with step 1.

### Step 2 — Create the target table

Same DDL you would write for a batch load:

```sql
CREATE OR REPLACE TABLE raw.orders_gcs (
  order_id    NUMBER,
  customer_id NUMBER,
  order_date  DATE,
  amount      NUMBER(10,2)
);
```

### Step 3 — Create the pipe

```sql
CREATE OR REPLACE PIPE raw.orders_pipe
  AUTO_INGEST = TRUE
AS
COPY INTO raw.orders_gcs
FROM @raw.my_gcs_stage
FILE_FORMAT = (FORMAT_NAME = 'ff_csv_gcs');
```

`AUTO_INGEST = TRUE` is the magic flag — it tells Snowflake to
provision a Pub/Sub topic for this pipe and to subscribe to events
from your bucket.

### Step 4 — Get the notification channel

```sql
SHOW PIPES LIKE 'orders_pipe';
```

Look for the `notification_channel` column. It will look something
like:

```
gcs://snowflake-customer-xxx/yyy
```

That is the resource Snowflake expects to receive Pub/Sub events on.

### Step 5 — Wire the bucket to the pipe

In GCP, you create a **Pub/Sub subscription** on Snowflake's topic
(filtered to the bucket's `object.finalize` events) and you set the
bucket's notification configuration to publish to that topic. From
that point on, every new file in the bucket triggers a Snowpipe
load.

### What "done" looks like

1. You `PUT` a new file to the bucket.
2. GCS fires `OBJECT_FINALIZE`.
3. Pub/Sub forwards the event to the topic Snowflake owns.
4. Snowpipe runs the wrapped `COPY INTO` against that single file.
5. Within ~1–2 minutes the rows are in `raw.orders_gcs`.

You can verify by querying `SELECT * FROM raw.orders_gcs ORDER BY
order_date DESC LIMIT 10;` after you drop a file.

## Key takeaways

- Five steps: confirm cloud, create table, create pipe, get
  notification channel, wire bucket to pipe.
- `AUTO_INGEST = TRUE` is what makes Snowflake provision the
  event channel for you.
- The pipe stores a `COPY INTO` — same statement, just triggered
  by events instead of by you.

## What's next

In **L83 — Creating stage (Snowpipe)** we revisit the GCS stage
specifically in the Snowpipe context, plus cover the
notification-channel name.
