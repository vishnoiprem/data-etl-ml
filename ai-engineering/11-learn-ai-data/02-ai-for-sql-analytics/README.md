# Module 2 — AI for SQL & Analytics

> 7 lessons · The highest-immediate-value module
> AI-assisted SQL, text-to-SQL limits, query optimisation, profiling, NL analytics, AI data quality.

---

## Lesson Index

| # | Lesson | Type | Notes |
|---|--------|------|-------|
| 1 | [AI-Assisted SQL Writing](./01-ai-assisted-sql-writing.md) | Article | [Open](./01-ai-assisted-sql-writing.md) |
| 2 | [Text-to-SQL](./02-text-to-sql.md) | Article | [Open](./02-text-to-sql.md) |
| 3 | [AI Query Optimization](./03-ai-query-optimization.md) | Article | [Open](./03-ai-query-optimization.md) |
| 4 | [Data Exploration & Profiling](./04-data-exploration-profiling.md) | Article | [Open](./04-data-exploration-profiling.md) |
| 5 | [NL Analytics Interfaces](./05-nl-analytics-interfaces.md) | Article | [Open](./05-nl-analytics-interfaces.md) |
| 6 | [AI Data Quality](./06-ai-data-quality.md) | Article | [Open](./06-ai-data-quality.md) |
| 7 | [Quiz: AI for SQL & Analytics](./07-quiz-sql-analytics.md) | Quiz | [Open](./07-quiz-sql-analytics.md) |

---

## Module Outcomes

By the end of Module 2 you can:

1. **Author** SQL faster with AI as a copilot, with verification habits that catch the silent bugs.
2. **Reason** about text-to-SQL's real accuracy on messy warehouses — and the failure patterns that drive the gap.
3. **Optimise** query plans using AI as a reading assistant, not a replacement for EXPLAIN.
4. **Profile** a new dataset in minutes instead of hours using AI-driven exploration patterns.
5. **Build** a NL analytics interface that respects the semantic layer instead of bypassing it.
6. **Operate** an AI data-quality stack (drift, anomaly, freshness) layered on top of hand-written assertions.

---

## Why this module is the highest immediate value

SQL is where AI gives the **most measurable, most immediate** productivity gain. It's also where the silent failure modes are most dangerous. Module 2 is about **shipping the gain without shipping the bugs**.

```
   ┌──────────────────────────────────────────────────────────┐
   │  THE TEXT-TO-SQL ACCURACY GAP                             │
   │                                                          │
   │  Spider (clean, 5-20 tables)        ████████████████ 85-90│
   │  BIRD    (messier, realistic)       █████████    ~52      │
   │  Real warehouses (200+ tables,      ██            5-18%   │
   │   inconsistent naming, views)                           │
   │                                                          │
   │  Human expert on BIRD:                ████████████████ ~93│
   └──────────────────────────────────────────────────────────┘
   The gap is not the model. It's the schema + semantic layer.
```
