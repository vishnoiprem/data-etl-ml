# 31 — Mock Interview: Design a Feature Store for an ML Platform

> **Lesson 31 of 31 — Mock Interviews**

A full 30-minute mock interview with a candidate designing a feature
store (Feast / Tecton-style) for an ML platform. The candidate is a
Senior ML Platform Engineer (L6 level). The scenario covers three of
the hardest problems in applied ML: training/serving skew,
point-in-time correctness, and feature freshness.

---

## Setup

**Company:** Mid-sized marketplace / fintech (hypothetical).
**Role:** Senior ML Platform Engineer.
**Level:** L6.
**Format:** 30-minute system design round, on-site whiteboard.
**Question:** *"Design a feature store for our ML platform. We have
200 data scientists, 5000 features, 10M training examples per day,
and sub-100ms online serving latency. The platform needs to support
both batch training (PyTorch + Spark) and real-time inference
(fraud, recommendation, ranking)."*

---

## Transcript (30 minutes)

### 0:00 — Opening framing

> **Candidate:** Before I draw, let me make sure I have the
> requirements right. You said 200 data scientists and 5000
> features — is that 5000 total, or 5000 per use case? And "10M
> training examples per day" — is that one big daily training job,
> or many smaller retraining jobs throughout the day? And the
> online serving: 100M predictions per second is very different from
> 10K predictions per second. What's the actual peak QPS for online
> inference?

> **Interviewer:** 5000 features total across the company, owned
> by maybe 20 different teams. 10M training examples per day, but
> the actual training jobs vary — some teams retrain every hour,
> some every week. Online inference peak: 50K predictions per
> second. Sub-100ms is the latency target *for feature lookup*,
> not for the model itself.

> **Candidate:** Got it. So the three drivers are:
>
> 1. **Many teams sharing features.** Without a feature store,
>    each team rebuilds the same features. Cross-team feature
>    reuse is the primary value driver.
> 2. **Training / serving parity.** A feature that has different
>    values at training time vs inference time is the #1 silent
>    killer of model quality.
> 3. **Online latency.** 50K QPS at sub-100ms means the feature
>    lookup has to be a single key-value call, no joins.
>
> These three drivers shape the architecture.

### 3:00 — High-level architecture

> **Candidate:** Seven boxes. **[DRAWING 1]**

```
┌────────────┐
│ Source     │     ┌──────────────┐    ┌─────────────────┐
│ data       │────►│ Batch        │───►│ Offline store   │
│ (Kafka,    │     │ pipeline     │    │ (Iceberg /      │
│  Postgres, │     │ (Spark /     │    │  Parquet on S3) │
│  S3)       │     │  Beam)       │    │                 │
└────────────┘     └──────────────┘    └────┬────────────┘
                                            │
                                            │ (materialized
                                            │  by Spark)
                                            ▼
┌────────────┐                       ┌─────────────────┐
│ Online    │ ◄──── async-sync ────►│ Feature         │
│ inference │                       │ registry        │
│ (serving) │                       │ (Feast /        │
└────┬───────┘                       │  Tecton)        │
     │                               └────┬────────────┘
     │ single-row                           │
     │ getFeatures()                         │ feature defs
     ▼                                       │
┌────────────┐                               │
│ Online     │ ◄──── population ─────────────┘
│ store      │
│ (DynamoDB /│
│  Redis /   │
│  Bigtable) │
└────────────┘
```

> **Candidate:** Five components. The source data goes through
> a batch pipeline (Spark or Beam) and lands in an offline store
> (Iceberg on S3). The feature registry (Feast / Tecton) holds
> the feature definitions — schema, owner, freshness SLA, online
> vs offline flag. A separate sync job materializes features
> into the online store (Dynamo / Redis / Bigtable). The online
> inference path does a single-row `getFeatures(entity_id)`
> against the online store, sub-100ms.
>
> The hot path is the **sync between offline and online**.
> Getting training / serving parity right is the deep dive.

### 6:00 — Back-of-envelope estimation

> **Candidate:** 10M training examples per day. If each example
> has 100 features at ~8 bytes each (after compression), that's
> 10M × 100 × 8 = 8 GB / day of training feature data, 3 TB / year
> of growth. At 5000 features, stored with the same 8 bytes
> average, that's 5000 × 8 × 200M users = 8 GB of feature
> values for the online store. So:
>
> - Offline: 3 TB / year on S3 = $70 / month
> - Online: 8 GB of hot data on DynamoDB ≈ $2K / month
> - Compute (Spark, hourly sync): $3K / month
> - Feast / Tecton: managed or self-hosted, $0-10K / month
>
> Total: ~$10K-15K / month for the platform itself. The bigger
> cost is the wasted data-science effort when teams can't reuse
> features — that's the value the feature store captures.

