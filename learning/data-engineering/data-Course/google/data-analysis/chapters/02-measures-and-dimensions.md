# Chapter 02 — Measures, Dimensions and the Additivity Problem

> **Module 1.2** · ~50 minutes · No cloud account required

---

## 🎯 What you will learn

- The three aggregations that behave differently: **additive**, **non-additive**
  and **ratio** — and how to tell which one you have.
- Why `count` and `count_distinct` are not the same measure, and why the
  difference is the difference between "orders" and "order lines".
- The **ratio problem**: why averaging an average is not the average, and how
  to compute a conversion rate correctly.
- How **filtering a measure** works, and why a filtered ratio is even harder.
- How Looker Studio, Looker and dbt each solve the ratio problem — and what
  Looker Studio does *not* solve for you.

---

## 🧠 Concept

### Three kinds of number

Almost every number on a dashboard is one of three kinds, and the three kinds
combine differently.

**Additive.** Sum them and you get the total.

```
EMEA revenue  £299,367
AMER revenue  £281,438
─────────────────────────
Total revenue £580,805    ← correct
```

Revenue, quantity, cost, the number of line items on an invoice — all
additive. This works because every pound belongs to exactly one region.

**Non-additive.** Summing them gives a number that looks right and is not.

```
EMEA order count   241
AMER order count   221
────────────────────────
Total order count  462    ← WRONG (there are 450 orders)
```

The count of *orders* in EMEA is 241 order **lines** in EMEA, because the
model's grain is the line. Summing counts across regions is only correct if
every order belongs to exactly one region — which is true here, but is an
accident of the data, not a property of the count.

`count_distinct` is not additive either, for a different reason:

```
EMEA distinct customers  180
AMER distinct customers  165
──────────────────────────────
Sum                     345    ← WRONG (there are 120 customers)
```

A customer can buy in EMEA and in AMER. Counting them in both regions and
adding gives 345, but there are only 120 customers. The number 345 is not
merely imprecise — it is larger than the population, which is a strong signal
that the measure is being used wrongly.

**Ratio.** Two things divided by each other, where the denominator is a
different aggregation.

```
gross margin = margin_amount / total_amount
```

A ratio is not additive, and it is not the average of the underlying ratios
either. Both of those mistakes produce numbers that are plausible and wrong.

### The additivity property

The semantic layer declares which kind a measure is. In the course's model:

```python
from model import Measure, SUM, SUM_TYPE, COUNT, COUNT_TYPE, RATIO_TYPE

revenue = Measure(
    name="total_revenue", label="Total Revenue",
    type=SUM_TYPE, aggregation=SUM, expression="total_amount",
)
orders = Measure(
    name="order_count", label="Order Count",
    type=COUNT_TYPE, aggregation=COUNT, expression="order_id",
)
margin = Measure(
    name="gross_margin", label="Gross Margin",
    type=RATIO_TYPE, aggregation=SUM, expression="margin_amount",
    filters=("total_amount",),
)

revenue.is_additive   # True
orders.is_additive    # False
margin.is_additive    # False
```

Why is a `count` not additive, formally? Because additivity requires that
every fact contributing to a sub-total contributes to exactly one parent
total. A `count` contributes to the count of its own group, and to *no
other* group — so summing counts over a partition of the whole is fine. But
counting *distinct* things contributes to several groups at once, and
summing those counts double-counts.

The general rule:

| Measure | Additive? | Why |
|---|---|---|
| `sum` of a fact column | Yes | Each fact belongs to one group |
| `count` of rows | Yes, if the groups partition | Each row is in one group |
| `count_distinct` | **No** | A distinct value can be in several groups |
| `avg` | **No** | The average of averages is not the average |
| `min` / `max` | Yes, but only by re-aggregating | `min(min(a,b)) = min(a,b)` |
| `ratio` | **No** | Must re-aggregate numerator and denominator |

Note the subtlety on `avg`: `avg` is not additive, but it *is* recoverable.
You cannot add the averages, but you can recompute the average over the
combined set if you keep the count and the sum. That is why the good BI
tools store a `count` and a `sum` behind an average, and recompute on
roll-up.

