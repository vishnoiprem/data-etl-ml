# Chapter 07 — Capstone: Building a Semantic Layer That Survives

> **Module 4.1** · ~60 minutes · No cloud account required

---

## 🎯 What you will learn

- How to build a **semantic layer from scratch**: the models, the measures,
  the dimensions, the joins, and the explores.
- How to **choose the grain** for each table, and how to record the decision
  so it survives.
- How to turn a semantic layer into **LookML**, and into **dbt models with
  tests**.
- How to build the **validation gate** and wire it into CI.
- How to build the **runbook** that keeps the layer maintainable.
- The shape of a BI project that is still trusted in two years.

---

## 🧠 Concept

### The deliverable

By the end of this chapter you will have built a complete semantic layer for
an e-commerce dataset:

```
project/core/model.py       the semantic layer — the source of truth
project/core/date_helpers.py  the date spine and the timeframes
project/core/lookml.py      the LookML reader and writer
project/core/validate.py    the validation gate
project/local_bi.py         the CLI that runs it all
project/lookml/ecommerce.model.lookml   the rendered LookML
sql/create_analytics.sql    the DDL, with the grain in the comments
sql/reconciliation.sql      the three nightly queries
```

The design decision that makes it work, and that makes it *teachable*:
**the semantic layer is pure standard library.** The hard part — the grain
logic, the additivity, the ratio semantics, the date arithmetic — is in plain
Python that runs in a quarter of a second with no credentials, no Looker
instance and no bill.

That is not a workaround. It is the reason the ideas transfer. A LookML file
is nearly impossible to unit-test, because rendering it requires the Looker
application. The same logic in a plain module is testable in milliseconds, and
you can assert things about it that no UI would let you assert:

```python
def test_distinct_orders_is_not_additive_across_regions():
    """Distinct orders summed across regions exceeds the total.

    This test asserts that the measure is NOT additive. That is a
    positive test of a negative property — it documents the trap.
    """
```

### The order of the work

The order matters, and it is not the order the tools present.

**1. The grain, before anything else.** For each table, write the sentence.
Not in a wiki page — in the DDL comment, the model description and the test.

```
analytics.orders        one row per order LINE
analytics.customers     one row per customer
analytics.products      one row per product
analytics.date_spine    one row per CALENDAR DAY
```

**2. The keys.** The primary key of each table, and the foreign keys between
them. These are the joins, and their cardinality follows from the grains.

```
orders.line_id          → unique
orders.customer_id      → many_to_one  customers.customer_id
orders.product_id       → many_to_one  products.product_id
```

**3. The measures.** Each with a type, an expression, and a description that
says what it excludes.

**4. The dimensions.** Each with a type, and a timeframe if it is a date.

**5. The explores.** The named starting points, and the joins available from
each.

**6. The validation gate.** The checks that catch the mistakes.

**7. The LookML and the dbt models.** The renderings of what you built.

### The grain, recorded three times

A grain that is written in one place is a grain that will be forgotten. A
grain written in three places is a grain that is enforced.

**In the DDL** — the machine-checked statement:

```sql
CREATE TABLE IF NOT EXISTS analytics.orders (
    line_id      STRING NOT NULL,
    order_id     STRING NOT NULL,
    -- The grain: one row per order LINE.
    --
    -- `order_id` is deliberately NOT the primary key and is NOT unique.
    -- An order with three lines has three rows.
    PRIMARY KEY (line_id),
    FOREIGN KEY (customer_id) REFERENCES analytics.customers (customer_id)
);
```

**In the model** — the thing the report author reads:

```python
Model(
    name="orders",
    label="Orders",
    table="analytics.orders",
    description=(
        "One row per order line. Note the grain: a single order with "
        "three lines appears three times."
    ),
    grain="one row per order line",
    primary_key="line_id",
)
```

**In the test** — the thing that fails the build:

```python
def test_the_grain_is_one_row_per_order_line():
    """The orders model's grain is the line, not the order."""
    model = build_sales_model()
    assert model.grain == "one row per order line"
    assert model.primary_key == "line_id"


def test_a_duplicated_primary_key_fails_the_gate():
    """A duplicated primary key must fail the validation gate."""
    rows = [
        {"line_id": "l1", "customer_id": "c1", "created_at": "2026-03-15"},
        {"line_id": "l1", "customer_id": "c1", "created_at": "2026-03-15"},
    ]
    report = validate_dataset(rows, build_sales_model())
    assert not report.passed
```

Three places, three different mechanisms — a comment nobody reads, a
description everybody reads, and a test that fails the build. The test is
the one that matters.

### What a measure's description must contain

Every measure in this course carries a description, and every description
answers the same four questions:

1. **What is it?** — "Sum of order line revenue."
2. **What grain is it over?** — "order line".
3. **What does it exclude?** — the filters.
4. **How does it behave when rolled up?** — additive or not.

```python
Measure(
    name="gross_margin",
    label="Gross Margin",
    type=RATIO_TYPE,
    aggregation=SUM,
    expression="margin_amount",
    description="Margin over revenue.",
    filters=("total_amount",),
)
```

That last description is thin. Here is the version that would actually
prevent the mistake:

```python
description=(
    "Margin over revenue. The denominator is total_amount — the SUM of "
    "both, never the average of per-row margins."
)
```

**One sentence. It is the difference between a correct margin rate and one
that is 3 points low and nobody can explain why.**

### The explores, and the fan-out risk

The explore is the contract with the report author. It fixes the base model
and the available joins, and — this is the part that matters — it tells the
author which joins are risky.

```python
Explore(
    name="customers",
    label="Customers",
    base_model="customers",
    description="A customer explore, for segmentation questions.",
    joins=[
        Join(
            name="orders",
            from_model="customers",
            to_model="orders",
            type=ONE_TO_MANY,
            foreign_key="customer_id",
            primary_key="customer_id",
            description=(
                "One customer has many orders. Traversing this fan-outs "
                "the order lines — and therefore the revenue — unless "
                "the measure is a distinct count."
            ),
        ),
    ],
)
```

The description is not decoration. It is the warning, and it appears in the
UI wherever the join appears.

### The three tables, and what each is for

| Table | Grain | Used for | Do not use for |
|---|---|---|---|
| `orders` | one row per order line | Revenue, order counts, product mix | Counting orders (use `distinct_orders`) |
| `customers` | one row per customer | Segmentation, LTV, cohort analysis | Revenue (it is not on this grain) |
| `products` | one row per product | Catalogue, pricing, supplier analysis | Sales volume |
| `date_spine` | one row per calendar day | Filling gaps, fiscal calendars | Anything else |

The last column is the important one. **A table's grain makes some questions
unanswerable on it**, and the discipline is to say so rather than to
approximate.

---

## 🛠️ Hands-On: Building It End to End

### 1. Generate the data

```bash
cd data-engineering/data-Course/google/data-analysis
python resources/sample_data.py --output-dir ./sample_data
```

The dataset is deterministic (`SEED = 42`) and deliberately imperfect:
a duplicated order line, an unresolved customer, a null product, a negative
revenue row, and a stale extract. Every one of those is caught by a check.

### 2. Inspect the semantic layer

```bash
python project/local_bi.py describe
python project/local_bi.py explores
```

Read the output the way you would read a schema. Two things matter: the
**grain**, and the **additive** column.

### 3. Ask the questions the dashboard will ask

```bash
python project/local_bi.py query \
    --input ./sample_data/orders.csv \
    --dimensions region,channel \
    --measures total_revenue,gross_margin,distinct_orders \
    --format csv \
    --output ./out/revenue_by_region.csv
```

```bash
python project/local_bi.py query \
    --input ./sample_data/orders.csv \
    --dimensions status \
    --measures total_revenue,order_count
```

The second query is the one to check by hand. `total_revenue` per status
sums to the total. `order_count` per status also sums to 901. Both are
right — but only one of them answers "how many orders?".

### 4. Prove the numbers are wrong when the model is wrong

Break it on purpose:

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

