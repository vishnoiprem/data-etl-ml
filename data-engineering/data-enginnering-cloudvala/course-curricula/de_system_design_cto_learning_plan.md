# Data Engineering System Design — CTO / Principal Study Plan

**Source course:** Data Vidhya — *Data Engineering System Design* by
Darshil Parmar.
**Course URL:** https://datavidhya.com/learn/de-system-design/
**Coverage:** 6 modules • 65 lessons
**Audience:** Data engineers targeting **Staff → Principal → Director →
VP/CTO** through mastery of large-scale data system design.

> **How to use this file.** Each lesson has four lenses:
>
> 1. **Theory** — mental model and the design primitive.
> 2. **Practical Example** — concrete numbers, code, decisions.
> 3. **AI Use Case** — where GenAI / ML slots in or on top of this lesson.
> 4. **CTO / Principal Motivation** — the career reason; what decisions
>    you're trusted with at senior levels.
>
> System design is the **differentiation layer** between mid and senior
> data engineers. Coding builds the pipeline; system design decides
> *which* pipeline to build, *how* it scales, *what* it costs, and
> *whether* it survives the next 10× growth. This course is the
> playbook for that decision-making.

---

# Module 1 · The Framework (11 lessons)

## Lesson 1 — How Interviews Work

### Theory

The DE system-design interview is not the same as an SWE system-design
interview. Mental model:

- **45-60 minutes total**, 1 interviewer (sometimes 2).
- **5 min** — clarifying questions (volume, latency, sources).
- **5 min** — back-of-envelope estimation.
- **10 min** — high-level architecture.
- **15 min** — deep dives (the data model, the pipeline, the trade-offs).
- **5 min** — monitoring, SLAs, failure modes.
- **5 min** — wrap-up, your questions.

The interviewer's evaluation rubric: did the candidate **ask the right
questions**, **make trade-offs explicit**, **identify the dominant
risk**, and **communicate the design clearly**? Coding is optional;
judgment is mandatory.

### Practical Example

The candidate who starts drawing boxes without asking "how much data
per day, what latency, what consistency" loses the rubric on
clarifying questions. The candidate who says "this looks like 10K
events/sec, 1 KB each = ~860 GB/day raw, I'll target sub-minute
freshness with a Kappa architecture" demonstrates the senior mental
model.

### AI Use Case

**AI as mock interviewer.** Use a Bedrock / OpenAI session in
"interviewer" mode: paste a question, answer aloud, get scored on
clarifying questions, trade-offs, deep dives. The Principal's edge:
practicing 20 systems with AI feedback is worth 5 with humans.

### CTO / Principal Motivation

Your CTO interview is the same format with the same rubric, just at
higher stakes. The principal-level candidate *teaches* the framework
to the interviewer; the CTO candidate *co-creates* with the board. The
habit of explicit trade-off articulation compounds.

---

## Lesson 2 — Delivery Framework

### Theory

The Data Vidhya delivery framework — the **8 steps** every DE system
design follows:

1. **Requirements gathering** (functional + non-functional).
2. **Sources & volume estimation** (back of the envelope).
3. **High-level architecture** (the boxes-and-arrows).
4. **Data model** (schema, partitioning, indexing).
5. **Pipeline design** (orchestration, transformation, error handling).
6. **Deep dives** (the two most important components).
7. **Monitoring & SLAs** (alerts, freshness, latency, accuracy).
8. **Top mistakes** (failure modes to defend against).

The framework is the **safety net** — when you're stuck in the
interview, fall back to the next step.

### Practical Example

Practice the framework on **"log aggregation at Uber scale"**:

| Step | Output |
|------|--------|
| 1. Requirements | 100B events/day, 100+ teams, 7-year retention |
| 2. Volume | 100B × 1 KB = 100 TB/day raw; 1 PB/day compressed |
| 3. Architecture | Kafka → Flink → S3 Iceberg → Athena/Presto + Splunk |
| 4. Data model | partitioned by service/date, clustered by user_id |
| 5. Pipeline | Kafka 7-day retention → Flink micro-batch → Iceberg MERGE |
| 6. Deep dives | Flink state backend (RocksDB), Iceberg compactor |
| 7. Monitoring | 5-min freshness SLO, consumer lag alarm, schema drift |
| 8. Mistakes | backpressure, hot partitions, orphaned data |

### AI Use Case

**AI as co-pilot during the interview.** A live AI in your ear can
remind you of the next framework step ("have you covered monitoring?")
without being heard by the interviewer. The Principal's edge: use AI
to drill 50 problems; not to cheat in the interview.

### CTO / Principal Motivation

The framework is the **shared language** for data engineering reviews.
Every architecture review at a Staff+ level is structured along these
8 steps. CTOs who follow it consistently make decisions 5× faster than
those who relitigate the structure each time.

---

## Lesson 3 — Requirements Gathering

### Theory

The single highest-leverage skill in system design. Mental model —
split requirements into:

