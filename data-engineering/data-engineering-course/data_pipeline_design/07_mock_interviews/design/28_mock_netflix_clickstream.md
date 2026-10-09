# 28 — Mock Interview: Design Netflix's Clickstream Pipeline

> **Lesson 28 of 30 — Mock Interviews**

A full 30-minute mock interview transcript with a candidate
designing Netflix's clickstream pipeline. The candidate is a
Senior Data Engineer (L5 / E5 level) at a hypothetical
interview. The transcript includes the architecture diagram
drawn on the whiteboard and a post-interview analysis.

---

## Setup

**Company:** Netflix (hypothetical loop).
**Role:** Senior Data Engineer.
**Level:** L5 / E5.
**Format:** 30-minute system design round, on-site whiteboard.
**Question:** *"Design a pipeline to ingest, process, and serve
Netflix's clickstream data — every play, pause, scrub, and
browse event from 250M users worldwide."*

---

## Transcript (30 minutes)

### 0:00 — Opening framing

> **Candidate:** Before I draw anything, let me make sure I
> understand the problem. You said 250M users — that's MAU or
> DAU? And when you say "clickstream," are we talking about
> every UI interaction, or just the major ones — play, pause,
> search, browse? And what's the consumer of the data?
> Real-time personalization, or is this an offline
> recommender training pipeline?

> **Interviewer:** Assume 250M DAU. Every UI event — clicks,
> scrolls, hovers, plays, pauses. Some events are 100/sec per
> user during a browse session, more during playback.
> Consumers: real-time personalization, A/B test analysis,
> offline recommender training, content acquisition.

> **Candidate:** Got it. So we're looking at high-volume
> (~50 billion events per day) with a mix of latency
> requirements — real-time personalization needs sub-minute,
> A/B test analysis is hourly, offline training is daily.
> The diversity of consumers is the key design driver.
>
> Let me lay out the high-level architecture. **[DRAWING 1]**
> I'll come back to the deep dive.

### 2:00 — High-level architecture

```
┌────────────┐    ┌────────────┐    ┌──────────────┐    ┌────────────┐
│ Clients    │───►│ API gateway│───►│ Kafka         │───►│ Stream     │
│ (mobile,   │    │ (REST/gRPC)│    │ (12+ topics, │    │ processor  │
│  web, TV)  │    │            │    │  partitioned │    │ (Flink)    │
└────────────┘    └────────────┘    │  by user_id) │    └─────┬──────┘
                                   └──────┬───────┘          │
                                          │                  │
                                          │                  ▼
                                          │           ┌──────────────┐
                                          │           │ Real-time    │
                                          │           │ feature store│
                                          │           │ (Redis/Dynamo)│
                                          │           └──────────────┘
                                          ▼
                                   ┌──────────────┐
                                   │ S3 landing   │ ──► Spark ──► Snowflake
                                   │ (Parquet,    │              (BI, A/B)
                                   │  partitioned │
                                   │  by hour)    │
                                   └──────────────┘
```

> **Candidate:** Five boxes. The clients send events to an
> API gateway, which forwards to Kafka. Kafka has multiple
> topics — one per event type — partitioned by `user_id` so
> all events for a user land on the same partition. From
> there, two paths: a Flink stream processor for the
> real-time feature store, and a S3 landing zone for the
> batch pipeline (Spark + Snowflake). The hot path is the
> Flink processor; the batch path is the deep dive.

### 5:00 — Back-of-envelope estimation

> **Candidate:** Let me size this. 250M DAU, average 200
> events per user per day, 1 KB per event (after gzip) =
> 250M × 200 × 1 KB = 50 TB/day. Peak QPS: 250M users /
> 86400 sec × burst factor 10 = 30K events/sec average, 300K
> events/sec peak. So we're at 50 TB/day, 300K events/sec
> peak. The Kafka cluster needs to be sized for 1M events/sec
> to handle bursts.

### 7:00 — The deep dive: Kafka ingestion

> **Interviewer:** Let's go deep on the Kafka ingestion layer.
> How do you handle 300K events/sec? What about ordering?
> Schema changes?

> **Candidate:** Sure. Three things matter: partitioning,
> schema, and backpressure. **[DRAWING 2]**

