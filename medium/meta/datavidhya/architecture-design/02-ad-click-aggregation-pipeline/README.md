# Ad Click Aggregation Pipeline

**Difficulty:** HARD
**Companies:** Meta, Google, Amazon
**Tags:** system-design, streaming, exactly-once, fraud-detection, billing, skew

---

## 1. Problem Statement

> An advertising platform processes a billion+ ad clicks per day. Advertisers need
> real-time dashboards showing spend, CTR, and conversions. 10–20% of clicks are
> fraudulent — bots, click farms, double-clicks — and must be filtered **before**
> they are counted, because every counted click is billed money. A single Super
> Bowl campaign can spike traffic 10x. Design the click aggregation pipeline.

### Hard Parts
- **1M+ events/sec** sustained, 10M during major campaigns
- **Exactly-once** counting — a double-counted click is a double charge
- **Fraud filtering upstream of counting**, but good fraud signals arrive *late*
- **<10s freshness** for dashboards, while billing must be **exact**
- **Hot keys** — one campaign can be 10x any other and lands on one partition

### Scale & Constraints

| Dimension | Value |
|---|---|
| Events/sec | 1M sustained, 10M peak |
| Clicks/day | 1B+ |
| Freshness | Aggregates available < 10s after the click |
| Accuracy | Billing-grade — every click counted **exactly once** |
| Fraud | 10–20% of raw clicks, filtered before counting |
| Retention | Aggregates 90 days, raw events 1 year |

---

## 2. Lead with this

The requirements as stated **contain a contradiction**, and naming it is the
answer to this question:

> **< 10-second freshness** and **financial-grade accuracy** cannot be satisfied
> by the same number.

Fraud detection is the reason. Some fraud is detectable inline in microseconds
(a datacenter IP, a malformed user-agent, the 4th click in 2 seconds). But click
farms and coordinated bot networks are only detectable by looking *across* many
events over minutes to hours. If you wait for that signal, you miss 10 seconds.
If you don't, you bill fraud.

So you do not build one pipeline. You build **two consumers of one immutable
log**, with different SLAs, and you say so out loud:

| | Consumer | Latency | Accuracy | Authority |
|---|---|---|---|---|
| **Speed layer** | advertiser dashboard | < 10s | approximate, **revisable** | no |
| **Batch layer** | billing / invoices | T+1 hours | exact, reconciled | **yes** |

The dashboard says *"CTR 2.3% (provisional)"*. The invoice is generated from the
batch layer after the async fraud scores land. The two are reconciled daily and
the delta is published as an **adjustment record**, never by mutating history.

Everything else in this design follows from that split. Candidates who try to
serve billing off the streaming aggregates either break exactly-once or break
the latency SLA, and the interviewer is waiting to see which.

---

## 3. The 5-Step Approach

### Step 1 — Clarify Requirements

Ask these before drawing anything:

- **Is the dashboard number allowed to change?** (If yes → Lambda split above.
  If no → you must delay it past the fraud window, and <10s is impossible.)
- **What is billed — clicks, or clicks net of fraud?** Net. So billing waits.
- **Is a missed click or a double-counted click worse?** Double-counted. It's a
  chargeback and a trust problem. Bias every ambiguous case toward *not* billing.
- **What's the dedup key and window?** "Same user + same ad within 60s" — is
  that per-device or per-account? Cross-device is a different (harder) problem.
- **Do we need per-advertiser data isolation?** Affects partitioning and the
  serving store's tenancy model.

### Step 2 — High-Level Architecture

