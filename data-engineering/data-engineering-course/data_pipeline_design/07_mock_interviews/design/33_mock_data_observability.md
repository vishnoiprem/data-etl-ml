# 33 — Mock Interview: Design a Data Observability / Monitoring Platform

> **Lesson 33 of 33 — Mock Interviews**

A full 30-minute mock interview with a candidate designing a data
observability platform (Monte Carlo–style or Great Expectations–
style). The candidate is a Staff Data Engineer (L6 level). The
scenario covers the five detection layers, alert fatigue, and the
operational on-call burden — the parts of the question that get
talked about less but dominate the day-to-day.

---

## Setup

**Company:** Mid-to-large enterprise with a mature data
infrastructure (hypothetical).
**Role:** Staff Data Engineer.
**Level:** L6.
**Format:** 30-minute system design round, on-site whiteboard.
**Question:** *"Design a platform that detects bad data before it
reaches downstream consumers. We have 10k tables, 500 pipelines,
1000 daily users (data engineers + analysts + data scientists).
The platform should integrate with our existing warehouse, our
Spark + Airflow stack, and our BI tools."*

---

## Transcript (30 minutes)

### 0:00 — Opening framing

> **Candidate:** Data observability has three flavors and they're
> often conflated. Let me make sure I understand the goal before
> I draw.
>
> First — is the goal *detect* (raise an alert when something is
> wrong), *prevent* (block a bad write from landing), or *recover*
> (auto-rollback a bad pipeline)? Each is a different architecture.
>
> Second — who is the user of the platform? "1000 daily users" —
> are they data engineers writing checks, analysts *querying* the
> platform for trust signals, or both? The UI is different for
> each audience.
>
> Third — what's the *cost of a miss*? If a bad row hits a
> downstream dashboard, is the consequence "a report is wrong" or
> "a regulator gets a wrong number"? The depth of detection is
> different.
>
> Fourth — "before it reaches downstream" — does that mean before
> it lands in the warehouse, or before the downstream consumer
> *reads* it? Pre-landing vs post-landing is a fundamental
> architecture choice.

> **Interviewer:** Detect is primary, prevent is a bonus, recover
> is out of scope. Users are mixed: 200 engineers writing checks,
> 800 analysts + scientists *consuming* trust signals (a green /
> red dot on a dashboard). Miss cost varies: regulatory reporting
> cannot be wrong; experimentation dashboards can tolerate some
> noise. "Before it reaches downstream" means before the
> downstream consumer reads it — pre-read monitoring.

> **Candidate:** So we're building a **post-write, pre-read**
> monitor. Every write lands; a check fires; the result is
> attached to the table as a trust signal; the consumers see it.
> Detect is the core; prevent is a side effect (we *could*
> block, but the prompt is detection).

### 3:00 — High-level architecture

> **Candidate:** Five boxes. **[DRAWING 1]**

```
┌─────────────────────────────────────────────────────────────┐
│                   Detection engine                          │
│                                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────┐ │
│  │ Row      │ │ Null     │ │ Distri-  │ │ Fresh-   │ │Sch │ │
│  │ count    │ │ rate     │ │ bution   │ │ ness     │ │ ema│ │
│  │ check    │ │ check    │ │ drift    │ │ check    │ │    │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └──┬─┘ │
│       │            │            │            │           │   │
└───────┼────────────┼────────────┼────────────┼───────────┼───┘
        ▼            ▼            ▼            ▼           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Trust signal store                         │
│   (per-table, per-column, per-time-bucket status)          │
└─────────────────────────────────┬───────────────────────────┘
                                  │
                                  ▼
                       ┌─────────────────┐
                       │ Alert + UI      │
                       │ (Slack, Pager,  │
                       │  web dashboard) │
                       └─────────────────┘
```

> **Candidate:** Four layers.
>
> 1. **Detection engine.** Five check types: row count, null
>    rate, distribution drift, freshness, schema. Each runs
>    against the warehouse metadata + a sampled read of the
>    data.
> 2. **Trust signal store.** A low-latency KV store (DynamoDB /
>    Postgres) of per-table + per-column status: green / yellow
>    / red, plus the running metric values. Updated on every
>    check run.
> 3. **Alerting.** Fires to Slack and PagerDuty based on
>    severity and ownership.
> 4. **UI.** Web dashboard for engineers (configure checks)
>    and consumers (see green / red on every table they touch).

### 6:00 — Back-of-envelope estimation

> **Candidate:** 10k tables. Average 5 checks per table = 50k
> active checks. Each check runs ~ every hour = ~1.2M check
> runs / day.
>
> Each check is small (a `SELECT count(*)` or a sample), maybe
> 100ms on a Snowflake X-Small. 1.2M × 0.1s = 120K Snowflake-
> seconds / day = ~3.5 hours of compute. Cost ≈ $20-50 / day
> on Snowflake, $600-1500 / month.
>
> Storage for trust signals: 10k tables × 30 columns × 30 days
> of hourly history × 1 KB = 9 GB. Negligible.
>
> Total platform cost: ~$5K-15K / month, mostly Snowflake.
> Reasonable for a 1000-user platform. The bigger costs are the
> *soft* ones — the on-call burden and the alert fatigue.

