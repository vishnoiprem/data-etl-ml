# Lesson 5 — Fraud Detection

> **Type:** Article · Module 8 · AI DE System Design
> Real-time fraud with sub-second features, model serving, and a delayed-label feedback loop.

---

## The problem

> Design a real-time fraud detection system for 100M transactions / day at a payment processor. Decision latency p99 < 100ms. False positive rate < 0.5%. False negative rate < 0.1%. Compliance: every decision logged, every override auditable. Must adapt to new fraud patterns within hours, not weeks.

---

## Step 1 — CLARIFY

```
   scale:        100M txns/day = ~1.2k QPS average, ~5k QPS peak
   latency:      p99 < 100ms (decision required synchronously)
   precision:    FP < 0.5% (don't block legit customers)
   recall:       FN < 0.1% (catch fraud, not perfect recall but close)
   freshness:    features: sub-second
                 rules: minutes (need to update quickly)
                 models: hourly retrain
   compliance:   every decision + every override + every input logged
   cost:         < $50k/mo for serving + features + models
   failure mode: false negative (fraud gets through)
                 false positive (legit customer blocked, lost trust)
                 adversarial (fraudster probes the system)
```

---

## Step 2 — SKETCH

```
   ┌──────────────────────────────────────────────────────────────┐
   │                                                              │
   │   TRANSACTION EVENT                                          │
   │        │                                                     │
   │        ▼                                                     │
   │   [STREAMING FEATURES (Flink)]                               │
   │     - velocity_5m: txns in last 5 min for this card         │
   │     - amount_zscore: how unusual this amount is             │
   │     - device_seen_before: is this device known?             │
   │     - geo_distance_from_last: distance from last txn         │
   │        │                                                     │
   │        ▼                                                     │
   │   [RULE LAYER]   ◄──── explicit patterns (block known bad) │
   │        │                                                     │
   │        ▼                                                     │
   │   [MODEL SCORE]   (XGBoost or DNN, p95 < 30ms)               │
   │        │                                                     │
   │        ▼                                                     │
   │   [DECISION ENGINE]                                         │
   │     score >= 0.95 → DECLINE                                  │
   │     score 0.5–0.95 → REVIEW (manual / step-up auth)          │
   │     score < 0.5 → APPROVE                                    │
   │        │                                                     │
   │        ▼                                                     │
   │   [RESPONSE]                                                │
   │        │                                                     │
   │        ├──► [DECISION LOG]  (every input, score, decision)  │
   │        │                                                     │
   │        └──► [LABEL DELAY PATH]                              │
   │                                                              │
   │   ──── delayed label ────                                  │
   │                                                              │
   │   [CHARGEBACK / DISPUTE EVENT]  (days/weeks later)         │
   │        │                                                     │
   │        ▼                                                     │
   │   [LABEL JOIN BACK TO ORIGINAL TXN]                         │
   │        │                                                     │
   │        ▼                                                     │
   │   [RETRAIN PIPELINE (hourly)]                                │
   │                                                              │
   │   ──── operations ────                                      │
   │                                                              │
   │   [DRIFT MONITORING]   [EVAL ON LABELED DATA]               │
   │   [ADVERSARIAL MONITORING]   [COST DASHBOARD]               │
   └──────────────────────────────────────────────────────────────┘
```

---

## Step 3 — DEEP-DIVE

### Box 1: Streaming features (sub-second)

The features that matter most for fraud are **velocity and recency**:

```
   STREAMING FEATURES (Flink)
   ──────────────────────────
   Per-card (or per-account, per-device, per-IP):
   - velocity_5m: count of txns in last 5 min
   - velocity_1h: count in last 1 hour
   - velocity_24h: count in last 24h
   - amount_sum_5m: total dollar in last 5 min
   - geo_distance_from_last_km: distance from last txn
   - device_new: boolean — has this device transacted before?
   - ip_new: boolean
   - bin_country_mismatch: country of card vs IP

   Latency budget: 5–15ms (Flink + Redis + state)
```

These features are **stateful** — they need access to recent history per entity. Flink with keyed state is the standard.

### Box 2: Two-layer decision (rules + model)

```
   ┌────────────────────────────────────────────┐
   │  WHY BOTH RULES AND MODELS?                 │
   │                                            │
   │  Rules:                                    │
   │   - Known bad BIN / device list            │
   │   - Hard limits (>$10k single txn)         │
   │   - Velocity caps                          │
   │   - Update in minutes (no retrain needed)  │
   │                                            │
   │  Model:                                    │
   │   - Catches novel patterns                 │
   │   - Uses rich feature set                  │
   │   - Probabilistic (threshold-driven)       │
   │                                            │
   │  Layered:                                  │
   │   - Rules first (fast, hard)               │
   │   - Model second (smart, probabilistic)    │
   │   - Manual review for medium-risk          │
   └────────────────────────────────────────────┘
```