- **Functional** — what the system does (e.g., "track every URL
  redirect").
- **Non-functional** — how it does it (e.g., "p99 latency < 100 ms",
  "30-day retention", "GDPR-compliant").
- **Operational** — how it runs (e.g., "managed service preferred",
  "on-call rotation exists").

The trap: candidates jump to architecture without explicit
requirements. The fix: write the requirements on the whiteboard first.
If the interviewer doesn't say, you ask. **Asking is the answer.**

### Practical Example

For "design Uber":

- **Functional:** rider-driver matching, pricing, ETA, payments,
  notifications, fraud detection.
- **Non-functional:** 30M trips/day, sub-second matching latency, 99.99%
  uptime, multi-region.
- **Operational:** Kafka for streaming, Flink for stream processing,
  HDFS/S3 for batch, MySQL/Cassandra for OLTP.

### AI Use Case

**AI-generated requirement templates.** Maintain a library of "for X
type of system, ask these 15 questions." The Principal's leverage:
encode the template in `copilot-instructions.md` so every system
design starts with the right questions.

### CTO / Principal Motivation

Requirements gathering is the **difference between a Senior and a
Principal**. Senior engineers accept the requirements as given.
Principals interrogate them: "is sub-second matching actually
required, or is 5 seconds acceptable?" The Principal's answer often
changes the architecture by 10×.

---

## Lesson 4 — Sources & Volume

### Theory

Back-of-envelope estimation is the **engineering lingua franca**.
Mental model — derive the four numbers that matter:

1. **QPS (queries per second)** — write, read, both.
2. **Data volume** — bytes per day, bytes per query.
3. **Storage** — daily × retention / compression ratio.
4. **Cost** — at AWS list price.

**Estimation rules:**

- 1 day = 100K seconds (~86,400).
- 1 year = 30M seconds (~31.5M).
- Bytes to GB: /10^9. To TB: /10^12. To PB: /10^15.
- Storage cost: $20/TB-month Standard. Compute: $0.04/vCPU-hour.
- Network: $0.01/GB egress.

### Practical Example

"Design a system to ingest 100M clickstream events per day":

- QPS = 100M / 100K = **1,000 events/sec average; ~3,000 peak**.
- Volume = 100M × 1 KB = **100 GB/day raw; 30 TB/month; 360 TB/year**.
- Storage with 5× compression (Parquet) = **72 TB/year**.
- Cost: S3 at $20/TB-month = $120/month for that year.

### AI Use Case

**AI-validated estimation.** "Sanity check this back-of-envelope
math" → AI confirms or corrects. The Principal's habit: estimate
before the interview, validate with AI, refine.

### CTO / Principal Motivation

Estimation is the **CTO's superpower in budget meetings**. "This
project will cost $X per year and serve Y users" is the language of
the board. Principals who can estimate confidently get budget
approved; those who can't, get questioned.

---

## Lesson 5 — High-Level Architecture

### Theory

The high-level architecture is the **first whiteboard artifact**.
Mental model:

- **Sources** on the left.
- **Ingestion** (Kafka, Kinesis, Event Hubs).
- **Storage** (data lake / warehouse / lakehouse).
- **Processing** (batch + streaming).
- **Serving** (warehouse / OLAP / search).
- **Consumption** (BI, ML, apps).

Draw the boxes, label the arrows with **data flow direction + protocol**
(Kafka, JDBC, REST). The interviewer's question: "why this and not
that?" — be ready.

### Practical Example

A canonical real-time analytics architecture:

```
Mobile/Web SDK → Kafka → Flink (CEP) → S3 Iceberg (history)
                             ↓
                         ClickHouse (real-time OLAP)
                             ↓
                         Grafana dashboard
```

The Flink layer can also write to **Redis** for live counters and
**OpenSearch** for full-text search.

### AI Use Case

**AI-generated architecture diagrams.** Describe a system in natural
language, get a Mermaid/PlantUML diagram. The Principal's leverage:
generate 10 candidate architectures in 30 minutes and pick the best.

### CTO / Principal Motivation

The high-level architecture is **the artifact a CTO shows the board**.
If you can't draw it in 10 minutes, you don't understand the system.
The Principal's deliverable: a single-page architecture diagram with
**5 boxes, 5 arrows, 5 trade-offs** annotated.

---

## Lesson 6 — Data Model Design

### Theory

The data model is where most candidates fail. Mental model:

- **Source model** — what arrives (often third-party, fixed).
- **Staging model** — 1:1 with source, type-coerced.
- **Conformed model** — entity-keyed, deduped, with type 2 SCD if needed.
- **Mart model** — wide, denormalized, BI-friendly.
- **Late-arriving data** — how the model handles it (merge keys, SCD2
  effective dates).

The two levers: **partitioning** (read-pruning) and **clustering**
(locality for filtered columns).

### Practical Example

Clickstream model:

```
staging.events_raw (PARTITION BY date, CLUSTER BY user_id)
  ↓
conformed.events (PARTITION BY date, CLUSTER BY user_id, event_type)
  - dedupe by event_id
  - SCD2 on user attributes (effective_at, is_current)
  ↓
mart.daily_user_kpi (PARTITION BY date)
  - daily active users, retention curves
```

### AI Use Case

**AI schema generation.** "Suggest a star schema for an e-commerce
warehouse" → AI proposes fact + dim tables, SCD type recommendations,
naming conventions. The Principal's edge: review AI suggestions, apply
company-specific standards.

### CTO / Principal Motivation

The data model is the **single most expensive artifact** to get wrong.
Rewriting a poorly-partitioned table at 10 PB costs $X; rewriting it
at 100 PB costs $10X. The Principal's deliverable: a **data modeling
standard** (naming, SCD type, partition strategy) enforced by CI.

---

## Lesson 7 — Pipeline Design

### Theory

Pipelines are the **lifeblood** of a data platform. Mental model:

- **Idempotency** — re-running produces the same output. Critical for
  backfill and retry.
- **Atomicity** — all-or-nothing per partition (Iceberg / Delta
  transactions).
- **Backpressure** — slow downstream doesn't crash upstream.
- **Schema evolution** — add columns without breaking consumers.
- **Error handling** — dead-letter queues for poison pills.

The pipeline design depends on the **freshness SLA**: hourly, daily,
real-time. Pick the simplest primitive that meets the SLA.

### Practical Example

A streaming pipeline with backpressure handling:

```python
# Kafka consumer with manual offset management
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'events',
    bootstrap_servers=['broker:9092'],
    auto_offset_reset='earliest',
    enable_auto_commit=False,  # manual commit
    max_poll_records=500,      # backpressure
)

for batch in consumer:
    try:
        # Process the batch
        process_batch(batch)
        consumer.commit()  # only commit on success
    except PoisonPillError:
        dead_letter(batch)    # quarantine bad messages
        consumer.commit()     # advance past them
    except Exception:
        # don't commit — will retry on next poll
        time.sleep(5)
```

### AI Use Case

**AI-generated pipeline skeletons.** "Write a Spark Structured
Streaming job that reads Kafka, deduplicates by event_id, writes to
Iceberg" → working Python. The Principal's call: which pipelines are
safe for AI generation vs. which need hand-coding (financial, PII).

### CTO / Principal Motivation

Pipeline design choices **compound**. A team that picks batch
where streaming is needed spends 6 months migrating. A team that
picks streaming where batch suffices spends $500k/year on
unnecessary Kafka. The Principal owns the **pipeline pattern
catalogue**; the CTO owns the **streaming vs batch ROI** conversation.

---

## Lesson 8 — Deep Dives

### Theory

The interviewer will pick **two components** and drill. Choose wisely:

- **Pick the highest-risk component** — the one most likely to fail.
- **Pick the highest-cost component** — the one with the largest spend.
- **Pick the most-novel component** — the one the candidate knows best.

The deep dive structure:

1. **State** — what data lives here.
2. **Throughput** — how much data moves per second.
3. **Failure modes** — what breaks and how you recover.
4. **Scaling** — how this scales 10×.
5. **Cost** — dollar per month at current scale.

### Practical Example

Deep dive on **the Kafka cluster**:

- **State** — 7 days of events on local disk (10 TB).
- **Throughput** — 100K msgs/sec, 100 MB/sec.
- **Failure modes** — broker down, leader election, ISR shrinkage.
- **Scaling** — add brokers, rebalance partitions.
- **Cost** — 10 brokers × `kafka.m5.2xlarge` = $5k/month.

### AI Use Case

**AI-driven deep-dive practice.** AI plays interviewer; candidate
chooses a component, AI drills with follow-ups. The Principal's edge:
practice 100 deep dives before the interview.

### CTO / Principal Motivation

The deep dive is where **Staff engineers show their depth** and
**Principals show their judgment**. "Why this and not that?" is the
question that separates ICs from leaders. The Principal's lever:
3-5 components where you can talk for 10 minutes without notes.

---

## Lesson 9 — Monitoring & SLAs

### Theory

Monitoring is **non-negotiable in production**. Mental model:

- **SLI (Service Level Indicator)** — the metric (latency, error rate,
  freshness).
- **SLO (Service Level Objective)** — the target (p99 < 200 ms,
  freshness < 5 min).
- **SLA (Service Level Agreement)** — the contract with customers (often
  99.9% uptime).

The four golden signals: **latency, traffic, errors, saturation**.
Plus the data-specific: **freshness, completeness, accuracy, lineage**.

### Practical Example

A pipeline SLO definition:

```yaml
# pipeline_slo.yaml
pipelines:
  - name: nightly-etl
    slos:
      freshness: 6h        # data delivered by 06:00 UTC
      completeness: 99.9%  # rows expected vs rows arrived
      accuracy: 99.5%      # rows passing DQ tests
    alerts:
      - if: freshness > 6h
        action: page_oncall
      - if: completeness < 99%
        action: open_ticket
```

### AI Use Case

**AI-augmented anomaly detection.** Use AI to learn normal pipeline
behavior and alert only on true anomalies. The Principal's leverage:
reduce alert fatigue by 70% while catching more real incidents.

### CTO / Principal Motivation

SLAs are **the contract a CTO signs**. When the SLA is breached,
the CTO is on the hook. Principals who build observable systems with
explicit SLOs save the CTO from sleepless nights. The board cares
about **error budget burn rate** — the faster you burn, the sooner
you have to slow down feature work.

---

## Lesson 10 — Top 15 Mistakes

### Theory

The 15 mistakes every candidate makes (and every Principal avoids):

1. **No requirements gathering.** Jumps to architecture.
2. **No estimation.** Doesn't size the system.
3. **Wrong shape.** Vertical slice vs. horizontal layer.
4. **Single point of failure.** No replication, no failover.
5. **Hot partitions.** Skewed keys.
6. **No idempotency.** Re-runs produce duplicates.
7. **No backpressure.** Consumer crashes on burst.
8. **Missing error handling.** Crashes on poison messages.
9. **Late-arriving data.** No late-event strategy.
10. **Schema drift.** No schema registry.
11. **No monitoring.** Alerts only after a customer complains.
12. **Ignoring cost.** Designs without dollar numbers.
13. **Ignoring security.** No encryption, no IAM.
14. **Over-engineering.** Kafka for 100 events/day.
15. **No trade-offs.** "Use the best" instead of "use the cheapest
    that meets the SLA."

### Practical Example

**Mistake 4 — Single point of failure.** A design with one Kafka
broker, one Postgres replica, one Glue job. Every Principal catches
this; every Senior forgets it.

**Mistake 14 — Over-engineering.** "Design a pipeline for 10K
events/day" → candidate specifies Kafka + Flink + Iceberg + dbt +
Snowflake. Correct answer: a Python script on Lambda + S3 Parquet.
The candidate who picks the simple answer gets the job.

### AI Use Case

**AI as mistake-checker.** After drawing a design, run it through AI
with: "review this data system design for the 15 most common
mistakes." The Principal's leverage: catch mistakes before the
interviewer does.

### CTO / Principal Motivation

The 15 mistakes are a **checklist for architecture reviews**. Every
design doc at a Staff+ level addresses these explicitly. CTOs who
have the checklist internalized give better feedback in 1/3 the
time.

---

## Lesson 11 — Quiz: The Framework

### Theory

The framework quiz validates that you can **defend the framework**,
not just recite it. For each of the 8 steps, write a 1-sentence
"if I only had 30 seconds on this step, I would say…" answer.

### Practical Example

The single best drill: take any system (Uber, Twitter, Netflix)
and write the 8-step framework for it. Time-box to 30 minutes.
Repeat 10 times. You'll be faster than 95% of candidates.

### AI Use Case

AI-generated flashcards from each step. Spaced-repetition drill.

### CTO / Principal Motivation

Framework mastery is the **prerequisite for every other lesson** in
this course. If you can't run the framework on autopilot, the deep
dives won't land.

---

# Module 2 · Core Concepts (11 lessons)

## Lesson 1 — Partitioning

### Theory

Partitioning is the **single most important performance lever** in
data engineering. Mental model:

- **Partition** = a physical subdivision of a table, usually by date
  or tenant.
- **Why** — query pruning (skip irrelevant partitions).
- **How to choose** — pick the column most often filtered, with
  reasonable cardinality (100s to millions, not millions to millions).
- **Anti-patterns** — over-partitioning (10M tiny files), under-
  partitioning (full scans).

### Practical Example

```sql
-- Good: date partitioning, 1000 rows per partition
CREATE TABLE events
PARTITION BY date
CLUSTER BY user_id
AS SELECT * FROM raw_events;

-- Bad: high-cardinality partitioning
PARTITION BY user_id;  -- 100M partitions = disaster
```

### AI Use Case

**AI partition advisor.** Feed query history → AI recommends partition
key + clustering key with expected pruning rate. The Principal's
leverage: AI-driven partitioning at petabyte scale.

### CTO / Principal Motivation

Partitioning is the **CTO's cost-control lever**. A poorly-partitioned
table costs $X/month; a well-partitioned one costs $X/10. The
Principal owns the **partitioning standard**; the CTO sees the
**AWS bill**.

---

## Lesson 2 — Ingestion Patterns

### Theory

Three canonical patterns:

| Pattern | Tool | Use case |
|---------|------|----------|
| **Batch** | S3 COPY, Snowpipe, ADF Copy | Daily/hourly ETL |
| **Streaming** | Kafka, Kinesis, Event Hubs | Real-time |
| **CDC** | Debezium, DMS, Airbyte | Database changes |

The decision rule: **start with batch, only reach for streaming when
the business SLA demands it.**

### Practical Example

A clickstream pipeline uses **streaming** because the business SLA is
"< 1 minute freshness for fraud detection." A daily sales ETL uses
**batch** because nobody cares about freshness.

### AI Use Case

**AI SLA advisor.** "Given this use case (fraud detection, sub-minute
latency required), recommend an ingestion pattern." The Principal's
edge: standardize AI-recommended patterns per use-case class.

