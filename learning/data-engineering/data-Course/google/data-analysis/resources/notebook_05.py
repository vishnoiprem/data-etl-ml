#!/usr/bin/env python3
"""
notebook_05.py — build notebook 05, Looker Studio and Looker.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_notebooks import code, md, notebook  # noqa: E402


def build() -> dict:
    """Build notebook 05.

    Returns:
        The notebook dict.
    """
    return notebook([
        md("""
# 05 · Looker Studio and Looker

> **Module 1 · Foundations · Lecture 1.5**

In this notebook you will:

- Tell the three tools apart: **Looker Studio**, **Looker** and **dbt**
- Render your semantic layer into **LookML** and read it back
- Catch a broken `{{ reference }}` before Looker ever sees it
- See the **calculated field** trap in Looker Studio, with the fix

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
"""),
        md("""
## 1. Three tools, three jobs

They get confused constantly, and the confusion is expensive because each
one solves a *different* problem.

| | **Looker Studio** | **Looker** | **dbt** |
|---|---|---|---|
| What it is | a consumer BI tool | a semantic layer + exploration | a transformation framework |
| Who uses it | everyone | analysts and engineers | engineers |
| Where the definitions live | inside the report | in LookML, versioned | in SQL models |
| The risk | every report re-defines revenue | needs a licence + git discipline | no exploration layer |
| Best at | dashboards, ad-hoc | governed metrics, many audiences | tested pipelines |

The important structural difference: **Looker Studio has no shared semantic
layer.** Every report author defines their own calculated fields, their own
joins, their own filters. Two dashboards about revenue are two unrelated
implementations, and they will disagree.

Looker fixes this by putting the definitions in LookML, in a repository,
reviewed like code.
"""),
        md("""
## 2. Rendering the semantic layer as LookML

The course's semantic layer lives in `project/core/model.py`. `lookml.py`
renders it. One source of truth, one rendering.

```bash
python project/local_bi.py lookml --with-explores
```
"""),
        code("""
from lookml import render_explore, render_view
from model import build_customer_model, build_explores, build_sales_model

sales_model = build_sales_model()
customer_model = build_customer_model()

print(render_view(sales_model))
"""),
        md("""
Every measure carries its `type:`. That is the single most important line
in the file, because **the type is what tells Looker how to aggregate** — and
getting it wrong is how a `count_distinct` becomes a `sum` and every
dashboard built on it doubles.
"""),
        code("""
print(render_view(customer_model))
"""),
        md("""
Look at the join. `relationship: one_to_many` is Looker's declaration that
this join fans out — the same information the course's `Join.type` carries.

And the `description:` on the join is the warning that travels with it into
the Looker UI, where a report author will see it next to the field.
"""),
        code("""
for explore in build_explores():
    print(render_explore(explore))
    print()
"""),
        md("""
## 3. Reading LookML back

Rendering is only half the story. A semantic layer you cannot read back is
a write-only artefact — you cannot diff it, review it, or migrate it.

The course ships a parser, so you can assert on the LookML as data.
"""),
        code("""
from lookml import parse_view

text = render_view(sales_model)
view = parse_view(text)

print("name        :", view.name)
print("label       :", view.label)
print("description :", view.description)
print()
print(f"measures    : {len(view.measures)}")
for measure in view.measures:
    print(f"  {measure.name:<22} type={measure.type:<16} sql={measure.sql}")
print()
print(f"dimensions  : {len(view.dimensions)}")
for dimension in view.dimensions:
    print(f"  {dimension.name:<22} type={dimension.type:<10} sql={dimension.sql}")
"""),
        md("""
## 4. The build-time safety net

Looker resolves `{{ }}` references when the model is compiled. A reference
to a field that does not exist is a **build error** — which is good, because
it fails loudly at deploy time rather than silently at query time.

The course reproduces that check locally, so you can catch it without a
Looker instance.

Note that the *generated* LookML has no references at all — every view is
self-contained. References appear when you **compose** views, which is where
the errors live.
"""),
        code("""
from lookml import collect_available_fields, find_broken_references, find_references

