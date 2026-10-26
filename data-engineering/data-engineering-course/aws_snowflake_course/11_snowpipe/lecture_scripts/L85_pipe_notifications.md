---
l_id: L85
title: Configure pipe & notifications
duration: "8:30"
prereqs: ["L84 - Create & configure pipe"]
---

# L85 — Configure pipe & notifications

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 11 — Snowpipe
> **Duration:** 8:30

## Prereqs

Pipe is created and `DESC PIPE` returns a `notification_channel`
starting with `gcs://`.

## Lecture

In L84 we created the pipe on the Snowflake side. In this lecture we
close the loop on the **GCP** side: Pub/Sub subscription + bucket
notification config. The shape is the same on AWS (SQS) and Azure
(Event Grid); only the resource names change.

### 1. Find the notification channel

```sql
DESC PIPE raw.orders_pipe;
```

Note the `notification_channel_name` — it looks like
`snowflake-customer-<account>-<region>/<pipe_id>`. The `<pipe_id>`
uniquely identifies *this* pipe's Pub/Sub topic.

### 2. Create a Pub/Sub subscription

In `gcloud`:

```bash
# Snowflake owns the topic; you create the subscription on it
gcloud pubsub subscriptions create orders-pipe-sub \
  --topic=snowflake-customer-<account>-<region>-<pipe_id> \
  --ack-deadline=60 \
  --message-retention-duration=7d
```

You can also add a filter so only `OBJECT_FINALIZE` events reach
Snowflake:

```bash
gcloud pubsub subscriptions update orders-pipe-sub \
  --message-filter='attributes.eventType="OBJECT_FINALIZE"'
```

### 3. Configure the bucket notification

Tell the bucket to publish object events to Snowflake's topic:

```bash
gsutil notification create \
  -t snowflake-customer-<account>-<region>-<pipe_id> \
  -f json \
  -e OBJECT_FINALIZE \
  gs://my-snowflake-demo-bucket
```

You should see:

```json
{ "service": "CLOUD_STORAGE", "eventTypes": ["OBJECT_FINALIZE"], ... }
```

### 4. Smoke test

```bash
# Drop a file
gsutil cp orders_2024_03.csv gs://my-snowflake-demo-bucket/orders/

# Wait ~60–90 seconds
```

Then verify on the Snowflake side:

```sql
SELECT file_name, status, row_count, last_loaded_time
FROM TABLE(INFORMATION_SCHEMA.PIPE_USAGE_HISTORY(
  DATE_RANGE_START => DATEADD('minute', -10, CURRENT_TIMESTAMP())
))
WHERE pipe_name = 'ORDERS_PIPE'
ORDER BY last_loaded_time DESC;

SELECT COUNT(*) FROM raw.orders_gcs;
```

You should see one new row in `PIPE_USAGE_HISTORY` with
`status = 'LOADED'` and the row count in `orders_gcs` should be
higher than before.

### 5. Common gotchas

- **Wrong topic name.** The `notification_channel_name` is
  per-pipe. Re-creating the pipe gives you a new name.
- **Bucket-level IAM.** The Snowflake service account needs
  `roles/storage.objectViewer` (read) and your producer needs
  `roles/storage.objectCreator` (write) on the bucket.
- **File format drift.** If the producer switches from
  comma-delimited to tab-delimited, the pipe fails. Either update
  the file format object or use a `MATCH_BY_COLUMN_NAME` copy
  option.
- **Cross-region cost.** Pub/Sub between regions can add latency
  and egress fees; keep the bucket and the Snowflake account in
  the same region when possible.

### 6. Operational hygiene

- `PIPE_USAGE_HISTORY` for per-file load details.
- `COPY_HISTORY` for the underlying load history (same rows,
  slightly different shape).
- `SYSTEM$PIPE_STATUS('<pipe>')` for a quick JSON health snapshot.

## Key takeaways

- The notification channel is created for you; you just attach a
  Pub/Sub subscription and a bucket notification rule.
- `OBJECT_FINALIZE` is the event that triggers Snowpipe — fired
  when a write to the bucket closes.
- `PIPE_USAGE_HISTORY` and `SYSTEM$PIPE_STATUS` are your two
  operational tools for a healthy pipe.

## What's next

In **L86 — Error handling for Snowpipe loads** we look at what
happens when files fail validation: error integrations, the
`VALIDATE_PIPE` function, and the `ON_ERROR` options that matter
for pipes.
