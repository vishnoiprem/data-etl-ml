# 30 — Mock Interview: Design a CDC Pipeline for a Banking System

> **Lesson 30 of 30 — Mock Interviews**

A full 30-minute mock interview transcript with a candidate
designing a Change Data Capture pipeline for a banking
system. The candidate is a Senior Data Engineer (L6 level)
at a hypothetical loop. The scenario is the most demanding
in the track: regulatory compliance, exactly-once, schema
evolution, and 24/7 uptime.

---

## Setup

**Company:** Big bank (hypothetical, modeled on the
canonical banking-CDC question).
**Role:** Senior Data Engineer.
**Level:** L6.
**Format:** 30-minute system design round, on-site whiteboard.
**Question:** *"Design a CDC pipeline that captures every
change to the core banking database (account balances,
transactions, customer records) and feeds it to a data
warehouse for regulatory reporting and fraud detection.
Volume: 50K transactions per second peak, 24/7 uptime
required, no data loss tolerated."*

---

## Transcript (30 minutes)

### 0:00 — Opening framing

> **Candidate:** Banking is a high-stakes environment, so
> let me make sure I have the requirements right before I
> draw. You said 50K transactions per second peak — that's
> the source-side rate or the change-event rate? And the
> "no data loss tolerated" — is that a regulatory
> requirement (Sarbanes-Oxley, BCBS 239) or an internal SLA?
> And the consumers — regulatory reporting is presumably
> daily, but fraud detection is real-time, right?

> **Interviewer:** Source-side. The transaction system
> processes 50K writes per second. Every write becomes a
> CDC event, so 50K events per second. Data loss is
> regulatory: BCBS 239 requires complete and accurate
> reporting. Fraud is real-time, sub-second to
> sub-minute. Regulatory is daily.

> **Candidate:** Three big constraints then. Regulatory
> means exactly-once or as-close-to-it-as-we-can-get. Real-time
> fraud means low-latency streaming. 24/7 means no maintenance
> windows — every change is online. The architecture has to
> support all three.

### 3:00 — High-level architecture

> **Candidate:** Six boxes. **[DRAWING 1]**

```
┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│ Core       │───►│ Debezium   │───►│ Kafka      │───►│ Flink      │
│ banking DB │    │ (Postgres  │    │ (100 part, │    │ stream     │
│ (OLTP,     │    │  WAL       │    │  3x repl)  │    │ processor  │
│  Postgres) │    │  reader)   │    │            │    │            │
└────────────┘    └────────────┘    └─────┬──────┘    └─────┬──────┘
                                         │                 │
                                         │                 ▼
                                         │          ┌────────────┐
                                         │          │ Real-time  │
                                         │          │ fraud      │
                                         │          │ detector   │
                                         │          │ (Redis +   │
                                         │          │  ML model) │
                                         │          └────────────┘
                                         ▼
                                   ┌────────────┐
                                   │ S3 /       │───► Snowflake
                                   │ Delta Lake │     (regulatory,
                                   │ (bronze)   │      reporting)
                                   └────────────┘
```

> **Candidate:** The source is the core banking OLTP
> database — likely Postgres or Oracle. Debezium reads
> the WAL and emits CDC events to Kafka. Kafka has
> 100 partitions with 3x replication. The Flink job
> consumes from Kafka, applies transformations, and
> feeds two downstream paths: the real-time fraud
> detector (Redis + ML) and the Delta Lake bronze layer.
> Snowflake reads from the bronze layer for regulatory
> reporting.
>
> The hot path is the Debezium → Kafka → Flink chain.
> The reliability story is the deep dive.

### 6:00 — Back-of-envelope estimation

> **Candidate:** 50K events/sec × 1 KB/event × 86400 sec
> = 4.3 TB/day. Peak rate 50K/sec, average maybe 20K/sec,
> so the cluster needs to handle 50K steady-state with
> 2x burst = 100K/sec.
>
> Kafka cluster sizing: each broker handles ~10K events/sec
> for a 1 KB message. 100K/sec = 10 brokers minimum,
> 30 brokers for headroom. The replication factor is 3, so
> the cluster is 30 brokers with 10 partitions per broker
> for a 100-partition topic.
>
> Flink cluster: 50 task managers, 4 GB heap each. State
> backend is RocksDB on local SSD (faster recovery than
> heap). Checkpointing every 30 seconds to S3.

### 8:00 — The deep dive: Debezium and exactly-once

> **Interviewer:** Walk me through the Debezium layer. How
> do you guarantee no data loss?

> **Candidate:** Three pieces. **[DRAWING 2]**

