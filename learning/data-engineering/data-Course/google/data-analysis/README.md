# Semantic Layers, Looker Studio & Looker — Master the Grain, the Measures, and the Joins

A complete, hands-on guide to **semantic layers** and **BI tooling** for data engineers and
analytics engineers — covering **Looker Studio**, **Looker**, and **dbt's semantic layer**, and the
**grain, additivity and join-cardinality** discipline that all three depend on.

Every topic is taught from first principles — the grain, the measures, the additivity rules, the
ratio problem, the join cardinalities, fan-out, the date spine, the validation gate and the
reconciliation — and then exercised for real through a **working project that runs locally with no
GCP account, no credentials and no bill**.

> **Duration:** 1 module · 7 chapters · 6 notebooks · ~10 hours
> **Audience:** Data engineers, analytics engineers and BI developers who build or maintain the
> layer that other people report from.

---

## What You Will Learn

- **The semantic layer** — the four objects it is made of (models, measures, dimensions, explores),
  and why it exists: not to make numbers *correct*, but to make them **the same number**.
- **The grain** — the one sentence about a table ("one row per order **line**"), why it determines
  the primary key, the join cardinalities and which questions are even answerable, and how to
  record it so it survives.
- **Additivity** — the three kinds of measure (additive, non-additive, ratio), how to check it in
  one comparison, and why the regional distinct counts summing to 799 against a global 450 is a
  **77.6%** inflation.
- **The ratio problem** — why a ratio must be `SUM(numerator) / SUM(denominator)`, why the naive
  average-of-ratios is *always* biased low, and why a Looker Studio calculated field gets it wrong
  by default.
- **Joins and fan-out** — the four cardinalities, the one rule that removes all guesswork, and the
  subtler trap: a **safe** join that still produces a wrong number.
- **The date spine** — why truncating a date is not the same as generating a calendar, and the
  nine missing days that turn a slow week into a fake cliff.
- **The validation gate** — the four check families, the three severities, and the rule that keeps
  a gate trusted instead of muted within a week.
- **Reconciliation** — comparing **values** rather than counts, and why the null-safe
  `IS DISTINCT FROM` matters more than the query that uses it.
- **The three tools** — Looker Studio (a consumer tool), Looker (a semantic layer) and dbt (a
  transformation layer), and what each is actually for.
- **106 interview questions** with answers written the way a senior engineer answers them.

---

## Course Structure

### Module 1 — Foundations & the Capstone

| # | Chapter | Covers |
|---|---------|--------|
| 1.1 | [What Is a Semantic Layer?](chapters/01-what-is-a-semantic-layer.md) | The four objects; the grain as a contract; the explore and its fan-out warnings; the three tools; the first query |
| 1.2 | [Measures and Dimensions](chapters/02-measures-and-dimensions.md) | Additivity; the ratio problem; `count` vs `count_distinct`; filters; the four-question description |
| 1.3 | [Joins and the Grain](chapters/03-joins-and-the-grain.md) | The four cardinalities; fan-out; grain mismatch; unresolved foreign keys; SCD validity windows |
| 1.4 | [The Date Spine](chapters/04-the-date-spine.md) | Generating the calendar; filling the gaps; the timeframes; date filters; period over period |
| 1.5 | [Looker Studio and Looker](chapters/05-looker-studio-and-looker.md) | The three tools; calculated fields; rendering LookML; the `{{ }}` build-time safety net; dbt |
| 1.6 | [Operations and Validation](chapters/06-operations-and-validation.md) | The four checks; freshness; reconciliation at the value level; SLOs; the runbook; query cost |
| 1.7 | [Capstone Project](chapters/07-capstone-project.md) | The order of the work; the grain in three places; the gate; the renderings; the runbook |

---

## Hands-On Notebooks

Six notebooks, each of which **executes top-to-bottom with no GCP account**.

| # | Notebook | Chapter | What you build |
|---|----------|---------|----------------|
| 01 | [What Is a Semantic Layer](notebooks/01-the-semantic-layer.ipynb) | 1.1 | The four objects; the grain; the first query; additivity |
| 02 | [Measures and Dimensions](notebooks/02-measures-and-dimensions.ipynb) | 1.2 | The three kinds of measure; the ratio problem, on real numbers |
| 03 | [Joins and the Grain](notebooks/03-joins-and-grain.ipynb) | 1.3 | A fan-out, reproduced and measured; grain mismatch; the fan-out check |
| 04 | [The Date Spine](notebooks/04-the-date-spine.ipynb) | 1.4 | The nine missing days; the timeframes; the year-grain off-by-one |
| 05 | [Looker Studio and Looker](notebooks/05-looker-studio-and-looker.ipynb) | 1.5 | The rendered LookML, read back; a broken reference caught locally |
| 06 | [End-to-End Project](notebooks/06-end-to-end-project.ipynb) | 1.6, 1.7 | The whole layer; the gate; the numbers broken on purpose; the runbook |

---

## The Project

The course ships a **working semantic layer** — pure standard library, so it runs anywhere:

```text
project/core/model.py        the semantic layer — models, measures, dimensions, explores
project/core/date_helpers.py  the date spine, the timeframes, the date filters
project/core/lookml.py        the LookML reader and writer
project/core/validate.py      the validation gate
project/local_bi.py           the CLI that runs it all
project/tests/                145 tests
project/lookml/               the rendered LookML
```

### The five-minute path

```bash
cd data-engineering/data-Course/google/data-analysis

pip install -r project/requirements.txt

# Generate the deterministic dataset
python resources/sample_data.py --output-dir ./sample_data

# Inspect the semantic layer
python project/local_bi.py describe
python project/local_bi.py explores

# Ask the question the dashboard will ask
python project/local_bi.py query \
    --input ./sample_data/orders.csv \
    --dimensions region,channel \
    --measures total_revenue,gross_margin,distinct_orders

# Run the validation gate (exits 1 — the sample data is deliberately broken)
python project/local_bi.py validate --input ./sample_data/orders.csv
```

Full walkthrough: [project/README.md](project/README.md) · Setup: [resources/SETUP.md](resources/SETUP.md)

---

## Break It on Purpose

The course's central exercise: **prove the numbers are wrong when the model is wrong**, and measure
the damage.

```bash
python3 - <<'PY'
import csv, sys
sys.path.insert(0, "project/core")
from model import build_sales_model, aggregate

rows = list(csv.DictReader(open("sample_data/orders.csv")))
model = build_sales_model()

def total(rs):
    r = aggregate(model, rs, ["region"], ["total_revenue"])
    return sum(x.measures["total_revenue"] for x in r.rows)

print("baseline  :", total(rows))
print("duplicated:", total(rows + rows))
PY
```

```text
baseline  : 1128941.37
duplicated: 2257882.74
```

Doubling the fact table doubles the revenue. **Nothing errors.** The chart still looks like a
chart. This is the mistake the whole course is about, and you have just made it in three lines.

---

## The Interview Bank

**[interview/](interview/)** — 106 questions, each answered the way a senior engineer who has
actually run this in production would say it out loud: the direct answer, the mechanism, when the
alternative wins, a production failure story, and the numbers.

| File | Questions | Covers |
|---|---:|---|
| [01-foundations-and-the-semantic-layer.md](interview/01-foundations-and-the-semantic-layer.md) | 14 | The layer, the grain, additivity, the ratio problem, fan-out, the spine, the three tools |
| [02-measures-and-dimensions.md](interview/02-measures-and-dimensions.md) | 14 | Measure kinds, descriptions, filters, deprecation, dimension types, conformed dimensions |
| [03-joins-and-grain.md](interview/03-joins-and-grain.md) | 14 | The grain in three places, grain mismatch, SCDs, surrogate keys, factless facts |
| [04-operations-and-validation.md](interview/04-operations-and-validation.md) | 14 | The gate, the four checks, reconciliation, `IS DISTINCT FROM`, SLOs, the runbook |
| [top-50.md](interview/top-50.md) | **50** | The highest-yield subset — read this the night before |

Study plan: [interview/README.md](interview/README.md)

---

## Reference

| Document | What it is |
|---|---|
| [resources/CHEATSHEET.md](resources/CHEATSHEET.md) | One page per topic. Keep it open in a tab. |
| [resources/GLOSSARY.md](resources/GLOSSARY.md) | Every term, defined once |
| [resources/FAQ.md](resources/FAQ.md) | The questions that come up most, answered properly |
| [resources/SETUP.md](resources/SETUP.md) | The 5-minute path, the CLI, and troubleshooting |
| [sql/create_analytics.sql](sql/create_analytics.sql) | The DDL, with the grain in the comments |
| [sql/reconciliation.sql](sql/reconciliation.sql) | The three nightly queries, ready to copy |

---

## Running Everything

```bash
python -m pytest project/tests/ -q          # 145 tests, ~2 seconds
python resources/test_course.py -v          # the course's structural tests
python resources/audit_course.py             # the linter
python resources/build_notebooks.py --check  # notebooks match their builders
python resources/run_notebooks.py            # execute every notebook, headless
```

---

## Why this course is written the way it is

A LookML file is nearly impossible to unit-test, because rendering it requires the Looker
application. The same logic in a plain module is testable in milliseconds — and you can assert
things about it that no UI would let you assert:

```python
def test_distinct_orders_is_not_additive_across_regions():
    """Distinct orders summed across regions exceeds the total.

    This test asserts that the measure is NOT additive. That is a
    positive test of a negative property — it documents the trap.
    """
```

So the hard part — the grain logic, the additivity, the ratio semantics, the date arithmetic — is
in plain Python that runs in a quarter of a second with no credentials, no Looker instance and no
bill. The LookML is then **generated** from it, so it is a rendering and not a second source of
truth, and a test keeps the two in sync.

That is not a workaround. It is the reason the ideas transfer.

---

## The One-Sentence Version

> **Know the grain, state it in three places, make the measures say what they exclude, and check
> that the numbers are still true every day.**

Everything else follows. The grain determines the keys, the joins and which questions are even
answerable. The descriptions are the guard rails that stop a correct definition being used
incorrectly. The validation gate turns trust from a habit into a mechanism. And the runbook is what
makes the whole thing maintainable by someone who was not there when it was built.