Rules are **fast and explainable** ("blocked because velocity > 5 in 1 min"). Models are **smart and probabilistic**. Both are needed.

### Box 3: Delayed labels (the feedback loop)

Fraud labels arrive **days or weeks later** (chargebacks). The retrain pipeline joins them back to the original decision.

```
   TIMELINE
   ────────
   T0      txn happens, decision made, logged
   T0+1h   txn cleared or pending
   T0+7d   customer files chargeback (maybe)
   T0+30d  network chargeback received
   T0+45d  fraud confirmed

   ── join ──

   T0+45d  the original txn gets label = "fraud"
           the original decision is "approved"
           this is a FALSE NEGATIVE
           → goes into retrain set
```

```
   RETRAIN (hourly)
   ────────────────
   1. Pull all txns with confirmed labels (from last 45 days)
   2. Re-fetch features as-of T0 (point-in-time correct)
   3. Train on (features_at_T0, label_at_T+45d)
   4. Validate on hold-out
   5. Shadow the new model for 24h
   6. Promote if metrics hold
```

The **point-in-time join is critical**. You must use features as they were at decision time, not features as they are now.

### Box 4: Drift + adversarial monitoring

```
   DRIFT
   ─────
   - Feature distribution (PSI per feature)
     → upstream changed, or fraud pattern shifted
   - Score distribution (more or fewer high-risk scores)
     → model no longer discriminative
   - Decision distribution (more declines, more reviews)
     → model behaviour changed
   - Actual chargeback rate
     → real fraud rate changed

   ADVERSARIAL
   ───────────
   - Sudden velocity from new IP range
   - Testing pattern: many small txns then a big one
   - BIN rotation (cycling through cards)
   - Device fingerprinting failure rate spike

   ALERTS
   ──────
   - Per-feature PSI > 0.25 → page
   - Fraud rate (chargeback / txn) up > 50% week-over-week → page
   - Model score distribution shift → page
   - Rule hit rate up > 100% → page (might be attack)
```

---

## Step 4 — TRADEOFFS

| Choice | Alternative | Why | Revisit if |
|---|---|---|---|
| **Flink for streaming features** | Spark Streaming | Sub-second latency | ops complexity > benefit (5-min SLA ok) |
| **XGBoost model** | DNN | Easier to debug, faster to train, smaller infra | AUC plateaus < 0.95 |
| **Two-tier decision (rules + model)** | Model only | Explainability + fast updates for known patterns | false positives too high |
| **Hourly retrain** | Daily | New patterns emerge quickly | drift detected in hours |
| **Manual review queue** | Auto-decline all high-risk | Catches fraud without false-positive backlash | review queue becomes bottleneck |
| **Chargeback labels (delayed)** | Synthetic labels / proxy | Real ground truth | need to detect fraud faster than chargeback cycle |

---

## Step 5 — SUMMARY

**Decision:**
- Sub-second streaming features in Flink, stored in Redis
- Two-layer decision: rules + XGBoost model
- Decision latency p99 < 100ms (rules: 5ms, model: 30ms, fetch: 15ms, decision: 5ms)
- Every decision logged with full input + score + decision
- Delayed labels joined back, hourly retrain
- Drift + adversarial monitoring with alerts

**Cost (rough):**
- Flink cluster (streaming features): ~$15k/mo
- Redis cluster (feature store): ~$10k/mo
- Model serving (XGBoost on CPU, 5k QPS): ~$5k/mo
- Decision log storage (S3, 100M txns/day × 45d): ~$3k/mo
- Retrain compute (hourly): ~$5k/mo
- Monitoring / dashboards: ~$2k/mo
- **Total: ~$40k/mo**

**Revisit if:**
- Fraud rate up > 50% → emergency retrain, broader feature set
- False positive rate up → tighten rules, lower model threshold
- p99 > 100ms → profile (Redis? model? decision?), shrink features
- New fraud pattern detected within hours → streaming feature update
- Adversarial pattern → add rule, alert on pattern

---

## The "adversarial robustness" checklist

```
   ADVERSARIAL TESTS (run weekly)
   ──────────────────────────────
   - Synthetic attacks: 1k txns with known fraud patterns, expect catch rate > 95%
   - Edge cases: $0.01 txn, $1M txn, same card 1000 txns / sec
   - Time-shift: features computed 1ms later → still consistent?
   - Concept drift: fraud from 6 months ago → would model catch today?
```

---

## What Comes Next

> Lesson 6 — **Multi-Modal Platform** — text + image + audio at scale, with unified embeddings and a single RAG / search API across modalities.