### 8:00 — The five detection layers (the deep dive)

> **Interviewer:** Walk me through the five check types. What's
> each one catching?

> **Candidate:** Each one catches a different class of bug. **[DRAWING 2]**

```
Layer 1: row count
  threshold: |today - baseline_7d_avg| / baseline > 0.20
  catches: pipeline didn't run, source is empty, double-write

Layer 2: null rate
  threshold: null_rate(col) > 0.05 (or +3σ from baseline)
  catches: upstream schema change, code path that returns NULL

Layer 3: distribution drift
  threshold: KS-test p-value < 0.01 against baseline
            OR PSI > 0.10 on binned numeric / categorical
  catches: data quality change, label shift, population change

Layer 4: freshness
  threshold: max(loaded_at) < now() - sla
  catches: pipeline failed silently, upstream didn't deliver,
           partition missing

Layer 5: schema
  threshold: |current_schema - registered_schema| > 0
  catches: dropped column, type change, new column
```

> **Candidate:** Each layer has a different test.
>
> **Row count** catches the binary "did the pipeline run at all?"
> — the silent failure where the job succeeds but writes zero
> rows. Threshold is dynamic (a 7-day rolling baseline), not a
> fixed number, because volumes have seasonality.
>
> **Null rate** catches when an upstream column becomes NULL
> unexpectedly. The threshold is *per column*, not global. A
> column called `email` has a baseline null rate of 5%; a
> column called `order_id` should be 0%. Each gets its own
> threshold.
>
> **Distribution drift** is the deep one. A column's mean shifts
> 5% — is that a bug or a real change? We use two statistical
> tests: the **Kolmogorov-Smirnov test** for numeric features
> (sensitive to any distribution shift) and **Population Stability
> Index (PSI)** for categorical features (binned counts). PSI
> > 0.10 is the industry-standard alert; > 0.25 is severe.
>
> **Freshness** checks the `loaded_at` column. If the latest
> row is older than the table's SLA, the table is stale. The
> SLA is per-table: a stream table is < 5 minutes; a daily
> batch is < 26 hours.
>
> **Schema** compares the registered schema (from the table's
> registration in the catalog) against the actual schema.
> Drift = drift alert.

### 14:00 — Deep dive #3: alert fatigue — the on-call burden

> **Interviewer:** With 50k checks, how do you keep alerts
> actionable? How do you prevent the on-call from ignoring
> PagerDuty?

> **Candidate:** This is the *real* hard problem. **[DRAWING 3]**

```
                    alert fires
                         │
                         ▼
                ┌───────────────────┐
                │ severity-router   │
                │                   │
                │ sev=critical      │ ──► PagerDuty (page)
                │ sev=high          │ ──► Slack #data-alerts
                │ sev=low           │ ──► Slack #data-warnings
                │                   │     (digest at EOD)
                │ sev=info          │ ──► UI only, no alert
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ group-by owner    │
                │                   │
                │ owner on-call?    │ ──► yes → page them
                │                   │ ──► no  → owner team
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ dedup + suppress  │
                │                   │
                │ same alert in     │ ──► 1 hour window:
                │ last hour?        │     update existing
                │                   │     don't re-page
                └───────────────────┘
```

> **Candidate:** Six things matter.
>
> **One, severity tiers.** Every alert has a severity.
> Critical = page on-call (must be fixed in 1 hour, blocks a
> downstream SLA). High = Slack channel, no page (must be fixed
> in 24 hours). Low = digest at end of day. Info = UI only.
> Most checks default to Low; only the regulatory-reporting
> tables default to Critical.
>
> **Two, ownership.** Every check has an owner team. The
> ownership graph is in a `meta.yaml` next to the table
> definition. The alert goes to the owner team's channel, not
> to a global "data-alerts" channel where it gets scrolled
> past.
>
> **Three, dedup.** If the same alert fires 50 times in an hour,
> the on-call gets *one* page + 49 updates. Don't page 50
> times.
>
> **Four, suppression windows.** Maintenance windows, known
> backfills, and on-call rotations suppress alerts. The
> suppression is owned by the alerting system; the user
> maintains it.
>
> **Five, auto-resolve.** If the next check run is clean, the
> alert auto-resolves. The on-call doesn't have to close it
> manually.
>
> **Six, weekly review.** A weekly digest of the top 10
> most-noisy checks, the top 10 most-ignored alerts, and the
> MTTR per severity tier. The platform team uses this to tune
> thresholds and prune dead checks. The goal: MTTR < 1 hour
> for Critical; < 24 hours for High; < 1 week for Low.

### 22:00 — Where checks run (the operational answer)

> **Interviewer:** Where do the checks physically run? Inside the
> warehouse, or in a separate service?