```
Postgres WAL
  ↓
Debezium connector
  - Replication slot "cdc_slot" (server-side cursor)
  - Records LSN (Log Sequence Number) as it consumes
  - Emits c / u / d events with before/after images
  ↓
Kafka topic "cdc.transactions"
  - 100 partitions, key = transaction_id
  - All events for a transaction go to the same partition
```

> **Candidate:** First, the replication slot. Postgres
> has a server-side cursor called a replication slot. The
> slot remembers the consumer's last position in the WAL.
> If the consumer (Debezium) disconnects, the WAL grows
> until the consumer reconnects. The slot is the
> exactly-once anchor: events are emitted from the slot
> in commit order, and the slot's LSN is updated
> transactionally with the Kafka write.
>
> Second, the Kafka topic is partitioned by `transaction_id`
> so all events for a transaction are ordered. The Flink
> consumer is also keyed on `transaction_id`, so the
> processing is per-transaction.
>
> Third, the Kafka producer is idempotent
> (`enable.idempotence=true`) and the consumer is
> read-committed. If Debezium crashes after writing to
> Kafka but before committing the slot, the retry reads
> the same events from the WAL and writes them again.
> Idempotency keys dedup the duplicates on the consumer.
>
> The result: at-least-once delivery with idempotent
> consumption = effectively exactly-once.

### 13:00 — Slot lag and operational concerns

> **Interviewer:** What about slot lag? What if the
> consumer is slow?

> **Candidate:** Slot lag is the silent killer in CDC.
> If the consumer falls behind, the WAL grows. If the
> disk fills up, the source database stops accepting
> writes. The whole bank stops.
>
> The mitigation: **[DRAWING 3]**
>
> One, monitor slot lag. A daily query:
> ```sql
> SELECT slot_name,
>        pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS lag
> FROM pg_replication_slots;
> ```
> Alert if lag > 1 GB or > 5 minutes behind.
>
> Two, set a hard cap on the WAL size. Postgres has
> `max_wal_size` (default 1 GB). I'd set it to 50 GB to
> give us 30 minutes of buffer.
>
> Three, autoscaling on the consumer. If Flink lag
> grows, add more task managers. The Flink job's
> parallelism is configurable; the orchestrator
> increases it on a lag alert.
>
> Four, a kill switch. If lag exceeds 10 GB, the
> Flink job pauses consumption. The events stay in
> the WAL. We page the on-call; humans decide.

### 17:00 — Schema evolution

> **Interviewer:** What happens when the source schema
> changes? A new column on `accounts`, say.

> **Candidate:** Two cases. **[DRAWING 4]**
>
> Backward-compatible change (new nullable column).
> Debezium emits a schema change event before the data
> event. The Flink job has a schema-aware deserializer
> that handles the new field: the existing schema is
> widened to include the new column, defaulting to NULL
> for old rows. The downstream Kafka topic gets the
> widened schema. Snowflake handles the new column
> via `ALTER TABLE ... ADD COLUMN`.
>
> Backward-incompatible change (rename, type narrowing).
> This is a deployment, not a config change. The team
> agrees on a migration plan: add the new column,
> backfill, dual-write for a transition period, drop
> the old column. The CDC pipeline runs in dual-write
> mode for the duration.
>
> The schema registry is the gatekeeper. Debezium
> publishes every schema to the registry. Breaking
> changes are rejected at registration time.

### 20:00 — The fraud detection path

> **Interviewer:** How does the real-time fraud
> detector work?

> **Candidate:** The Flink job has two output streams.
> **[DRAWING 5]**

```
Flink job output 1: real-time fraud
  ↓
Redis (per-user features)
  - rolling 1-hour transaction count
  - rolling 1-hour total spend
  - last transaction timestamp
  ↓
ML model (Python, runs in Flink)
  - input: per-user features + current transaction
  - output: fraud probability 0-1
  ↓
If fraud_prob > 0.9: alert (Kafka "fraud.alerts")
If 0.5 < fraud_prob < 0.9: queue for human review
If fraud_prob < 0.5: pass
```

> **Candidate:** The Flink job maintains per-user
> features in keyed state (RocksDB). For every
> transaction, the job:
>
> 1. Reads the current user's features from state.
> 2. Updates the features with the new transaction.
> 3. Calls the ML model with the features + transaction.
> 4. If fraud score > 0.9, emits to the alerts topic.
>
> The ML model is small (~50ms inference) so it fits in
> the Flink job. If the model is large, we'd use a
> side-car Python service and an async call.
>
> The deep dive here is the state management: how the
> per-user features are kept consistent under Flink
> failover. RocksDB state + checkpointing to S3
> handles it. The features are recovered from the
> last checkpoint.

