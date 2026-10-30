#!/usr/bin/env python3
"""
notebook_02.py — build notebook 02, Measures and Dimensions.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_notebooks import code, md, notebook  # noqa: E402


def build() -> dict:
    """Build notebook 02.

    Returns:
        The notebook dict.
    """
    return notebook([
        md("""
# 02 · Measures and Dimensions

> **Module 1 · Foundations · Lecture 1.2**

In this notebook you will:

- Learn the three kinds of measure: **additive, non-additive and ratio**
- Reproduce the **ratio problem** — the most common silently-wrong number in BI
- See why `count` and `count_distinct` are different measures
- Write the four-question description that keeps a measure from being
  misused

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
        code("""
from model import aggregate, build_sales_model

model = build_sales_model()
rows = list(csv.DictReader(open(COURSE_ROOT / "sample_data" / "orders.csv")))

print(f"{len(rows):,} order lines loaded")
"""),
        md("""
## 1. The three kinds of measure

A measure answers "what number?". The *aggregation* says how to reduce many
rows to one number, and that choice decides what the number means when you
roll it up.

| Kind | Aggregation | Rolls up? | Example |
|---|---|---|---|
| **Additive** | `sum`, `count` | yes | total revenue |
| **Non-additive** | `count_distinct`, `avg` | no | distinct orders, average order value |
| **Ratio** | `sum(n) / sum(d)` | no | margin rate |

The third kind is the dangerous one, because a ratio *looks* like it should
roll up. It does not.
"""),
        code("""
for measure in model.measures:
    kind = (
        "ratio" if measure.needs_denominator
        else ("additive" if measure.is_additive else "non-additive")
    )
    print(f"{measure.name:<22} {measure.aggregation:<16} {kind}")
"""),
        md("""
## 2. Additivity, demonstrated

An additive measure summed over a breakdown equals the coarser total. A
non-additive one does not.
"""),
        code("""
regional = aggregate(
    model, rows, ["region"], ["total_revenue", "order_count", "distinct_orders"]
)

print(f"{'region':<8} {'revenue':>14} {'lines':>7} {'orders':>7}")
for row in regional.rows:
    m = row.measures
    print(
        f"{row.dimensions['region']:<8} {m['total_revenue']:>14,.2f} "
        f"{m['order_count']:>7} {m['distinct_orders']:>7}"
    )

print()
for name in ("total_revenue", "order_count", "distinct_orders"):
    parts = sum(r.measures[name] for r in regional.rows)
    whole = aggregate(model, rows, [], [name]).rows[0].measures[name]
    verdict = "rolls up" if abs(parts - whole) < 0.01 else "DOES NOT roll up"
    print(f"{name:<18} parts={parts:>14,.2f}  whole={whole:>14,.2f}  {verdict}")
"""),
        md("""
`distinct_orders` does not roll up — summing the regional distinct counts
gives a larger number than the global one, because an order with lines in
two regions is counted twice.

That is not a bug in the tool. It is a fact about distinct counts, and it is
why the measure is labelled **non-additive** rather than quietly pretending
otherwise.
"""),
        md("""
## 3. The ratio problem

A ratio is `SUM(numerator) / SUM(denominator)`.

It is **not** the average of the per-row ratios. Those are different numbers,
and the difference is always in the same direction: the average-of-ratios
weights every row equally, while the correct answer weights every *pound* of
denominator equally. Rows with small denominators get too much say, and
because small-denominator rows are typically the extreme ones, the average-of-ratios
is **biased low**.
"""),
        code("""
# Two rows with very different sizes.
sales = [
    {"region": "big", "total_amount": 900, "margin_amount": 810},
    {"region": "small", "total_amount": 100, "margin_amount": 10},
]

# The engine does the right thing. Compute the wrong thing by hand.
numerator = sum(r["margin_amount"] for r in sales)
denominator = sum(r["total_amount"] for r in sales)
correct_ratio = numerator / denominator

naive_ratio = sum(r["margin_amount"] / r["total_amount"] for r in sales) / len(sales)

print(f"correct (sum/sum)      : {correct_ratio:.4f}")
print(f"naive (average of rows): {naive_ratio:.4f}")
print(f"error                  : {naive_ratio - correct_ratio:+.4f}  (biased low)")
"""),
        md("""
On the real data the effect is smaller but just as real — a few percentage
points of margin, which is exactly the size of error nobody investigates.

Here it is on the course's own numbers.
"""),
        code("""
# The engine's ratio, region by region, against the naive alternative.
engine_rates = {}
for row in aggregate(model, rows, ["region"], ["gross_margin"]).rows:
    engine_rates[row.dimensions["region"]] = row.measures["gross_margin"]

naive_rates = {}
for region in engine_rates:
    subset = [r for r in rows if r.get("region") == region]
    total = sum(float(r["total_amount"]) for r in subset)
    margin = sum(float(r.get("margin_amount") or 0) for r in subset)
    per_row = [float(r.get("margin_amount") or 0) / float(r["total_amount"])
               for r in subset if float(r["total_amount"]) != 0]
    naive_rates[region] = sum(per_row) / len(per_row)

print(f"{'region':<8} {'engine':>9} {'naive':>9} {'error':>9}")
for region in sorted(engine_rates):
    e, n = engine_rates[region], naive_rates[region]
    print(f"{region:<8} {e:>9.4f} {n:>9.4f} {n - e:>+9.4f}")
"""),
        md("""
### What this looks like in a BI tool

**Looker Studio calculated fields are evaluated *after* aggregation.** So
this is wrong:

```
margin_rate = margin_amount / total_amount
```

and this is right:

```
margin_rate = SUM(margin_amount) / SUM(total_amount)
```

The first one divides two already-summed numbers per row and then averages
the results. The second sums first and divides once.

**Always write `SUM(x) / SUM(y)` explicitly, with a `NULLIF` guard on the
denominator.** A ratio with a zero denominator is either an error or a divide-
by-zero, and `NULLIF(SUM(y), 0)` turns it into `NULL` — which charts render
as a gap rather than as infinity.
"""),
        md("""
## 4. `count` versus `count_distinct`

The same table, the same number, two measures.

- `count` — how many rows. On the line grain, that is **order lines**.
- `count_distinct` on `order_id` — how many **orders**.

The naming discipline that prevents the confusion: name the measure for
what it counts. `order_line_count` versus `order_count`. `distinct_orders`.
Never a bare `count`.
"""),
        code("""
by_status = aggregate(model, rows, ["status"], ["order_count", "distinct_orders"])

print(f"{'status':<12} {'lines':>7} {'orders':>7}")
for row in by_status.rows:
    m = row.measures
    print(f"{row.dimensions['status']:<12} {m['order_count']:>7} {m['distinct_orders']:>7}")

print()
print("lines total :", sum(r.measures["order_count"] for r in by_status.rows))
print("orders total:", sum(r.measures["distinct_orders"] for r in by_status.rows))
"""),
        md("""
## 5. Filters: what the measure excludes

Every measure description should answer four questions:

1. **What is it?**
2. **What grain is it over?**
3. **What does it exclude?**
4. **How does it behave when rolled up?**

Here is a thin description, and a good one.
"""),
        code("""
margin = next(m for m in model.measures if m.name == "gross_margin")
print("thin :", margin.description)
print()
print("better:")
print(
    "  Gross margin over revenue. The denominator is total_amount — "
    "the SUM of both, never the average of per-row margins."
)
"""),
        md("""
That one sentence is the difference between a correct margin rate and one
that is three points low and nobody can explain why.

## 6. Dimensions

A dimension is a column with a type. Types constrain what you can do with
it: a `time` dimension gets timeframes, a `string` dimension does not.
"""),
        code("""
for dimension in model.dimensions:
    timeframes = f"  [{', '.join(dimension.timeframe)}]" if dimension.timeframe else ""
    print(f"{dimension.name:<22} {dimension.type:<10}{timeframes}")
"""),
        md("""
## Takeaways

1. Three kinds of measure: **additive**, **non-additive**, **ratio**. Know
   which is which before you roll one up.
2. A ratio is `SUM(numerator) / SUM(denominator)`. Never the average of
   per-row ratios — that is biased low.
3. `count` counts rows; `count_distinct` counts keys. On the line grain they
   differ by a factor of two.
4. In Looker Studio, write `SUM(x) / SUM(y)` explicitly — calculated fields
   run after aggregation.
5. Name a measure for what it counts. `order_line_count` and `order_count`
   are different numbers.
6. The description is the guard rail. Four questions, one sentence.
"""),
    ])
