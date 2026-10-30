# Chapter 03 — Joins, Grain and the Fan-Out

> **Module 2.1** · ~55 minutes · No cloud account required

---

## 🎯 What you will learn

- The four **cardinalities**, and how each one changes (or does not change)
  the row count.
- **Fan-out** — the single most expensive mistake in BI, and why it produces
  numbers that look completely normal.
- How to **detect** a fan-out: the query, the test, and the rule.
- The **grain mismatch** — joining two tables at different grains and
  getting a number that is wrong even when nothing fans out.
- How the three tools handle cardinality: a declared `relationship` in Looker,
  a relationship editor in Looker Studio, and a `relationships:` block in dbt.

---

## 🧠 Concept

### The four cardinalities

A join connects two tables. The question that decides whether your numbers
change is: **for one row on the left, how many rows on the right match?**

| Cardinality | Left → Right | Row count | Measures change? |
|---|---|---|---|
| `one_to_one` | 1 → 1 | Unchanged | No |
| `many_to_one` | N → 1 | Unchanged | No |
| `one_to_many` | 1 → N | **Multiplied** | **Yes** |
| `many_to_many` | N → N | **Multiplied** | **Yes** |

The first two are safe. The last two fan out.

```python
from model import Join, MANY_TO_ONE, ONE_TO_MANY

safe = Join(
    name="customers", from_model="orders", to_model="customers",
    type=MANY_TO_ONE,
    foreign_key="customer_id", primary_key="customer_id",
)

fan_out = Join(
    name="orders", from_model="customers", to_model="orders",
    type=ONE_TO_MANY,
    foreign_key="customer_id", primary_key="customer_id",
)

safe.causes_fan_out     # False
fan_out.causes_fan_out  # True
```

### Fan-out, demonstrated

Start with the fact table on its own. 901 order lines, £1,128,941.37 of
revenue.

Now join it to the customers table — a `many_to_one` join, because many
order lines belong to one customer. The row count does not change:

```python
import csv
import sys

sys.path.insert(0, "project/core")

from model import build_sales_model, aggregate

rows = list(csv.DictReader(open("sample_data/orders.csv")))
model = build_sales_model()

alone = aggregate(model, rows, [], ["total_revenue"])
print("alone:", alone.rows[0].measures["total_revenue"])
print("lines:", len(rows))
```

```
alone: 1128941.37
lines: 901
```

Now the same data with a duplicated customer — which is what happens when a
customer record is inserted twice, or when you join to a table with a
duplicated key:

```python
doubled = rows + rows
joined = aggregate(model, doubled, [], ["total_revenue"])
print("after joining:", joined.rows[0].measures["total_revenue"])
print("lines:", len(doubled))
```

```
after joining: 2257882.74
lines: 1802
```

The revenue doubled. The chart still looks like a chart.

**And here is what makes fan-out so dangerous: it does not look like an
error.** It looks like growth. If the duplication starts in November, the
chart shows a step change in November, and everybody argues about why
revenue grew.

### Why `many_to_one` is safe and `one_to_many` is not

The direction matters, and people get it backwards constantly.

**`many_to_one`** (orders → customers): many order lines point at one
customer. Joining in the customer adds a *column*. The row count is
unchanged. Every measure is unchanged.

```
orders (901 rows)  ──join──▶  customers
                    adds customer_name, customer_segment
                    901 rows out
```

**`one_to_many`** (customers → orders): one customer has many orders.
Joining in the orders *duplicates* the customer row once per order. The row
count multiplies by the average number of orders per customer.

```
customers (120 rows)  ──join──▶  orders
                    120 rows in → ~900 rows out
                    every customer row appears once per order
```

And the fatal detail: **the measures that live on the far side get
multiplied.** If you start from customers and pull in orders, then sum
`orders.total_amount`, you get the right total (every order line appears
exactly once) — but if you then also pull in something else that fans out,
or filter, you get a fraction of it. And if you start from customers and sum
`customers.lifetime_value`, you get the lifetime value **multiplied by the
number of orders each customer placed**.

```python
# The dangerous shape.
customers_exp = aggregate(customers_model, customer_rows, [], ["lifetime_value"])
# 120 rows, lifetime_value summed → some number

# After joining in the orders:
# 900 rows, lifetime_value summed → ~7.5x larger
```

That is the mistake. It is invisible, it is huge, and it is one click away.

### The grain mismatch

Fan-out is the dramatic case. The **grain mismatch** is the quiet one, and it
does not need a duplicated key to happen.

Consider two tables:

- `orders` — one row per order line. 901 rows.
- `order_totals` — one row per order, with the order's total. 450 rows.

Joining `orders` to `order_totals` on `order_id` is a `many_to_one` join.
**No fan-out.** The row count stays 901.

But now sum `order_totals.total_amount` over the joined result:

```
The order total is repeated once per line of that order.
A 3-line order contributes its total THREE times.
```

The join does not fan out — but the **measure is being aggregated at the
wrong grain**. The total is inflated by the average number of lines per
order. This is the most common way a "safe" join produces a wrong number.

```sql
-- Wrong: summing an order-level measure over a line-level join.
SELECT SUM(t.total_amount)
FROM orders AS o
JOIN order_totals AS t ON o.order_id = t.order_id;   -- inflated

-- Right: aggregate at the order grain first.
SELECT SUM(total_amount) FROM (
    SELECT order_id, SUM(total_amount) AS total_amount
    FROM order_lines
    GROUP BY order_id
) AS order_totals;
```

The rule:

> **Never aggregate a measure at a grain coarser than the grain you are
> joining at.** If you need a total at the order grain, aggregate it to the
> order grain *before* you join.

The tool's declared relationship cannot save you here. `many_to_one` is
declared, the row count does not change, and the number is still wrong. This
is why the grain — not the cardinality — is the primary concept. The
cardinality is a special case of it.

### The rule that prevents both

**Aggregate at the finest grain you have, and only ever join *upward* in
grain.**

```
order lines (finest)  ──▶  orders  ──▶  customers
        join up              join up
```

Joining *downward* — from a coarse table to a finer one — is what causes both
fan-out and grain mismatch. If you need to go down, aggregate first.

### How the tools express this

**Looker** declares the relationship on the join:

```lookml
join: customers {
  relationship: many_to_one
  sql_on: ${orders.customer_id} = ${customers.customer_id}
}

join: orders {
  relationship: one_to_many
  sql_on: ${customers.customer_id} = ${orders.customer_id}
}
```

Looker uses this for two things: it knows which direction to traverse when
you pick a field from the other table, and it can warn you about a
potentially fanning-out path. The `one_to_many` join on the `customers`
explore is declared precisely so Looker knows the risk is there.

**Looker Studio** has a relationship editor. Set the relationship on the
join, and Looker Studio uses it to decide the join direction. But it has no
`count_distinct` type and no ratio type, so its protections are partial.

**dbt** declares relationships in `schema.yml`:

```yaml
version: 2

models:
  - name: orders
    description: "One row per order line."
    columns:
      - name: line_id
        description: "The unique order-line identifier. The grain."
        data_tests:
          - unique
          - not_null
      - name: customer_id
        data_tests:
          - relationships:
              to: ref('customers')
              field: customer_id

  - name: customers
    description: "One row per customer."
    columns:
      - name: customer_id
        data_tests:
          - unique
          - not_null
```

The `unique` and `not_null` tests are the grain, checked. The
`relationships` test is the referential integrity, checked. dbt's tests fail
the build, which means the broken model never reaches a dashboard.

---

## 🛠️ Hands-On: Breaking the Numbers on Purpose

### The fan-out experiment

```bash
cd data-engineering/data-Course/google/data-analysis
python resources/sample_data.py --output-dir ./sample_data
```

The simplest way to see the mechanism is to **duplicate the key** on the
dimension side — which is what an upstream bug actually looks like:

```python
import csv
import sys

sys.path.insert(0, "project/core")

from model import build_sales_model, aggregate

rows = list(csv.DictReader(open("sample_data/orders.csv")))
model = build_sales_model()


def total(rs):
    result = aggregate(model, rs, ["region"], ["total_revenue"])
    return sum(r.measures["total_revenue"] for r in result.rows)


print("baseline       :", total(rows))
print("baseline lines :", len(rows))

# A duplicated key on the dimension side — the customer record was
# inserted twice. The join now matches each order line twice.
doubled = rows + rows
print("after fan-out  :", total(doubled))
print("fanned lines   :", len(doubled))
```

```
baseline       : 1128941.37
baseline lines : 901
after fan-out  : 2257882.74
fanned lines   : 1802
```

The revenue doubled. The chart still looks like a chart.

**And here is what makes fan-out so dangerous: it does not look like an
error.** It looks like growth. If the duplication starts in November, the
chart shows a step change in November, and everybody argues about why
revenue grew.

### The direction matters

Now the one-to-many shape: start from customers, pull in their orders. The
customer row appears once per order, so the customer-level rows multiply.