### CTO / Principal Motivation

The ingestion-pattern decision is **the most reversible** if you get
it wrong. Moving from batch to streaming is a 6-month project; moving
from streaming to batch is a 6-week project. The Principal's call:
"start batch, only stream when SLA forces it" — saves $500k/year.

---

## Lesson 3 — Backfill & Reprocessing

### Theory

Backfill = re-process historical data. Reprocessing = re-process
recent data after a code change. Mental model:

- **Idempotent** pipelines can be re-run safely.
- **Backfill windows** — daily batch window can backfill 30 days in
  ~30 minutes of compute (parallelize).
- **Event-time vs processing-time** — always re-process on event-time
  for correctness.
- **Snapshot isolation** — Iceberg/Delta MERGE for atomic rewrites.

### Practical Example

```sql
-- Backfill January 2026 with new logic
INSERT INTO gold.daily_kpi
SELECT * FROM silver.events_v2
WHERE event_date BETWEEN '2026-01-01' AND '2026-01-31';
```

The MERGE handles deduplication if needed:

```sql
MERGE INTO gold.daily_kpi t
USING (SELECT * FROM silver.events_v2
       WHERE event_date BETWEEN '2026-01-01' AND '2026-01-31') s
ON t.event_date = s.event_date
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;
```

### AI Use Case

**AI-driven backfill planner.** "Given a 30-day backfill with X
compute, recommend the optimal window size and parallelism." The
Principal's edge: avoid over-provisioning during backfills.

### CTO / Principal Motivation

Backfill capability is the **CTO's safety net for bad code**. When
a Principal deploys a broken pipeline, the CTO asks "can we backfill
in 24 hours?" The answer determines whether the bug is a P1 incident
or a minor cleanup.

---

## Lesson 4 — Data Lineage

### Theory

Data lineage = **where the data came from, where it went, what
transformed it**. Mental model:

- **Table-level lineage** — table A comes from tables B, C.
- **Column-level lineage** — column A.x comes from B.y + C.z.
- **OpenLineage + Marquez** — open standards for lineage metadata.
- **DataHub / Unity Catalog / Glue Catalog** — commercial implementations.

### Practical Example

```
raw.events → bronze.events → silver.events → gold.daily_kpi
                              ↓
                          feature_store.user_features
```

When `gold.daily_kpi` is wrong, lineage says: "this came from
silver.events, which came from bronze, which came from raw.events at
13:42 UTC, ingested by Kafka topic X." This is **the time-to-diagnose
killer feature**.

### AI Use Case

**AI-driven lineage inference.** AI scans SQL/PySpark code, infers
column-level lineage automatically. The Principal's leverage:
100% lineage coverage without manual annotation.

### CTO / Principal Motivation

Lineage is the **CTO's compliance and trust artifact**. SOC 2,
GDPR, HIPAA all require "we know where our data came from." The
Principal owns the **lineage tool**; the CTO owns the **compliance
narrative**.

---

## Lesson 5 — Cost Optimization

### Theory

The five cost levers, ranked by impact:

1. **Right-sizing** — biggest wins.
2. **Storage tiering** — S3 lifecycle.
3. **Spot / preemptible** — for fault-tolerant workloads.
4. **Reserved / Savings Plans** — for steady-state.
5. **Cleanup orphans** — abandoned resources.

Plus: **finOps culture** — every team sees their bill.

### Practical Example

A 100-node EMR cluster running 4 hours/day at $0.30/hr Spot = $438/year.
A 10-node cluster for the same job (better partitioning + Spark tuning)
= $44/year. **10× savings from optimization.**

### AI Use Case

**AI cost advisor.** AI scans Terraform/IaC and recommends
right-sizing, instance type, scheduling changes. The Principal's
edge: $100k+/year savings from AI-augmented reviews.

### CTO / Principal Motivation

Cost optimization is the **CTO's board-level contribution**. "We
saved $X this year from FinOps" is a board bullet. The Principal
owns the FinOps tooling; the CTO owns the FinOps narrative.

---

## Lesson 6 — Monitoring & Alerting

### Theory

The four golden signals + four data-specific:

- **Latency** (pipeline duration, query p99).
- **Traffic** (events/sec, queries/sec).
- **Errors** (failed runs, bad rows).
- **Saturation** (queue depth, lag).
- **Freshness** (data age since last update).
- **Completeness** (% rows expected).
- **Accuracy** (% rows passing DQ).
- **Lineage** (upstream health).

### Practical Example

```yaml
# alert on freshness (most critical)
alert: PipelineStale
expr: time() - max(events_last_loaded_timestamp) > 1800
for: 5m
labels:
  severity: page
annotations:
  summary: "ETL stale for {{ $value | humanizeDuration }}"
```

### AI Use Case

**AI-augmented anomaly detection.** AI learns normal patterns, alerts
only on true anomalies. The Principal's edge: 70% reduction in alert
fatigue.

### CTO / Principal Motivation

MTTR (mean time to recovery) is the **CTO's reliability metric**.
The Principal owns the **alert standard**; the CTO owns the
**reliability narrative**.

---

## Lesson 7 — Data Contracts

### Theory

A data contract is an **SLA between data producers and consumers**.
Mental model:

- **Producer promises:** schema, freshness, completeness, semantics.
- **Consumer promises:** usage patterns, deprecation notice.
- **Enforced** via CI/CD: producer's PR fails if it breaks the contract.
- **Tools:** Schema Registry, OpenLineage, custom YAML in `contracts/`.

### Practical Example

```yaml
# contracts/orders.yaml
table: orders
producer: payments-team
version: 2

schema:
  required:
    - order_id: string
    - user_id: string
    - amount: decimal(10, 2)
    - currency: string

freshness:
  max_age_minutes: 60
  partition_column: created_at

completeness:
  required_columns: [order_id, user_id]
  null_rate_threshold: 0.01
```

### AI Use Case

**AI contract generator.** AI watches producer schemas and
auto-drafts contracts. The Principal's edge: contracts on every
table without manual effort.

### CTO / Principal Motivation

Data contracts are the **CTO's tool against data quality fires**.
"We have contracts; the producer broke it; here's the SLA
violation." The Principal owns the **contract library**; the CTO
owns the **quality narrative**.

---

## Lesson 8 — Late-Arriving Data

### Theory

Late-arriving data = events arriving **after their event time**. Common
causes: mobile offline buffer, third-party delays, network partitions.
Mental model:

- **Watermarks** — define how late is acceptable (e.g., 24 hours).
- **Event-time vs processing-time** — always process on event-time.
- **Reconciliation** — daily job compares event-time counts to arrival
  counts.
- **SCD2** — track multiple versions of a record for late corrections.

### Practical Example

```python
# Flink: 24-hour watermark
watermark_strategy = (EventTimeForMonotonousTimestamps()
                      .with_timestamp_assigner(
                          lambda event, ts: event["event_time"])
                      .with_idleness(Duration.of_minutes(5)))
```

### AI Use Case

**AI-driven late-data detection.** AI watches partition arrival
patterns, alerts when partitions are abnormally late. The Principal's
edge: catch upstream issues before the business does.

### CTO / Principal Motivation

Late-data handling is the **difference between an analyst trusting
the data and re-checking it daily**. The Principal owns the
**watermark policy**; the CTO owns the **trust narrative**.

---

## Lesson 9 — Deduplication at Scale

### Theory

Dedup at scale is non-trivial. Mental model:

- **Exact dedup** — hash(event_id), insert into set, ignore duplicates.
  Works until the set outgrows memory.
- **Probabilistic dedup** — Bloom filter (1% false positive rate at
  10 bits/element). Memory-efficient.
- **Distributed dedup** — partition by hash(event_id), dedup per
  partition, aggregate.
- **Storage-level dedup** — Iceberg/Delta with `MERGE` on event_id.

### Practical Example

```python
# Spark dedup at scale
df = (spark.read.parquet("s3://raw/events/")
      .dropDuplicates(["event_id"]))  # exact, may shuffle
# At 100B rows, use a Bloom filter:
from pyspark.sql.functions import bloom_filter
df_dedup = df.filter(~bloom_filter("event_id", expected_items=1e10,
                                    fpp=0.01).isNull())
```