```
                    1M–10M events/s
                          │
            ┌─────────────▼─────────────┐
            │  Edge Collectors (global) │  stamp event_id (UUIDv7), event_ts,
            │  + inline fraud tier 1    │  ingest_ts; reject obvious bots
            └─────────────┬─────────────┘
                          │
            ┌─────────────▼─────────────┐
            │  Kafka  raw_ad_events     │  1024 partitions, key = hash(user_id)
            │  7-day replay, acks=all   │  ← partition key chosen for DEDUP
            └─────────────┬─────────────┘
                          │
            ┌─────────────▼─────────────┐
            │  Flink: Dedup             │  keyed state (user_id, ad_id)
            │  60s window, RocksDB      │  TTL 60s + watermark
            └─────────────┬─────────────┘
                          │
            ┌─────────────▼─────────────┐
            │  Kafka  deduped_clicks    │  RE-KEYED to hash(campaign_id + salt)
            └──────┬──────────────┬─────┘  ← key changes here. This matters.
                   │              │
      ┌────────────▼───┐   ┌──────▼────────────────────┐
      │ Flink: Windowed│   │ Iceberg: raw_events       │
      │ Aggregation    │   │ (immutable, 1yr, by hour) │
      │ 1m/5m/1h/1d    │   └──────┬────────────────────┘
      └────────────┬───┘          │
                   │              │        ┌──────────────────────┐
      ┌────────────▼───┐          │        │ Async Fraud Scoring  │
      │ Druid / Pinot  │          │◀───────│ (ML, minutes–hours)  │
      │ SPEED LAYER    │          │        │ → fraud_verdicts     │
      │ <10s, provis'l │          │        └──────────────────────┘
      └────────────┬───┘          │
                   │       ┌──────▼──────────────────────┐
         Dashboards ◀──────┤ Spark: Billing Reconciliation│
                           │ BATCH LAYER — authoritative  │
                           │ raw ⨝ fraud_verdicts, T+1     │
                           └──────┬──────────────────────┘
                                  │
                        Invoices ◀┴─▶ adjustment records
```

See `diagrams/architecture.mermaid` and `diagrams/data-flow.mermaid`.

### Step 3 — The Four Decisions That Carry the Interview

#### 3.1 The partition key changes mid-pipeline

This is the detail most candidates miss.

- **Dedup** needs all clicks for a given `(user_id, ad_id)` on the **same
  worker**, or you cannot see the duplicate. → partition by `hash(user_id)`.
- **Aggregation** needs all clicks for a given `campaign_id` on the same worker.
  → partition by `hash(campaign_id)`.

These are different keys, so there is a **mandatory shuffle** between the two
stages. Put a Kafka topic there (`deduped_clicks`) rather than a network shuffle:
it gives you a restart boundary, independent scaling, and a replay point for the
aggregation stage without re-running dedup.

#### 3.2 Dedup is a watermark problem, not a `DISTINCT`

`SELECT DISTINCT` over an unbounded stream needs unbounded state. The 60-second
window is what makes the state bounded:

```
state key   = (user_id, ad_id)
state value = first_seen_event_ts
TTL         = 60s past the watermark
```

A click is a duplicate iff a state entry exists and `event_ts - first_seen < 60s`.
State size ≈ (active users × ads per user in 60s) × ~64 B — a few hundred GB at
peak, which is why it lives in **RocksDB with incremental checkpoints**, not on
the JVM heap.

**The trap:** `dropDuplicates()` on an unbounded stream in Spark keeps state
forever and the job dies in hours. Use `dropDuplicatesWithinWatermark()` (Spark
3.5+) or Flink keyed state with TTL. See `pyspark/dedup_clicks.py`.

**Boundary semantics to state explicitly:** is the 60s window *sliding from the
last click* or *fixed from the first*? "Same user + same ad within 60s = 1 click"
means fixed-from-first — otherwise a bot clicking every 59s is deduped forever
and never billed at all. Asserted in `pyspark/dedup_clicks.py`.

#### 3.3 Fraud is two tiers with different latencies

| Tier | Where | Latency | Catches | Action |
|---|---|---|---|---|
| **1 — inline** | edge collector | µs | datacenter IPs, known bot UAs, malformed, per-IP rate limit, >N clicks/sec/user | **drop before counting** |
| **2 — async** | ML scoring job | minutes–hours | click farms, coordinated networks, conversion-rate anomalies, device-farm fingerprints | **retroactive invalidation** |

