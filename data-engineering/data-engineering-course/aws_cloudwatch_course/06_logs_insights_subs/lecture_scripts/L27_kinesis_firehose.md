---
lecture: L27
title: "Kinesis Data Streams + Firehose as Destinations"
duration: "12:00"
section: 6
prereqs: ["L26"]
---

# L27 — Kinesis Data Streams + Firehose as Destinations

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 6 — Logs Insights + Subscriptions
> **Duration:** 12:00

## Prereqs

L26 (filter pattern syntax).

## Key terms

- **Kinesis Data Streams (KDS)** — a low-level real-time stream.
  Records stay until you expire them (default 24h, max 365d). You
  provision **shards**.
- **Kinesis Data Firehose** — a *delivery* stream. Auto-batches,
  optionally transforms records with a Lambda, delivers to S3 /
  Redshift / OpenSearch / HTTP endpoint. No shards to manage.
- **Shard** — the unit of throughput in KDS. 1 MB/s write, 2 MB/s
  read; 1,000 records/s.
- **`PutRecord` / `PutRecords`** — the API calls KDS / Firehose use to
  ingest a record.

## Lecture

The two *streaming* destinations for subscription filters. Pick
**Firehose** if you just want to land events in S3 / OpenSearch;
pick **KDS** if you want to do per-record processing with a Lambda
consumer or Kinesis Data Analytics.

### Kinesis Data Streams

```python
import boto3
kinesis = boto3.client("kinesis")
kinesis.create_stream(StreamName="logs-stream", ShardCount=1)

# Then in put_subscription_filter:
#   destinationArn = "arn:aws:kinesis:us-east-1:111122223333:stream/logs-stream"
```

**Pros:**

- Sub-second latency.
- Records are durably stored (replicated across 3 AZs).
- Replayable: you can re-read events from the past N days.

**Cons:**

- You manage shards. Pick wrong size → cost or throttling.
- You write the consumer (Lambda, KCL, etc.).
- Records ≤ 1 MB (subscription filter events are tiny so OK).

### Kinesis Data Firehose

```python
firehose = boto3.client("firehose")
firehose.create_delivery_stream(
    DeliveryStreamName="logs-firehose",
    DeliveryStreamType="DirectPut",
    S3DestinationConfiguration={
        "RoleARN": "arn:aws:iam::111122223333:role/firehose-s3",
        "BucketARN": "arn:aws:s3:::my-logs-bucket",
        "Prefix": "raw/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/",
        "BufferingHints": {"SizeInMBs": 5, "IntervalInSeconds": 300},
        "CompressionFormat": "GZIP",
    },
)

# Then in put_subscription_filter:
#   destinationArn = "arn:aws:firehose:us-east-1:111122223333:deliverystream/logs-firehose"
```

**Pros:**

- No shards to manage — auto-scales.
- Buffers up to 5 MB / 5 min before flushing (configurable).
- Can transform records with a Lambda before delivery.
- Native S3 partition patterns (`year=YYYY/month=MM/...`).

**Cons:**

- Higher end-to-end latency (buffers).
- Records are *not* replayable from Firehose itself (but you can read
  them from S3).

### Decision matrix

| Need | Pick |
|---|---|
| Land in S3 / OpenSearch for analytics | Firehose |
| Need sub-second latency for alerting | KDS + Lambda |
| Want to replay past events | KDS |
| Want to transform records before S3 | Firehose + Lambda transform |
| Building a Kinesis Data Analytics pipeline | KDS |

### Buffering tuning for Firehose

The defaults are **5 MB / 5 min**. For debugging "where are my
ERRORs?", that's a long wait. Tighten the interval:

```python
"BufferingHints": {"SizeInMBs": 1, "IntervalInSeconds": 60}
```

This flushes every minute or every 1 MB, whichever comes first.

## Hands-on

In your AWS account, create a Firehose delivery stream that targets
an S3 bucket you own, with the partitioning prefix above. Then point
a subscription filter at it.

```bash
aws firehose create-delivery-stream --cli-input-json file://firehose.json
```

## Quiz prep

- Which is replayable — KDS or Firehose? (KDS.)
- How many subscription filters per log group? (2.)
- What are the default Firehose buffering hints? (5 MB / 300 s.)

## Further reading

- `https://docs.aws.amazon.com/firehose/latest/dev/what-is-this-service.html`
- `https://docs.aws.amazon.com/streams/latest/dev/introduction.html`

## What's next

L28 — Lambda as a Subscription Destination.
