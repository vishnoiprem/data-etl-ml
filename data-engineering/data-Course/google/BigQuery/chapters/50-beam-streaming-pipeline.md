# 9.2 — Apache Beam: Streaming Pipeline

> **Section 9 · Pub/Sub & Streaming · Lecture 9.2 · 6:50**

## 🎯 What you will learn

- Streaming fundamentals in Beam: unbounded `PCollection`s, windows, and triggers
- A Pub/Sub → Dataflow → BigQuery streaming pipeline
- Windowing: fixed, sliding, and session windows
- Combining, state, and deduplication in a streaming context
- Exactly-once semantics and the BigQuery streaming buffer

---

## 🧠 Concept

A streaming pipeline processes an **unbounded** collection — data that never ends. Beam
handles this with three additions to the batch model:

1. **Windows** — group elements by time
2. **Triggers** — decide when to emit results
3. **State & timers** — remember things across the stream

```
Batch:  ReadFromText(...)      → finite
Stream: ReadFromPubSub(...)    → unbounded
```

---

## 🧠 The three output modes

| Mode | When output is emitted | Latency | Cost |
|------|------------------------|---------|------|
| **Streaming** | Continuously, as data arrives | Seconds | Higher — per-window processing |
| **Batch** | At the end of the window | Hours | Lower |
| **Hybrid** | Streaming, then periodically a final batch window | Seconds, then corrected | Highest |

💡 **Hybrid mode is the right choice for financial reporting.** You get live numbers, and
periodic batch windows reconcile them exactly. This is how you avoid "the dashboard changed
and now the revenue is different."

---

## 🛠️ Hands-On

### 1. A complete streaming pipeline

```python
"""
beam_stream_ingest.py — Pub/Sub → BigQuery, continuously.
"""
from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone

import apache_beam as beam
from apache_beam.io.gcp import bigquery_io
from apache_beam.io.gcp.bigquery_io import BigQueryDisposition
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions
from apache_beam.transforms.window import FixedWindows, TimestampedValue
from apache_beam.utils.timestamp import Timestamp

log = logging.getLogger(__name__)

PROJECT = "YOUR_PROJECT_ID"
BUCKET = "gs://YOUR_PROJECT_ID-bq-course"
TOPIC = "projects/YOUR_PROJECT_ID/topics/retailmart.events"
TABLE = "retailmart.raw.events"

EVENT_SCHEMA = {
    "fields": [
        {"name": "event_id", "type": "STRING", "mode": "REQUIRED"},
        {"name": "user_id", "type": "STRING", "mode": "REQUIRED"},
        {"name": "event_type", "type": "STRING", "mode": "REQUIRED"},
        {"name": "amount", "type": "NUMERIC"},
        {"name": "event_ts", "type": "TIMESTAMP"},
        {"name": "event_date", "type": "DATE"},
        {"name": "ingested_at", "type": "TIMESTAMP"},
    ]
}


def to_event(message: bytes, attributes: dict) -> dict:
    """Decode a Pub/Sub message into a typed event row."""
    import json

    raw = json.loads(message.decode("utf-8"))

    # The event timestamp may come from the payload or the attribute
    event_ts = attributes.get("event_ts") or raw.get("event_ts")
    if isinstance(event_ts, (int, float)):
        event_ts = datetime.fromtimestamp(event_ts, tz=timezone.utc)
    elif isinstance(event_ts, str):
        event_ts = datetime.fromisoformat(event_ts.replace("Z", "+00:00"))

    return {
        "event_id": raw["event_id"],
        "user_id": raw.get("user_id"),
        "event_type": raw.get("event_type"),
        "amount": raw.get("amount"),
        "event_ts": event_ts.isoformat() if event_ts else None,
        "event_date": event_ts.date().isoformat() if event_ts else None,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner", default="DataflowRunner")
    parser.add_argument("--window_seconds", type=int, default=300)
    args, beam_args = parser.parse_known_args(argv)

    options = PipelineOptions(beam_args)
    options.view_as(SetupOptions).save_main_session = True

    with beam.Pipeline(options=options) as p:
        (
            p
            | "Read Pub/Sub" >> beam.io.ReadFromPubSub(
                topic=TOPIC,
                with_attributes=True,
                id_label="event_id",
            )
            | "Parse" >> beam.Map(to_event)
            | "Window (5 min)" >> beam.WindowInto(
                FixedWindows(args.window_seconds)
            )
            | "Write BQ" >> bigquery_io.WriteToBigQuery(
                TABLE,
                schema=EVENT_SCHEMA,
                create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
                write_disposition=BigQueryDisposition.WRITE_APPEND,
                custom_gcs_temp_location=f"{BUCKET}/beam/bq_tmp",
                with_sharding=True,
            )
        )


if __name__ == "__main__":
    run()
```

