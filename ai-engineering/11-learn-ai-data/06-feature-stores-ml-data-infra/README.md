# Module 6 — Feature Stores & ML Data Infrastructure

> 7 lessons · Online vs offline serving, training-data versioning, ML observability, LLMOps

---

## Lesson Index

| # | Lesson | Type | Notes |
|---|--------|------|-------|
| 1 | [Feature Store Fundamentals](./01-feature-store-fundamentals.md) | Article | [Open](./01-feature-store-fundamentals.md) |
| 2 | [Feature Store Comparison](./02-feature-store-comparison.md) | Article | [Open](./02-feature-store-comparison.md) |
| 3 | [Training Data Versioning](./03-training-data-versioning.md) | Article | [Open](./03-training-data-versioning.md) |
| 4 | [Online vs Offline Serving](./04-online-vs-offline-serving.md) | Article | [Open](./04-online-vs-offline-serving.md) |
| 5 | [ML Observability](./05-ml-observability.md) | Article | [Open](./05-ml-observability.md) |
| 6 | [LLMOps](./06-llmops.md) | Article | [Open](./06-llmops.md) |
| 7 | [Quiz: Feature Stores & ML Data Infra](./07-quiz-feature-stores.md) | Quiz | [Open](./07-quiz-feature-stores.md) |

---

## Module Outcomes

By the end of Module 6 you can:

1. **Explain** what a feature store is, who owns it, and why training/serving skew matters.
2. **Pick** the right feature-store architecture for your scale, freshness, and team.
3. **Version** training datasets and tie them to model versions, code, and configs.
4. **Serve** features online (low-latency) and offline (high-throughput) without skew.
5. **Detect** data drift, concept drift, and silent feature regressions.
6. **Operate** LLM-backed applications with eval, monitoring, and feedback loops.
7. **Reason** about point-in-time correctness for backfills and retroactive labelling.

---

## The training/serving skew problem

```
   ┌──────────────────────────────────────────────────────────────┐
   │  TRAINING-SERVING SKEW                                       │
   │                                                              │
   │   Training (offline)              Serving (online)           │
   │   ─────────────────              ────────────────           │
   │   100M rows batch                1 row, <50ms               │
   │   Computed nightly               Computed on read            │
   │   pandas/Spark aggregate         Redis/Dynamo lookup         │
   │   "last 30 days" = static       "last 30 days" = rolling    │
   │                                                              │
   │   If these don't agree, your model silently degrades.       │
   │   The feature store's job is to make them agree.             │
   └──────────────────────────────────────────────────────────────┘
```
