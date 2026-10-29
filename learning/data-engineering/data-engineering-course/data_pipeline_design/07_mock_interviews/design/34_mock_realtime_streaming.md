# 34 — Mock Interview: Design a Real-Time Ad Impression Dedup Pipeline

> **Lesson 34 of 34 — Mock Interviews**

A full 30-minute mock interview with a candidate designing a
real-time ad impression dedup pipeline (Kafka + Flink + Redis +
Bigtable). The candidate is a Senior Data Engineer (L6 level) at
a hypothetical ad-tech company. The scenario is the highest-volume
real-time question in the track: 10B impressions per day, 100K
events/sec peak, sub-second dedup, exactly-once.

---

## Setup

**Company:** Ad-tech / programmatic advertising (hypothetical,
modeled on the canonical streaming question).
**Role:** Senior Data Engineer.
**Level:** L6.
**Format:** 30-minute system design round, on-site whiteboard.
**Question:** *"Design a real-time ad impression dedup pipeline.
We process 10B impressions per day, with peaks of 100K events
per second. The dedup window is 1 hour (a duplicate impression
within 1 hour is the same impression). End-to-end latency budget
is 1 second. We need exactly-once semantics so the same
impression is not counted twice downstream."*

---

## Transcript (30 minutes)

### 0:00 — Opening framing

> **Candidate:** Before I draw, three things I need to nail
> down.
>
> First, the dedup key. Is "duplicate" defined as
> `(user_id, ad_id, hour)` — or do we need a tighter key like
> `(user_id, ad_id, creative_id, placement_id)`? The cardinality
> of the dedup state is the dominant cost driver.
>
> Second, the 1-hour window. Is that a tumbling window (fixed
> 1-hour buckets) or a sliding window (any 60-minute period)? A
> tumbling window is cheap; a sliding window is expensive.
>
> Third, "exactly-once downstream" — does that mean *at the
> dedup output* (a single event per ad impression to the
> dashboard), or *at the warehouse load* (the warehouse has
> exactly one row per impression)? These are different guarantees.

> **Interviewer:** Key is `(user_id, ad_id, creative_id)`. The
> window is tumbling — 1-hour buckets, fixed. Exactly-once means
> downstream dashboards and the warehouse see one row per
> impression. We accept a small false-positive rate in dedup
> (collisions) to keep the cost down.

> **Candidate:** Three big numbers then:
>
> 1. **Cardinality.** `user_id × ad_id × creative_id` is up to
>    200M × 1M × 10 = 2 × 10^15 — but in any 1-hour window it's
>    much smaller. Realistically 50M unique impressions per
>    hour. 50M × 200 bytes = 10 GB of dedup state per hour. That
>    fits in memory on a 100 GB Redis cluster.
> 2. **Throughput.** 100K events/sec peak. Kafka cluster: 30
>    brokers, 1K partitions. Flink: 200 task managers.
> 3. **Latency.** 1 second end-to-end. Dedup state lookup has to
>    be sub-100ms; serialization and network round-trip eat the
>    rest.

### 3:00 — High-level architecture

> **Candidate:** Six boxes. **[DRAWING 1]**

```
┌────────────┐    ┌────────────┐   ┌─────────────┐   ┌────────────┐
│ Ad        │───►│ API       │──►│ Kafka       │──►│ Flink      │
│ exchanges │    │ gateway   │   │ (topic      │   │ (dedup     │
│ + SDKs    │    │ (HTTP)    │   │  impressions│   │  + enrich) │
└────────────┘    └────────────┘   │  1000 part) │   └─────┬──────┘
                                  └─────────────┘         │
                                                          │
                                       ┌──────────────────┴─────┐
                                       ▼                        ▼
                              ┌──────────────┐         ┌──────────────┐
                              │ Redis /      │         │ Bigtable /   │
                              │ Flink state  │         │ HBase        │
                              │ (dedup state,│         │ (dedup state,│
                              │  10 GB/h)    │         │  hot + warm) │
                              └──────┬───────┘         └──────┬───────┘
                                     │                        │
                                     ▼                        ▼
                              ┌─────────────────────────────────────┐
                              │ Flink sink:                         │
                              │  -1- first-seen → Kafka "unique"    │
                              │  -N- duplicate → Kafka "dup"        │
                              │  -D- dashboard + Iceberg batch      │
                              └─────────────────────────────────────┘
```

> **Candidate:** Six components. Ad SDKs send impressions to
> the API gateway, which forwards to a Kafka topic with 1000
> partitions (keyed by `user_id` for ordering). A Flink job
> consumes, does the dedup against a state backend (RocksDB
> for hot, Redis for cross-job sharing), and emits two
> streams: a "unique" stream and a "duplicate" stream. A
> downstream pipeline writes the unique stream to a
> Bigtable serving store and an Iceberg batch table for
> reporting.

### 6:00 — Back-of-envelope estimation