### 2. Launch it on Dataflow

```bash
python beam_stream_ingest.py \
  --runner DataflowRunner \
  --project YOUR_PROJECT_ID \
  --region europe-west1 \
  --temp_location gs://YOUR_PROJECT_ID-bq-course/beam/tmp \
  --staging_location gs://YOUR_PROJECT_ID-bq-course/beam/staging \
  --streaming \
  --window_size 300 \
  --save_main_session \
  --autoscaling_algorithm=THROUGHPUT_BASED \
  --max_num_workers=20 \
  --machine_type=n1-standard-2
```

```bash
# With streaming update for faster worker startup
python beam_stream_ingest.py \
  --runner DataflowRunner \
  --streaming_update \
  --sdk_location=gs://YOUR_PROJECT_ID-bq-course/beam/sdk \
  ...
```

💡 **`--streaming_update`** restarts only the changed workers instead of the whole job. It
drastically shortens deployments of a streaming job.

### 3. Windowing — the core streaming concept

```python
from apache_beam.transforms.window import FixedWindows, SlidingWindows, SessionWindows, IntervalWindow
from apache_beam.transforms.trigger import (
    AfterCount,
    AfterProcessingTime,
    AfterWatermark,
    AccumulateMode,
)

# Fixed windows: non-overlapping buckets
| "Fixed 1 min" >> beam.WindowInto(FixedWindows(60))

# Sliding windows: overlapping buckets
| "Sliding 5 min every 1 min" >> beam.WindowInto(
    SlidingWindows(size=300, period=60)
)

# Session windows: grouped by activity gaps
| "Session 30 min gap" >> beam.WindowInto(SessionWindows(gap_size=1800))
```

```python
# Trigger: emit after 1000 elements OR after 30 seconds of processing time
| "Trigger" >> beam.WindowInto(
    FixedWindows(60),
    trigger=AfterCount(1000).or_later(AfterProcessingTime(30)),
    accumulation_mode=AccumulateMode.ACCUMULATE,
)
```

| Trigger | Fires when | Use case |
|---------|-----------|----------|
| `AfterCount(n)` | n elements seen | Batch-like, low latency |
| `AfterProcessingTime(d)` | d seconds of processing | Latency bound |
| `AfterWatermark()` | Watermark passes the window end | Complete, accurate data |
| `DefaultTrigger` | At the end of each window | Simple aggregations |

💡 **The watermark is the estimated "no more data before this time" marker.** Beam advances it
based on observed event timestamps. Late data (beyond the watermark) is dropped unless you
set an allowed lateness.

```python
| "Allow lateness" >> beam.WindowInto(
    FixedWindows(60),
    allowed_lateness=3600,      # 1 hour
)
```

### 4. Aggregating per window

```python
from apache_beam import combiners, window

with beam.Pipeline(options=options) as p:
    (
        p
        | "Read" >> beam.io.ReadFromPubSub(topic=TOPIC, with_attributes=True)
        | "Parse" >> beam.Map(to_event)
        | "Key by event_type" >> beam.Map(lambda e: (e["event_type"], e))
        | "Window" >> beam.WindowInto(FixedWindows(300))
        | "Count per type" >> combiners.Count.PerKey()
        | "Format" >> beam.Map(
            lambda kv: {
                "event_type": kv[0],
                "event_count": kv[1],
                "window_end": kv[0] and int(kv[0]) if False else None,
            }
        )
        | "Write" >> bigquery_io.WriteToBigQuery(
            "retailmart.mart.event_counts",
            write_disposition=BigQueryDisposition.WRITE_APPEND,
        )
    )
```

### 5. Session windows — grouping a user journey

```python
from apache_beam.transforms.window import SessionWindows

(
    p
    | "Read" >> beam.io.ReadFromPubSub(topic=TOPIC, with_attributes=True)
    | "Parse" >> beam.Map(to_event)
    | "Key by user" >> beam.Map(lambda e: (e["user_id"], e))
    | "Session" >> beam.WindowInto(SessionWindows(gap_size=1800))   # 30 min gap
    | "Per session" >> beam.Map(lambda kv: (kv[0], kv[1]))
    | "Summarise" >> beam.Map(
        lambda kv: {
            "user_id": kv[0],
            "event_count": len(kv[1]),
            "session_start": min(e["event_ts"] for e in kv[1]),
            "session_end": max(e["event_ts"] for e in kv[1]),
            "total_amount": sum(float(e["amount"] or 0) for e in kv[1]),
        }
    )
    | "Write" >> bigquery_io.WriteToBigQuery(
        "retailmart.mart.user_sessions",
        write_disposition=BigQueryDisposition.WRITE_APPEND,
    )
)
```