### 8:00 — Deep dive #1: training / serving skew

> **Interviewer:** Walk me through training / serving skew. Why is
> it the #1 silent killer?

> **Candidate:** Training / serving skew is when the feature value
> the model saw at training time is different from the feature
> value the model sees at inference time. The model's prediction
> was calibrated for the training values; the inference values
> drift, and the model degrades. **[DRAWING 2]**

```
Training time (batch):
  user_features(user_id=42)
    - total_purchases_30d = 12
    - avg_basket_size    = $24.50
    - last_login_days    = 1
  Model was trained on these exact values.

Inference time (online):
  user_features(user_id=42)
    - total_purchases_30d = 12   ← should be same!
    - avg_basket_size    = $24.50
    - last_login_days    = 14   ← 13 days later, drifted
  The drift is the silent killer.
```

> **Candidate:** Two ways the feature values can differ. **First,
> the computation differs.** At training time you wrote a Spark
> job that computes "purchases in last 30 days." At inference
> time you wrote a Python function that does the same. The two
> implementations drift: they treat `>` vs `>=`, or they handle
> timezones differently, or the offline one uses a snapshot table
> while the online one queries the OLTP directly. The value the
> model saw is from one implementation; the value the model sees
> now is from the other.
>
> **Second, the freshness differs.** At training, you used the
> feature value *as of the event timestamp*. At inference, you use
> the feature value *as of now*. For a feature that updates
> hourly, the inference value is the latest one — which is
> *newer* than what was available at training. The further you go
> after training, the more the features drift.
>
> The fix is the feature store. There is exactly one
> implementation of each feature. Both training and inference use
> it. Online values are a *snapshot* of the offline values at a
> specific timestamp; inference never recomputes the feature.
> Single source of truth for the computation, single source of
> truth for the value.

### 13:00 — Deep dive #2: point-in-time correctness

> **Interviewer:** That snapshot story — explain point-in-time
> correctness. Why is it the #1 hard problem in feature stores?

> **Candidate:** Point-in-time correctness is what happens when
> your training labels have a timestamp and the features have to
> match that timestamp. **[DRAWING 3]**

```
Training rows:

  label_ts           label   user_id
  ─────────────────  ──────  ───────
  2026-09-01 14:23   fraud   user_42
  2026-09-03 09:11   legit   user_77
  2026-09-07 18:45   fraud   user_42

For each training row, the feature store must return
"the feature values for that user AS OF the label_ts".

  user_42 as of 2026-09-01 14:23: feature values at that moment
  user_42 as of 2026-09-03 09:11: different feature values
    (they did other things in between)
  user_42 as of 2026-09-07 18:45: yet different values.
```

> **Candidate:** The bug — and it's the most common feature-store
> bug — is when the training pipeline joins the *latest* feature
> values to the labels. The label says "user_42 is fraud on Sept 1"
> but the feature join used the September 10 values. The model
> learns that fraud is correlated with the September 10 values of
> user_42, even though the fraud occurred on September 1. This is
> **label leakage in time**, and it makes the model look great in
> training but fail in production.
>
> The fix is a **point-in-time join**. The offline store keeps
> every historical value of every feature (it's an event-sourced
> store, not a "latest value" store). The training job does:
>
> ```sql
> SELECT
>   l.label_ts, l.label, l.user_id,
>   f.total_purchases_30d,
>   f.avg_basket_size,
>   ...
> FROM labels l
> ASOF JOIN features f
>   ON l.user_id = f.user_id
>   AND f.feature_ts <= l.label_ts
> QUALIFY f.feature_ts = MAX(f.feature_ts) ...
> ```
>
> The `ASOF JOIN` is the primitive. Iceberg supports it natively
> via hidden partitioning on `feature_ts`. BigQuery supports it
> via `AS OF` syntax. The point is: never join labels to the latest
> feature values; always join to the value at the right moment in
> the past.

### 19:00 — Deep dive #3: feature versioning and freshness

> **Interviewer:** When a feature definition changes — say the
> data scientist changes the SQL for `avg_basket_size` — what
> happens?