### AI Use Case

**AI-driven dedup at the schema level.** AI detects duplicate events
based on fuzzy logic (event_id differs but payload matches). The
Principal's leverage: catch business-level duplicates, not just
exact-match ones.

### CTO / Principal Motivation

Dedup correctness is the **CTO's defense in regulatory audits**. "Show
me you deduplicate customer PII correctly." The Principal owns the
**dedup pattern**; the CTO owns the **privacy narrative**.

---

## Lesson 10 — Key DE Numbers

### Theory

The numbers every DE Principal has at their fingertips:

| Number | Value |
|--------|-------|
| AWS S3 Standard | $20/TB-month |
| S3 IA | $12.50/TB-month |
| S3 Glacier Instant | $4/TB-month |
| Athena / Trino | $5/TB scanned |
| Snowflake Standard | $2/credit, ~$0.0005/sec-medium |
| BigQuery on-demand | $6.25/TB scanned |
| Redshift | $0.25-$13/hr per node |
| Kafka m5.large | $0.21/hr |
| Kinesis shard | $0.015/hr + $0.014/1M PUT |
| Lambda | $0.20/1M requests + $0.0000166667/GB-s |
| Network egress | $0.01-0.09/GB |

### Practical Example

"Estimate the cost of a 1 TB/day pipeline":
- Storage: 1 TB/day × 365 × 5× compression = 73 TB × $20 = **$1,460/mo**.
- Athena queries: assume 100 TB scanned/day = $500/day = **$15k/mo**.

### AI Use Case

**AI cost estimator.** "Estimate the AWS cost of [system]" → AI does
the math. The Principal's edge: validate AI estimates, sanity-check.

### CTO / Principal Motivation

These numbers are the **CTO's ammunition in budget meetings**. "This
project costs $X per year" beats "this project costs some amount."
The Principal's deliverable: a memorized table of these numbers.

---

## Lesson 11 — Quiz: Core Concepts

### Theory

Validate that you can **defend each concept under pressure**. The
quiz pattern: "tell me about partitioning" → 5-minute deep dive on
trade-offs.

### Practical Example

For each concept, write a 1-page cheat sheet with: definition, when
to use, when NOT to use, alternative, cost.

### AI Use Case

AI-generated flashcards + spaced repetition.

### CTO / Principal Motivation

Concept mastery is the **prerequisite for system design fluency**.
If you fumble partitioning, the interviewer assumes you don't know
it at scale.

---

# Module 3 · Architecture Patterns (10 lessons)

## Lesson 1 — Lambda Architecture

### Theory

The classic split: **batch layer + speed layer + serving layer**.
Mental model:

- **Batch layer** — accurate, eventually-consistent, recomputed from
  all historical data.
- **Speed layer** — real-time, eventually-correct, handles recent data.
- **Serving layer** — merges batch + speed views for queries.

Trade-off: code duplication (same logic in two places), ops overhead.

### Practical Example

```
All data → Kafka → Batch layer (Spark nightly) → batch view
                       ↓
              Speed layer (Flink real-time) → real-time view
                       ↓
              Query = batch view + (real-time view - batch overlap)
```

Used by: LinkedIn, Netflix (historically).

### AI Use Case

**AI on Lambda views.** Real-time view writes are forwarded to an ML
model that predicts which batch views are about to be queried, pre-
computing them. The Principal's edge: lower query latency.

### CTO / Principal Motivation

Lambda is **over-engineered for most companies**. The Principal
calls it out: "we don't need Lambda, we can do Kappa." Saves $500k/year
in duplicated code. CTOs approve the consolidation.

---

## Lesson 2 — Kappa Architecture

### Theory

Simplification of Lambda: **single streaming pipeline** that handles
all data, with reprocessing by replaying Kafka. Mental model:

- **All data** flows through Kafka (or similar) with long retention.
- **Stream processing** computes the views.
- **Reprocessing** = restart the job from an earlier Kafka offset.
- **No batch layer**.

Trade-off: requires Kafka with long retention (30+ days) or equivalent.

### Practical Example

```
All events → Kafka (30-day retention) → Flink → ClickHouse
```

To reprocess: reset Flink job to Kafka offset 0, re-run.

### AI Use Case

**AI-optimized Kappa.** AI watches Flink job performance and tunes
parallelism, checkpoint interval, state backend. The Principal's
edge: 2× throughput from AI tuning.

### CTO / Principal Motivation

Kappa is the **default for new systems in 2026**. The Principal owns
the **decision framework** (when Kappa, when Lambda, when neither).
The CTO owns the **architecture standardization** narrative.

---

## Lesson 3 — Medallion Architecture

### Theory

Three layers — bronze (raw), silver (cleaned), gold (curated). Mental
model:

- **Bronze** — append-only, raw data, schema-on-read.
- **Silver** — cleaned, deduplicated, conformed, schema-enforced.
- **Gold** — aggregated, business-logic applied, BI-ready.

Used by: Databricks, Fabric, most modern lakehouses.

### Practical Example

```sql
-- Bronze: raw ingest from Kafka
CREATE TABLE bronze.events AS
SELECT * FROM kafka_events;

-- Silver: clean + dedup
CREATE TABLE silver.events AS
SELECT * FROM bronze.events
WHERE event_id IS NOT NULL
QUALIFY ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY ts) = 1;

-- Gold: aggregate
CREATE TABLE gold.daily_kpi AS
SELECT date_trunc('day', event_time) AS day, count(*) AS events
FROM silver.events
GROUP BY 1;
```

### AI Use Case

**AI-curated gold layer.** AI watches analyst queries and recommends
new gold tables to materialize. The Principal's leverage: lower
analyst query latency, lower compute cost.

### CTO / Principal Motivation

Medallion is the **standard data architecture in 2026**. The
Principal owns the **layer definitions**; the CTO owns the **governance
narrative** (bronze is collected, gold is trusted).

---

## Lesson 4 — CDC Patterns

### Theory

CDC = Change Data Capture, replicating database changes to the data
warehouse. Mental model:

- **Log-based CDC** (Debezium) — reads the database WAL.
- **Trigger-based CDC** — database triggers write change rows.
- **Query-based CDC** — periodic SELECT with timestamp filter.

Trade-offs: log-based is best for completeness; trigger-based is
easiest to set up; query-based is least intrusive.

### Practical Example

```
Postgres WAL → Debezium → Kafka → Iceberg bronze → silver → gold
```

Debezium captures INSERT/UPDATE/DELETE as separate events with `before`
and `after` rows.

### AI Use Case

**AI-driven CDC schema evolution.** AI watches Debezium schema
changes and auto-updates downstream Iceberg schema. The Principal's
edge: zero-downtime schema changes.

### CTO / Principal Motivation

CDC is the **foundation for replication, audit, and real-time
analytics**. The Principal owns the **CDC tool selection**; the CTO
owns the **data replication strategy**.

---

## Lesson 5 — Event Sourcing

### Theory

Event sourcing = **store every state change as an event, derive state
by replaying events**. Mental model:

- **Event store** — append-only log.
- **Snapshots** — periodic materialized state.
- **Projections** — derived views.
- **Replay** — rebuild state from scratch by replaying events.

Used by: financial systems, audit-heavy domains.

### Practical Example

```python
# Event store
events = [
    {"type": "AccountCreated", "id": "acc1", "balance": 0},
    {"type": "Deposit", "id": "acc1", "amount": 100},
    {"type": "Withdrawal", "id": "acc1", "amount": 30},
]
# Current state = replay all events for acc1
state = {"balance": 100 - 30}  # 70
```

### AI Use Case

**AI-augmented event replay.** AI decides which events need
re-processing and which can be skipped. The Principal's edge:
faster replay, lower compute.

### CTO / Principal Motivation

Event sourcing is **the CTO's tool for audit-grade systems**. "We
have a complete audit trail; we can replay any moment in time."
The Principal owns the **event store**; the CTO owns the **audit
narrative**.

---

## Lesson 6 — Data Mesh

### Theory

Data mesh = **domain-oriented decentralized data ownership**. Mental
model:

- **Domain ownership** — each business domain owns its data products.
- **Data as a product** — domains publish data with SLAs.
- **Self-serve platform** — central team provides tooling.
- **Federated governance** — global standards enforced via contracts.

Trade-off: organizational complexity, requires strong platform team.

### Practical Example

```
Sales domain → publishes orders data product (contract, SLA, catalog)
Marketing domain → publishes campaigns data product
                  ↓
         Federated catalog (data.world / Unity Catalog)
                  ↓
         Consumers subscribe to products
```

### AI Use Case

**AI-augmented data contracts.** AI watches domain data products
and auto-suggests contracts, flags violations. The Principal's edge:
50% less contract overhead.

### CTO / Principal Motivation

Data mesh is **the CTO's tool for large organizations**. Above 100
data engineers, central control breaks down; mesh scales. The
Principal owns the **platform team**; the CTO owns the **organizational
design**.

---

## Lesson 7 — Data Fabric

### Theory

Data fabric = **automated, unified data integration layer** with
metadata-driven discovery and access. Mental model:

- **Knowledge graph** of all data assets.
- **Automated discovery** — AI finds and catalogs data.
- **Unified access** — single query interface across sources.
- **Active metadata** — usage, lineage, quality, all tracked.

Tools: IBM Data Fabric, Azure Purview, Denodo, Starburst.