### The ratio problem, precisely

This is the mistake that produces the most confidently wrong dashboards.

Suppose you want the **margin rate** per region, and your fact table has one
row per order line with a margin and a revenue.

**The wrong way** — average the per-row rates:

```
Row 1:  revenue 900, margin 810  →  rate 0.90
Row 2:  revenue 100, margin  10  →  rate 0.10
                                  ─────────
        average of the rates     =  0.50    ← WRONG
```

**The right way** — sum the numerators, sum the denominators, then divide:

```
        total margin  810 + 10  =  820
        total revenue 900 + 100 = 1000
        margin rate              =  0.82    ← CORRECT
```

The two differ, and **the wrong answer is biased toward small orders**. If
your table is mostly tiny orders and a few huge ones, the average-of-rates
will understate the margin badly — because the huge order's rate gets one
vote, same as the tiny order's.

Let me prove it on the course's own data:

```python
import csv
import sys
from collections import defaultdict

sys.path.insert(0, "project/core")

from model import build_sales_model, aggregate

rows = list(csv.DictReader(open("sample_data/orders.csv")))
model = build_sales_model()

# The right way.
correct = aggregate(model, rows, ["region"], ["gross_margin"])
print("correct:", sorted(r.measures["gross_margin"] for r in correct.rows))

# The wrong way.
per_row = defaultdict(list)
for row in rows:
    amount = float(row["total_amount"] or 0)
    margin = float(row["margin_amount"] or 0)
    if amount:
        per_row[row["region"]].append(margin / amount)
print("wrong:  ", sorted(round(sum(v) / len(v), 4) for v in per_row.values()))
```

```
correct: [0.4987, 0.5029, 0.5226, 0.5245]
wrong:   [0.4711, 0.4717, 0.4908, 0.4918]
```

Every region's margin is understated by 2–3 percentage points. The chart
still looks like a chart.

**How the tools solve it.** Looker declares `type: ratio` on the measure and
knows to aggregate numerator and denominator separately:

```lookml
measure: gross_margin {
  label: "Gross Margin"
  type: ratio
  sql: ${margin_amount} / nullif(${total_amount}, 0)
  filters:
    dimensions:
      - include_all: true
}
```

Looker Studio **has no `ratio` type**. When you create a metric with a
calculated field like `SUM(margin) / SUM(revenue)`, Looker Studio evaluates
that expression *after* aggregating — which gives the right answer, and only
because you wrote the aggregation inside the expression rather than using the
UI's "Average" aggregation.

The trap in Looker Studio is a metric with the **Average** aggregation over a
ratio column:

```
Average of (margin_amount / total_amount)   ← the wrong way
```

The fix, in Looker Studio's own language, is a **calculated field**:

```
SUM(margin_amount) / SUM(total_amount)
```

with the null-safe `NULLIF` on the denominator. This is worth knowing before
you build a dashboard in Looker Studio, because the UI will not stop you.

### Filters on a measure

A measure can carry a filter — "count only orders where `status` is
'delivered'".

```python
Measure(
    name="gross_margin",
    label="Gross Margin",
    type=RATIO_TYPE,
    aggregation=SUM,
    expression="margin_amount",
    filters=("total_amount",),
)
```

In this course's model, a ratio measure's `filters[0]` is its **denominator
expression** — the thing being divided into. That is a small simplification,
but it makes the semantics explicit and testable:

```python
from model import _compute_ratio  # the implementation
```

The general rule for a filtered measure is the same as for a ratio:

* the filter is applied **before** aggregation, at the fact level;
* the same filter must be applied to numerator and denominator;
* a ratio with a filtered denominator and an unfiltered numerator is not a
  ratio — it is a rate with an arbitrary scale.

### The dimension type

A dimension's type decides how the tool sorts it and what it offers you.

| Type | Example | Notes |
|---|---|---|
| `string` | region, channel | Sorts alphabetically by default |
| `number` | customer_id | Sorts numerically — `2` before `10` |
| `time` | created_at | Carries timeframes; sorts chronologically |
| `boolean` | is_returned | Two buckets, usually filtered not charted |