Tier 1 is deterministic and cheap, so it runs synchronously and its output is
authoritative immediately. Tier 2 needs cross-event context — you cannot know a
click came from a farm until you've seen the other 10,000 clicks. It emits
`fraud_verdicts` records that the batch layer joins against.

**Never mutate the raw log.** A tier-2 verdict produces an adjustment row. The
raw event stays; the invoice reflects `billable = raw − tier1 − tier2_verdicts`.
That's what makes the pipeline auditable when an advertiser disputes a charge.

See `python/fraud_rules.py` for the tier-1 rules, with the money math:
**1B clicks/day × 15% fraud × $0.50 CPC = $75M/day of mis-billing risk.** That
number is why fraud sits upstream of counting rather than in a cleanup job.

#### 3.4 The Super Bowl hot key

A single campaign at 10x volume hashes to **one partition**, and that partition's
worker becomes the bottleneck while 1023 others idle. Three mitigations, in the
order you should offer them:

1. **Two-stage aggregation with key salting** (the real fix): aggregate on
   `(campaign_id, salt)` where `salt = hash(event_id) % 64`, then sum the 64
   partials. Parallelism goes from 1 to 64 for the hot key. Cost: one extra
   aggregation stage. See `pyspark/windowed_aggregation.py`.
2. **Pre-aggregate at the edge** — collectors emit per-second partial counts
   instead of individual events for high-volume campaigns. Reduces the event
   count by orders of magnitude, but you lose per-event fraud scoring, so only
   apply it to campaigns already past tier-2 review.
3. **Separate topic for whale campaigns** with its own scaled consumer group.
   Operationally simple, but it's manual capacity management.

Do **not** propose "just add partitions" — the hot key still maps to one of them.

### Step 4 — Exactly-Once, Concretely

"Exactly-once" is not a checkbox. Name the four places it can break:

| Failure point | Mechanism |
|---|---|
| Producer retry after timeout | idempotent producer (`enable.idempotence=true`), `event_id` as the dedup key |
| Consumer reprocesses after crash | checkpointed offsets **committed atomically with state** (Flink 2PC / Kafka transactions) |
| Sink writes twice | idempotent upsert keyed on `(window_start, ad_id, salt)` — re-running a window overwrites rather than adds |
| Dedup state lost on restart | RocksDB + checkpoint to durable storage; never in-memory only |

The invariant to state: **the aggregation sink must be idempotent, so
at-least-once delivery becomes effectively-once.** That's strictly easier than
true exactly-once delivery and is what production systems actually do.

`pyspark/billing_reconciliation.py` asserts the difference: an `append`-mode sink
double-bills on replay; an idempotent `MERGE` does not.

### Step 5 — Storage & Retention

| Layer | Store | Grain | Retention | Size |
|---|---|---|---|---|
| Replay buffer | Kafka | event | 7 days | ~300 TB × 3 replicas |
| Raw events | Iceberg/S3, Parquet+zstd | event | 1 year | ~3 PB compressed |
| 1-min aggregates | Druid/Pinot | ad_id × minute | 7 days | ~100 GB |
| 1-hour aggregates | Druid + Iceberg | ad_id × hour | 90 days | ~60 GB |
| Daily aggregates | Iceberg | ad_id × day | 2 years+ | small |
| Fraud verdicts | Iceberg | event_id | 1 year | ~50 TB |
| Billing ledger | Iceberg (append-only) | invoice line | 7 years (legal) | small |

**The retention decision worth defending:** 1-minute grain for 90 days would be
~10M active ads × 1440 × 90 ≈ 1.3 trillion rows. It isn't worth it. Keep 1-min
for 7 days (incident debugging), roll up to hourly for the 90-day window. State
the rollup, don't let the interviewer find the hole.

