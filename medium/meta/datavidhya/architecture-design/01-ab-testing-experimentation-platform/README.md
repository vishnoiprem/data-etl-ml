# A/B Testing & Experimentation Data Platform

**Difficulty:** HARD
**Companies:** Netflix, Spotify, Uber, Meta
**Tags:** system-design, experimentation, statistics, big-data, streaming, batch

---

## 1. Problem Statement

> Design the data platform that powers experimentation at scale: 5,000+ concurrent
> experiments across 500M+ users, 10B+ metric events/day. Must support deterministic
> user-to-variant assignment, metric computation, statistical analysis, guardrail
> monitoring, and protect against peeking / early stopping errors.

### Hard Parts
- Computing metrics across **billions of events** with low latency
- Handling **interaction effects** between simultaneous experiments
- Preventing **peeking bias** (PMs looking at dashboards daily)
- **Auto-stopping** experiments that regress guardrail metrics (latency, crash rate)
- Maintaining **statistical correctness** — false positives ship bad features

### Scale & Constraints

| Dimension | Value |
|---|---|
| Users | 500M+ |
| Concurrent experiments | 5,000+ |
| Metric events / day | 10B+ |
| Result freshness | Daily (hourly for guardrails) |
| Experiment duration | 1–4 weeks (some long-running holdouts for months) |
| Correctness | Statistical validity is non-negotiable |

---

## 2. The 5-Step Approach

### Step 1 — Clarify Requirements
- **Who are the consumers?** PMs, data scientists, ML engineers, automated control loops
- **What decisions does it drive?** Ship / kill / iterate, ramp-up traffic, holdout allocation
- **What are the metrics?** North-star (engagement), feature metrics, guardrails (latency/crash/revenue)
- **What's the lifecycle?** Design → Allocate → Run → Monitor → Conclude → Archive

### Step 2 — High-Level Architecture (Components)

```
┌─────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌────────────────┐
│ Experiment  │───▶│  Assignment      │───▶│  Event Ingestion │───▶│  Metric        │
│ Config      │    │  Service         │    │  (Kafka → Iceberg)│    │  Computation   │
│ Service     │    │  (deterministic) │    │                  │    │  (Spark/Airflow)│
└─────────────┘    └──────────────────┘    └──────────────────┘    └────────────────┘
                                                                            │
                                              ┌──────────────────┐          ▼
                                              │  Guardrail       │   ┌────────────────┐
                                              │  Monitor         │   │  Statistical   │
                                              │  (hourly)        │   │  Engine        │
                                              └──────────────────┘   │  (Sequential   │
                                                                      │   Testing)     │
                                                                      └────────────────┘
```

### Step 3 — Core Data Model

See `sql/schema.sql` for the full DDL. Key entities:

- **experiments** — id, name, owner, status, start_ts, end_ts, traffic_allocation, variants[]
- **experiment_assignments** — (user_id, experiment_id, variant_id, assigned_ts)
- **events** — (user_id, event_ts, event_name, properties JSON, experiment_tags[])
- **metric_definitions** — (metric_id, name, sql/formula, type, owner)
- **user_metric_daily** — (user_id, experiment_id, variant_id, metric_id, date, value)
- **experiment_results** — (experiment_id, metric_id, variant_id, point_est, ci_low, ci_high, p_value, sample_size)

### Step 4 — Scale the Design

| Concern | Approach |
|---|---|
| 10B events/day | Kafka → Iceberg on S3, partitioned by (date, experiment_id) |
| Assignment lookup | Precomputed table; deterministic hash for O(1) check |
| Metric aggregation | Spark batch hourly; Flink streaming for guardrails |
| Peeking bias | Sequential testing (mSPRT / Always-Valid CIs) |
| Multiple experiments per user | Layered/orthogonal bucketing; mutex groups |
| Long-running holdouts | Persistent global holdout population (5–10%) |

### Step 5 — Address Non-Functional

- **Correctness:** Deterministic hashing (MD5/SHA1), reproducibility audits
- **Latency:** Assignment < 5ms p99; metric refresh hourly; guardrail hourly, alerted < 15 min
- **Reliability:** Idempotent pipelines, replayable event streams
- **Observability:** Data lineage (DataHub), assignment-coverage dashboards
- **Security/PII:** Hashed user IDs, fine-grained ACLs on raw events

---