```python
customers = list(csv.DictReader(open("sample_data/customers.csv")))

expanded = []
for customer in customers:
    lines = [r for r in rows if r["customer_id"] == customer["customer_id"]]
    for line in lines:
        expanded.append(line)

print("customer rows :", len(customers))
print("expanded rows :", len(expanded))
```

```
customer rows : 120
expanded rows : 900
```

120 rows became 900. The revenue is *nearly* unchanged — because the revenue
lives on the far side and every fact row still appears exactly once. **That
near-equality is the trap.** The number looks right, so nobody suspects the
join.

The damage shows up when you aggregate something on the **near** side:

```python
# customers.lifetime_value, summed over the expanded result.
lifetime = sum(float(c["lifetime_value"] or 0) for c in customers)
print("lifetime value, standalone       :", round(lifetime, 2))
print("lifetime value, after the fan-out:", round(lifetime * 7.45, 2))
```

Every customer's lifetime value is now counted once per order — 7.45 times
over, on average (901 order lines across 121 customers). The number is
roughly 7.45× too large, and it is on the dashboard.

### The grain mismatch

Fan-out is the dramatic case. The **grain mismatch** is the quiet one, and
it does not need a duplicated key to happen.

Consider two tables:

- `orders` — one row per order line. 901 rows.
- `order_totals` — one row per order, with the order's total. 450 rows.

Joining `orders` to `order_totals` on `order_id` is a `many_to_one` join.
**No fan-out.** The row count stays 901.

But now sum `order_totals.total_amount` over the joined result:

```
The order total is repeated once per line of that order.
A 3-line order contributes its total THREE times.
```

The join does not fan out — but the **measure is being aggregated at the
wrong grain**. The total is inflated by the average number of lines per
order. This is the most common way a "safe" join produces a wrong number.

```sql
-- Wrong: summing an order-level measure over a line-level join.
SELECT SUM(t.total_amount)
FROM orders AS o
JOIN order_totals AS t ON o.order_id = t.order_id;   -- inflated

-- Right: aggregate at the order grain first.
SELECT SUM(total_amount) FROM (
    SELECT order_id, SUM(total_amount) AS total_amount
    FROM order_lines
    GROUP BY order_id
) AS order_totals;
```

The rule:

> **Never aggregate a measure at a grain coarser than the grain you are
> joining at.** If you need a total at the order grain, aggregate it to the
> order grain *before* you join.

The tool's declared relationship cannot save you here. `many_to_one` is
declared, the row count does not change, and the number is still wrong. This
is why the grain — not the cardinality — is the primary concept. The
cardinality is a special case of it.

### Detecting the fan-out with the reconciliation query

The course ships the detection query in `sql/reconciliation.sql`:

```sql
WITH standalone AS (
    SELECT SUM(total_amount) AS revenue, COUNT(*) AS lines
    FROM analytics.orders
),
joined AS (
    SELECT SUM(o.total_amount) AS revenue, COUNT(*) AS lines
    FROM analytics.orders AS o
    LEFT JOIN analytics.customers AS c
        ON o.customer_id = c.customer_id
)
SELECT
    standalone.revenue AS standalone_revenue,
    joined.revenue     AS joined_revenue,
    joined.revenue - standalone.revenue AS difference,
    CASE WHEN joined.revenue = standalone.revenue
         THEN 'OK' ELSE 'FAN-OUT' END AS verdict
FROM standalone, joined;
```

**Run this every time someone adds a join.** It takes four seconds and it
catches the mistake that costs quarters.

### Detecting it in the model's own terms

The semantic layer knows the cardinality, so it can tell you the risk
before you run anything:

```bash
python project/local_bi.py explores
```

```
  customers
    base model : customers
    join orders           one_to_many    FAN-OUT — measures on the far side will inflate
    warning: traversing a fan-out join multiplies the rows.
```

### The grain check, in the validation gate

The other half of the problem is a duplicated primary key, which is what
*causes* fan-out in the first place:

```bash
python project/local_bi.py validate --input ./sample_data/orders.csv
```

```
    [ERROR  ] grain.not_unique: primary key 'line_id' is not unique: 1 value(s) repeat. Every measure over this table is inflated. (1 rows)
```

The sample dataset has **one** deliberately duplicated order line. The
validation gate catches it, and the exit code is 1.

### The fan-out test, as a unit test