Capacity math in `python/capacity_model.py` — runnable, so the numbers above are
derived rather than asserted.

---

## 4. Folder Layout

```
02-ad-click-aggregation-pipeline/
├── README.md                        # this file
├── diagrams/
│   ├── architecture.mermaid         # full component diagram
│   └── data-flow.mermaid            # event lifecycle, speed vs batch
├── sql/
│   ├── schema.sql                   # Iceberg DDL: raw, verdicts, aggregates, ledger
│   ├── dedup_query.sql              # 60s dedup in SQL (batch equivalent)
│   ├── window_aggregation.sql       # 1m/5m/1h/1d rollups + salted two-stage
│   └── billing_reconciliation.sql   # authoritative billable-click query
├── python/
│   ├── capacity_model.py            # the scale math, runnable
│   ├── fraud_rules.py               # tier-1 inline rules + money math
│   └── dedup_state.py              # keyed-state dedup with TTL, no Spark
└── pyspark/
    ├── dedup_clicks.py              # 60s dedup, boundary semantics, watermarks
    ├── windowed_aggregation.py      # multi-window + hot-key salting
    └── billing_reconciliation.py    # speed vs batch, idempotent vs append
```

Every `python/` and `pyspark/` file is **runnable and self-asserting** — it
proves the claim in the README rather than restating it, including the failure
modes:

```bash
cd 02-ad-click-aggregation-pipeline
../../../../../.env/bin/python python/capacity_model.py
../../../../../.env/bin/python pyspark/dedup_clicks.py
```

---

## 5. Failure Modes & Operations

| Failure | Blast radius | Mitigation |
|---|---|---|
| Kafka partition leader loss | brief write stall | `acks=all`, `min.insync.replicas=2`, producer retries |
| Dedup job crash | duplicates if state lost | RocksDB checkpoints every 10s; replay from last checkpoint offset |
| Late events beyond watermark | undercounted window | route to a side output; batch layer picks them up; **never** silently drop billable events |
| Async fraud scorer down | fraud gets billed | hold invoices, don't bill; alert on verdict-lag SLO |
| Serving store lag | stale dashboard | show the watermark timestamp in the UI — "data as of 14:32:05" |
| 10x spike | backpressure | salted keys + autoscaled consumers; Kafka absorbs the burst as buffer |

**The SLO that matters:** not "uptime" but **watermark lag**. If the watermark is
more than 10s behind wall clock, the freshness requirement is already violated,
whatever the dashboard says. Alert on that, and expose it to advertisers.

---

## 6. Interview Talking Points

Hit these beats in order:

1. **Name the contradiction first** — <10s and billing-grade are different
   numbers with different consumers. This reframes the whole question and is the
   single highest-signal thing you can say.
2. **Partition key changes mid-pipeline** — `hash(user_id)` for dedup,
   `hash(campaign_id)` for aggregation, Kafka topic at the boundary.
3. **Dedup is bounded by the watermark** — `(user_id, ad_id)` keyed state with
   60s TTL in RocksDB; `DISTINCT` needs unbounded state and will kill the job.
4. **Fraud is two tiers** — inline deterministic drops, async ML retroactive
   invalidation via adjustment records. Never mutate the raw log.
5. **Hot key → salted two-stage aggregation** — and reject "add more partitions."
6. **Idempotent sink, not exactly-once delivery** — upsert on
   `(window_start, ad_id, salt)` makes at-least-once safe.
7. **Rollup the retention** — 1-min for 7 days, hourly for 90. Show the row-count
   math that forces it.

**Bonus line that lands:** *"Every ambiguous click should fail toward not
billing. A missed click costs us a fraction of a cent of revenue; a
double-billed click costs a chargeback, an audit, and an advertiser."*

**If asked "what would you build first?"** — the immutable raw log and the
idempotent batch reconciliation. The dashboard is the visible part, but the
ledger is the part you get sued over, and everything else can be rebuilt from
raw events by replay.