> **Candidate:** 10B events / day, 100K peak / sec. Average
> event 1 KB (compressed). That's 10 TB / day raw, 3 TB / day
> on Kafka with ZSTD. 7 days retention = 21 TB on Kafka.
>
> Dedup state: 50M unique per hour × 200 bytes = 10 GB per
> hour. 24 hours × 10 GB = 240 GB. Fits in a single Redis
> cluster with eviction by TTL.
>
> Flink: 200 task managers, 4 GB heap each, RocksDB state on
> local SSD. State is checkpointed to S3 every 30 seconds.
>
> Cost:
> - Kafka (30 brokers × $2K) = $60K / month
> - Flink (200 TMs × $1K) = $200K / month
> - Redis (10 nodes) = $5K / month
> - Bigtable (1 TB hot) = $1K / month
>
> Total: ~$270K / month. The dominant cost is Flink; the
> dominant *latency* cost is the state-backend lookup.

### 8:00 — Deep dive #1: dedup at scale

> **Interviewer:** Three ways to dedup: bloom filters, Redis,
> RocksDB. Walk me through the tradeoffs.

> **Candidate:** Three options. **[DRAWING 2]**

```
Option A: Bloom filter
  - In-memory, fixed size, O(1) lookup
  - False-positive rate: 0.1% at 1B items / 10 GB
  - State fits in one Flink TM heap
  - Pros: simplest, fastest
  - Cons: can't delete, can't reset, no audit trail

Option B: Redis cluster
  - O(1) GET, O(1) SET, but network round-trip (~1ms)
  - 50M keys × 200 bytes = 10 GB per hour
  - TTL on each key = 1 hour
  - Pros: shared across Flink TMs, auditable
  - Cons: cross-network, costs $$$, eviction races

Option C: RocksDB on local SSD
  - Embedded in Flink; no network hop
  - 50M keys × 200 bytes = 10 GB per hour on local SSD
  - Sorted, O(log n) lookup
  - Pros: lowest latency, no network
  - Cons: state is per-TM; need key-by routing to ensure all
    events for a key land on the same TM
```

> **Candidate:** The senior answer: **RocksDB as primary, Redis
> as a backstop**. RocksDB is embedded in Flink; the
> `(user_id, ad_id, creative_id)` key routes to a specific
> task manager via hash partitioning. Within a single TM,
> lookup is a local SSD read — sub-millisecond.
>
> Redis is the fallback when:
> 1. A TM's local state is too large (we overflow to Redis).
> 2. A TM is restarted and the local state is rebuilding; we
>    consult Redis in parallel.
>
> Bloom filters are an *optimization on top of RocksDB* — we
> keep a small bloom filter of "keys I've seen" in memory to
> avoid the SSD read for clear non-matches. Bloom gives us a
> 0.1% false positive rate; the false positive causes a
> duplicate to slip through, which is acceptable per the
> requirements ("we accept a small false-positive rate").

### 14:00 — Deep dive #2: late-arriving events

> **Candidate:** Real-time dedup has a late-event problem. **[DRAWING 3]**

```
Event timeline:

  T=0:00   ad impression A fires for user_42
  T=0:01   ad impression A fires for user_42 (DUPLICATE, caught)

  T=0:30   network glitch; the upstream retry of A from
           T=0:00 arrives at T=0:30
  T=0:30   Flink sees A at T=0:30

  If the dedup window is "the 1-hour bucket starting at T=0:00"
  and we're now at T=0:30 (still in the same bucket),
  → caught by dedup. Good.

  If the dedup window is "the 1-hour bucket starting at T=0:00"
  and we're now at T=1:30 (next bucket), and the late A from
  T=0:00 has not been seen yet at T=1:30 because the bucket
  rotated
  → A is treated as fresh. We get a duplicate downstream.
  → This is the late-event bug.
```

> **Candidate:** Three ways to handle late events.
>
> **Watermarks.** Flink's event-time watermark tracks
> "max event time seen so far - allowed lateness." We set
> allowed lateness to 5 minutes. Events more than 5 minutes
> late go to a side output; a separate reprocessor ingests
> them and *re-checks* against the dedup state.
>
> **Buffer the state.** Instead of TTLing the dedup state
> exactly at 1 hour, we keep it for 1 hour + 5 minutes of
> lateness. The dedup state window is 65 minutes, not 60.
> Late events within 5 minutes are caught.
>
> **Bucket versioning.** Each hour bucket has a version
> number. Late events specify their original bucket's version.
> We maintain dedup state for both the current bucket and the
> previous bucket (in case of straddle). When the previous
> bucket is "sealed" (5 minutes past the hour), we drop its
> state. This is the production answer.

### 20:00 — Deep dive #3: exactly-once semantics

> **Candidate:** Exactly-once has two flavors. **[DRAWING 4]**

```
Flavor A: at-least-once + idempotent sink
  - Kafka producer is idempotent (enable.idempotence=true)
  - Flink checkpoints every 30s to S3
  - On restart, we re-read the offset and re-process
  - The dedup state is keyed on event_id, so re-processing
    is a no-op for already-processed events
  - The downstream sink (Bigtable write, Iceberg commit) is
    idempotent on event_id

Flavor B: two-phase commit
  - Kafka transactions + Flink's TwoPhaseCommitSink
  - Pre-commit at checkpoint; commit at next checkpoint
  - Stronger guarantee; higher latency
  - Reserved for the regulatory path (e.g., billing)
```

