#!/usr/bin/env python3
"""
notebook_01.py — build notebook 01, What Is a Semantic Layer.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_notebooks import code, md, notebook  # noqa: E402


def build() -> dict:
    """Build notebook 01.

    Returns:
        The notebook dict.
    """
    return notebook([
        md("""
# 01 · What Is a Semantic Layer

> **Module 1 · Foundations · Lecture 1.1**

In this notebook you will:

- Meet the four objects every semantic layer is made of: **models, measures,
  dimensions and explores**
- Build your first model in Python and read its grain
- Query it the way a dashboard would query it
- See the one sentence that explains most BI bugs: **"one row per X"**

Everything here runs with **no GCP account, no credentials and no bill**.
"""),
        code("""
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
print("python      :", sys.version.split()[0])
"""),
        md("""
## 1. Generate the sample data

The course ships a deterministic generator. Seeded, so every run produces
byte-identical output — which is what lets the chapters quote exact numbers.
"""),
        code("""
import subprocess

result = subprocess.run(
    [
        sys.executable,
        str(COURSE_ROOT / "resources" / "sample_data.py"),
        "--output-dir",
        str(COURSE_ROOT / "sample_data"),
    ],
    capture_output=True,
    text=True,
)
print(result.stdout.strip().splitlines()[-1] if result.stdout else "ok")
"""),
        code("""
import csv

SAMPLE_DIR = COURSE_ROOT / "sample_data"

for name in ("orders.csv", "customers.csv", "products.csv"):
    path = SAMPLE_DIR / name
    with path.open() as handle:
        rows = list(csv.DictReader(handle))
    print(f"{name:<16} {len(rows):>5,} rows   {path.stat().st_size:>7,} bytes")

print()
with (SAMPLE_DIR / "orders.csv").open() as handle:
    reader = csv.DictReader(handle)
    print("orders columns:", reader.fieldnames)
"""),
        md("""
## 2. The four objects

A semantic layer is not a magic feature. It is four plain things:

| Object | What it is | One sentence |
|---|---|---|
| **Model** | a table, plus what it means | "one row per order line" |
| **Measure** | a number, with an aggregation | "sum of order line revenue" |
| **Dimension** | a column, with a type | "the region a sale happened in" |
| **Explore** | a starting point, with joins | "orders, joined to customers" |

Everything else — the charts, the filters, the drill-downs — is the BI tool
rendering these four things.

The model is the one that matters most, because it carries the **grain**.
"""),
        code("""
from model import build_sales_model

model = build_sales_model()

print("name        :", model.name)
print("label       :", model.label)
print("table       :", model.table)
print("grain       :", model.grain)
print("primary key :", model.primary_key)
print()
print("description :")
print(" ", model.description)
"""),
        md("""
Read that grain line again: **"one row per order line"**.

That is not a description of the data. It is a *contract*. It tells you:

- `line_id` is unique and `order_id` is **not**;
- summing revenue across regions is legitimate;
- **counting** rows counts *lines*, not orders;
- joining `orders` to `customers` cannot fan out (many lines to one
  customer), but joining `customers` to `orders` absolutely can.

Almost every BI bug is somebody violating this sentence.
"""),
        code("""
print("Measures:")
for measure in model.measures:
    print(f"  {measure.name:<22} {measure.type:<16} {measure.description}")

print()
print("Dimensions:")
for dimension in model.dimensions:
    timeframes = f"  [{', '.join(dimension.timeframe)}]" if dimension.timeframe else ""
    print(f"  {dimension.name:<22} {dimension.type:<10}{timeframes}")
"""),
        md("""
## 3. The query engine

The course ships a tiny local BI engine. It is the same shape as every real
semantic layer: you name the dimensions and the measures, and it works out
the grouping.

This matters for the rest of the course: **the semantic layer is the thing
under test**, not the SQL it generates. Everything runs in pure standard
library, so a full query takes a quarter of a second.
"""),
        code("""
from model import aggregate

rows = list(csv.DictReader(open(SAMPLE_DIR / "orders.csv")))

result = aggregate(
    model,
    rows,
    dimensions=["region"],
    measures=["total_revenue", "order_count", "distinct_orders"],
)

for row in result.rows:
    measures = row.measures
    print(
        f"{row.dimensions['region']:<8} "
        f"revenue={measures['total_revenue']:>12,.2f}  "
        f"lines={measures['order_count']:>4}  "
        f"orders={measures['distinct_orders']:>4}"
    )
"""),
        md("""
Look at the last two columns. They are **not the same**, and the difference
is the whole point.

`order_count` counts rows — 901 order lines.
`distinct_orders` counts unique `order_id` values — 450 orders.

If a dashboard says "orders" and you built it on `order_count`, it is wrong
by the average number of lines per order — and it is wrong in the direction
that looks like growth.
"""),
        code("""
total_lines = sum(r.measures["order_count"] for r in result.rows)
total_orders = sum(r.measures["distinct_orders"] for r in result.rows)

print(f"total lines : {total_lines:>6,}")
print(f"total orders: {total_orders:>6,}")
print(f"lines per order: {total_lines / total_orders:.2f}")
"""),
        md("""
## 4. Additivity: the property that decides everything

A measure is **additive** when the values can be summed across a finer
breakdown and still equal the coarser value.

- `total_revenue` (a sum) — additive. Regions sum to the total.
- `distinct_orders` (a count distinct) — **not** additive. Summing the
  regional counts double-counts any order with lines in two regions.
- `gross_margin` (a ratio) — not additive. This is the subtle one.

The engine knows which is which, and so should you.
"""),
        code("""
for measure in model.measures:
    print(f"{measure.name:<22} additive={str(measure.is_additive):<6} {measure.type}")
"""),
        code("""
# The additive property, demonstrated.
regional = aggregate(model, rows, ["region"], ["total_revenue"])
by_region = {r.dimensions["region"]: r.measures["total_revenue"] for r in regional.rows}
total = aggregate(model, rows, [], ["total_revenue"]).rows[0].measures["total_revenue"]

print("sum of regions :", round(sum(by_region.values()), 2))
print("grand total    :", round(total, 2))
print("additive?      :", abs(sum(by_region.values()) - total) < 0.01)
"""),
        md("""
## 5. The explore

A model is a table. An **explore** is a starting point for a report author:
it names the base model and the joins available from it.

The explore carries the warning about fan-out, which is the warning that
appears in the UI wherever the join appears.
"""),
        code("""
from model import build_explores

for explore in build_explores():
    print(f"{explore.name}  ({explore.base_model})")
    print(" ", explore.description)
    for join in explore.joins:
        flag = "FAN-OUT" if join.causes_fan_out else "safe"
        print(f"    join {join.name:<12} {join.type:<14} {flag}")
    print()
"""),
        md("""
## 6. Try it yourself

The CLI is the same engine, exposed. Run it from the course root:

```bash
python project/local_bi.py describe
python project/local_bi.py explores
python project/local_bi.py query \\
    --input ./sample_data/orders.csv \\
    --dimensions region \\
    --measures total_revenue,gross_margin,distinct_orders
```

**`describe` prints the grain and the additive flag for every measure.** Those
are the two columns worth reading before you trust a number.

## Takeaways

1. A semantic layer is **models, measures, dimensions, explores** — nothing
   magical.
2. The model carries the **grain**, and the grain is a contract, not a
   description.
3. `order_count` and `distinct_orders` answer different questions. Saying
   which one a dashboard means is half of the job.
4. Additivity decides whether you can roll a number up. Learn to check it.
5. The explore's join list is where fan-out is either prevented or warned
   about.
"""),
    ])
