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
| `12_DataVidhya_Meta_Set/` | 81 | **all 76 Meta-tagged DataVidhya problems** + 5 data-modeling questions |
| `13_Ten_Methods/` | 1 | one problem solved 10 different ways, all verified |

**Status:** 113 files, 409 assertions, all passing (`./run_all.sh`).

`12_DataVidhya_Meta_Set/` now covers **every problem behind DataVidhya's Meta
company filter** — 76 problems, which is all 4 pages of that filter: 10 Easy,
47 Medium, 19 Hard. Files `01`–`20` are the 20 originally worked; `26`–`81` are
the remaining 56; `21`–`25` are data-modeling questions with no site equivalent.

Files `26`–`81` were built against the **site's own published schema, sample
rows, and expected output**, pulled from `datavidhya.com/api/v1/questions/<slug>/`
rather than paraphrased — so a green run means the answer matches the grader's,
not just my reading of the prose.

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

## Near-identical question pairs

The Meta set contains several pairs that look alike and want **opposite**
answers. These are the highest-value things in the folder, because pattern
matching fails on exactly these:

| Pair | Looks the same | Actually differs |
|---|---|---|
| `31` vs `36` | popularity % over a social graph | `31` is **undirected** (canonicalise pairs); `36` is **directed** (never mirror) |
| `40` vs `58` | month-over-month user metric | `40` wants the previous **calendar** month (`add_months`); `58` wants the previous month **in the result** (`LAG`). They diverge on a data gap |
| `33` vs `65` | rolling N-period window | `33` wants a 7-**day** range (`ROWS` is wrong); `65` wants 3 **rows** and says calendar gaps must not count |
| `26` vs `34` | keyword scoring over review text | `26` **retains** punctuation in tokens (so `"Excellent,"` doesn't match); `34` doesn't say that, so split on non-word chars |
| `30` vs `80` | "3rd highest distinct value" | `30` returns the **value** as a scalar and needs a NULL row when absent; `80` returns **every row** in that tier |
| `56` vs `60` | latest/max row per group | `56` must return **all** ties (`RANK`); `60` must return **exactly one** (`ROW_NUMBER` + tiebreak) |
| `42` vs `54` | interpolated percentiles | Both need exact `percentile()`, but `54` then applies **per-group** Tukey fences — pooling the groups hides the anomaly |

## Traps the shipped sample data cannot catch

Roughly a third of these questions ship sample data that gives the *right*
answer to a *wrong* query. Those files assert the bug separately on constructed
rows, so the failure mode is documented rather than discovered later:

- `46` — ids are contiguous, so a `LAG`-based "consecutive" check passes; it breaks on an id gap.
- `52` — every friendship is stored author-first, so a one-directional join coincidentally works.
- `47` — a combined `COUNT(*) >= 8` threshold passes; an 8/0 year split slips through it.
- `59`/`80` — counts/prices are consecutive, so `RANK` and `DENSE_RANK` agree until a gap or a top-tier tie appears.
- `69` — the one other-domain login lands on a day the user was also active, so dropping the domain filter changes nothing.
- `54` — both spikes are extreme enough that fleet-wide fences still catch them; a merely-anomalous reading is missed.
- `61`/`64`/`73` — no boundary row, so `<` vs `<=` and `BETWEEN` vs half-open ranges look equivalent.
- `35`/`49` — one promotion per product and matching card numbers, so fan-out and the wrong dedup key stay hidden.

## Two defects in the source data

Found while matching the site's published expected output; both are flagged in
the relevant file's docstring:

- **`47_consistent_monthly_shoppers`** — the published expected output lists
  `Eve`, who has no row in `csf_users` and no transactions. The data supports
  `Alice` only. The file asserts `Alice` and proves the per-year counts row by row.
- **`75_email_validation_filter`** — the explanation says "the table contains 7
  rows" but only 6 are published. The 6 published rows reproduce the published
  expected output exactly; the 7th is unrecoverable.

## A Spark-specific gotcha worth memorising

Spark SQL string literals consume **one level of backslash escaping** before the
regex engine sees the pattern. So `'\.'` in SQL text reaches the matcher as a
bare `.` — which matches *any* character:

```sql
-- these two are NOT the same predicate
email RLIKE '^[a-z]+@dataplatform\.com$'    -- backslash eaten: '.' matches anything
email RLIKE '^[a-z]+@dataplatform\\.com$'   -- correct in SQL text
```

The DataFrame API takes the pattern verbatim, so `F.col("email").rlike(r"...\.com$")`
needs only the single backslash. `26`, `34` and `75` all hit this; `75` asserts
both behaviours side by side.