💡 **Session windows need an allowed lateness** to be useful. A session that ends 20 minutes
ago can still receive an event, which extends the session backwards. Beam handles this by
re-firing the window.

### 6. State and timers — memory across the stream

```python
class DeduplicateEvents(beam.DoFn):
    """Deduplicate by event_id using a bounded cache."""

    CACHE_SIZE = 100_000

    def __init__(self):
        self._seen = set()
        self._order = deque()

    def process(self, event, window=beam.DoFn.WindowParam):
        event_id = event["event_id"]

        if event_id in self._seen:
            yield {"duplicate": event_id}
            return

        self._seen.add(event_id)
        self._order.append(event_id)
        if len(self._order) > self.CACHE_SIZE:
            self._seen.discard(self._order.popleft())

        yield event


(
    p
    | "Read" >> beam.io.ReadFromPubSub(topic=TOPIC)
    | "Parse" >> beam.Map(to_event)
    | "Dedupe" >> beam.ParDo(DeduplicateEvents())
    | "Write" >> bigquery_io.WriteToBigQuery(TABLE, schema=EVENT_SCHEMA)
)
```

```python
# Stateful DoFn with a timer
class LateEventCounter(beam.DoFn):
    def process(self, element, timestamp=beam.DoFn.TimestampParam):
        key = element["user_id"]
        self._counts[key] = self._counts.get(key, 0) + 1
        self._output.add(key)
        yield element

    def on_timer(self, timestamp=beam.DoFn.TimerParam, window=beam.DoFn.WindowParam,
                 ts=beam.DoFn.TimerParam, key=beam.DoFn.KeyParam):
        yield {
            "user_id": key,
            "window_end": ts.isoformat(),
            "count": self._counts.get(key, 0),
        }
```

💡 **Beam's `DoFn.State` and `DoFn.Timer` are the right way to hold state.** A plain Python
attribute is per-instance and per-bundle, which means it is **not** guaranteed to be correct
across bundles or workers.

### 7. Hybrid mode — streaming with periodic batch reconciliation

```python
from apache_beam import window as beam_window
from apache_beam.transforms.window import FixedWindows

with beam.Pipeline(options=options) as p:
    (
        p
        | "Read" >> beam.io.ReadFromPubSub(topic=TOPIC, with_attributes=True)
        | "Parse" >> beam.Map(to_event)
        | "Window" >> beam.WindowInto(FixedWindows(300))
        | "Streaming counts" >> beam.Map(lambda e: (e["event_type"], 1))
        | "Sum" >> combiners.Sum.PerKey()
        | "Write streaming" >> bigquery_io.WriteToBigQuery(
            "retailmart.mart.event_counts_streaming",
            write_disposition=BigQueryDisposition.WRITE_APPEND,
        )
    )
```

```bash
# Hybrid mode with a periodic batch window
python beam_stream_ingest.py \
  --runner DataflowRunner \
  --streaming \
  --batch_window 3600 \
  ...
```

💡 **Hybrid mode gives you both.** Streaming results arrive every 5 minutes for the live
dashboard; a batch window every hour produces the authoritative number by re-reading the
window with the watermark fully advanced.

### 8. The BigQuery streaming buffer — what you need to know

```sql
-- The streaming buffer is queryable but not cached
SELECT COUNT(*) FROM `retailmart.raw.events`;

-- Total rows ever, including the buffer
SELECT
  total_rows,
  total_logical_bytes,
  total_physical_bytes
FROM `retailmart.raw.events.__TABLES__`;
```

| Behaviour | Detail |
|-----------|--------|
| **Not cached** | A query that hits the buffer never uses the result cache |
| **Billed at active storage** | Buffer data costs 50% more than long-term storage |
| **Streaming inserts free up to 1 GB/day/table** | After that, $0.01 per 200 MB |
| **Row limit** | 1,000 rows per insert request, 10 MB per request |
| **Table limit** | 1,000 tables per project can be streaming-enabled |
| **Deletion** | Deleting a streaming buffer row does not free storage until 24h later |

### 9. Exactly-once in the streaming path

```python
# Dataflow's exactly-once write to BigQuery
options = PipelineOptions(beam_args)
options.view_as(DataflowRunnerOptions).experiments = ["enable_cdf_2"]
```

💡 **The strongest guarantee is still the "BigQuery table as the source of truth" pattern:**
read from BigQuery (not from the topic) when you need a complete, deduplicated history. Pub/Sub
gives you the stream; BigQuery gives you the record.