> **Candidate:** The right answer for ad dedup is **Flavor A**:
> at-least-once with idempotent sink. Reasoning:
>
> 1. **Latency.** Two-phase commit doubles the end-to-end
>    latency. We have a 1-second budget. A is 200ms; B is
>    500ms.
> 2. **Cost.** Two-phase commit holds Kafka partitions locked
>    during the commit window. Throughput drops 30-50%. We have
>    100K events / sec to handle.
> 3. **The dedup itself is the exactly-once mechanism.** If
>    every event is checked against the dedup state and the
>    state is durable, we get the right answer on every replay.
>    The replay doesn't double-count because the dedup state
>    survives the replay.
>
> The senior move is to name the cost of exactly-once and
> propose at-least-once + idempotent sink as the production
> answer. True exactly-once is expensive and rarely worth it
> at this scale.

### 25:00 — Failure modes

> **Candidate:** Five. **[DRAWING 5]**
>
> One, **Kafka is down.** Producers retry with exponential
> backoff. The gateway buffers up to 30 seconds. After that,
> impressions are dropped with a 503 and a metric fires. We
> never buffer for more than 30 seconds because the dedup
> state window is 1 hour and old events are no longer useful
> downstream.
>
> Two, **Flink TM dies.** Jobmanager reschedules on a new TM.
> The state is recovered from the last checkpoint (RocksDB
> on S3). Recovery time: ~30 seconds for 50 GB of state.
> During recovery, the affected partitions pause; backlog
> drains after recovery.
>
> Three, **Dedup state is too big for memory.** A burst hour
> produces 30 GB of dedup state; a single TM has 8 GB heap.
> The TM evicts to Redis; subsequent lookups for evicted
> keys go to Redis. We alert if the Redis hit rate drops
> below 90%.
>
> Four, **Late events pile up.** The side output fills up;
> the reprocessor is behind. We alert on side-output depth
> > 1M events; on-call scales the reprocessor.
>
> Five, **Schema break.** A new ad format adds a field.
> Flink's Avro deserializer handles backward-compatible
> changes. Backward-incompatible changes are caught by the
> schema registry; the source is paused until the migration
> is complete.

### 30:00 — Wrap-up

> **Candidate:** The architecture is: Kafka → Flink → RocksDB
> dedup → unique/dup streams → Bigtable + Iceberg. The three
> hard problems are dedup at scale (RocksDB with Redis backstop
> + bloom filter optimization), late events (5-minute watermark
> + 65-minute state window), and exactly-once (at-least-once +
> idempotent sink; we use the dedup state as the exactly-once
> primitive, not transactions). The cost driver is Flink
> ($200K / month); the latency driver is the state-backend
> lookup. End-to-end p95 is ~600ms.

---

## Post-interview analysis

**What was good:**

- The cardinality-vs-cost sizing for the dedup state is the
  right move — most candidates skip it.
- Three dedup options compared; RocksDB + Redis + bloom is
  the production answer.
- Late-event handling covers watermarks + buffer + bucket
  versioning — the senior move is naming all three.
- Exactly-once is addressed with the *cost* of true
  exactly-once named; the at-least-once + idempotent answer
  is justified.
- Five failure modes named unprompted.
- Cost estimate is in the right order of magnitude.

**What was missing:**

- **Multi-region / geo-distribution.** Ad-tech runs in
  multiple regions; cross-region dedup state replication is
  non-trivial. The senior answer would name the
  regional-local-first approach with eventual state
  synchronization.
- **Backpressure and shed-load semantics.** What happens
  when the dedup state is fully saturated and Redis is also
  saturated? The pipeline has to *shed load* — drop events
  in a controlled way. The interview answer would name
  which events are shed (probably the lowest-value ad
  formats).
- **PII and ad-fraud signals.** Impressions contain
  user_id which is PII. The pipeline needs to enforce
  retention, encryption, and the ad-fraud signals (click
  injection, bot traffic) are an adjacent system.
- **The reconciliation.** A daily Spark job compares
  unique-event counts from the dedup pipeline against the
  raw ad-exchanger reports. Drift > 0.5% pages the on-call.

**Score against the rubric:**

| Bucket | Score |
|---|---|
| Problem framing (15%) | 5/5 — three clarifying questions, three drivers named |
| Estimation (10%) | 5/5 — math shown, cardinality derived |
| High-level architecture (20%) | 5/5 — six boxes, all the right pieces |
| Hot-path deep dive (35%) | 5/5 — dedup, late events, exactly-once |
| Tradeoff articulation (20%) | 4/5 — multi-region + backpressure missing |

**Overall: senior+ answer.** Would pass at L6 for an ad-tech
or real-time streaming role.

---

## Try it

Re-do this mock out loud. The heart is the dedup-state story
(RocksDB + Redis + bloom) and the late-event handling
(watermarks + 65-minute window + bucket versioning). If you
can describe those in five sentences each, you have the
framework.

---

*Author: Prem Vishnoi <pvishnoi@avilx.com>*