print("baseline :", total(rows))
print("duplicated:", total(rows + rows))
PY
```

```
baseline  : 1128941.37
duplicated: 2257882.74
```

Doubling the fact table doubles the revenue. Nothing errors. The chart still
looks like a chart. **This is the mistake the whole course is about**, and
you have just made it in three lines.

### 5. Run the validation gate

```bash
python project/local_bi.py validate --input ./sample_data/orders.csv
```

```
Validation report
----------------------------------------------------
  source            : ./sample_data/orders.csv
  rows checked      : 901
  result            : FAIL
  findings:
    [ERROR  ] grain.not_unique: primary key 'line_id' is not unique: 1 value(s) repeat. Every measure over this table is inflated. (1 rows)
    [ERROR  ] freshness.stale: newest row in 'created_at' is 126 day(s) old; the limit is 2. The numbers are not current — say so on the dashboard. (1 rows)
    [WARNING] value.negative: 1 row(s) have a negative 'total_amount'. Legitimate for refunds; suspicious for a sign-flip bug. (1 rows)
```

Exit code 1. Put it in CI.

### 6. Fill the gaps

```bash
python project/local_bi.py spine \
    --input ./sample_data/orders.csv \
    --timeframe day \
    --output ./out/spine.csv
```

### 7. Render the LookML

```bash
python project/local_bi.py lookml --with-explores \
    --output project/lookml/ecommerce.model.lookml