### Practical Example

```
Knowledge graph (Purview)
    ↓
Auto-discovery (Glue crawlers + AI)
    ↓
Unified query (Starburst / Trino / Athena Federation)
    ↓
Active metadata (lineage, DQ, usage)
```

### AI Use Case

**AI-driven discovery.** Purview and Glue use ML to auto-classify
data, suggest PII tags, infer relationships. The Principal's edge:
100% catalog coverage without manual effort.

### CTO / Principal Motivation

Data fabric is **the CTO's tool against data sprawl**. "We have one
catalog for all our data." The Principal owns the **fabric platform**;
the CTO owns the **governance narrative**.

---

## Lesson 8 — Micro-batch vs Streaming

### Theory

The spectrum:

| Approach | Latency | Tools |
|----------|---------|-------|
| **Batch** | Hours-days | Spark, Hive |
| **Micro-batch** | Seconds-minutes | Spark Structured Streaming |
| **Streaming** | Sub-second | Flink, Kafka Streams |

Trade-off: **latency vs cost vs complexity**. Micro-batch is the
sweet spot for most use cases.

### Practical Example

Spark Structured Streaming with 30-second micro-batch:

```python
stream = (spark.readStream
          .format("kafka")
          .option("kafka.bootstrap.servers", "broker:9092")
          .option("subscribe", "events")
          .load())

(stream.writeStream
       .trigger(processingTime="30 seconds")
       .format("iceberg")
       .outputMode("append")
       .start("s3://silver/events"))
```

### AI Use Case

**AI-tuned micro-batch size.** AI watches query latency and tunes
the micro-batch interval dynamically. The Principal's edge: lower
latency without manual tuning.

### CTO / Principal Motivation

Micro-batch is **the CTO's default for 80% of use cases**. The
Principal owns the **micro-batch pattern**; the CTO owns the
**latency-vs-cost narrative**.

---

## Lesson 9 — Reverse ETL

### Theory

Reverse ETL = **syncing warehouse data back to operational systems**.
Mental model:

- **Source** — warehouse (Snowflake, BigQuery).
- **Destination** — CRM (Salesforce), marketing (HubSpot), support
  (Zendesk).
- **Tools** — Hightouch, Census, Airbyte Reverse.
- **Use case** — operationalize analytics (give sales the lead score).

### Practical Example

```yaml
# Hightouch sync: warehouse → Salesforce
source:
  model: customer_scores
  fields: [email, score, last_active]

destination:
  type: salesforce
  object: lead
  match: email

schedule: every 1 hour
```

### AI Use Case

**AI-scored segments.** AI computes customer scores in the
warehouse, syncs to CRM for sales rep prioritization. The Principal's
edge: closed-loop analytics.

### CTO / Principal Motivation

Reverse ETL is **the CTO's tool for making data actionable**. "Our
data doesn't just sit in a dashboard; it goes back into our products."
The Principal owns the **reverse ETL platform**; the CTO owns the
**activation narrative**.

---

## Lesson 10 — Quiz: Architecture Patterns

### Theory

Pattern selection is the **CTO's strategic decision**. The
quiz: "given X requirements, which pattern and why?" Practice
10 patterns on 10 problems.

### Practical Example

The pattern selection matrix:

| Pattern | Latency SLA | Complexity | Cost |
|---------|-------------|------------|------|
| Batch | Hours+ | Low | $ |
| Lambda | Seconds | High | $$$ |
| Kappa | Seconds | Medium | $$ |
| Medallion | Hours-minutes | Low | $ |
| Data Mesh | Any | High | $$ |
| Data Fabric | Any | Medium | $$ |

### AI Use Case

AI-pattern-advisor: "given these requirements, recommend a pattern
with trade-offs."

### CTO / Principal Motivation

Pattern selection compounds. The Principal's deliverable: a
**pattern decision matrix** for the team. The CTO owns the
**architecture consistency** narrative.

---

# Module 4 · Technology Deep Dives (11 lessons)

## Lesson 1 — Spark Internals

### Theory

Spark = in-memory distributed compute. Mental model:

- **Driver** — runs the main, holds the DAG, schedules tasks.
- **Executors** — run tasks, hold data in memory.
- **DAG** — directed acyclic graph of stages.
- **Stages** — separated by shuffles.
- **Tasks** — one per partition.
- **Shuffle** — exchange of data between executors.
- **Catalyst** — query optimizer.
- **Tungsten** — memory + codegen layer.

### Practical Example

```python
df = (spark.read.parquet("s3://raw/events/")
      .filter(col("event_type") == "click")
      .groupBy("user_id")
      .agg(count("*").alias("clicks")))
# Catalyst optimizes filter pushdown; Tungsten codegens.
```

### AI Use Case

**AI Spark tuner.** AI reads Spark UI logs and recommends:
`spark.sql.shuffle.partitions`, memory fraction, broadcast thresholds.
The Principal's edge: 2-5× faster jobs from AI tuning.

### CTO / Principal Motivation

Spark internals knowledge is **the difference between a Senior and a
Principal data engineer**. The Principal owns the **Spark tuning
standard**; the CTO owns the **compute cost narrative**.

---

## Lesson 2 — Kafka

### Theory

Kafka = distributed commit log. Mental model:

- **Broker** — Kafka server.
- **Topic** — stream of records.
- **Partition** — ordered shard within topic.
- **Producer** — writes to topic.
- **Consumer** — reads from topic.
- **Consumer group** — share partitions.
- **Offset** — position in the log.
- **Replication** — leader + followers per partition.

### Practical Example

```bash
# Producer
kafka-console-producer.sh --broker-list localhost:9092 --topic events

# Consumer group
kafka-console-consumer.sh --bootstrap-server localhost:9092 \
  --topic events --group my-group --from-beginning
```

### AI Use Case

**AI Kafka tuner.** AI watches consumer lag, partition skew, broker
CPU and recommends: more partitions, more brokers, different
replication factor. The Principal's edge: AI-tuned Kafka at scale.

### CTO / Principal Motivation

Kafka is the **backbone of streaming architecture**. The Principal
owns the **Kafka sizing and tuning**; the CTO owns the **streaming
platform** narrative.

---

## Lesson 3 — Airflow

### Theory

Airflow = workflow orchestrator. Mental model:

- **DAG** — directed acyclic graph of tasks.
- **Operator** — type of work (PythonOperator, BashOperator, etc.).
- **Task instance** — running instance of a task.
- **Scheduler** — decides when to run tasks.
- **Executor** — how tasks run (Sequential, Local, Celery, Kubernetes).
- **Metadata DB** — tracks state (Postgres/MySQL).

### Practical Example

```python
@dag(schedule='@daily', start_date=datetime(2026, 1, 1))
def etl():
    @task
    def extract():
        return s3.get_object(...)

    @task
    def transform(data):
        return ...

    @task
    def load(data):
        ...

    load(transform(extract()))

etl()
```

### AI Use Case

**AI DAG generator.** Describe a pipeline in natural language → AI
generates the Airflow DAG. The Principal's edge: 5× faster DAG
authoring.

### CTO / Principal Motivation

Airflow is **the default orchestrator for batch pipelines**. The
Principal owns the **DAG standard**; the CTO owns the **orchestration
strategy**.

---

## Lesson 4 — dbt

### Theory

dbt = SQL-based transformation. Mental model:

- **Model** — SELECT statement.
- **Materialization** — view, table, incremental, ephemeral.
- **Tests** — schema and data quality.
- **Snapshots** — SCD Type 2.
- **Sources** — declared incoming tables.
- **Documentation** — auto-generated from YAML.

### Practical Example

```sql
-- models/gold/daily_kpi.sql
{{ config(materialized='incremental', unique_key='event_date') }}

SELECT event_date, count(*) AS events
FROM {{ ref('silver_events') }}
{% if is_incremental() %}
  WHERE event_date > (SELECT max(event_date) FROM {{ this }})
{% endif %}
GROUP BY 1
```

### AI Use Case

**AI dbt assistant.** AI generates dbt models from business logic,
writes tests, suggests documentation. The Principal's edge: 3×
faster transformation authoring.

### CTO / Principal Motivation

dbt is **the de facto analytics engineering tool**. The Principal
owns the **dbt project standard**; the CTO owns the **analytics
productivity** narrative.

---

## Lesson 5 — Snowflake

### Theory

Snowflake = cloud-native data warehouse. Mental model:

- **Virtual warehouse** — compute cluster.
- **Database / Schema / Table** — standard.
- **Stage** — file location (S3/Azure/GCS).
- **File format** — CSV, JSON, Parquet, etc.
- **COPY INTO** — bulk load.
- **Snowpipe** — auto-ingest on file arrival.
- **Streams & Tasks** — CDC + scheduling.

### Practical Example

```sql
-- Load from stage
COPY INTO raw.events
FROM @s3_stage/events/
FILE_FORMAT = (TYPE = PARQUET)
ON_ERROR = 'ABORT_STATEMENT';

-- Incremental via stream
MERGE INTO gold.daily_kpi t
USING (SELECT * FROM stream_changes) s
ON t.event_date = s.event_date
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;
```

### AI Use Case

**Snowflake Cortex** — AI functions in SQL. `SNOWFLAKE.CORTEX.SENTIMENT()`,
`COMPLETE()` etc. The Principal's edge: AI in the warehouse, no
Python.

### CTO / Principal Motivation

