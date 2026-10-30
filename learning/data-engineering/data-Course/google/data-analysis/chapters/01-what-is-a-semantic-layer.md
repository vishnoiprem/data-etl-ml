# Chapter 01 — What Is a Semantic Layer?

> **Module 1.1** · ~45 minutes · No cloud account required

---

## 🎯 What you will learn

- Why a BI tool is not a chart builder — it is a **semantic layer** with a chart
  builder attached.
- The three things every semantic layer has: **measures**, **dimensions** and
  **joins** — and why each one has a *type* that matters.
- The **grain**: the single sentence that says what one row of a table
  represents, and why almost every wrong number in BI is a grain mistake.
- How Looker Studio, Looker and dbt implement the *same* ideas behind different
  interfaces.
- Why your `SELECT SUM(revenue)` and the dashboard's "Total Revenue" can
  disagree — and which one is right.

---

## 🧠 Concept

### The tool is not the point

Open Looker Studio for the first time and you are greeted with three panels:
a data source on the left, a chart in the middle, and a settings pane on the
right. It looks like a chart builder.

It is not a chart builder. It is a **semantic layer** with a chart builder
attached, and the semantic layer is where every interesting decision lives.
The chart is the last five minutes of the work.

Here is the distinction that matters. Consider two reports that both show
"Revenue by Region":

| | Report A | Report B |
|---|---|---|
| Source | `orders` joined to `customers` | `orders` joined to `customers` |
| Filter | none | `status != 'cancelled'` |
| Rows | 100,000 | 100,000 |
| Revenue | **£4,812,904** | **£4,106,221** |

Both are "revenue by region". Both are drawn by the same tool. They disagree
because the semantic layer underneath them made different decisions. **The
chart is not where the disagreement lives.** The chart is downstream of it.

The questions you must answer before you draw anything are:

