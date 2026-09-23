# Meta Data Engineer Interview Prep — 10 Solutions Per Pattern

> Compiled from the DataVidhya Meta DE Interview Guide. Each folder contains **10 solutions** for one high-frequency pattern, with thinking framework, memory aid, and AI use cases.

## Folder Map (11 patterns × 10 problems = 110 solutions)

| # | Folder | Pattern | Maps to Round |
|---|--------|---------|---------------|
| 1 | `01_SQL_Window_Functions/` | ROW_NUMBER, RANK, NTILE, LAG/LEAD, PERCENT_RANK | SQL round |
| 2 | `02_Retention_Cohorts/` | D1 / D7 / D28 retention, weekly cohorts | SQL + Product |
| 3 | `03_Funnel_Analysis/` | Multi-step funnels, drop-off rates | SQL + Product |
| 4 | `04_DAU_MAU_Metrics/` | Stickiness, L7, L28, rolling metrics | SQL + Product |
| 5 | `05_AB_Test_Metrics/` | Lift, variance, t-stat, CUPED | SQL + Product |
| 6 | `06_Sessionization/` | Gap-and-island session detection | SQL + Python |
| 7 | `07_Star_Schema_Modeling/` | Fact / dim / grain for Meta products | Modeling |
| 8 | `08_SCD_Types/` | Type 1 / 2 / 3 historical tracking | Modeling |
| 9 | `09_Python_Idempotent_ETL/` | Dedup, backfill, retry-safe jobs | Python + Pipeline |
| 10 | `10_Product_Sense_Frameworks/` | Define → prioritize → SQL → interpret | Product Sense |
| 11 | `11_Pipeline_Orchestration/` | Airflow DAGs, retries, partitioning | Python + Pipeline |

## Universal Prep Framework

### How to Think (apply to every problem)
1. **Restate the goal in business terms.** "We want X to support Y decision."
2. **Confirm definitions.** Stickiness = DAU/MAU? Or active-days-in-28? Always ask.
3. **Pick the right grain.** One row = one what?
4. **Build smallest correct version first.** Add partitions / SCD / streaming later.
5. **Optimize at the end.** Mention partition pruning, broadcast joins, predicate pushdown.

### How to Remember (mnemonics)
- **Window functions**: ROW_NUMBER vs RANK → "ROW_NUMBER breaks ties arbitrarily; RANK leaves gaps; DENSE_RANK does not."
- **Retention**: "Signups → cohorts → Day-N-active join."
- **Funnels**: "Self-join on event_id step-by-step OR ARRAY of events."
- **Stickiness**: "DAU / MAU, capped at 1."
- **A/B test**: "Mean × Variance × Sample size. Use Welch's t-test."
- **Sessionization**: "Gap > 30 min? New session. SUM-over-flag trick."
- **Star schema**: "One fact, many dims, one grain per fact."
- **SCD2**: "Effective_from + effective_to + is_current."

### How to Use These in AI / ML
- **Feature stores** depend on the same retention / funnel / sessionization queries.
- **Recommendation systems** mirror funnel drop-off to find friction.
- **Experiment platforms** (ML A/B testing) require the same lift / variance / CUPED math.
- **Streaming feature pipelines** use the same idempotency and backfill patterns.
- **Knowledge graphs** mirror SCD2 versioning for entity history.

## 4-Week Plan (Meta-tuned)

| Week | Focus | Daily Mix |
|------|-------|-----------|
| 1 | SQL mastery | 4-5 SQL window/retention/funnel problems |
| 2 | Modeling + Product Sense | 1 schema + 1 product sense + 1 SQL each day |
| 3 | Python + Pipeline | 2 Python idempotent + 1 orchestration problem |
| 4 | Mocks | 1 full mock loop (4 rounds back-to-back) |

## Top 5 Mistakes to Avoid
1. Jumping to SQL before defining the metric.
2. Saying "DAU" without checking whether it's the right metric.
3. Skipping the grain conversation in modeling.
4. Defaulting to Type 1 SCD when Meta wants Type 2 for history.
5. Treating Python as LeetCode instead of production ETL.

## Naming Convention
Each file follows: `NN_<problem_slug>.py` and `NN_<problem_slug>.md`
- `NN` = 01–10 inside the folder.
- `.py` = runnable, self-contained Python/SQL demo.
- `.md` = explainer: problem, thinking, memory aid, AI use cases.