```
Producer (gateway) ──► Kafka topic "events.plays"
  partition key: user_id
  
  topic config:
    partitions: 200
    replication: 3
    retention: 3 days
    cleanup.policy: delete
```

> **Candidate:** Partitioning: I'd use 200 partitions on the
> `plays` topic. 200 gives us 200 consumers in the Flink job
> for full parallelism. The partition key is `user_id`, so
> all events for a user are ordered. The trade-off: if one
> user is hot, that partition is hot. I'd monitor
> per-partition lag and rebalance if any partition is more
> than 2x the median.
>
> Schema: every event is Avro with a schema in the Confluent
> Schema Registry. The schema is backward compatible — adding
> a new optional field is fine, removing a field breaks
> compatibility. The producer checks compatibility before
> publishing. A bad schema change is rejected at registration
> time, not at runtime.
>
> Backpressure: the Flink consumer uses bounded buffers. If
> the consumer can't keep up, it pauses the partitions. The
> producer's `linger.ms` and `batch.size` smooth out spikes.
> At 300K events/sec, the Flink cluster needs 50-100 task
> managers with 4 GB heap each.

### 12:00 — Schema and event design

> **Interviewer:** Show me what a single event looks like.

> **Candidate:** Sure. **[DRAWING 3]**

```json
{
  "event_id": "uuid-v4",      // idempotency key
  "user_id": "uuid-v4",
  "session_id": "uuid-v4",
  "event_type": "play",
  "ts": "2024-01-15T10:30:00.123Z",
  "properties": {
    "title_id": "80123456",
    "position_sec": 1234,
    "device_type": "tv",
    "country": "US",
    "app_version": "14.2.0"
  },
  "context": {
    "ab_test_bucket": "control-A",
    "experiment_id": "rec_v2_2024"
  }
}
```

> **Candidate:** Five top-level fields: `event_id` is the
> idempotency key (consumer dedups on this), `user_id` is
> the partition key, `event_type` is the routing key (goes
> to a per-type topic), `ts` is the event time (with
> millisecond precision for play/pause), and `properties`
> is the type-specific payload. The `context` block is for
> A/B test attribution — every event carries the bucket
> and experiment ID so we can do per-experiment analysis
> without a join.

### 15:00 — The Flink stream processor

> **Interviewer:** Walk me through the Flink job. What does
> it actually compute?

> **Candidate:** The Flink job has three stages. **[DRAWING 4]**

```
Kafka topic "events.plays"
  ↓
Stage 1: Filter + parse
  - drop malformed events (DLQ)
  - extract user_id, title_id, ts
  ↓
Stage 2: Windowed aggregation
  - 1-minute tumbling window per (user_id, title_id)
  - compute play_count, total_watch_sec
  ↓
Stage 3: Sink
  - write to Redis (real-time features)
  - write to Kafka "features.user_profile" (downstream)
```

> **Candidate:** Stage 1 filters and parses. Malformed
> events — schema mismatch, missing required fields — go
> to a DLQ topic. We never drop silently.
>
> Stage 2 is the windowed aggregation. A 1-minute tumbling
> window per `(user_id, title_id)` computes play count and
> total watch seconds. The window is keyed on the same
> `user_id` so all events for a user land on the same
> Flink task. Watermarks handle late events up to 30
> seconds.
>
> Stage 3 has two sinks: the real-time feature store
> (Redis) and a downstream Kafka topic for the batch
> pipeline. The Redis write is `SET user:{user_id}:
> rec_features <json> EX 86400` — features expire after
> 24 hours. The downstream topic is consumed by Spark
> for the batch pipeline.

### 20:00 — The batch pipeline

> **Interviewer:** How does the batch pipeline work? What's
> the S3 → Snowflake path?

> **Candidate:** The Flink job also writes raw events to
> S3 in Parquet format, partitioned by hour. **[DRAWING 5]**

```
S3 layout:
  s3://netflix-events/
    year=2024/month=01/day=15/hour=10/
      part-0001.parquet  (128 MB each, ~6 per hour)
      part-0002.parquet
      ...
      _SUCCESS

Spark job (hourly):
  - reads new partitions
  - dedupes by event_id
  - joins to user_dim, content_dim
  - writes to Snowflake
    - fact_events (event-grain)
    - agg_user_daily (user-day grain)
    - agg_title_daily (title-day grain)
```