available = collect_available_fields([sales_model, customer_model])
print(f"available fields ({len(available)}):")
for name in available:
    print("  ", name)
"""),
        code("""
# A composed view — the kind that carries references.
composed = '''
view: order_summary {
  sql: SELECT * FROM ${orders} ;;
  measure: revenue {
    type: sum
    sql: ${total_revenue} ;;
  }
  dimension: segment {
    sql: ${customers.customer_segment} ;;
  }
}
'''

print("references:", find_references(composed))
print("broken    :", find_broken_references(composed, available))
assert not find_broken_references(composed, available)
print("✓ every reference resolves")
"""),
        code("""
# Now break one deliberately.
broken = composed.replace("${customers.customer_segment}", "${customers.no_such_field}")

print("references:", find_references(broken))
broken_refs = find_broken_references(broken, available)
print("broken    :", broken_refs)
assert broken_refs, "the checker should have caught the broken reference"
print()
print("✓ the broken reference is caught locally, before Looker ever sees it")
"""),
        md("""
That is the value of a **semantic layer as code**: the safety net that
Looker provides at build time, available in a unit test, in a quarter of a
second, with no licence.

## 5. The Looker Studio calculated field trap

Looker Studio calculated fields are evaluated **after aggregation**. This is
documented, it is sensible, and it is the cause of a large share of
"the dashboard margin is wrong" tickets.

**Wrong** — divides per row, then averages:

```
margin_rate = margin_amount / total_amount
```

**Right** — sums first, divides once:

```
margin_rate = SUM(margin_amount) / SUM(total_amount)
```

And guard the denominator, so a zero produces a `NULL` (a gap on the chart)
rather than a divide-by-zero:

```
margin_rate = SUM(margin_amount) / NULLIF(SUM(total_amount), 0)
```

Let's see the difference on real data.
"""),
        code("""
import csv

from model import aggregate

orders = list(csv.DictReader(open(COURSE_ROOT / "sample_data" / "orders.csv")))

print(f"{'region':<8} {'SUM/SUM':>10} {'AVG of rows':>13} {'error':>9}")
for region in sorted({r["region"] for r in orders}):
    subset = [r for r in orders if r["region"] == region]

    numerator = sum(float(r.get("margin_amount") or 0) for r in subset)
    denominator = sum(float(r["total_amount"]) for r in subset)
    correct = numerator / denominator

    per_row = [
        float(r.get("margin_amount") or 0) / float(r["total_amount"])
        for r in subset
        if float(r["total_amount"]) != 0
    ]
    naive = sum(per_row) / len(per_row)

    print(f"{region:<8} {correct:>10.4f} {naive:>13.4f} {naive - correct:>+9.4f}")
"""),
        md("""
Every regional rate is off by 2–5 percentage points, and always in the same
direction: **low**. A margin that reads 49% when it is 52% is the kind of
error that survives for a year, because the number still looks plausible and
nobody knows what it should be.

## 6. The same layer in dbt

dbt's semantic layer is the modern equivalent, and it looks like this:

```yaml
semantic_models:
  - name: orders
    description: "One row per order line."
    entities:
      - name: line
        type: primary
        expr: line_id
    measures:
      - name: total_revenue
        description: "Sum of order line revenue."
        agg: sum
        expr: total_amount
```

Note the same four fields the course's `Measure` carries: name, description,
aggregation, expression. The concepts transfer even when the syntax does not.

## Takeaways

1. **Looker Studio** is a consumer tool with no shared definitions.
   **Looker** is a semantic layer. **dbt** is a transformation framework.
2. Render the layer, then **read it back** — a semantic layer you cannot
   diff is not reviewable.
3. The `type:` on a measure is what tells the tool how to aggregate. Getting
   it wrong doubles the number.
4. `{{ }}` references are a build-time safety net. Reproduce that check
   locally and you catch the error before deploy.
5. Looker Studio calculated fields run **after aggregation**. Always write
   `SUM(x) / SUM(y)`, and guard the denominator with `NULLIF`.
6. The average-of-ratios error is always **low**. A margin that reads 49%
   when it is 52% is a bug, not a variance.
"""),
    ])
