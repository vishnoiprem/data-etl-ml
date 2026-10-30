#!/usr/bin/env python3
"""
notebook_06.py — build notebook 06, End-to-End Project.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_notebooks import code, md, notebook  # noqa: E402


def build() -> dict:
    """Build notebook 06.

    Returns:
        The notebook dict.
    """
    return notebook([
        md("""
# 06 · End-to-End Project

> **Module 1 · Capstone · Lecture 1.6**

In this notebook you will:

- Assemble the whole semantic layer in the **order that works**: grain, keys,
  measures, dimensions, explores, gate
- Run the **validation gate** and read its findings
- Prove the numbers are wrong when the model is wrong — **on purpose**
- Render the LookML and check it stays in sync
- Leave with the **runbook** that keeps it maintainable

Everything here runs with **no GCP account, no credentials and no bill**.
"""),
        code("""
import csv
import sys
from pathlib import Path

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent.parent

PROJECT_DIR = COURSE_ROOT / "project"
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PROJECT_DIR / "core"))

print("course root :", COURSE_ROOT)
"""),
        md("""
## 1. The order of the work

The tools present the work in a different order — you click things until
something appears. The order that works is:

1. **The grain**, before anything else. For each table, write the sentence.
2. **The keys.** The primary key, and the foreign keys. The joins follow.
3. **The measures.** Type, expression, and a description that says what it
   excludes.
4. **The dimensions.** Type, and a timeframe if it is a date.
5. **The explores.** The starting points, and the joins from each.
6. **The validation gate.** The checks that catch the mistakes.
7. **The renderings.** LookML and dbt, generated from the model.

Step 1 is the one everybody skips, and it is the one that determines whether
the rest is right.
"""),
        code("""
from model import (
    build_customer_model,
    build_explores,
    build_product_model,
    build_sales_model,
)

models = {
    "orders": build_sales_model(),
    "customers": build_customer_model(),
    "products": build_product_model(),
}

for name, model in models.items():
    print(f"{name}")
    print(f"  grain        : {model.grain}")
    print(f"  primary key  : {model.primary_key}")
    print(f"  measures     : {len(model.measures)}")
    print(f"  dimensions   : {len(model.dimensions)}")
    print(f"  joins        : {len(model.joins)}")
    print()
"""),
        md("""
## 2. The grain, recorded three times

A grain written in one place is a grain that will be forgotten. A grain
written in three places is a grain that is **enforced**.

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
    model = build_sales_model()
    assert model.grain == "one row per order line"
    assert model.primary_key == "line_id"