```

A test asserts the committed file matches the generator, so the two can
never drift apart silently.

### 8. Run everything

```bash
python3 -m pytest project/tests/ -q
python resources/audit_course.py
python resources/build_notebooks.py --check
python resources/run_notebooks.py
```

```
145 passed in 2.21s
```

---

## 🛠️ Common Errors and Fixes

### "I built the semantic layer and nobody uses it"

The most common outcome, and it is a design problem, not a marketing problem.

The cause is usually that the layer makes the *hard* questions easy and the
*easy* questions slightly harder. A report author who wants "revenue by
region" has to pick the right explore and the right measure — and if the
wrong choice is also available, they will pick it, because they do not know
the difference.

**The fixes:**

- **Name things so the right choice is obvious.** `order_line_count` versus
  `order_count`. `gross_margin_pct` versus `margin`. The name is the
  documentation.
- **Make the wrong thing hard to do.** In Looker, do not put a
  non-additive measure in a view a report author will find first.
- **Make the right thing the default.** The explore that most people want
  should be the one with the safe joins.

### "We changed a measure and every number on every dashboard moved"

That is what happens when you redefine a measure in place. The safe pattern
is additive:

1. Add the new measure beside the old one.
2. Move the dashboards over, one at a time, comparing the numbers.
3. Deprecate the old one — do not delete it, because a report you cannot
   see is still a report somebody will build.

### "The LookML and the dbt model disagree"

They will, eventually, because they are two renderings of the same intent in
two systems. The course's answer is to have **one** source of truth and
generate the other. That is what `project/core/model.py` and
`lookml.py` do.

If you must maintain both, the reconciliation query catches it — as long as
you compare *values*, not counts.

### "The validation gate blocks the pipeline and people hate it"

The gate is firing on a warning, or on a check that is too strict.

Rules that keep a gate trusted:

- **ERROR** only for things that make the number wrong or not current.
- **WARNING** for things worth a look.
- **INFO** for things that passed.
- **Never** fail a build on a check that has fired before without a human
  deciding what to do.

A gate that fires on good data gets switched off within a week, and then it
protects nothing.

---

## 💡 Production Notes

### The semantic layer is the highest-leverage asset

In a mature BI organisation, the dashboards are replaceable and the semantic
layer is not. The layer encodes the business rules that took months to
learn, and it is the only place they are written down.

Treat it accordingly:

- **Version-controlled**, always.
- **Reviewed**, like code.
- **Tested**, like code.
- **Documented** in the descriptions, not in a wiki.
- **Owned** by a named person.

### Change the layer additively

Every change to a measure is a change to every dashboard that uses it.
Before changing one:

1. Count the dashboards that use it.
2. Write the new measure beside the old one.
3. Compare the numbers on a few dashboards.
4. Migrate.
5. Deprecate — do not delete.

The rule "never delete a measure" is uncomfortable and correct. A measure you
cannot see is still a measure somebody will build.

### The runbook is part of the deliverable

Not documentation — a deliverable. It should contain:

- the grain of every table;
- the fan-out risk of every join;
- the freshness expectation for every model;
- the exact queries to run, in order, when a number is questioned;
- who to page, and who to ask.

This is the artefact that turns a semantic layer from a set of files into an
institution.

### Version the metrics, not just the models

When a metric's definition changes, record both the old and the new, and the
date. Then a question like "why does March 2025 revenue differ from what we
said in March 2025?" has an answer.

In Looker this is the version history of the LookML file. In dbt it is the
git history. In a UI-built semantic layer it is **nothing** — which is
another reason to build the layer in code.

### Watch the query cost, not just the runtime

A dashboard that takes 30 seconds is annoying. A dashboard that scans 2 TB
because a join fanned out is expensive, and the fan-out will get worse as
the data grows.

**The check:** compare the scanned bytes of the dashboard's query against
the bytes of the fact table. A large ratio means a join is multiplying
work.

### Automate the boring parts of the semantic layer

The parts that are mechanical — generating a dimension from a table's
columns, generating a measure from a numeric column, generating the tests —
should be generated, not typed. The course's `render_view` is the idea in
miniature: the model is the source of truth, the LookML is a rendering, and
a test keeps them in sync.

---

## 🔑 Key Takeaways

1. **The grain comes first**, and it is recorded in three places: the DDL
   comment, the model description, and the test.
2. **A measure's description must say what it excludes** and how it behaves
   when rolled up.
3. **The explore is the contract with the report author.** Warn about the
   fan-out joins in the join's own description.
4. **A table's grain makes some questions unanswerable on it.** Say so
   rather than approximating.
5. **Change the layer additively.** Add, migrate, deprecate — never delete.
6. **The runbook is a deliverable**, not documentation.
7. **One source of truth, generated renderings.** The LookML and the dbt
   model are outputs, and a test keeps them in sync.

---

## 📚 Practice Exercises

1. Add a fourth model to the course's semantic layer — `analytics.sessions`
   with a `session_id` primary key and a grain of "one row per session" —
   and join it to `orders` with the correct cardinality. Write the
   description that explains which measures are safe across that join and
   which are not.

2. Add a `channel_attribution` model at the order grain and demonstrate the
   grain mismatch from Chapter 03: join it to `orders` and show the
   inflation, then show the fix.

3. Build the reconciliation as a CLI subcommand — `local_bi.py reconcile
   --source A.csv --dashboard B.csv --key line_id` — that reports MISSING,
   EXTRA and VALUE_MISMATCH. Test it with three deliberate differences.

4. Write the runbook for this course's semantic layer: the grain of every
   table, the fan-out risk of every join, and the five queries to run when
   a number is questioned, in order.

5. Extend the model with a `cohort` model — a factless table with one row
   per customer per acquisition month — and write the cohort analysis query.
   This is the canonical use of a fact table with no measures, and it is
   where the date spine earns its keep.

6. Add a `deprecated` flag to `Measure` and a `deprecated_measures()` method
   to `Model`. Write a test that fails when a deprecated measure is still
   used by an explore — the "never delete, only deprecate" rule, enforced.

7. Write the dbt version of the course's semantic layer: three models, a
   `schema.yml` with `unique`/`not_null`/`relationships` tests, and the
   grain in each description. Then write a dbt test that reconciles the
   modelled table against the raw one at the value level.

---

## 📖 Further Reading

- **The course's `project/README.md`** — the full walkthrough, including
  the "break it on purpose" exercises.
- **`sql/reconciliation.sql`** — the three nightly queries, ready to copy.
- **`project/lookml/ecommerce.model.lookml`** — the semantic layer rendered
  as LookML.
- **dbt's "Quickstart" and "dbt Semantic Layer"** — `docs.getdbt.com`. The
  fastest way to see the same ideas in a different tool.
- **Kimball & Ross, *The Data Warehouse Toolkit*** (3rd ed., 2013) — the
  dimensional modelling reference behind the whole course.
- **"The Semantic Layer"** in *Fundamentals of Data Engineering* (O'Reilly,
  2022) — the clearest short treatment of grain and the measure/dimension
  split.
