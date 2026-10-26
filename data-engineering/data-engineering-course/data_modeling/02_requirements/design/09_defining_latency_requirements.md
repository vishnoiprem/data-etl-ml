# Defining Latency Requirements

## Why this lesson

Latency is the single most consequential non-functional requirement in a data warehouse design. A daily-batch warehouse looks architecturally different from a real-time one: the former has an overnight ETL pipeline and a star schema optimized for periodic snapshots; the latter has streaming ingestion, an event-time partitioned fact table, and a serving layer. Conflating the two leads to a schema that is wrong for both. This lesson — using a subscription SaaS worked example — teaches you how to discover the right latency tier (batch / micro-batch / near-real-time / real-time), what the SLA looks like in minutes, and how the choice cascades into partitioning, freshness, and fact-table grain.

---

## The prompt

> Interviewer: "Design a data warehouse for a subscription
> product (think Notion or Linear) so the analytics team can
> measure monthly recurring revenue, churn, and expansion."

The candidate's job: surface the latency requirement first,
because it determines the rest of the architecture.

---

## The latency tiers

There are four latency tiers a senior candidate is expected to
know cold:

| Tier | End-to-end latency | Typical use case | Pipeline shape |
|---|---|---|---|
| **Daily batch** | 12–24 hours | Executive dashboards, finance close | Nightly ETL, fact table overwritten or appended by day partition |
| **Hourly / micro-batch** | 1 hour | Ops dashboards, product analytics | Hourly ETL or 5–15 min micro-batch, fact table partitioned by hour |
| **Near-real-time** | 1–5 minutes | Customer-facing dashboards, live ops | Streaming ingest (Kafka → warehouse), event-time partitioning, materialized views |
| **Real-time** | < 1 second | Fraud detection, bidding, live recommendations | Stream processing (Flink, Spark Streaming), serving store (Redis, Druid) |

The interview signal: the candidate names the *tier* explicitly
and asks the interviewer which one applies. Without this, the
schema is guesswork.

---

## Latency discovery — the subscription worked example

> Candidate: "Subscription products have specific latency
> tradeoffs. Before I draw, can I ask a few discovery questions?"

1. **What's the freshness tier?**
   > "Are we building this for **daily batch** (12–24h latency,
   > finance-close level), **hourly** (ops dashboards, churn
   > alerts), **near-real-time** (1–5 min, customer-facing
   > dashboards), or **real-time** (<1s, fraud or in-product
   > use)?"
2. **What does the SLA look like in minutes?**
   > "If a customer cancels, when does that cancellation need to
   > show up — in tomorrow's MRR report, in this morning's
   > ops dashboard, or in a live customer-success alert?"
3. **Are there different SLAs for different consumers?**
   > "Does finance need 24h-accurate MRR, while customer success
   > needs 5-minute-accurate churn signals? In that case we'd
   > build two pipelines with different freshness, not one."
4. **Can the source system actually support the SLA?**
   > "What does the source OLTP actually publish at — change
   > data capture at sub-minute, or polling at hourly? The
   > warehouse SLA can be no fresher than the source."
