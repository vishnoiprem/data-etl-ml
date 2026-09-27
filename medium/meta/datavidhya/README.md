# Meta Data Engineer Interview Prep — DataVidhya Set

Runnable, **self-asserting** PySpark + Spark SQL solutions. Every file checks its
query against hand-computed expected output, so a green run means the SQL is
actually right — not merely syntactically valid.

```bash
./run_all.sh                 # run the whole suite
cd 02_Retention_Cohorts && ../../../.env/bin/python 01_d1_retention.py
```

**Every file is fully self-contained.** It builds its own `SparkSession`, defines
its own sample data inline with `spark.createDataFrame(...)`, and carries its own
`expect()` assertion helper. There is no shared seed module to import — copy any
single file anywhere and it runs. Sample data is deliberately tiny and
hand-checkable, and each table carries the trap the question is really testing.

Each file prints its intermediate result with `.show()` before asserting, so you
can eyeball the per-row logic rather than trusting an aggregate.

## What the interview actually is

Per Meta's own candidate guide, the initial loop is **two rounds**:

| Round | Length | Scope |
|---|---|---|
| Sr Leadership Screen | 30 min | Ownership, impact, scope |
| Sr Technical Screen | 60 min | **Coding, Data Modeling, Architecture, & SQL** |

Calibration from reported loops: Meta holds the **hardest SQL bar** of any FAANG
and the fastest pace (~8 min/question). Python is data manipulation — dicts,
parsing, dedup — **not** LeetCode DSA. No trees, no DP. Skip cloud-service study;
Meta's stack is internal (Presto, Spark, Hive-style tables, Scuba).

The most-reported rejection pattern is the **silent SQL savant**: flawless
queries written without narration, scored as "strong technically, no product
signal." Say *why* this metric, *why* this grain, and *what you'd check* when the
number moves. Correct-and-silent loses to slightly-imperfect-and-narrated.

## Contents

| Folder | Files | Covers |
|---|---|---|
| `01_SQL_Window_Functions/` | 2 | ROW_NUMBER top-N, LAG/LEAD deltas |
| `02_Retention_Cohorts/` | 3 | D1 / D7 / D28 retention by cohort |
| `03_Funnel_Analysis/` | 3 | loose vs **strict ordered** funnel, time-to-convert |
| `04_DAU_MAU_Metrics/` | 3 | DAU series, stickiness, rolling 7-day unique, L7/L28 |
| `05_AB_Test_Metrics/` | 3 | lift, variance, Welch t-test, **CUPED** |
| `06_Sessionization/` | 3 | gap-and-island, session metrics, the global-id trap |
| `07_Star_Schema_Modeling/` | 3 | Marketplace, News Feed, Reels schemas |
| `08_SCD_Types/` | 3 | Type 1 / 2 / 3 + point-in-time attribution |
| `09_Python_Idempotent_ETL/` | 3 | deterministic dedup, partition overwrite, backfill |
| `10_Product_Sense_Frameworks/` | 3 | metric→grain→query chain, drop investigation |
| `11_Pipeline_Orchestration/` | 3 | Airflow DAG shape, watermarks, retries + gates |
| `12_DataVidhya_Meta_Set/` | 25 | 20 Meta-tagged SQL questions + **5 data-modeling questions** |
| `13_Ten_Methods/` | 1 | one problem solved 10 different ways, all verified |

**Status:** 58 files, 93 assertions, all passing. The 11 pattern folders hold 3
worked problems each (not the 10 per folder an earlier draft of this README
promised), plus all 20 Meta-tagged SQL questions and all 5 Meta-tagged modeling
questions in `12_`. Several patterns deliberately include the **wrong** answer
asserted alongside the right one, so the failure mode is documented rather than
discovered in production.

`07_Star_Schema_Modeling/` files are DDL + reasoning only — they define schemas
rather than run queries, so `run_all.sh` executes them as no-ops.

## The universal framework

**How to think** (apply to every problem):
1. Restate the goal in business terms.
2. **Confirm definitions.** Stickiness = DAU/MAU? L7 = active in last 7 days, or
   7 of 7? Always ask — the asking is scored.
3. **Pick the grain.** "One row = one what?" If you can't say it in a sentence,
   you've already failed the modeling question.
4. Build the smallest correct version first; add partitions/SCD/streaming after.
5. Optimize last — partition pruning, broadcast joins, predicate pushdown.

**Mnemonics:**
- ROW_NUMBER breaks ties arbitrarily; RANK leaves gaps; DENSE_RANK doesn't.
- Retention: "signups → cohorts → Day-N-active LEFT JOIN."
- Sessionization: "LAG, flag, cumulative SUM."
- SCD: "Type 1 forgets. Type 2 remembers all (rows). Type 3 remembers one (columns)."
- SCD2 intervals are `[from, to)` — half-open, or boundary joins double-count.
- Star schema: "One fact, many dims, one grain per fact."

**Top mistakes:**
1. Integer division — `COUNT(a)/COUNT(b)` returns 0. Multiply by `100.0`.
2. Summing DAU to get MAU (double counts returning users).
3. INNER JOIN in retention — silently drops churned users, inflates to 100%.
4. Skipping the grain conversation in modeling.
5. Defaulting to SCD Type 1 when the question needs point-in-time history.
6. `dropDuplicates()` for dedup — non-deterministic, so the job isn't reproducible.
7. `append` in a retryable pipeline — duplicates on every retry.
8. Treating Python as LeetCode instead of production ETL.

## Naming convention

`NN_<problem_slug>.py` — runnable, self-asserting, self-contained.
Each file: docstring (problem + how to think + traps) -> inline sample data ->
Spark SQL solution -> PySpark DataFrame API equivalent -> assertion.