```

Three places, three different mechanisms — a comment nobody reads, a
description everybody reads, and a test that fails the build. **The test is
the one that matters.**
"""),
        code("""
# The DDL, the model and the test all say the same thing.
model = models["orders"]
print("DDL comment  : -- The grain: one row per order LINE.")
print("model.grain  :", model.grain)
print("model.key    :", model.primary_key)
print("model.desc   :", model.description[:60] + "...")

assert model.grain == "one row per order line"
assert model.primary_key == "line_id"
print()
print("✓ the three places agree")
"""),
        md("""
## 3. The measures, and what their descriptions must say

Every description answers the same four questions:

1. **What is it?**
2. **What grain is it over?**
3. **What does it exclude?**
4. **How does it behave when rolled up?**

The difference between a thin description and a good one is the difference
between a correct margin rate and one that is three points low.
"""),
        code("""
for measure in model.measures:
    print(f"{measure.name}")
    print(f"  type        : {measure.type}")
    print(f"  aggregation : {measure.aggregation}")
    print(f"  expression  : {measure.expression}")
    print(f"  additive    : {measure.is_additive}")
    print(f"  description : {measure.description}")
    print()
"""),
        md("""
## 4. The validation gate

The gate is what turns a semantic layer from a set of files into something
you can trust unattended. It runs four families of checks:

- **Grain** — is the primary key actually unique?
- **Referential** — do the foreign keys resolve?
- **Completeness** — are the required fields populated?
- **Freshness** — is the data recent enough to be believed?

And three severities: `ERROR` fails the build, `WARNING` is worth a look,
`INFO` records what passed.
"""),
        code("""
from validate import validate_dataset

orders = list(csv.DictReader(open(COURSE_ROOT / "sample_data" / "orders.csv")))
customers = list(csv.DictReader(open(COURSE_ROOT / "sample_data" / "customers.csv")))

report = validate_dataset(
    orders,
    model,
    required=["order_id", "customer_id", "total_amount"],
    source="./sample_data/orders.csv",
)

print(report.to_text())
"""),
        md("""
Read the findings carefully — each one is a real defect in this data,
planted on purpose:

| Finding | Severity | What it means |
|---|---|---|
| `grain.not_unique` | ERROR | One order line is duplicated. **Every measure is inflated.** |
| `freshness.stale` | ERROR | The newest row is 126 days old. The numbers are not current. |
| `value.negative` | WARNING | One negative revenue. Legitimate for a refund; suspicious for a sign-flip bug. |

The gate exits non-zero, so in CI it stops the pipeline.

**Rules that keep a gate trusted:**

- `ERROR` only for things that make the number wrong or not current.
- `WARNING` for things worth a look.
- `INFO` for things that passed — so a passing run still leaves a record.
- **Never** fail a build on a check that has fired before without a human
  deciding what to do.

A gate that fires on good data gets switched off within a week, and then it
protects nothing.
"""),
        code("""
# The individual checks, so you can see them in isolation.
from validate import (
    check_completeness,
    check_freshness,
    check_grain,
    check_no_negative_revenue,
    check_referential_integrity,
)

grain_report = check_grain(orders, "line_id")
print("grain:")
for finding in grain_report.findings:
    print(f"  [{finding.severity}] {finding.code}: {finding.message}")

print()
ref_report = check_referential_integrity(orders, "customer_id", customers, "customer_id")
print("referential:")
for finding in ref_report.findings or [None]:
    if finding:
        print(f"  [{finding.severity}] {finding.code}: {finding.message}")
    else:
        print("  (no findings)")
"""),
        code("""
# The same check on clean data — the INFO path.
clean = [r for r in orders if r["line_id"] != "L0011"]
print("rows after removing the duplicate:", len(clean))

clean_report = check_grain(clean, "line_id")
for finding in clean_report.findings:
    print(f"  [{finding.severity}] {finding.code}: {finding.message}")
"""),
        md("""
## 5. Prove the numbers are wrong when the model is wrong

This is the exercise that teaches the most. Break it on purpose, and
measure the damage.
"""),
        code("""
from model import aggregate


def total_revenue(rs):
    result = aggregate(model, rs, ["region"], ["total_revenue"])
    return sum(r.measures["total_revenue"] for r in result.rows)


baseline = total_revenue(orders)
duplicated = total_revenue(orders + orders)

print(f"baseline   : {baseline:>14,.2f}")
print(f"duplicated : {duplicated:>14,.2f}")
print(f"difference : {duplicated - baseline:>14,.2f}  ({(duplicated/baseline - 1) * 100:.0f}%)")
"""),
        md("""
Doubling the fact table doubles the revenue. **Nothing errors.** The chart
still looks like a chart.

This is the mistake the whole course is about, and you have just made it in
three lines.

Now the harder variant — a *safe* join that still produces a wrong number,
which is grain mismatch rather than fan-out.
"""),
        code("""
# The customer table has one row per customer; orders has one per line.
# Joining customers -> orders multiplies the customer rows.
by_id = {c["customer_id"]: c for c in customers}
expanded = []
for row in orders:
    cust = by_id.get(row["customer_id"])
    if cust:
        expanded.append(cust)

alone = sum(float(c.get("lifetime_value") or 0) for c in customers)
joined = sum(float(c.get("lifetime_value") or 0) for c in expanded)

print(f"customer rows, unjoined : {len(customers):>6,}")
print(f"customer rows, joined   : {len(expanded):>6,}")
print()
print(f"lifetime_value, unjoined: {alone:>14,.2f}")
print(f"lifetime_value, joined  : {joined:>14,.2f}")
print(f"inflation               : {joined / alone:.4f}x")
"""),
        md("""
The join is cardinality-legal, the SQL is correct, and the number is wrong.
The customer-level measure got summed once per order line.

**The rule:** never aggregate a measure at a grain coarser than the grain
you are joining at.

## 6. The renderings

The LookML is an *output*. It is generated from the model, and a test keeps
the two in sync — so they can never drift apart silently.
"""),
        code("""
from lookml import render_explore, render_view

print(render_view(model))
print(render_explore(build_explores()[0]))
"""),
        code("""
# The sync check, as a test would run it.
committed = (PROJECT_DIR / "lookml" / "ecommerce.model.lookml").read_text()

expected_parts = [render_view(m) for m in models.values()]
for part in expected_parts:
    assert part.strip() in committed, "the committed LookML is stale"

print("✓ the committed LookML matches the generator")
print(f"  {len(committed.splitlines())} lines, {len(committed)} characters")
"""),
        md("""
## 7. The runbook

Not documentation — a **deliverable**. It should contain:

- the grain of every table;
- the fan-out risk of every join;
- the freshness expectation for every model;
- the exact queries to run, in order, when a number is questioned;
- who to page, and who to ask.

This is the artefact that turns a semantic layer from a set of files into an
institution.

The "exact queries, in order" part is the one people skip, and it is the one
that matters at 9am on a Monday. When someone says "revenue looks wrong",
the runbook should say: run this, then this, then this.

```bash
# 1. Is the data fresh?
python project/local_bi.py validate --input ./sample_data/orders.csv

# 2. Is the grain intact?
python project/local_bi.py describe

# 3. What do the numbers say, by dimension?
python project/local_bi.py query \\
    --input ./sample_data/orders.csv \\
    --dimensions region \\
    --measures total_revenue,distinct_orders

# 4. Does the rendered model match the code?
python resources/build_notebooks.py --check
```

## Takeaways

1. **Grain first.** It determines the keys, the joins, the measures and
   which questions are even answerable.
2. Record the grain in **three places**: DDL comment, model description,
   test. The test is the one that matters.
3. The **validation gate** turns trust from a habit into a mechanism.
4. Break the model **on purpose** and measure the damage. The numbers teach
   what the prose cannot.
5. Grain mismatch is more common than fan-out, and harder to see — the join
   looks fine.
6. The renderings are **outputs**. Generate them, and test that they are in
   sync.
7. The **runbook is a deliverable**. Write the queries in the order they
   get run.
"""),
    ])