1. **What does one row of this table represent?** (the grain)
2. **How do I add up the numbers?** (the measure, and its type)
3. **What do I group by?** (the dimension)
4. **When I join, does the row count change?** (the join's cardinality)

Every BI tool answers these four questions for you — which is why they are
worth understanding.

### The four objects

#### The model

A **model** is a table plus a description of what that table means. The
description is not documentation. It is the thing that stops the next person
from asking what the numbers mean.

```python
from model import Model

orders = Model(
    name="orders",
    label="Orders",
    table="analytics.orders",
    description="One row per order line.",
    grain="one row per order line",
    primary_key="line_id",
)
```

The `grain` field is the important one. "One row per order line" and "one row
per order" are different grains, and a query that mixes them produces a
number that is wrong in a way nobody can see.

#### The measure

A **measure** is an aggregation with a *type*. The type is what tells the tool
whether the result can be added up again.

```python
from model import Measure, SUM, SUM_TYPE, COUNT, COUNT_TYPE

revenue = Measure(
    name="total_revenue",
    label="Total Revenue",
    type=SUM_TYPE,
    aggregation=SUM,
    expression="total_amount",
)

orders_measure = Measure(
    name="order_count",
    label="Order Count",
    type=COUNT_TYPE,
    aggregation=COUNT,
    expression="order_id",
)
```

Notice the second one. `total_revenue` is additive: sum the EMEA number and
the AMER number and you get the total, because every pound of revenue belongs
to exactly one region.

`order_count` is **not** additive. The count of orders in EMEA is 12,000 and
in AMER is 9,000, and their sum is 21,000 — but only because every order
happens to be in exactly one region. Change the grain so that an order can
appear under two regions (say, because a customer changed region mid-year),
and the sum of the counts is no longer the count.

```python
revenue.is_additive     # True
orders_measure.is_additive  # False
```

This distinction is the reason a BI tool asks you to declare a measure's type.
The tool uses it to decide whether it can roll a number up into a parent
chart, and whether it should warn you when you try.

#### The dimension

A **dimension** is a grouping key.

```python
from model import Dimension

region = Dimension(
    name="region",
    label="Region",
    type="string",
    expression="region",
)

created_at = Dimension(
    name="created_at",
    label="Order Date",
    type="time",
    expression="created_at",
    timeframe=("raw", "day", "week", "month", "quarter", "year"),
)
```

Time dimensions carry a **timeframe**: the granularities the tool offers when
you drop them into a chart. Drag `created_at` into a chart and pick "Month",
and every row in March becomes 1 March — the rows collapse into buckets. That
collapse is what a date *granularity* is.

#### The join

A **join** connects two models, and its **cardinality** is the thing that
changes numbers.

```python
from model import Join, MANY_TO_ONE, ONE_TO_MANY

safe = Join(
    name="customers",
    from_model="orders",
    to_model="customers",
    type=MANY_TO_ONE,
    foreign_key="customer_id",
    primary_key="customer_id",
)

dangerous = Join(
    name="orders",
    from_model="customers",
    to_model="orders",
    type=ONE_TO_MANY,
    foreign_key="customer_id",
    primary_key="customer_id",
)

safe.causes_fan_out    # False
dangerous.causes_fan_out  # True
```

A `many_to_one` join **adds columns without adding rows**. A `one_to_many`
join **multiplies rows**, and every additive measure on the far side is
inflated by the same factor.

That is the whole story. Chapter 03 spends an entire chapter on it because it
is the single most expensive mistake in BI.

### The explore

An **explore** is a named path through the model graph. It is what a report
author picks from the dropdown.

```python
from model import Explore, build_explores

explores = {e.name: e for e in build_explores()}
explores["orders"].base_model        # 'orders'
explores["customers"].fan_out_joins  # [<Join orders one_to_many>]
```

An explore fixes the base model and the joins that are available from it. It
is the contract between the person who built the model and the person who
builds the report.

### The same ideas, three tools

| | Looker Studio | Looker | dbt |
|---|---|---|---|
| The model | a data source | a `view` in LookML | a `model` |
| The measure | a metric | a `measure` | a metric (in the semantic layer) |
| The dimension | a dimension | a `dimension` | a dimension |
| The join | a join + relationship | a `join` + `relationship` | a `relationship` in `schema.yml` |
| The grain | implied by the data source | the `sql:` and the docs | `config.materialized` and the docs |
| Timeframes | the date grain dropdown | `timeframe:` | a macro |
| Type safety | none — you write the SQL | `type: count` | none — you write the SQL |

Looker Studio has no `type: count` and no `relationship: many_to_one` field.
That is not because Looker Studio is worse. It is because Looker Studio is a
**consumer** of a semantic layer, and the layer it consumes was built
somewhere else — by a data engineer, in LookML, in Looker, or in a
transform tool.

**This is the thing to take away from the course.** If you only ever use
Looker Studio's UI, you will learn to live around its missing type system. If
you understand the semantic layer itself, you can build one — and then the UI
becomes a front end to your work rather than a set of boxes to fill in.

---

## 🛠️ Hands-On: The Semantic Layer, Running

The course ships a semantic layer in pure Python, with no dependencies and no
cloud account. It is in `project/core/model.py`.

```bash
cd data-engineering/data-Course/google/data-analysis
python resources/sample_data.py --output-dir ./sample_data
python project/local_bi.py describe
```

```
Model: orders
  label        : Orders
  table        : analytics.orders
  grain        : one row per order line
  primary key  : line_id
  description  : One row per order line. Note the grain: a single order with three lines appears three times.

  Measures:
    total_revenue          sum            additive      Sum of order line revenue.
    order_count            count          non-additive  Number of order lines. To count orders rather than lines, use count_distinct on order_id.
    distinct_orders        count_distinct non-additive  Number of unique orders.
    average_order_value    avg            additive      Average revenue per order line.
    gross_margin           sum            non-additive  Margin over revenue.

  Dimensions:
    order_id               string
    line_id                string
    customer_id            string
    region                 string
    channel                string
    status                 string
    created_at             time          [raw, day, week, month, quarter, year]
    product_category       string
```

Read that output the way you would read a schema. The two things that matter
are on the second and fourth lines: the **grain** and the **additive column**.

### Ask a question

```bash
python project/local_bi.py query \
    --input ./sample_data/orders.csv \
    --dimensions region \
    --measures total_revenue,distinct_orders,order_count
```

```
region  total_revenue  distinct_orders  order_count
------  -------------  ---------------  -----------
AMER    281438.1       191              221
APAC    281238.51      193              217
EMEA    299367.27      219              241
LATAM  266897.49       196              222
```

Look at the last two columns. `distinct_orders` counts 219 orders in EMEA;
`order_count` counts 241 order *lines*. The difference is 22 — those are the
EMEA orders with more than one line.

**Both columns are correct.** They answer different questions. Which one you
put on the dashboard depends on what you are claiming, and the moment you put
`order_count` on a slide that says "number of orders", you have made a false
statement that nobody can detect from the chart.

### Ask the same question with the model in Python

```python
import csv
import sys

sys.path.insert(0, "project/core")

from model import build_sales_model, aggregate

rows = list(csv.DictReader(open("sample_data/orders.csv")))
model = build_sales_model()

result = aggregate(
    model,
    rows,
    dimensions=["region"],
    measures=["total_revenue", "distinct_orders"],
)

for row in result.to_dicts():
    print(row)
```

```
{'region': 'AMER', 'total_revenue': 281438.1, 'distinct_orders': 191}
{'region': 'APAC', 'total_revenue': 281238.51, 'distinct_orders': 193}
{'region': 'EMEA', 'total_revenue': 299367.27, 'distinct_orders': 219}
{'region': 'LATAM', 'total_revenue': 266897.49, 'distinct_orders': 196}
```

The CLI is a thin wrapper over this. That is deliberate: everything the tool
does is inspectable, testable, and running without a network.

---

## 🛠️ Common Errors and Fixes

### "Total revenue is £5.2M but the finance team's number is £4.9M"

Nine times out of ten this is a **filter** difference, not a bug. Check, in
this order:

1. **Does the finance number exclude cancelled orders?** A cancelled order in
   your table still has a `total_amount`. If theirs excludes it and yours does
   not, you differ by the cancelled amount — which is usually large, because
   cancelled orders are often the big ones.

2. **Is one of you counting order lines and the other counting orders?**
   `order_count` and `distinct_orders` differ on every table with multi-line
   orders.

3. **Does one of you include tax and the other not?**

4. **Is one of you using a different date range?** A "month to date" report
   compared against a closed month will differ by design.

The technique that resolves all four: ask both sides to produce the same
query and diff the rows, rather than reasoning about the definitions. This is
the `reconciliation.sql` query in `sql/`, and it is the subject of Chapter 06.

### "The chart has gaps in it"

The chart has gaps because there were **no rows** for those days. A fact table
has a row for each thing that happened; a day on which nothing happened has
no row; a chart with no row has a gap.

This is not a display bug. It is a modelling gap, and the fix is a **date
spine** — a generated table with one row per day that you join to the fact
table. Chapter 04 builds one.

```bash
python project/local_bi.py spine --input ./sample_data/orders.csv --timeframe day
```

```
  buckets           : 177
  buckets with data : 168
  empty buckets     : 9
```

### "I added a filter and the revenue went UP"

That is the fan-out, and it is the subject of Chapter 03. A filter on a
joined table changes the row count of the *base* table when the join
multiplies rows, so filtering can remove some copies of a fact row and not
others — which means the "filtered" total is a fraction of the original and
the ratio between them is meaningless.

### "Looker Studio says `Order Count` and Looker says `Order Count` and they differ"

Looker Studio's metric is `count(order_id)` — it counts order lines, because
the data source's grain is order lines. Looker's measure is
`count_distinct(${order_id})` — it counts orders. **Same label, different
number.** The label is a string; the measure is a definition.

### "My LookML will not compile: `Undefined field customers.name`"

The `{{ }}` reference points at a field nobody defined. Looker catches this at
build time, which is good — it means the mistake cannot reach a dashboard. The
course's linter catches it locally:

```bash
python resources/audit_course.py
```

---

## 💡 Production Notes

### The semantic layer is an API

Once a measure exists in a semantic layer, it is referenced by every report
that uses it. That makes it an **API with a hundred callers**, and it changes
how you change it.

The safe change is **additive**: add a new measure, leave the old one. The
unsafe change is to redefine an existing measure — even if the new definition
is "more correct". Every dashboard that used it changes its number, and
nobody is told.

If you must redefine a measure, do it in three moves:

1. Add the new measure alongside the old one.
2. Move the dashboards over, one at a time, and compare the numbers.
3. Deprecate the old one — do not delete it, because a report you cannot see
   is still a report somebody will build.

### Descriptions are not optional

A measure with no description gets a name that somebody else guesses at. The
description is the only place the *meaning* is written down, and it is the
only thing that makes the semantic layer usable by someone who was not there
when it was built.

The course's model is explicit about this:

```python
Measure(
    name="order_count",
    label="Order Count",
    type=COUNT_TYPE,
    aggregation=COUNT,
    expression="order_id",
    description=(
        "Number of order lines. To count orders rather than lines, "
        "use count_distinct on order_id."
    ),
)
```

That description tells the next person the exact thing they would otherwise
get wrong. It costs one sentence.

### Own the grain in the DDL, not in a wiki page

A primary key on the fact table is a **machine-checked** statement of the
grain. A comment in a wiki page is not:

```sql
CREATE TABLE analytics.orders (
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

The course's validation gate checks exactly this, at runtime, on the data
rather than on the schema:

```bash
python project/local_bi.py validate --input ./sample_data/orders.csv
```

```
    [ERROR  ] grain.not_unique: primary key 'line_id' is not unique: 1 value(s) repeat. Every measure over this table is inflated. (1 rows)
```

### Give every measure an owner

A measure with no owner rots. The owner is the person who answers "why does
this number say that?" when a director asks in a meeting. In LookML this is a
`description` with a name in it; in Looker Studio it is a note on the metric;
in practice it is a line in a spreadsheet.

### The test that catches everything

The single highest-value test in a BI codebase is the **fan-out check** —
compare the fact table's own total against the joined total. If they differ,
a join is fanning out.

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
    CASE WHEN joined.revenue = standalone.revenue
         THEN 'OK' ELSE 'FAN-OUT' END AS verdict
FROM standalone, joined;
```

Run it in CI. It takes four seconds and it catches the mistake that costs
quarters.

---

## 🔑 Key Takeaways

1. **A BI tool is a semantic layer with a chart builder attached.** The
   interesting decisions are all upstream of the chart.
2. **A measure is an aggregation with a type.** The type is what decides
   whether the number can be added up again.
3. **Counts are not additive.** A `count` summed across a coarser grain is
   only right by accident. Use `count_distinct` when you mean "how many
   distinct things".
4. **The grain is the most important sentence about a table.** "One row per
   order line" and "one row per order" are different models.
5. **A join's cardinality decides whether it changes your numbers.** A
   `many_to_one` join adds columns. A `one_to_many` join multiplies rows.
6. **The same concepts are in Looker Studio, Looker and dbt.** Learn the
   concepts and you can use whichever tool you are handed.
7. **Descriptions are not documentation.** They are the only place the
   meaning is written down.

---

## 📚 Practice Exercises

1. Add a `net_revenue` measure to the orders model that sums
   `total_amount` minus a `discount_amount` column, with a description that
   says what it excludes. Give it a `SUM` type and an `additive` behaviour.

2. Add a `is_first_order` dimension to the customers model of type `boolean`,
   with the expression `signup_date = first_order_date`. Then write the
   `count_distinct` measure that uses it.

3. Change the orders model's grain to "one row per order" and add a
   `line_count` measure. Now write down — in a comment, in the model's
   description — what changed about every measure that referenced the table,
   and which of them are now wrong.

4. Build a model for `analytics.date_spine` with `calendar_date` as its
   primary key and `year_month` as a dimension. Then write the join from
   `orders` to `date_spine` and decide — with a sentence — whether it fans
   out.

5. Take any dashboard you have access to and find the semantic layer
   underneath it. Write down the grain of every table it uses and every
   join it makes. Then compute, by hand, one number from the dashboard and
   check it against the underlying data. This is the exercise that teaches
   the most.

6. Extend `project/core/model.py` with a `median` aggregation and a
   `p90` (90th percentile) measure. The percentile is the interesting one:
   a percentile is **not** additive, and your `is_additive` property should
   say so.

---

## 📖 Further Reading

- **Looker Studio documentation** — *Data sources*, *Data transformations*,
  and *Chart interactions*. Google Cloud, `cloud.google.com/looker/docs/studio`.
- **LookML reference** — *Views*, *Measures*, *Joins*, *Explores*,
  *Timeframes*. Google Cloud, `cloud.google.com/looker/docs/reference/lookml`.
- **dbt's semantic layer** — *Metrics*, *Semantic models*, *Entities* and
  *Relationships*. `docs.getdbt.com`.
- **"The Semantic Layer"** — the section on measures and dimensions in
  *Fundamentals of Data Engineering* by Joe Reis and Joseph H. J. Kim
  (O'Reilly, 2022). The clearest treatment of grain and the measure/dimension
  split anywhere.
- **"Data Modeling for BI"** — Ralph Kimball's *The Data Warehouse Toolkit*
  (3rd ed., 2013), chapter 10 on dimensional modelling. The grain language
  comes from here.
- **dbt's "fanning out" documentation** — `docs.getdbt.com/docs/collisions`.
  The best short explanation of the same problem in a different tool.