The `number` type is not a detail. A customer ID stored as a string sorts as
`1, 10, 100, 2` — which looks like a bug and is not. Declaring it a number
fixes the sort.

---

## 🛠️ Hands-On: Proving Additivity

### The core experiment

```bash
cd data-engineering/data-Course/google/data-analysis
python resources/sample_data.py --output-dir ./sample_data
```

```python
import csv
import sys

sys.path.insert(0, "project/core")

from model import build_sales_model, aggregate

rows = list(csv.DictReader(open("sample_data/orders.csv")))
model = build_sales_model()

# Measure at the fine grain.
fine = aggregate(model, rows, ["region"], measures=[
    "total_revenue", "order_count", "distinct_orders", "gross_margin",
])
print("--- by region ---")
for row in fine.to_dicts():
    print(row)

# Measure at the coarse grain.
coarse = aggregate(model, rows, [], measures=[
    "total_revenue", "order_count", "distinct_orders", "gross_margin",
])
print("\n--- total ---")
print(coarse.to_dicts()[0])
```

```
--- by region ---
{'region': 'AMER', 'total_revenue': 281438.1, 'order_count': 221, 'distinct_orders': 191, 'gross_margin': 0.5029}
{'region': 'APAC', 'total_revenue': 281238.51, 'order_count': 217, 'distinct_orders': 193, 'gross_margin': 0.5245}
{'region': 'EMEA', 'total_revenue': 299367.27, 'order_count': 241, 'distinct_orders': 219, 'gross_margin': 0.5226}
{'region': 'LATAM', 'total_revenue': 266897.49, 'order_count': 222, 'distinct_orders': 196, 'gross_margin': 0.4987}

--- total ---
{'total_revenue': 1128941.37, 'order_count': 901, 'distinct_orders': 450, 'gross_margin': 0.5125}
```

Now check additivity by hand:

```
total_revenue:      281438.10 + 281238.51 + 299367.27 + 266897.49 = 1128941.37  ✓
order_count:              221 +         217 +         241 +         222 =         901  ✓
distinct_orders:          191 +         193 +         219 +         196 =         799  ✗
gross_margin:            0.5029 + 0.5245 + 0.5226 + 0.4987 = 2.0487 ≠ 0.5125     ✗
```

Three findings:

1. **`total_revenue` is additive.** The parts sum to the whole.
2. **`order_count` happens to be additive here** — because each order line is
   in exactly one region. It is additive *by accident*, and the
   `is_additive` property says `False` because the property describes the
   measure, not this particular dataset.
3. **`distinct_orders` is not additive.** 799 ≠ 450. The difference is
   orders that span more than one region.
4. **`gross_margin` is not additive.** 2.0487 ≠ 0.5125. The coarse number
   (0.5125) is the *correct* margin rate. The sum of the four regional rates
   is a meaningless number.

That last one is the one people ship. A dashboard with a stacked area chart
whose values sum to 2.05 and an axis labelled "margin rate" looks fine.

### Additivity as a test

You can make this a unit test, and you should:

```python
def test_revenue_is_additive_across_regions():
    """Revenue summed across regions equals the total."""
    model = build_sales_model()
    rows = load_rows()

    fine = aggregate(model, rows, ["region"], ["total_revenue"])
    coarse = aggregate(model, rows, [], ["total_revenue"])

    summed = sum(r.measures["total_revenue"] for r in fine.rows)
    total = coarse.rows[0].measures["total_revenue"]

    assert summed == total


def test_distinct_orders_is_not_additive_across_regions():
    """Distinct orders summed across regions exceeds the total.

    This test asserts that the measure is NOT additive. That is a
    positive test of a negative property — it documents the trap.
    """
    model = build_sales_model()
    rows = load_rows()

    fine = aggregate(model, rows, ["region"], ["distinct_orders"])
    coarse = aggregate(model, rows, [], ["distinct_orders"])

    summed = sum(r.measures["distinct_orders"] for r in fine.rows)
    total = coarse.rows[0].measures["distinct_orders"]

    assert summed > total
```