> **Candidate:** Two-prong answer. **[DRAWING 4]**

```
A. Lightweight metadata-only checks
   (row count, freshness, schema)
   → run against the catalog / INFORMATION_SCHEMA
   → no warehouse compute, near-zero cost

B. Sampling-based checks
   (null rate, distribution drift)
   → run inside the warehouse with SAMPLE 1%
     or TABLESAMPLE BERNOULLI (1)
   → 100x cheaper than full scans
   → pays $0.50-$5 per check per day per table
```

> **Candidate:** Most senior candidates get this wrong because
> they think checks run in their own engine. The right answer
> is **the warehouse is the engine**. Metadata checks are
> free; sampling checks pay only for the sample. We don't
> replicate the data; we read it where it lives. The cost
> stays inside the existing warehouse budget.

### 26:00 — Failure modes

> **Interviewer:** Five things that can go wrong.

> **Candidate:** Five. **[DRAWING 5]**
>
> One, **alert storm.** A pipeline failure takes out 100 tables
> in 10 minutes. 100 alerts fire at once. Mitigation: the
> dependency graph — only the leaf nodes that have no
> descendants fire; everything else is suppressed as
> "consequential." Root cause is one place.
>
> Two, **threshold drift.** A column's mean shifts slowly over
> 6 months; the threshold adapts and the alert never fires. The
> real bug gets masked. Mitigation: re-baseline quarterly, not
> continuously. The baseline is the *intent*, not the *current
> state*.
>
> Three, **false negative.** A bug introduces a subtle null
> pattern that the null-rate check misses because the rate is
> still below threshold. Mitigation: per-column uniqueness
> checks (caught at low rates) and per-column range checks
> (`age` should be 0-150; if `age < 0` it fails).
>
> Four, **the platform itself is down.** The check engine
> can't reach the warehouse. Mitigation: the platform runs as
> a *passive* signal — when it's down, the consumer UI shows
> "unknown" not "green." A red signal is more valuable than a
> missing one.
>
> Five, **on-call burnout.** The most important failure mode.
> Mitigation: weekly review, top-10 noisy checks, MTTR targets
> that are real (1 hour for Critical). The platform team's job
> is to *reduce* the alert volume, not raise it.

### 30:00 — Wrap-up

> **Candidate:** The architecture is: catalog → check engine
> (5 layer types) → trust signal store → alerts → UI. The five
> detection layers are row count, null rate, distribution drift,
> freshness, schema. The hard problem isn't the checks — it's
> alert fatigue. The senior answer is severity-tiered, ownership-
> routed, deduped, auto-resolving alerts with a weekly review.
> The cost driver is the sampling-based checks in the warehouse,
> which is why we sample 1% and don't scan the full table.

---

## Post-interview analysis

**What was good:**

- The pre-write vs post-write vs pre-read framing is the
  senior move most candidates miss.
- The five detection layers are named with what each catches
  and the test for each.
- Alert fatigue addressed at length — MTTR targets, dedup,
  auto-resolve, weekly review.
- Checks run inside the warehouse with sampling — this is
  the cost-savvy answer.
- Five failure modes named unprompted.
- Cost estimate in the right order of magnitude.

**What was missing:**

- **The dependency graph and root-cause analysis.** When 100
  tables fail, what alerts? The interview answer needs the
  graph; this was implicit in failure mode #1 but could have
  been a deep-dive topic.
- **Lineage to the *consumer*.** When a column is suspect,
  who is affected? Monte Carlo's killer feature is propagating
  the trust signal through the lineage to consumers, so the
  analyst sees "this report uses column X, which has a current
  red." That's the *consumer-facing* answer; this transcript
  leaned engineer-facing.
- **Auto-tuning thresholds.** Most observability platforms in
  2026 auto-tune; this answer had fixed thresholds plus
  quarterly re-baselining.
- **Data contracts** as the upstream prevention layer. Tests
  are detection; contracts are prevention. The "prevent"
  branch of the platform is upstream and worth a sentence.

**Score against the rubric:**

| Bucket | Score |
|---|---|
| Problem framing (15%) | 5/5 — three flavors named, pre-read framed |
| Estimation (10%) | 5/5 — math shown, ~$5K-15K/month |
| High-level architecture (20%) | 5/5 — five boxes, all the right pieces |
| Hot-path deep dive (35%) | 5/5 — five detection layers + alert fatigue |
| Tradeoff articulation (20%) | 4/5 — missed lineage-to-consumer, contracts |

**Overall: senior+ answer.** Would pass at L6 for a data
platform / observability role.

---

## Try it

Re-do this mock out loud. The heart is alert fatigue, not the
detection checks. Candidates who can describe severity tiers +
ownership routing + dedup + weekly review will sound senior even
if the rest is rough. Conversely, candidates who detail the
checks but never address alert fatigue lose points.

---

*Author: Prem Vishnoi <prem.vishnoi@example.com>*
