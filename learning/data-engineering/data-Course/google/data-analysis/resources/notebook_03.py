#!/usr/bin/env python3
"""
notebook_03.py — build notebook 03, Joins and the Grain.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_notebooks import code, md, notebook  # noqa: E402


def build() -> dict:
    """Build notebook 03.

    Returns:
        The notebook dict.
    """
    return notebook([
        md("""
# 03 · Joins and the Grain

> **Module 1 · Foundations · Lecture 1.3**

In this notebook you will:

- Learn the four join cardinalities and which of them **fan out**
- Reproduce a fan-out **with real numbers from this course's data**
- See the subtler trap: a *safe* join that still produces a wrong number
- Read a join's description and know exactly what it is warning you about

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
from model import aggregate, build_customer_model, build_sales_model

model = build_sales_model()
customer_model = build_customer_model()

orders = list(csv.DictReader(open(COURSE_ROOT / "sample_data" / "orders.csv")))
customers = list(csv.DictReader(open(COURSE_ROOT / "sample_data" / "customers.csv")))

print(f"{len(orders):,} order lines")
print(f"{len(customers):,} customers")
"""),
        md("""
## 1. Cardinality, and the direction that matters

A join's cardinality says how many rows of one table match one row of the
other. Four possibilities:

| Cardinality | Reads | Fan-out? |
|---|---|---|
| `one_to_one` | one ↔ one | no |
| `many_to_one` | many ↔ one | no |
| `one_to_many` | one ↔ many | **yes, from the one side** |
| `many_to_many` | many ↔ many | **yes, from both sides** |

The rule that removes all the guesswork:

> **Fan-out happens when you traverse *from* the "one" side *to* the "many"
> side.** Traversing the other way is always safe.

`orders → customers` is `many_to_one`: each order line finds exactly one
customer. Safe.

`customers → orders` is `one_to_many`: each customer finds many order lines.
**Fan-out.**
"""),
        code("""
for join in model.joins:
    direction = "from_model -> to_model"
    print(f"{model.name}.{join.foreign_key} -> {join.to_model}.{join.primary_key}")
    print(f"  type        : {join.type}")
    print(f"  fan-out     : {join.causes_fan_out}")
    print(f"  safe        : {join.is_safe_to_traverse}")
    print(f"  description : {join.description}")
    print()
"""),
        md("""
## 2. Reproducing a fan-out

Here is the mistake, made deliberately and measured.

The simplest way to fan out an orders table is to duplicate it. It is
equivalent to joining it to a table that contains two copies of every order
— which is exactly what a badly-modelled dimension produces.
"""),
        code("""
def total_revenue(rs):
    result = aggregate(model, rs, ["region"], ["total_revenue"])
    return sum(r.measures["total_revenue"] for r in result.rows)

baseline = total_revenue(orders)
duplicated = total_revenue(orders + orders)

print(f"baseline   : {baseline:>14,.2f}   ({len(orders):,} rows)")
print(f"duplicated : {duplicated:>14,.2f}   ({len(orders) * 2:,} rows)")
print(f"ratio      : {duplicated / baseline:.2f}x")
"""),
        md("""
**Nothing errors.** The chart still looks like a chart. The revenue simply
doubled, and a doubling reads like growth.

This is why fan-out is a *semantic* problem and not a technical one: there is
no exception, no warning, no red cell. The number is wrong in a way that
looks exactly like a business event.
"""),
        md("""
## 3. The subtler trap: a safe join with a wrong number

A join can be cardinality-safe and still inflate a measure. The mechanism is
**grain mismatch**, and it is far more common than fan-out because the join
looks fine.

The setup: you want total revenue per customer. But `total_amount` is
recorded on the **order line**, and the customer table has one row per
customer. So you join orders to customers, and then — the mistake — you sum
`total_amount` while the join is at the line grain, then attribute it to a
customer.

The number is right. The *attribution* is wrong.

Let's build it concretely.
"""),
        code("""
# How many order lines does each customer have?
lines_per_customer = {}
for row in orders:
    cid = row["customer_id"]
    lines_per_customer[cid] = lines_per_customer.get(cid, 0) + 1

counts = sorted(lines_per_customer.values())
print(f"customers with orders      : {len(lines_per_customer)}")
print(f"min lines per customer     : {counts[0]}")
print(f"max lines per customer     : {counts[-1]}")
print(f"average lines per customer : {sum(counts) / len(counts):.2f}")
"""),
        md("""
Now the inflation. Joining `customers` to `orders` multiplies each customer
row by their line count — but the *revenue* is not multiplied the same way,
because revenue is a sum over lines, not per customer.

The dangerous version is when a **customer-level** measure is summed over
that expanded result.

```sql
-- Wrong: summing a customer-level measure over a line-level join.
SELECT SUM(c.lifetime_value)
FROM customers AS c
JOIN orders AS o ON c.customer_id = o.customer_id;
```

The join is `one_to_many`. `lifetime_value` is already a customer total. Now
it is summed once per order line.