> **Candidate:** Three things need to happen. **[DRAWING 4]**
>
> **First, the feature is versioned.** Every change to the SQL
> creates a new version. v1 of `avg_basket_size` is preserved
> forever — old models keep using v1, new models use v2.
>
> **Second, the backfill is explicit.** The change to v2 doesn't
> silently re-derive historical values. It writes new values for
> *new* events. A separate backfill job (often Spark, often
> idempotent on `(user_id, feature_ts)`) re-derives historical
> values if the data scientist wants them.
>
> **Third, the model is re-trained.** Any model that uses v2 of
> the feature needs to be retrained. The feature registry tracks
> which model versions use which feature versions — that's the
> lineage graph.
>
> Freshness is the *operational* counterpart. Each feature has
> an SLA. `last_login_days` updates every minute; `total_30d`
> updates hourly. The sync job from offline to online has a
> freshness budget. We alert if `total_30d` is more than 90
> minutes stale; that's the platform's reliability story.

### 24:00 — Failure modes

> **Interviewer:** Five failure modes, please.

> **Candidate:** Five. **[DRAWING 5]**
>
> One, **online store is stale.** The Spark sync job is delayed,
> features are an hour old. Inference uses stale values; model
> degrades. Mitigation: freshness SLA with alert; graceful
> degradation (use last-known value, do not 500).
>
> Two, **offline store is missing history.** Someone ran a
> compaction that dropped old feature values. Now point-in-time
> joins return NULL for old labels. Mitigation: separate hot /
> cold storage; archival to S3 Glacier; never drop a feature
> value from the offline store without a retention policy
> review.
>
> Three, **the online store is down.** DynamoDB has a regional
> outage. Mitigation: read-through cache (Redis) with
> 30-second TTL; cascading failure if both are down.
>
> Four, **a feature breaks.** The SQL has a bug; values become
> NULL or wildly out of range. Mitigation: feature-level schema
> + range checks; per-feature alerts on null rate and mean shift;
> roll back the feature version.
>
> Five, **training / serving skew creeps back in.** A data
> scientist computes the feature in a notebook for ad-hoc
> training, bypassing the feature store. Mitigation: governance
> — the registry only models that use registered features get
> promoted to production.

### 28:00 — Wrap-up

> **Candidate:** The architecture is: source → Spark → offline
> store (Iceberg on S3) → async sync to online store (Dynamo or
> Bigtable) → inference. The three hard problems are training /
> serving skew (single source of truth for the computation),
> point-in-time correctness (the offline store is event-sourced,
> not "latest value"), and feature versioning (every change is
> versioned, retraining is explicit). The cost driver is the
> online store at 50K QPS; the latency driver is the lookup
> path — keep it to a single KV call.

---

## Post-interview analysis

**What was good:**

- Three clarifying questions before drawing. Repeated back the
  three drivers (reuse, parity, latency) in one sentence.
- Training / serving skew is named explicitly with both flavors
  (computation drift and freshness drift).
- Point-in-time correctness is described with a concrete example
  and the `ASOF JOIN` primitive.
- Feature versioning covers backfill, lineage, and freshness SLA.
- Five failure modes named unprompted.
- Cost estimate at the right order of magnitude ($10K-15K/month).

**What was missing:**

- Could have named the **feature monitoring** layer more
  concretely — drift detection on the *input features* (not just
  the output predictions).
- The **multi-region** story is missing — 50K QPS online often
  means serving is in multiple regions; how does the online store
  replicate?
- The **access control** story is missing — features often
  contain PII (email, SSN), and the registry needs to enforce who
  can read which features.
- **Lineage at the model level** — for a regulated model (credit,
  insurance), the regulator wants to know which features, which
  versions, which data, on which day. This is governance-grade
  lineage, not just dbt-style lineage.

**Score against the rubric:**

| Bucket | Score |
|---|---|
| Problem framing (15%) | 5/5 — three clarifying questions, three drivers named |
| Estimation (10%) | 4/5 — math is right; could derive QPS / storage from the 50K QPS |
| High-level architecture (20%) | 5/5 — seven boxes, all the right pieces |
| Hot-path deep dive (35%) | 5/5 — skew, point-in-time, versioning |
| Tradeoff articulation (20%) | 4/5 — governance + multi-region missing |

**Overall: senior+ answer.** Would pass at L6 for an ML platform
role.

---

## Try it

Re-do this mock interview out loud. The heart of the answer is
the point-in-time join story. If you can describe an `ASOF JOIN`
in SQL without hesitation, you have the framework.

---

*Author: Prem Vishnoi <pvishnoi@avilx.com>*