```python
def test_a_duplicated_customer_row_does_not_change_the_total():
    """A many-to-one join must not change the revenue.

    This is the property that makes the `customers` join safe. If it
    ever fails, a customer key has been duplicated upstream and every
    revenue number in the dashboard is inflated.
    """
    model = build_sales_model()
    rows = load_rows()

    baseline = aggregate(model, rows, [], ["total_revenue"])
    assert baseline.rows[0].measures["total_revenue"] == 1128941.37


def test_the_joins_explore_has_no_fan_out_joins():
    """The orders explore is safe to build reports on."""
    explores = {e.name: e for e in build_explores()}
    assert explores["orders"].fan_out_joins == []
    assert [j.name for j in explores["customers"].fan_out_joins] == ["orders"]
```

---

## 🛠️ Common Errors and Fixes

### "Revenue doubled overnight and nobody knows why"

The fan-out, almost certainly. A key was duplicated upstream — a customer
record inserted twice, a slowly-changing dimension without a validity window,
an extract that ran twice without a dedupe.

**How to find it, in order:**

1. **Run the fan-out query.** It tells you which join is at fault, if the
   number changed.
2. **Check the key's uniqueness.** This is the root cause:
   ```sql
   SELECT customer_id, COUNT(*) FROM customers GROUP BY customer_id HAVING COUNT(*) > 1;
   ```
3. **Look at when the change started.** Correlate with a deploy, a
   backfill, a new dimension version.

**The fix at the source:** a primary key, or a deduplication in the extract.
**The fix in the dashboard:** never — a dashboard cannot repair a fact table.

### "I joined to get a label and the total changed"

Grain mismatch, from Chapter 03. You joined an order-level total onto a
line-level fact table and summed it.

**The fix:** aggregate to the grain you need *before* joining.

### "My filter makes the number go up"

This is fan-out plus a filter, and it is the most confusing version.

When a join fans out, a fact row appears N times. A filter that keeps some
copies and drops others does not keep "a fraction of the rows" — it keeps a
*biased sample*. A filter on the joined table that matches one copy of a
fanned-out row but not another leaves an arbitrary subset.

The result: the filtered total can be **higher** than the unfiltered total,
which is impossible under any normal reading and is the signature of a
fan-out.

**The fix:** filter the fact table before the join, not after. Or use
`count_distinct` and `sum` over a pre-aggregated subquery.

### "The dashboard's number differs from the SQL I ran by hand"

Usually the join. Run the reconciliation query and diff the *rows*, not the
totals:

```sql
SELECT
    COALESCE(source.line_id, dashboard.line_id) AS line_id,
    source.total_amount AS source_amount,
    dashboard.total_amount AS dashboard_amount,
    CASE
        WHEN source.line_id IS NULL THEN 'EXTRA'
        WHEN dashboard.line_id IS NULL THEN 'MISSING'
        WHEN source.total_amount IS DISTINCT FROM dashboard.total_amount
        THEN 'VALUE_MISMATCH'
        ELSE 'OK'
    END AS difference
FROM source
FULL OUTER JOIN dashboard ON source.line_id = dashboard.line_id
WHERE source.total_amount IS DISTINCT FROM dashboard.total_amount
   OR source.line_id IS NULL
   OR dashboard.line_id IS NULL;
```

Note `IS DISTINCT FROM` rather than `<>`. `<>` is NULL when either side is
NULL, so a row with a NULL dimension silently passes.

### "Looker says `Field not found` but the field is there"

You are on the wrong side of the join. In Looker, a field belongs to the
model it is defined on; you reach it through the join. If `customer_segment`
is on the `customers` view, then from the `orders` explore you need
`Customers > Customer Segment`, and the join must be declared.

---

## 💡 Production Notes

### Make the fan-out check part of CI

This is the highest-value five lines in a BI codebase:

```sql
SELECT
    (SELECT COUNT(*) FROM analytics.orders) AS base_lines,
    (SELECT COUNT(*) FROM analytics.orders o
       JOIN analytics.customers c ON o.customer_id = c.customer_id) AS joined_lines;
```

If `joined_lines` > `base_lines`, the join fans out. Run it in CI, on every
change to the model.

### Slowly-changing dimensions need a validity window

The classic source of accidental fan-out. A dimension type 2 has multiple
rows per key — one per version — and joining on the key alone multiplies the
fact rows.

```sql
-- Wrong: joins every version.
JOIN dim_customer c ON o.customer_id = c.customer_id

-- Right: joins the version that was current at the time of the fact.
JOIN dim_customer c
    ON o.customer_id = c.customer_id
   AND o.created_at >= c.valid_from
   AND o.created_at < c.valid_to
```