### 25:00 — The regulatory path

> **Interviewer:** And the regulatory reporting path?

> **Candidate:** The Flink job's second output is the
> Delta Lake bronze layer. **[DRAWING 6]**

```
Flink job output 2: Delta Lake
  ↓
Delta table "bronze.transactions"
  - partitioned by event_date
  - all CDC events: c, u, d with before/after
  - schema enforced (additive only, via mergeSchema)
  ↓
Daily dbt run
  - reads bronze
  - applies SCD2 for accounts and customers
  - computes daily aggregates
  - writes to gold tables:
    - fct_transactions_daily
    - fct_account_balance_daily
    - dim_account_scd2
    - dim_customer_scd2
  ↓
Snowflake (regulatory schema)
  - daily snapshot for regulators
  - 7-year retention
```

> **Candidate:** The Delta Lake is the source of truth
> for the regulatory path. The dbt run is daily; it
> reads the bronze layer, applies SCD2 for accounts and
> customers (so we have point-in-time history), computes
> aggregates, and writes to gold tables. Snowflake
> reads from the gold layer for the regulatory
> submission.
>
> The deep dive on the regulatory path is the
> reconciliation: the daily dbt run compares the
> account balance in the warehouse against the source
> system. Any drift > $1 pages the on-call. The
> regulators care about pennies, so the threshold is
> strict.

### 28:00 — Failure modes

> **Interviewer:** Five things that can go wrong, please.

> **Candidate:** Five failure modes. **[DRAWING 7]**
>
> One, the source database is down. The WAL is still
> being written, but the CDC connector can't read.
> When the database comes back, Debezium reconnects
> and resumes from the last LSN. No data loss.
>
> Two, Kafka is unavailable. Debezium buffers up to
> its memory limit; if exceeded, it pauses. The WAL
> keeps growing. If Kafka is down for > 5 minutes,
> page on-call.
>
> Three, Flink TaskManager dies. The jobmanager
> reschedules on a new TaskManager. The state is
> recovered from the last checkpoint (RocksDB on
> S3). Recovery time is ~ 1 minute for 50 GB of state.
>
> Four, slot lag grows. Covered above. The kill
> switch pauses consumption; the WAL holds the events.
>
> Five, schema breaks. The schema registry rejects
> the change; the Debezium connector stays on the old
> schema. The on-call investigates; the team plans
> the migration.

### 30:00 — Wrap-up

> **Candidate:** The architecture is Debezium → Kafka
> → Flink → Delta → dbt → Snowflake for the regulatory
> path; Flink → Redis → ML for the fraud path. The
> hot path is the Debezium → Kafka chain, with the
> replication slot as the exactly-once anchor. The
> deep dive is the slot-lag monitoring — that's
> the silent killer in any CDC pipeline. The cost
> driver is the Kafka cluster (30 brokers × $2K/month
> = $60K/month) and the Flink cluster (50 task managers
> × $1K/month = $50K/month). Total ~$150K/month,
> which is small for a bank.

---

## Post-interview analysis

**What was good:**

- Asked about the regulatory context (BCBS 239) — a
  sign of senior experience.
- The replication slot mechanism is described at the
  right level of detail.
- The slot-lag concern is named unprompted — this is
  the #1 thing that gets banking CDC pipelines wrong.
- The schema evolution answer covers both compatible
  and incompatible changes.
- The reconciliation check is a banking-specific
  detail that shows real-world experience.
- The cost estimate is in the right ballpark.

**What was missing:**

- Could have named the encryption story (TLS in
  transit, encryption at rest on S3, KMS key
  rotation). Banking is heavily regulated.
- The audit log was not mentioned. Every CDC event
  should be auditable; regulators may ask for it.
- The PII handling — names, SSNs — should be
  redacted before the data lands in Snowflake. A
  separate tokenization service is common.
- The DR story — what if the region goes down? Multi-
  region replication, RPO/RTO targets.

**Score against the rubric:**

| Bucket | Score |
|---|---|
| Problem framing (15%) | 5/5 — asked about regulatory context, real-time vs batch |
| Estimation (10%) | 5/5 — math is right, broker count is derived |
| High-level architecture (20%) | 5/5 — six boxes, all the right pieces |
| Hot-path deep dive (35%) | 5/5 — replication slot, idempotency, slot lag |
| Tradeoff articulation (20%) | 4/5 — schema evolution good; encryption/audit/PII missing |

**Overall: senior+ answer.** Would pass at L6.

---

## Try it

Re-do this mock interview out loud. The slot-lag story is
the heart of the answer. If you can describe it cold, you
have the framework.