5. **What's the cost of being late?**
   > "If MRR is 4 hours stale, what's the cost — a slightly
   > delayed board deck, or a real customer-success miss? The
   > cost justifies (or doesn't) the engineering cost of a
   > streaming pipeline."
6. **How are late-arriving events handled?**
   > "If a billing event from yesterday arrives today, do we
   > re-process yesterday's partition, or do we drop the event?
   > This affects whether we partition by event-time or
   > arrival-time."
7. **What's the freshness for fact vs dim?**
   > "Do dims need to refresh at the same cadence as facts, or
   > can dims be daily-batch while facts are near-real-time?
   > The asymmetry is common and a real optimization."

---

## How latency drives schema choice

| Latency tier | Fact table pattern | Partitioning | SCD strategy |
|---|---|---|---|
| **Daily batch** | Periodic snapshot or transactional fact, refreshed by day partition | Partition by `date_key` (int 20240115) | SCD 2 dims, refreshed daily |
| **Hourly** | Transactional fact, appended hourly | Partition by `date_key` + `hour_key` | SCD 2 dims, refreshed hourly |
| **Near-real-time** | Event fact at the event grain, partitioned by event-time | Partition by event-time (timestamp) | SCD 2 dims, CDC-streamed |
| **Real-time** | Event fact + serving store (Redis / Druid) | Event-time + watermark | SCD 1 dim, point-in-time dim lookups in app |

The interview move: name the tier, name the partitioning
strategy, name the SCD strategy. Three sentences that show
end-to-end fluency.

---

## The interviewer's answers (compressed)

> Interviewer: Daily batch. Finance needs 24h-accurate MRR for
> board reporting. Customer-success churn signals are a phase-2
> problem; daily is fine for v1. Source OLTP publishes CDC
> hourly, so we *could* go hourly, but finance is the bottleneck,
> so daily is the right answer.

The candidate's call: **daily batch**, partitioned by `date_key`,
SCD 2 on `dim_customers` and `dim_plans`. Note that the
*capability* (hourly CDC) is higher than the *requirement* (daily
finance) — the candidate correctly anchors on the requirement,
not the capability.

---

## The latency-driven requirements doc (3 minutes)

The candidate writes (or narrates):

```markdown
# Requirements — Subscription SaaS

## Latency tier
- **Daily batch** (24h SLA) for finance and board reporting
- (Phase 2: hourly churn signals for customer success)

## Consumers
- **Analytics** — MRR, churn, expansion dashboards (daily)
- **Data Science** — churn prediction, expansion propensity
- **Customer Success** — accounts-at-risk alerts (phase 2)

## Use cases
1. MRR by month, by plan, by acquisition channel
2. Net new MRR (new + expansion − churn − contraction)
3. Logo churn by cohort
4. Revenue churn (lost MRR) by cohort
5. Expansion rate (upgrades as % of starting MRR) by cohort

## Source systems
| name | system | volume | freshness |
| --- | --- | --- | --- |
| customers | PostgreSQL | 10k/day | CDC hourly (capability) |
| subscriptions | PostgreSQL | 5k/day | CDC hourly (capability) |
| invoices | PostgreSQL | 50k/day | CDC hourly (capability) |
| plans | PostgreSQL | 100 rows | daily |

## Fact tables
- **fact_subscriptions_monthly** — grain: one row per
  customer-month (periodic snapshot)
  - measures: mrr, arr, is_active, is_new, is_churned,
    is_expansion, is_contraction
  - dimensions: dim_customers, dim_plans, dim_date
- **fact_subscription_events** — grain: one row per subscription
  event (created, upgraded, downgraded, churned, reactivated)
  - measures: mrr_delta
  - dimensions: dim_customers, dim_plans, dim_date, dim_event_type

## Non-functional
- **Latency tier:** daily batch (24h SLA)
- **Volume:** 100k active subs, 1M+ historical customer-months
- **Freshness:** daily (driven by finance, not by source CDC)
- **Retention:** 7 years (finance / audit)
```

---

## The grain commitment (1 minute)

> Candidate: "OK — to make sure I have this right: the primary
> fact table is `fact_subscriptions_monthly` at the grain of
> **one row per customer-month**, with `mrr`, `is_active`, and
> `is_churned` as the headline measures. The latency tier is
> **daily batch** — even though the source CDC is hourly, the
> finance SLA is 24h, so the schema is partitioned by
> `date_key` and refreshed nightly. The
> `fact_subscription_events` table at the event grain handles
> the change events (new, upgrade, downgrade, churn). `dim_plans`
> is SCD Type 2 (we need historical plan prices for accurate
> revenue). Free trials are modeled as a $0 plan with an
> `is_trial` flag. Does that match what you had in mind?"

The interviewer confirms. The candidate has committed to:

1. **Latency tier:** daily batch (anchored on the *requirement*,
   not the *capability*).
2. **Grain:** customer-month (a periodic snapshot fact — see
   Module 05).
3. **Plan SCD:** Type 2.
4. **Event model:** separate event-level fact table for
   transitions.
5. **Trial model:** $0 plan with a flag (not a separate
   entity).
6. **Churn definition:** voluntary cancel only.

These six decisions drive the star schema in Module 05, where we
look at the *periodic snapshot* pattern in detail.

---

## What the candidate did right

- Asked the **MRR definition** question first — MRR is a
  famously slippery metric.
- Asked the **churn definition** question second — another
  famously slippery metric.
- Named the **latency tier** explicitly (daily batch).
- Distinguished between **capability** (hourly CDC) and
  **requirement** (24h finance SLA) — a real engineering
  answer to a real scoping question.
- Deferred ASC 606 to a "later phase" — a real engineering
  answer to a real scoping question.

---

## What the candidate did *not* do

- Did not ask about **multi-currency**.
- Did not ask about **enterprise contracts** (annual commits,
  ramp deals).
- Did not ask about **usage-based pricing** (if the product
  meters by usage, the model is very different — see Lesson 09
  for a separate treatment).

---

## Try it

Re-do this exercise on a different subscription product. Try
Headspace (consumer subscription with annual plans), AWS (usage-
based with commits), or Slack (per-seat workspace subscription).
Time yourself: 5 minutes for latency discovery, 3 minutes for
the doc, 1 minute for the grain commitment. Total: under 10
minutes.

Notice how the **latency tier** changes for usage-based products
(it can shift from daily batch to hourly or near-real-time) and
how the **grain** changes too (no longer customer-month — it's
customer-meter-month or even customer-API-call).

---

## In the interview, you would say...

> "I need to anchor the design on the **latency tier** the
> business actually requires — daily batch, hourly,
> near-real-time, or real-time — not on the capability of the
> source CDC. The tier drives the partitioning, the SCD
> strategy, and the fact-table pattern. I'm going to name the
> tier, name the SLA in minutes, and explicitly distinguish
> capability from requirement."

---

*Author: Prem Vishnoi <pvishnoi@avilx.com>*