> **Candidate:** Each hourly partition is ~6 GB of Parquet
> at 50 TB/day / 24 hours. Spark reads new partitions,
> dedupes on `event_id` (idempotency), and joins to the
> user and content dimensions. The output is three
> Snowflake tables: `fact_events` (event grain), and two
> aggregations for the BI / A/B team.
>
> The hourly Spark job has a 90-minute SLA. It's idempotent
> — re-running for the same hour produces the same result.
> Watermarks + `_SUCCESS` markers tell Spark which
> partitions are ready.

### 25:00 — Failure modes and reliability

> **Interviewer:** What fails? How do you handle it?

> **Candidate:** Five things I worry about. **[DRAWING 6]**
>
> First, Kafka broker down. The producer retries with
> exponential backoff; the gateway buffers up to 30 seconds
> of events. If Kafka is down for longer, the gateway
> starts dropping with a 503.
>
> Second, Flink consumer lag growing. Per-partition lag
> is monitored. If any partition is more than 60 seconds
> behind, page on-call.
>
> Third, late events. Flink's watermark is 30 seconds, so
> events more than 30 seconds late go to a side output. A
> separate Spark job re-processes them.
>
> Fourth, schema change. The schema registry rejects
> breaking changes. The Flink job has a fallback Avro
> reader that uses the schema version at the time of the
> event.
>
> Fifth, S3 landing zone corruption. The `_SUCCESS` marker
> is only written after the file is fully written and
> fsynced. Spark only reads partitions with the marker.
>
> The reconciliation: a daily Spark job compares
> `COUNT(*) FROM fact_events` against `SUM(events) FROM
> Kafka metrics`. If they diverge by more than 0.1%, page
> on-call.

### 28:00 — Cost and wrap-up

> **Interviewer:** Anything else?

> **Candidate:** One thing — cost. At 50 TB/day, S3 is
> $30K/month just for storage. The Glacier tier after 30
> days brings it to $3K/month. Kafka cluster is ~$20K/month
> for the brokers. Flink is $10K/month. Snowflake is
> $30K/month for the daily credit consumption. So we're at
> ~$100K/month for the whole pipeline. The cost lever:
> Parquet compression (we use ZSTD level 3) gives us 5x
> compression, so 50 TB raw becomes 10 TB on S3.
>
> That's the architecture. The deep dive is the Flink job
> — the windowing, the watermark, the late-event handling.
> Those are the parts that determine whether the
> real-time feature store is actually real-time.

---

## Post-interview analysis

**What was good:**

- Opening framing — asked 3 clarifying questions before drawing.
  Strong signal.
- One-sentence summary at 0:00.
- The high-level diagram is correct: 5 boxes, sensible flow.
- Back-of-envelope math is in the right ballpark.
- Schema and idempotency are addressed in the deep dive.
- The 5 failure modes are named unprompted.
- Cost is named unprompted.

**What was missing:**

- Could have been more concrete about the Flink state backend
  (RocksDB? Heap?).
- The reconciliation check is a good idea but the cadence
  (daily) is too slow for a real-time pipeline.
- The S3 partition size is fine but the file rotation strategy
  is not addressed.
- Could have named the consumer-group sizing rule (consumers
  ≤ partitions) explicitly.

**Score against the 5-bucket rubric:**

| Bucket | Score |
|---|---|
| Problem framing (15%) | 5/5 — three clarifying questions, repeated back |
| Estimation (10%) | 4/5 — math is right, but the "1M events/sec" cap is asserted, not derived |
| High-level architecture (20%) | 5/5 — 5 boxes, labeled arrows, sensible flow |
| Hot-path deep dive (35%) | 4/5 — Flink stages are clear; late-event handling is good; could be more specific on watermarks |
| Tradeoff articulation (20%) | 5/5 — partition sizing, hot-key handling, cost, schema evolution |

**Overall: senior answer.** Would pass at L5.

---

## Try it

Re-do this mock interview out loud. Set a 30-minute timer.
Cover the same five sections: framing, high-level,
back-of-envelope, deep dive, failure modes. Compare your
transcript to the one above.