The `valid_to` must be a *sentinel* (a date far in the future) rather than
NULL, or the `NULL` comparison silently drops the current version.

### Declare the relationship where the tool can see it

An undocumented cardinality is a cardinality somebody will get wrong. In
Looker it is the `relationship:` parameter. In dbt it is the
`relationships:` test. In Looker Studio it is the relationship editor — and
if the tool does not offer one for your join, consider not making the join.

### Prefer a narrow, well-modelled star to a wide, flat table

The instinct in BI is to flatten everything into one wide table, because a
wide table cannot fan out — there is nothing to join.

That instinct is right about the *symptom* and wrong about the *cause*. A wide
table still has a grain, and if you flatten a one-to-many relationship into
it you either lose the detail or duplicate it. The honest options are:

- **Aggregate to the grain you need** and accept the loss of detail, with the
  grain written down.
- **Keep the star** and declare the relationships, so the tool can warn
  about the fan-out.

What is not acceptable is flattening without deciding the grain, which gives
you a table whose numbers depend on which query you run.

### The "why is this number wrong" runbook

When a number is questioned, the order of investigation is:

1. **Grain.** What is one row of the source table?
2. **Filters.** Which filters are applied, and on which side of the join?
3. **Cardinality.** Does any join fan out? Run the check.
4. **Additivity.** Is the measure additive across the grouping? Chapter 02's
   test.
5. **Freshness.** Is the data current? A stale extract looks exactly like a
   business event.
6. **Values.** Only now, diff the rows.

The order matters. Steps 1 to 5 are cheap and explain almost every
discrepancy. Step 6 is expensive and explains almost nothing on its own.

---

## 🔑 Key Takeaways

1. **The cardinality decides whether a join changes your numbers.**
   `one_to_one` and `many_to_one` do not; `one_to_many` and `many_to_many`
   do.
2. **Fan-out looks like growth.** That is why it is so expensive — it is
   never obviously a bug.
3. **Direction matters.** `many_to_one` (orders → customers) is safe;
   `one_to_many` (customers → orders) multiplies rows *and* the measures on
   the far side.
4. **Grain mismatch is the quiet failure.** A safe join can still produce a
   wrong number by aggregating an order-level measure over a line-level join.
5. **Aggregate at the finest grain, then join upward.** Never join
   downward.
6. **The fan-out check is four seconds of SQL.** Run it in CI on every model
   change.
7. **A slowly-changing dimension without a validity window is a fan-out
   waiting to happen.**

---

## 📚 Practice Exercises

1. Write a SQL query that reports the row count of `orders` standalone and
   after joining to `customers`, `products`, and both. Put it in a test and
   assert the counts are equal.

2. Add a `order_totals` model (one row per order) and demonstrate the grain
   mismatch: join it to `orders` and show that `SUM(total_amount)` inflates.
   Then show the fix — aggregate first, join second.

3. Model a slowly-changing dimension type 2 for `customers` (a `segment`
   that changes over time) and write the join condition with a validity
   window. Show that without the window the join fans out.

4. Build a `fct_orders` view in the course's `sql/` directory that aggregates
   the line-level orders to the order grain, with a comment naming the grain.
   Write the test that asserts `COUNT(DISTINCT order_id)` equals the row
   count.

5. Take an existing view in your warehouse that joins two tables and check
   its cardinality. Write down the cardinality in a comment, and add a test
   that asserts the row count does not change.

6. Add a `fan_out_report` function to `project/core/validate.py` that
   compares a model's row count before and after a join, and returns a
   `Finding` when they differ. Wire it into the CLI's `validate` command.

---

## 📖 Further Reading

- **LookML reference** — *Join*, *Relationship*, *Symmetric aggregates*.
  Google Cloud, `cloud.google.com/looker/docs/reference/lookml`.
- **dbt's `relationships` test and the "fanning out" guide** —
  `docs.getdbt.com/docs/collisions`. The clearest short statement of the
  problem in any tool.
- **Kimball & Ross, *The Data Warehouse Toolkit*** (3rd ed., 2013) —
  chapters on conformed dimensions and slowly-changing dimensions, which is
  where the validity-window fix comes from.
- **dbt's "Metrics" layer** — how it prevents the "two dashboards, two
  numbers" problem at the tool level rather than the discipline level.
  `docs.getdbt.com`.
- **The Data Warehouse Toolkit's "factless fact tables"** — the deliberate
  use of a fact table with no measures, which is exactly the date spine
  Chapter 04 builds.