Snowflake is **the strategic warehouse choice**. The Principal owns
the **warehouse sizing**; the CTO owns the **Snowflake vs Databricks
vs Redshift** narrative.

---

## Lesson 6 — Delta Lake

> Full deep-dive article body: [`delta_lake_full_detail.md`](./delta_lake_full_detail.md)
> (verbatim reproduction of Darshil Parmar's article; stub pending source paste).

### Theory

Delta = open table format with ACID. Mental model:

- **Delta table** — Parquet + `_delta_log/`.
- **Transaction log** — JSON files tracking commits.
- **Optimize** — compaction.
- **Z-order** — clustering.
- **Vacuum** — delete old files.
- **Time travel** — `VERSION AS OF`.

### Practical Example

```sql
OPTIMIZE silver.events ZORDER BY (user_id, event_time);
VACUUM silver.events;  -- removes old files
SELECT * FROM silver.events VERSION AS OF 42;
```

### AI Use Case

**Delta Lake IQ** — AI-driven Optimize and Vacuum recommendations.
The Principal's edge: lower storage cost from AI-tuned compaction.

### CTO / Principal Motivation

Delta is **the open standard for lakehouse tables**. The Principal
owns the **table operations**; the CTO owns the **lakehouse
strategy**.

---

## Lesson 7 — Iceberg

### Theory

Iceberg = open table format with REST catalog. Mental model:

- **Metadata files** — JSON/Avro describing snapshot state.
- **Manifest list** — list of manifest files.
- **Manifest** — list of data files.
- **Hidden partitioning** — partition spec is metadata, not path.
- **REST catalog** — Polaris, Unity, Glue.
- **Multi-engine** — Spark, Trino, Flink, Athena.

### Practical Example

```sql
-- Hidden partition: writes to year=2026/month=09/day=28/
INSERT INTO events VALUES (101, '2026-09-28', 'click');

-- Read by partition without knowing path
SELECT * FROM events WHERE event_date = '2026-09-28';
```

### AI Use Case

**AI partition evolution.** AI watches query patterns and recommends
partition spec changes. The Principal's edge: optimized partitioning
without manual analysis.

### CTO / Principal Motivation

Iceberg is **the lakehouse format of choice for multi-engine shops**.
The Principal owns the **catalog**; the CTO owns the **multi-engine
strategy**.

---

## Lesson 8 — Flink

### Theory

Flink = true stream processing. Mental model:

- **Stream** — unbounded data.
- **Window** — bounded subset of stream (tumbling, sliding, session).
- **Watermark** — event-time progress marker.
- **State** — operator state (RocksDB).
- **Checkpoint** — consistent snapshot.
- **Exactly-once** — guarantees.

### Practical Example

```java
stream.keyBy(event -> event.userId)
      .window(TumblingEventTimeWindows.of(Time.minutes(5)))
      .aggregate(new ClickCounter())
      .print();
```

### AI Use Case

**Flink AI** — real-time ML scoring on streams. The Principal's
edge: sub-second ML inference at scale.

### CTO / Principal Motivation

Flink is **the premium stream processor**. The Principal owns the
**state backend**; the CTO owns the **streaming ML strategy**.

---

## Lesson 9 — Debezium & CDC Tools

### Theory

Debezium = log-based CDC. Mental model:

- **Connector** — per database (Postgres, MySQL, MongoDB).
- **Source connector** — reads WAL.
- **Sink connector** — writes to Kafka.
- **Schema evolution** — auto-tracks schema changes.

Alternatives: AWS DMS, Airbyte, Fivetran, Striim.

### Practical Example

```bash
# Postgres connector
curl -X POST http://debezium:8083/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "postgres-connector",
    "config": {
      "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
      "database.hostname": "postgres",
      "database.port": "5432",
      "database.dbname": "app",
      "database.user": "debezium",
      "database.password": "...",
      "plugin.name": "pgoutput",
      "publication.autocreate.mode": "filtered",
      "table.include.list": "public.orders,public.users"
    }
  }'
```

### AI Use Case

**AI CDC schema advisor.** AI watches schema changes and recommends
downstream Iceberg schema updates. The Principal's edge: zero-downtime
schema evolution.

### CTO / Principal Motivation

CDC is **the foundation of replication and real-time analytics**.
The Principal owns the **CDC tool selection**; the CTO owns the
**replication strategy**.

---

## Lesson 10 — Orchestrator Comparison

### Theory

The five leading orchestrators:

| Orchestrator | Type | Best for |
|--------------|------|----------|
| **Airflow** | Python DAGs | Batch, complex DAGs |
| **Step Functions** | JSON state machine | AWS-native, simple |
| **Prefect / Dagster** | Python-native | Modern DX, observability |
| **MWAA** | Managed Airflow | AWS-hosted Airflow |
| **Argo Workflows** | Kubernetes-native | K8s shops |

### Practical Example

```python
# Dagster: code-first, testable
@asset(group_name="events")
def silver_events() -> DataFrame:
    return transform(bronze_events())
```

### AI Use Case

**AI orchestrator advisor.** "Given this team and these requirements,
which orchestrator?" The Principal's edge: standardized choice.

### CTO / Principal Motivation

Orchestrator choice is **sticky**. The Principal owns the **decision
framework**; the CTO owns the **orchestration standardization**
narrative.

---

## Lesson 11 — Quiz: Technology Deep Dives

### Theory

Validate that you can **explain trade-offs** between technologies, not
just features.

### Practical Example

For each technology, write: "Use this when X, instead of Y when Z,
cost $A vs $B."

### AI Use Case

AI-generated comparison tables from your notes.

### CTO / Principal Motivation

Technology literacy is the **prerequisite for architecture
decisions**. CTOs who can defend their tech stack win board
approval.

---

# Module 5 · Question Breakdowns — Core (11 lessons)

## Lesson 1 — Log Aggregation

### Theory

Design a log aggregation system (think Splunk, Datadog Logs).

**Requirements:**
- 100B events/day, 100+ teams.
- 7-year retention for security.
- Sub-second search latency for recent data.
- SQL-like query language.

**Architecture:**
- Agents → Kafka (1-day retention) → Spark/Flink → S3 Iceberg (cold).
- Hot tier: Elasticsearch / OpenSearch (recent 30 days).
- Splunk for security use case.

### Practical Example

```
App logs → Filebeat → Kafka → Spark → S3 Iceberg → Athena (ad-hoc)
                              ↓
                          OpenSearch → Kibana (real-time search)
```

### AI Use Case

**AI log summarization.** LLM summarizes error logs into incident
reports. The Principal's edge: faster MTTR.

### CTO / Principal Motivation

Log aggregation is the **CTO's compliance tool**. "We have all logs
for 7 years." The Principal owns the **pipeline**; the CTO owns the
**audit narrative**.

---

## Lesson 2 — URL Shortener Analytics

### Theory

Design analytics for a URL shortener (think bit.ly).

**Requirements:**
- 100K URLs/sec creation.
- 1B clicks/day.
- Real-time click counts.
- Geographic distribution.
- Bot detection.

**Architecture:**
- Kafka → Flink → ClickHouse (real-time counters).
- Click events → S3 Iceberg (historical).
- Bot detection ML model on stream.

### Practical Example

```sql
-- ClickHouse: top URLs in last hour
SELECT url_id, count() AS clicks
FROM clicks
WHERE event_time > now() - INTERVAL 1 HOUR
GROUP BY url_id
ORDER BY clicks DESC
LIMIT 100;
```

### AI Use Case

**AI bot detection.** ML model classifies clicks as bot/human in
real-time. The Principal's edge: cleaner analytics.

### CTO / Principal Motivation

Real-time analytics is the **CTO's product differentiator**. The
Principal owns the **streaming pipeline**; the CTO owns the
**real-time feature** narrative.

---

## Lesson 3 — E-Commerce Warehouse

### Theory

Design a warehouse for an e-commerce company.

**Requirements:**
- Orders, customers, products, inventory.
- Sub-second dashboard queries.
- Customer 360 view.
- Real-time inventory updates.

**Architecture:**
- OLTP (MySQL/Postgres) → CDC (Debezium) → Kafka → Snowflake/BigQuery.
- Star schema: fact_orders, dim_customer, dim_product, dim_date.
- ML features in feature store.

### Practical Example

```sql
-- Star schema
fact_orders (order_id, customer_id, product_id, date_id, quantity, revenue)
dim_customer (customer_id, name, segment, country)
dim_product (product_id, name, category, price)
dim_date (date_id, date, day_of_week, holiday)
```

### AI Use Case

**AI customer 360.** LLM unifies customer data from support tickets,
emails, orders into a single view. The Principal's edge: better
personalization.

### CTO / Principal Motivation

E-commerce warehouse is the **CTO's revenue engine**. "Our analytics
drive $X in incremental revenue." The Principal owns the **schema**;
the CTO owns the **revenue narrative**.

---

## Lesson 4 — Real-time Dashboard

### Theory

Design a real-time dashboard (think Datadog, Grafana).

**Requirements:**
- 1M metrics/sec ingestion.
- Sub-second query latency.
- 1-year retention.
- Alerting.

**Architecture:**
- Metrics → Kafka → Flink → Druid / ClickHouse / TimescaleDB.
- Dashboards query the OLAP store.
- Alerts evaluated by Prometheus / Alertmanager.

### Practical Example

```
Metrics → Kafka → Flink (windowed aggregation) → ClickHouse
                                          ↓
                                      Grafana dashboards
                                          ↓
                                      Alertmanager
```

### AI Use Case

**AI-powered alerting.** AI watches alert noise, deduplicates,
summarizes. The Principal's edge: 70% less alert fatigue.

### CTO / Principal Motivation

Real-time dashboards are the **CTO's reliability tool**. "We know
about incidents before customers do." The Principal owns the
**metric pipeline**; the CTO owns the **observability narrative**.

---

## Lesson 5 — CDC Replication

### Theory

Design a CDC pipeline replicating Postgres to Snowflake with sub-minute
latency.

**Architecture:**
- Postgres WAL → Debezium → Kafka (long retention) → Kafka Connect
  Snowflake sink → Snowflake.

### Practical Example

```bash
# Snowflake Kafka connector
curl -X POST http://connect:8083/connectors \
  -d '{
    "name": "snowflake-sink",
    "config": {
      "connector.class": "com.snowflake.kafka.connector.SnowflakeSinkConnector",
      "topics": "postgres.public.orders",
      "snowflake.url.name": "account.snowflakecomputing.com",
      "snowflake.user": "debezium",
      "snowflake.private.key": "...",
      "snowflake.database.name": "RAW",
      "snowflake.schema.name": "CDC",
      "tasks.max": "4"
    }
  }'
```

### AI Use Case

**AI-driven schema mapping.** AI auto-maps source types to Snowflake
types. The Principal's edge: zero-touch CDC.

### CTO / Principal Motivation

CDC replication is the **CTO's tool for analytics freshness**.
"Our warehouse is always <5 minutes stale." The Principal owns the
**CDC pipeline**; the CTO owns the **data freshness** narrative.

---

## Lesson 6 — Medallion Data Lake

### Theory

Design a medallion data lake on S3.

**Architecture:**
- Bronze: raw Kafka → S3 (Parquet, partitioned by date).
- Silver: Spark job → Delta/Iceberg, dedup + schema enforce.
- Gold: dbt models → Delta/Iceberg, business aggregates.

### Practical Example

```python
# Bronze: raw ingest
(spark.readStream.format("kafka")
 .option("subscribe", "events")
 .load()
 .writeStream
 .format("parquet")
 .partitionBy("year", "month", "day")
 .start("s3://bronze/events/"))

# Silver: DLT
@dlt.table
def silver_events():
    return dlt.read_stream("bronze.events").dropDuplicates(["event_id"])
```

### AI Use Case

**AI-curated gold.** AI watches analyst queries, recommends new
gold tables. The Principal's edge: faster analytics.

### CTO / Principal Motivation

Medallion lake is **the 2026 default**. The Principal owns the
**layer definitions**; the CTO owns the **data architecture
narrative**.

---

## Lesson 7 — ETL Framework

### Theory

Design a generic ETL framework (think Airbyte, Fivetran).

**Requirements:**
- 100+ sources, 50+ destinations.
- Schema auto-discovery.
- Backfill + incremental.

**Architecture:**
- Connectors (per source) → Kafka → Normalizer → Kafka → Destination
  connectors.
- Metadata DB for sync state.
- Web UI for management.

### Practical Example

```python
class Connector(ABC):
    @abstractmethod
    def discover(self): pass
    @abstractmethod
    def extract(self): pass
    @abstractmethod
    def normalize(self): pass

class PostgresConnector(Connector):
    def discover(self):
        return self.inspect_catalog()
    def extract(self):
        return self.read_wal()
```

### AI Use Case

**AI connector generator.** AI reads API docs and generates new
connectors. The Principal's edge: faster connector ecosystem.

### CTO / Principal Motivation

ETL framework is **the CTO's product**. If you sell one, this is
the architecture. The Principal owns the **framework**; the CTO
owns the **product roadmap**.

---

## Lesson 8 — Feature Store

### Theory

Design a feature store (think Tecton, Feast).

**Requirements:**
- Online + offline features.
- Point-in-time correctness.
- Sub-10ms online latency.

**Architecture:**
- Offline: Delta/Iceberg tables, partitioned by entity + time.
- Online: Redis / DynamoDB, keyed by entity_id.
- Feature definitions in Python.
- Materialization jobs (Spark).

### Practical Example

```python
# Feature definition
@feature_view(
    entities=["user_id"],
    ttl="30d",
    online=True
)
def user_clicks_7d(user_id):
    return spark.sql(f"""
        SELECT user_id, count(*) AS clicks
        FROM silver.events
        WHERE event_date >= current_date - INTERVAL 7 DAYS
        GROUP BY user_id
    """)
```

### AI Use Case

**AI feature discovery.** AI watches model training, suggests
features. The Principal's edge: better models, faster.

### CTO / Principal Motivation

Feature store is **the CTO's ML productivity tool**. "Our models
ship 5× faster." The Principal owns the **store**; the CTO owns
the **ML velocity** narrative.

---

## Lesson 9 — DQ Monitoring

### Theory

Design a Data Quality monitoring system (think Great Expectations,
Monte Carlo).

**Requirements:**
- Schema, freshness, volume, value, custom tests.
- Alert on violations.
- Lineage integration.

**Architecture:**
- Test runner → Kafka → DQ DB → Grafana dashboards.
- Lineage from catalog → DQ propagation.

### Practical Example

```yaml
# Great Expectations suite
expectations:
  - expect_column_values_to_not_be_null: order_id
  - expect_column_values_to_be_between: [amount, 0, 1000000]
  - expect_table_row_count_to_be_between: [100000, 10000000]
```

### AI Use Case

**AI-driven DQ.** AI learns normal patterns, detects anomalies.
The Principal's edge: catches issues manual tests miss.

### CTO / Principal Motivation

DQ monitoring is **the CTO's trust tool**. "Our data is correct."
The Principal owns the **DQ platform**; the CTO owns the **trust
narrative**.

---

## Lesson 10 — Uber Surge Pricing

### Theory

Design the surge pricing system.

**Requirements:**
- Real-time pricing per geo-cell.
- Driver supply + rider demand.
- Sub-second updates.

**Architecture:**
- Stream of trip requests + driver locations → Kafka → Flink → Redis
  (supply/demand per cell) → ML pricing model → driver app.

### Practical Example

```python
# Flink: compute supply/demand per cell
stream.key_by(event -> event.geo_cell)
      .window(TumblingEventTimeWindows.of(Time.seconds(30)))
      .aggregate(new SupplyDemandAggregator())
      .sink_to(redis_sink)
```

### AI Use Case

**ML pricing model.** Gradient-boosted trees on (supply, demand,
weather, events, time-of-day) → surge multiplier. The Principal's
edge: better price = better margin.

### CTO / Principal Motivation

Surge pricing is **the CTO's revenue driver**. "$X in incremental
revenue from better pricing." The Principal owns the **model
pipeline**; the CTO owns the **margin narrative**.

---

## Lesson 11 — Quiz: Question Breakdowns — Core

### Theory

Validate that you can **solve each problem in 30 minutes**. Drill the
8-step framework on each.

### Practical Example

For each problem, time yourself. Target: 30 min from "design X" to
"here's the architecture with trade-offs."

### AI Use Case

AI-mock-interviewer. Practice 20 problems with AI feedback.

### CTO / Principal Motivation

Speed + accuracy under pressure is the **CTO's interview edge**.

---

# Module 6 · Question Breakdowns — Advanced (11 lessons)

## Lesson 1 — Spotify Analytics

### Theory

Design Spotify's analytics system.

**Requirements:**
- 500M users, plays per day at billion scale.
- "Discover Weekly", "Daily Mix" playlists.
- Real-time + batch analytics.
- ML-driven recommendations.

**Architecture:**
- Kafka → Flink → Iceberg → Athena/Trino.
- ML features in feature store, models in SageMaker/Vertex.
- A/B test framework.

### Practical Example

```python
# Recommendation pipeline
plays = spark.read.parquet("s3://silver/plays/")
features = (plays.groupBy("user_id")
                 .agg(F.count("*").alias("plays_30d"),
                      F.countDistinct("track_id").alias("unique_tracks")))
features.write.parquet("s3://features/user_features/")
```

### AI Use Case

**AI music recommendation.** LLM-based embeddings of audio + lyrics.
The Principal's edge: better recommendations, longer sessions.

### CTO / Principal Motivation

Spotify-scale analytics is **the CTO's product differentiator**.
"Our recommendations drive 30% of streams." The Principal owns
the **feature pipeline**; the CTO owns the **engagement narrative**.

---

## Lesson 2 — Netflix Recommendations

### Theory

Design Netflix's recommendation system.

**Components:**
- Implicit feedback (views, ratings, time-watched).
- Content embeddings (video, audio, subtitles, metadata).
- Two-tower model for retrieval.
- Re-ranker with contextual bandits.

### Practical Example

```python
# Two-tower retrieval
user_emb = user_tower(user_features)  # shape (N, d)
item_emb = item_tower(item_features)  # shape (M, d)
scores = user_emb @ item_emb.T         # shape (N, M)
top_k = scores.topk(100)
```

### AI Use Case

**LLM-based embeddings.** Use a multimodal LLM (CLIP, etc.) to embed
content. The Principal's edge: better cold-start recommendations.

### CTO / Principal Motivation

Recommendations are **Netflix's moat**. The Principal owns the
**embedding pipeline**; the CTO owns the **engagement narrative**.

---

## Lesson 3 — Fraud Detection

### Theory

Design a real-time fraud detection system.

**Requirements:**
- Sub-100ms decision latency.
- 10K transactions/sec.
- 0.1% false positive rate.
- Explainability.

**Architecture:**
- Transaction → Kafka → Feature lookup (Redis) → ML model → Decision
  (approve / decline / review).

### Practical Example

```python
# Online scoring
features = feature_store.get_online_features(user_id, transaction)
risk_score = fraud_model.predict_proba(features)
if risk_score > 0.95:
    decline()
elif risk_score > 0.7:
    flag_for_review()
```

### AI Use Case

**LLM-based feature engineering.** LLM extracts features from
unstructured data (email, chat). The Principal's edge: better
fraud detection.

### CTO / Principal Motivation

Fraud detection is **the CTO's risk management tool**. "We saved
$X in fraud this year." The Principal owns the **model**; the
CTO owns the **risk narrative**.

---

## Lesson 4 — Twitter/X Analytics

### Theory

Design Twitter's analytics (the engagement metrics, not the timeline).

**Requirements:**
- Real-time impressions, likes, retweets.
- 500M tweets/day.
- Trending topics.

**Architecture:**
- Tweet events → Kafka → Flink → Cassandra (timeline) + Druid (analytics).
- ML for trending topic detection (HLL sketches).

### Practical Example

```sql
-- Druid: top hashtags last hour
SELECT hashtag, count(*) AS tweets
FROM tweets
WHERE __time > now() - INTERVAL '1' HOUR
GROUP BY hashtag
ORDER BY tweets DESC
LIMIT 100;
```

### AI Use Case

**LLM-based content moderation.** LLM classifies tweets as
toxic / safe / spam. The Principal's edge: safer platform.

### CTO / Principal Motivation

Real-time analytics is **the CTO's product differentiator**. The
Principal owns the **pipeline**; the CTO owns the **engagement
narrative**.

---

## Lesson 5 — Multi-tenant Platform

### Theory

Design a multi-tenant data platform (think Snowflake, Databricks).

**Requirements:**
- Thousands of tenants.
- Per-tenant isolation.
- Per-tenant billing.

**Architecture:**
- Tenant-aware scheduler, isolation per tenant.
- Resource quotas enforced at the warehouse.
- Per-tenant cost attribution via tags.

### Practical Example

```yaml
# Tenant policy
tenants:
  - id: acme
    warehouse_size: medium
    max_dbu_per_day: 1000
    isolation: dedicated
  - id: smallco
    warehouse_size: xsmall
    max_dbu_per_day: 10
    isolation: shared
```

### AI Use Case

**AI-based tenant sizing.** AI watches tenant usage, recommends
right-sizing. The Principal's edge: higher margin.

### CTO / Principal Motivation

Multi-tenant platforms are **the CTO's business model**. The
Principal owns the **platform**; the CTO owns the **unit economics**
narrative.

---

## Lesson 6 — Recommendation Engine

### Theory

Design a generic recommendation engine.

**Components:**
- Candidate generation (two-tower / ANN).
- Filtering (already-watched, geo, business rules).
- Ranking (LambdaMART, neural).
- Re-ranking (diversity, freshness).
- Calibration.

### Practical Example

```python
# ANN retrieval (FAISS)
import faiss
index = faiss.IndexFlatL2(d)
index.add(item_embeddings)
scores, indices = index.search(user_emb, k=100)
```

### AI Use Case

**LLM-based recommendations.** LLM understands natural language
queries ("cozy mystery novels"). The Principal's edge: better UX.

### CTO / Principal Motivation

Recommendation engines are **the CTO's engagement driver**. The
Principal owns the **model pipeline**; the CTO owns the
**engagement narrative**.

---

## Lesson 7 — LinkedIn Activity Feed

### Theory

Design LinkedIn's activity feed.

**Components:**
- Fan-out on write (push) vs fan-out on read (pull).
- Ranking model.
- Notification system.

**Architecture:**
- Post → Kafka → Fan-out service → User feed cache (Redis).
- Ranking service reads feed + signals → ML score → display.

### Practical Example

```python
# Fan-out service
def on_post_created(post):
    followers = get_followers(post.author_id)
    for follower in followers:
        feed_cache.insert(follower.user_id, post.id)
```

### AI Use Case

**AI-ranked feed.** LLM as the ranker, fine-tuned on engagement.
The Principal's edge: better engagement.

### CTO / Principal Motivation

Activity feed is **LinkedIn's product**. The Principal owns the
**fan-out + ranking**; the CTO owns the **engagement narrative**.

---

## Lesson 8 — Ad Clickstream

### Theory

Design an ad clickstream attribution system.

**Requirements:**
- 10B events/day.
- Multi-touch attribution.
- Sub-minute attribution feedback.

**Architecture:**
- Click → Kafka → Flink → ClickHouse (real-time attribution).
- ML attribution model (shapley value).
- Per-campaign dashboards.

### Practical Example

```sql
-- Attribution per campaign
SELECT campaign_id,
       count(DISTINCT user_id) AS reach,
       sum(converted) AS conversions,
       sum(revenue) AS revenue
FROM attribution
WHERE event_date = today
GROUP BY campaign_id;
```

### AI Use Case

**ML attribution.** Shapley-value-based multi-touch attribution.
The Principal's edge: better ad spend optimization.

### CTO / Principal Motivation

Ad clickstream is **the CMO's tool**. The Principal owns the
**attribution pipeline**; the CTO owns the **ad revenue narrative**.

---

## Lesson 9 — Data Mesh Platform

### Theory

Design a data mesh platform (the central platform that supports
domain teams).

**Components:**
- Self-serve infrastructure (Terraform templates).
- Federated catalog (Unity Catalog / DataHub).
- Data contracts.
- Domain SLAs.

### Practical Example

```yaml
# Domain registration
domain: sales
owner: sales-data-team
slos:
  freshness: 6h
  completeness: 99%
products:
  - orders_v1
  - customer_v1
```

### AI Use Case

**AI-augmented mesh.** AI watches domain products, suggests
contract updates, flags violations. The Principal's edge:
self-healing mesh.

### CTO / Principal Motivation

Data mesh is **the CTO's org-scale tool**. The Principal owns the
**platform**; the CTO owns the **org design**.

---

## Lesson 10 — IoT Sensor Pipeline

### Theory

Design an IoT sensor pipeline (factory, smart city).

**Requirements:**
- 1M sensors × 1Hz = 1M events/sec.
- Sub-second anomaly detection.
- 1-year retention.

**Architecture:**
- Sensors → MQTT broker → Kafka → Flink (anomaly detection) → TSDB
  (Prometheus / InfluxDB) + S3 Iceberg (long-term).

### Practical Example

```python
# Flink: anomaly detection on temperature stream
stream.key_by(sensor -> sensor.id)
      .process(new AnomalyDetector(threshold=80))
      .sink_to(alert_topic)
```

### AI Use Case

**ML-based predictive maintenance.** Train on historical sensor data,
predict failures 24h ahead. The Principal's edge: lower downtime.

### CTO / Principal Motivation

IoT is **the CTO's product moat** in industrial domains. The
Principal owns the **pipeline**; the CTO owns the **reliability
narrative**.

---

## Lesson 11 — Quiz: Question Breakdowns — Advanced

### Theory

Validate that you can **solve each advanced problem in 45 minutes**.
Drill the 8-step framework with deep dives on the trickiest component.

### Practical Example

Time-box yourself: 45 minutes per problem. 20 problems = 15 hours of
drill. The Principal's edge: repetition.

### AI Use Case

AI-mock-interviewer with deep-dive follow-ups.

### CTO / Principal Motivation

The advanced problems are **the CTO interview's hardest questions**.
The Principal's deliverable: 5 problems where you can defend your
design for 45 minutes without notes.

---

# Closing Notes

## The Promotion Path from this Course

| Level        | Skill unlocked by this course | Compensation signal |
|--------------|-------------------------------|---------------------|
| Senior DE    | Designs single-system solutions; runs the framework | $150-200k |
| Staff DE     | Designs cross-system solutions; defends trade-offs at scale | $200-280k |
| Principal DE | Designs platform patterns; sets org-wide standards | $280-400k |
| Director / VP | Designs org structure; picks platform vs build vs buy | $350-500k+ |
| CTO          | Designs data strategy; negotiates with board | $400-700k+ |

## The Single Most Important Habit

After each lesson, **solve one problem from the question-breakdown
modules** using the 8-step framework. Time-box yourself. The
compound effect of 65 problems × 8 steps × 1-hour drill is the
fastest path from Senior to Principal.

## The Two CTO Pillars

This course is the **technical pillar** of becoming a Principal / CTO.
The **other pillar** is communication — the ability to write
defensible artifacts, present trade-offs to executives, and mentor
junior engineers. Both pillars are required; neither is sufficient.

## Cross-References

- **AWS DE CTO plan** — `aws_de_cto_learning_plan.md` in this folder.
- **Azure DE CTO plan** — `azure_de_cto_learning_plan.md` in this folder.
- **DE Foundations track** — `01_de_foundations_track.md`.
- **DE Interview Prep full** — `05_de_interview_prep.md` — the original
  interview-prep course this builds on.