The second test is the interesting one. A test that asserts a number *is
wrong* is a specification. When someone later changes the data so that
distinct orders *become* additive (because every customer now belongs to
exactly one region), the test fails and tells you to update the model.

### The LookML side

The same measure in LookML, with the type that makes the tool behave:

```lookml
measure: total_revenue {
  label: "Total Revenue"
  type: sum
  sql: ${total_amount}
  description: "Sum of order line revenue. Additive."
}

measure: order_count {
  label: "Order Count"
  type: count
  sql: ${order_id}
  description: "Number of order LINES. Use distinct_orders to count orders."
}

measure: distinct_orders {
  label: "Distinct Orders"
  type: count_distinct
  sql: ${order_id}
  description: "Number of unique orders. NOT additive across regions."
}

measure: gross_margin {
  label: "Gross Margin"
  type: ratio
  sql: ${margin_amount} / nullif(${total_amount}, 0)
  description: "Margin over revenue. NOT the average of per-row margins."
}
```

Note the `nullif`. A division by zero in BigQuery returns an error, and a
chart with one broken row fails to render. `nullif(x, 0)` turns it into a
`NULL`, which charts as a gap.

Render it and compare:

```bash
python project/local_bi.py lookml --with-explores | head -40
```

---

## 🛠️ Common Errors and Fixes

### "The average is wrong on the drill-down"

An `avg` measure is not additive, so a rolled-up average is only correct if
the tool recomputed it. Some tools — and hand-written SQL — compute
`AVG(region_average)`, which is the average of averages.

**The fix:** always compute `SUM(x) / COUNT(x)` (or `SUM(x) / NULLIF(COUNT(x), 0)`),
never `AVG` of a pre-aggregated average.

```sql
-- Wrong
SELECT region, AVG(region_avg) FROM (SELECT region, AVG(total_amount) AS region_avg ...) GROUP BY region;

-- Right
SELECT region, SUM(total_amount) / NULLIF(COUNT(*), 0) FROM orders GROUP BY region;
```

### "My conversion rate is 3% but the ads team says 5%"

The classic ratio mismatch. Three causes, in order of likelihood:

1. **The denominator is filtered but the numerator is not.** If the numerator
   counts all sessions and the denominator counts sessions from paid traffic
   only, you get a rate above 1, not below. If the reverse, you get a rate
   that is too *high* — wait, no: a numerator over a larger denominator is
   lower. Check which side is filtered.
2. **One of you is averaging the per-event rate.** Proved above; it biases
   low.
3. **They count a "conversion" as any purchase, and you count it as a
   *paid* purchase.** A definitional difference, not a bug.

### "The count on the dashboard is higher than the count in the database"

Almost always one of:

- the dashboard counts **rows** and the database counts **distinct values**;
- the dashboard counts **after a join that fanned out** (Chapter 03);
- the dashboard's filter includes rows the database's query excludes.

### "My percentage change shows `Infinity`"

The previous period was zero. A percentage change from zero is undefined.
Return `NULL` and chart it as a gap:

```sql
CASE
    WHEN previous_value = 0 OR previous_value IS NULL THEN NULL
    ELSE (current_value - previous_value) / previous_value
END
```

The course's `period_over_period` does exactly this:

```python
from date_helpers import period_over_period

period_over_period(125, 100)   # 0.25
period_over_period(100, 0)     # None — undefined, not infinite
```

### "My `count_distinct` is slower than a `count`"

It is — it has to deduplicate. In BigQuery, `APPROX_COUNT_DISTINCT` is
dramatically faster and usually accurate enough:

```sql
SELECT region, APPROX_COUNT_DISTINCT(order_id) AS orders FROM orders GROUP BY region;
```

The trade-off is that it is approximate. For a dashboard tile that says
"1.2M orders", approximate is fine. For a finance reconciliation, it is not.

---

## 💡 Production Notes

### Name the measure after the grain it counts

`order_count` is ambiguous. `order_line_count` is not. The naming convention
costs nothing and eliminates the most common source of dashboard
disagreement:

| Instead of | Say |
|---|---|
| `count` | `order_line_count` |
| `revenue` | `gross_revenue_usd` |
| `margin` | `gross_margin_pct` |
| `aov` | `avg_revenue_per_order_line` |