Here is the same thing with the course's own data.
"""),
        code("""
# The customer table carries a lifetime_value per customer.
print("customers with lifetime_value:", sum(1 for c in customers if c.get("lifetime_value")))

# Simulate the fan-out by expanding customers to one row per order line.
expanded = []
for row in orders:
    for cust in customers:
        if cust["customer_id"] == row["customer_id"]:
            expanded.append(cust)
            break

print("customer rows before join :", len(customers))
print("customer rows after join  :", len(expanded))
print()
print("sum of lifetime_value, joined   :", round(sum(float(c.get("lifetime_value") or 0) for c in expanded), 2))
print("sum of lifetime_value, unjoined :", round(sum(float(c.get("lifetime_value") or 0) for c in customers), 2))
"""),
        md("""
The joined sum is **larger** than the true total — the customer total is
counted once per order line.

This is the shape of the bug in real life: a "revenue by customer" report
where the top customers look implausibly profitable, because the busiest
customers are counted most often.

**The rule:**

> **Never aggregate a measure at a grain coarser than the grain you are
> joining at.** If you need a total at the order grain, aggregate it to the
> order grain *before* you join.
"""),
        md("""
## 4. The fan-out check query

The check is one query, and it belongs in CI.

The idea: compare the measure computed on the fact table alone against the
same measure computed after the join. If they differ, the join changed the
number.

Here it is on the course's data.
"""),
        code("""
# A fan-out check, in Python, that you can port straight into SQL.
def fan_out_check(fact_rows, expanded_rows, measure="total_revenue"):
    alone = aggregate(model, fact_rows, [], [measure]).rows[0].measures[measure]
    after = aggregate(model, expanded_rows, [], [measure]).rows[0].measures[measure]
    ratio = after / alone if alone else 0
    print(f"{measure:<18} alone={alone:>14,.2f}  after join={after:>14,.2f}  "
          f"ratio={ratio:.4f}  {'FAN-OUT' if abs(ratio - 1) > 0.0001 else 'ok'}")
    return ratio

# Duplicating the fact table is a fan-out.
fan_out_check(orders, orders + orders)
"""),
        code("""
# The safe direction does not fan out.
# orders -> customers is many_to_one: every line finds exactly one customer.
by_id = {c["customer_id"]: c for c in customers}
matched = [dict(row, customer_segment=by_id[row["customer_id"]]["segment"])
           for row in orders if row["customer_id"] in by_id]

print(f"order lines       : {len(orders):,}")
print(f"after the join    : {len(matched):,}  (one customer per line — no growth)")
print()
fan_out_check(orders, matched)
"""),
        md("""
## 5. The explore tells you which joins are risky

The explore is the contract with the report author. It names the base model,
the joins available, and — critically — **which joins fan out**.
"""),
        code("""
from model import build_explores

for explore in build_explores():
    print(f"explore: {explore.name}")
    print(f"  base model : {explore.base_model}")
    print(f"  description: {explore.description}")
    for join in explore.joins:
        marker = "FAN-OUT" if join.causes_fan_out else "safe"
        print(f"    {join.name:<12} {join.type:<14} {marker}")
        if join.description:
            print(f"      {join.description}")
    print()
"""),
        md("""
Note the wording of the fan-out join's description:

> One customer has many orders. Traversing this fan-outs the order lines —
> and therefore the revenue — unless the measure is a distinct count.

That is not decoration. It is the warning, and it appears in the UI wherever
the join appears. In LookML it is the `description:` on the join; in dbt it
is the `description` on the relationship.

## 6. Unresolved foreign keys

A related failure that produces a *right total with a wrong breakdown*: a
fact row whose foreign key does not resolve. In a left join it gets a blank
label — and the row still counts towards the total.

This course's sample data has one, deliberately.
"""),
        code("""
known = {c["customer_id"] for c in customers}
unresolved = [r for r in orders if r["customer_id"] not in known]
print(f"order lines with an unresolved customer_id : {len(unresolved)}")
for row in unresolved[:5]:
    print(f"  line_id={row['line_id']}  customer_id={row['customer_id']}  "
          f"amount={row['total_amount']}")
"""),
        md("""
The total is correct. The breakdown by customer is wrong — those rows land
in a blank bucket. That combination is worse than either being wrong alone,
because nobody checks the parts when the whole looks right.

## Takeaways

1. Fan-out happens when you traverse **from the "one" side to the "many"
   side**. `orders → customers` is safe; `customers → orders` is not.
2. A join can be cardinality-safe and still wrong — that is **grain
   mismatch**, and it is the more common bug.
3. Duplicate the fact table to *see* a fan-out. The number changes and
   nothing errors.
4. The fan-out check — compare the measure before and after the join —
   belongs in CI.
5. Put the fan-out warning in the **join's own description**, so it travels
   with the join into every tool.
6. An unresolved foreign key gives you a right total and a wrong breakdown.
   Watch for the blank label.
"""),
    ])