### 10. Monitoring a streaming job

```bash
# Dataflow job metrics
gcloud dataflow jobs describe <job-id> --region=europe-west1 \
  --format="value(status)"

# BigQuery streaming buffer stats
bq show --format=json YOUR_PROJECT_ID:retailmart.raw.events | jq '.streamingBuffer'
```

```python
# Worker lag / backlog
from apache_beam.runners.dataflow.runner import DataflowPipelineRunner

# In practice: monitor in Cloud Monitoring
# Metric: dataflow.googleapis.com/worker/execution_parallelism
# Metric: dataflow.googleapis.com/worker/worker_healthy
```

---

## 🛠️ Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `AttributeError: 'NoneType' object has no attribute ...` in `DoFn` | State used across bundles | Use `DoFn.State` with a spec |
| `Dataflow job keeps restarting` | OOM on a worker | Increase `--machine_type` or reduce the window |
| `Duplicate rows in BigQuery` | At-least-once delivery | Deduplicate on `event_id` |
| `Pipeline stuck: watermark not advancing` | All events have the same future timestamp | Check the timestamp parsing; use event time correctly |
| `Late data dropped` | Watermark advanced past the window | Set `allowed_lateness` |
| `BigQuery quota: too many API requests` | Per-row inserts | Use `WriteToBigQuery` with sharding, not `insert_rows` |
| `Session window never fires` | Continuous activity | Add a `GapDetectionTrigger` or use fixed windows |
| `Resource exhausted: BigQuery per-table rate` | Streaming insert rate limit | Batch inserts, or use the Dataflow sink |

---

## 💡 Production Notes

- **Use the Dataflow BigQuery sink, not `insert_rows_json`.** The sink batches, shards, and
  handles backpressure.
- **Choose window size from your SLA.** 5-minute windows with a 5-minute SLA is a race; use
  1-minute windows if you need sub-5-minute latency.
- **State must be in `DoFn.State`**, not a Python attribute.
- **Set `allowed_lateness`** whenever late events matter, and understand that it increases cost.
- **Use the BigQuery table as the authoritative record.** Streams are ephemeral; tables are not.
- **Monitor watermark lag**, not just throughput. A stalled watermark means missing data.
- **Version your streaming job like any other code** — a broken deploy takes the whole feed
  down.
- **Dead-letter in Beam**: catch exceptions in the `DoFn`, write failures to a side output, and
  let the main path continue.

---

## 🔑 Key Takeaways

- Streaming = unbounded `PCollection` + **windows** + **triggers** + **state/timers**.
- Three output modes: streaming, batch, hybrid. **Hybrid** is right for financial reporting.
- `FixedWindows`, `SlidingWindows`, `SessionWindows` — the window type is the design decision.
- Triggers control *when* results emit; `allowed_lateness` controls how much late data you keep.
- **State belongs in `DoFn.State`,** never in a plain attribute.
- The **BigQuery streaming buffer is not query-cached** and is billed at active storage rates.
- Use the **Dataflow BigQuery sink with `with_sharding=True`** — never per-row inserts.

---

## 📚 Practice Exercises

1. **Streaming pipeline from scratch.** Build a Pub/Sub → BigQuery pipeline that ingests orders,
   aggregates revenue per region per 5-minute window, and writes to a mart table. Test it
   locally with the Direct Runner.

2. **Window comparison.** Run the same aggregation with fixed, sliding, and session windows.
   Produce a table comparing latency, output row count, and cost. Write the recommendation for
   (a) a live ops dashboard, (b) daily reporting, (c) user journey analysis.

3. **Exactly-once investigation.** Construct a scenario where a worker dies mid-bundle. Show the
   duplicate rows. Then fix it with deduplication and prove the fix. Document the trade-off.

4. **Hybrid mode design.** Design a hybrid pipeline for revenue reporting: live numbers that
   are eventually corrected. Specify the tables, the windows, the triggers, and how the
   correction is applied without double-counting.

5. **Cost analysis.** Model the cost of streaming 400M events/day into BigQuery: Pub/Sub
   messages, Dataflow worker time, BigQuery streaming inserts, and the active-storage premium
   on the buffer. Compare with a batch alternative.

---

## 📖 Further Reading

- Beam windowing guide — https://beam.apache.org/documentation/sdks/python/apache-beam-intro/#windowing
- Dataflow streaming — https://cloud.google.com/dataflow/docs/streaming-processing
- BigQuery streaming data — https://cloud.google.com/bigquery/docs/streaming-data-into-bigquery
- BigQuery streaming buffer — https://cloud.google.com/bigquery/docs/streaming-data-into-bigquery#streaming_buffer