If the name says "per order line", nobody can misread it.

### Store the denominator, not the rate

If you store a computed rate column in your warehouse, you have baked in a
grain decision and you cannot change it. Store the numerator and the
denominator as separate columns, and compute the rate in the semantic layer.

This is the difference between a table that can answer new questions and one
that answers exactly the question you thought of when you built it.

### Make the ratio's denominator explicit in the description

```python
description=(
    "Margin over revenue. The denominator is total_amount — the SUM of "
    "both, never the average of per-row margins."
)
```

One sentence. It is the difference between a correct margin rate and one
that is 3 points low and nobody can explain why.

### The reconciliation query is the safety net

The `sql/reconciliation.sql` file in this course compares values, not
counts. Its third query is the fan-out check, and its fifth is the freshness
check. Run both nightly. They take seconds and they catch the two problems
that make a dashboard quietly wrong.

### Version your semantic layer like code

The semantic layer *is* code. It should be in version control, it should be
reviewed, and it should have tests. A measure that changed without a review
is a measure that changed the number on somebody's slide.

---

## 🔑 Key Takeaways

1. **Three kinds of number: additive, non-additive, ratio.** Most dashboard
   disputes are a disagreement about which kind a number is.
2. **`count` and `count_distinct` are different measures.** One counts rows;
   the other counts distinct things. The labels must say which.
3. **A ratio is never the average of the underlying ratios.** Sum the
   numerator, sum the denominator, then divide. The error biases low.
4. **Looker Studio has no `ratio` type.** Use a calculated field with
   `SUM(...) / SUM(...)`, and `NULLIF` on the denominator.
5. **`avg` is not additive but is recoverable** — compute it as
   `SUM(x) / COUNT(x)`, never as the average of an average.
6. **A percentage change from zero is undefined**, not infinite. Return
   `NULL`.
7. **Test additivity.** A test that asserts a number is *not* additive is a
   specification of the trap.

---

## 📚 Practice Exercises

1. Write a test that asserts `total_revenue` is additive across `region` and
   that `gross_margin` is not. Make the assertions fail if someone changes
   the model.

2. Add a `conversion_rate` measure to a new `sessions` model: a numerator of
   `converted` and a denominator of `sessions`. Compute it as a ratio and
   write the description that says why it is not the average of per-row
   rates.

3. Build the exact same ratio the wrong way in plain Python — averaging the
   per-row rates — and find a grouping where the two answers differ by more
   than 5 percentage points. Then explain why the error is larger when the
   group has a few large rows and many small ones.

4. Add a `net_revenue` measure that subtracts a `discount_amount` column, and
   a `discount_rate` ratio measure over it. Prove the discount rate is not
   the average of per-row discount rates.

5. Change `average_order_value` from an `avg` aggregation to a `sum` over
   `total_amount` divided by `count_distinct` of `order_id`. Which is
   correct — and what is the difference between them on this dataset?

6. Write the LookML for a ratio measure with a filtered denominator, and
   explain in a comment why the numerator must carry the same filter.

---

## 📖 Further Reading

- **LookML reference** — *Measure types*, *Filters*, *Ratio measures*.
  Google Cloud, `cloud.google.com/looker/docs/reference/lookml`.
- **Looker Studio** — *Metrics*, *Calculated fields*, *Data blending*.
  `cloud.google.com/looker/docs/studio`.
- **dbt Metrics** — the `numerator`/`denominator` model of a metric, and why
  the denominator must be a metric of its own. `docs.getdbt.com`.
- **"Are You Sure You Want to Average That?"** — the aggregation pitfalls,
  in the language of dashboards rather than statistics. A widely circulated
  piece that makes the same argument as this chapter with fewer equations.
- **Kimball & Ross, *The Data Warehouse Toolkit*** (3rd ed., 2013) — the
  treatment of "non-additive facts" and how a conformed dimension handles
  them.
- **The BigQuery docs on `APPROX_COUNT_DISTINCT`** — the accuracy and cost
  trade-off. `cloud.google.com/bigquery/docs/reference/standard-sql/aggregate_functions`.