## 3. The Critical Design Decisions

### 3.1 Deterministic Assignment
Use `hash(user_id + experiment_id) % 10000` to bucket users. A user gets the same
variant for the same experiment across all sessions, devices, and time. This is
**the** foundation — if assignment is non-deterministic, all downstream stats are garbage.

### 3.2 Handling 5,000 Simultaneous Experiments
**Orthogonal / layered bucketing:**
- Layer 0: global holdout (5% of users)
- Layer 1: high-priority experiments (rank, feed)
- Layer 2: standard product experiments
- Layer 3: marketing / lifecycle
- Each layer uses independent hash salts; users can be in one experiment per layer.
- "Mutually exclusive groups" prevent interaction contamination for related tests.

### 3.3 Anti-Peeking: Sequential Testing
Don't use fixed-horizon p-values when results are checked daily. Use:
- **mSPRT** (mixture Sequential Probability Ratio Test) — always-valid p-values
- **Always-Valid Confidence Intervals** (Howard et al.) — coverage holds at any stopping time
- Optionally **alpha-spending functions** (OBrien-Fleming) if fixed max duration

### 3.4 Guardrail Auto-Stop
Separate **streaming pipeline** checks hourly:
- Crash rate per variant vs. control
- p99 latency per variant
- Revenue / DAU drops
If guardrail metric crosses threshold → webhook → experiment service → auto-pause.

### 3.5 Variance Reduction (CUPED)
Pre-experiment covariate adjustment:
`metric_adj = metric - θ * (pre_experiment_metric - pre_experiment_mean)`
Reduces variance 20–50%, lets you detect smaller effects with the same sample size.

---

## 4. Folder Layout

```
01-ab-testing-experimentation-platform/
├── README.md                  # this file
├── docs/
│   └── design-decisions.md    # deeper rationale on each choice
├── diagrams/
│   └── architecture.mermaid   # editable architecture diagram
├── sql/
│   ├── schema.sql             # tables: experiments, assignments, events, metrics
│   ├── assignment_query.sql   # deterministic assignment query
│   ├── metric_aggregation.sql # per-user-per-experiment metric rollup
│   └── results_query.sql      # statistical results query
├── python/
│   ├── assignment.py          # hash-based deterministic assignment
│   ├── stats_engine.py        # t-test, sequential, CUPED
│   ├── guardrail_monitor.py   # streaming guardrail checks
│   └── peeking_protection.py  # mSPRT / always-valid CI
├── pyspark/
│   ├── ingest_events.py       # Kafka → Iceberg landing
│   ├── compute_metrics.py     # aggregate events → user_metric_daily
│   ├── interaction_detector.py# find experiment conflicts
│   └── experiment_results.py  # final stats pipeline
├── spark/
│   └── README.md              # when to use Spark vs PySpark
├── config/
│   ├── experiment_template.json
│   └── metric_definitions.json
├── sample_data/
│   ├── users.csv
│   ├── experiments.json
│   └── events.jsonl
└── tests/
    ├── test_assignment.py     # determinism + uniformity tests
    ├── test_stats.py          # type-I error, CI coverage
    └── test_guardrails.py     # trigger thresholds
```

---

## 5. How to Run End-to-End

```bash
# 1. Generate sample data
python python/assignment.py --generate-sample

# 2. Ingest events (mock)
python pyspark/ingest_events.py --input sample_data/events.jsonl

# 3. Compute daily metrics
python pyspark/compute_metrics.py --date 2026-09-26

# 4. Run statistical analysis
python python/stats_engine.py --experiment exp_001

# 5. Check guardrails
python python/guardrail_monitor.py --experiment exp_001
```

See `tests/` for unit-level validation.

---

## 6. Interview Talking Points

When presenting this design, hit these beats in order:

1. **Determinism first** — assignment is the foundation
2. **Orthogonal bucketing** — how you scale to 5K experiments
3. **Sequential testing** — why you ban p-values for daily checks
4. **CUPED** — variance reduction to ship experiments faster
5. **Guardrails + auto-stop** — protect users from bad rollouts
6. **Data quality** — SRM (sample ratio mismatch) checks daily
7. **Long-running holdouts** — incremental learning + global control

**Bonus:** Mention the **"peeking penalty"** in plain English — "if you check 20 times,
your nominal 5% false-positive rate becomes ~30% without correction."
