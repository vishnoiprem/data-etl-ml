# Chapter 05 — Looker Studio, Looker and dbt

> **Module 3.1** · ~55 minutes · The cloud sections are optional

---

## 🎯 What you will learn

- The **three tools and their boundaries** — Looker Studio (the consumer),
  Looker (the semantic layer), dbt (the transformation layer) — and where
  each one starts and stops.
- How to build a **Looker Studio data source**: the schema, the connection,
  the custom query, and the field types you have to set by hand.
- **Looker Studio's calculated fields** — the syntax, the aggregation traps,
  and how to write a ratio correctly when the UI has no ratio type.
- **LookML** — views, explores, measures, dimensions, joins, and the
  `lookml-validate` loop.
- **dbt's semantic layer** — models, metrics, entities and relationships,
  and how they map onto the concepts from Chapter 01.
- How to **choose**: which tool for which job, and what to build first.

---

## 🧠 Concept

### Three tools, three jobs

The most common confusion in this space is treating these as three ways to
do the same thing. They are not. They sit at different points in the stack.

```
┌──────────────────────────────────────────────────────────┐
│  CONSUMPTION      Looker Studio (the dashboard)          │
│                   Explore, Power BI, Tableau, Metabase   │
├──────────────────────────────────────────────────────────┤
│  SEMANTIC LAYER   Looker (LookML)                        │
│                   dbt Semantic Layer                     │
├──────────────────────────────────────────────────────────┤
│  TRANSFORMATION   dbt (models, tests, docs)              │
│                   Dataform, ELT scripts                  │
├──────────────────────────────────────────────────────────┤
│  STORAGE          BigQuery, Cloud SQL, Snowflake         │
└──────────────────────────────────────────────────────────┘
```

**Looker Studio** is a *consumer*. It connects to data, lets you build
charts, and it has a thin semantic layer of its own — fields, metrics,
calculated fields, and a relationship editor. It does not have a
`count_distinct` type, a ratio type, or a measure hierarchy.

**Looker** is a *semantic layer*. It has views, explores, measures with
types, joins with declared relationships, and a query builder that uses all
of it. Its unit of authorship is the LookML file.

**dbt** is a *transformation layer*. It turns raw tables into modelled
tables, runs tests on them, and publishes documentation. Its newer
**semantic layer** adds metrics, entities and relationships, which moves it
up the stack.

The practical consequence:

> If you only use Looker Studio, you are consuming someone else's semantic
> layer — or building a very thin one yourself in the UI. To build a
> *real* semantic layer, you need Looker or dbt.

### Looker Studio's data source

A Looker Studio data source is a **table plus a schema**. The schema is the
part people get wrong, because the connector infers some types and guesses
others.

Three things to check every time:

1. **The types.** A `total_amount` column that comes in as a *string* will
   concatenate instead of summing. BigQuery connectors usually get this
   right; CSV and Sheets connectors usually do not.
2. **The aggregation.** A numeric field defaults to `SUM` in some tools and
   `AVG` in others. **A revenue field with `AVG` as its default is the
   single most common Looker Studio mistake** — you drag it onto a chart and
   get the average order value on a chart labelled "Total Revenue".
3. **The grain.** Looker Studio has no grain field. The grain is whatever
   the query returns. Write it down.

### Calculated fields — the aggregation trap

A calculated field in Looker Studio is a SQL expression evaluated **after**
the base aggregation. This is the single most important thing to understand
about it.

Given a field `revenue` with a `SUM` aggregation, and a field `margin` with
a `SUM` aggregation:

```
margin / revenue          ← the fields, summed, then divided  ✓ CORRECT
SUM(margin) / SUM(revenue) ← identical, written explicitly       ✓ CORRECT
AVG(margin / revenue)      ← the ratio per row, then averaged    ✗ WRONG
```

The third one is what the UI produces if you create a metric from a
*calculated field* that is itself a division, and set the metric's
aggregation to `Average`.

**The rule:** in a calculated field, always write the aggregation explicitly
around the base fields. `SUM(margin) / SUM(revenue)`. Then the metric's own
aggregation is irrelevant, because the calculated field is already an
aggregate.

Two more details that bite:

```sql
-- Division by zero. BigQuery errors on this, and one broken row
-- fails the whole chart.
SUM(margin) / SUM(revenue)

-- The safe version.
SUM(margin) / NULLIF(SUM(revenue), 0)
```

```sql
-- The date dimension. In Looker Studio, DATE() truncates to the day
-- in UTC. If the business operates in another timezone, this is wrong.
DATE(created_at)

-- The safe version, for a Sydney business.
DATE(created_at, 'Australia/Sydney')
```

### The relationship editor

Looker Studio's relationship editor lets you declare the cardinality of a
join, and it uses that to decide the join direction and the aggregation
behaviour.

Three things it does with the relationship:

1. **Join direction.** With a `Many-to-one` relationship, the many side
   drives the aggregation. With `One-to-many`, the tool knows a fan-out is
   possible.
2. **Aggregation defaults.** With a `One-to-many` relationship, Looker
   Studio may switch an aggregation to `SUM` and add a note — because a
   `MAX` across a fan-out is meaningless.
3. **The warning.** It shows a "data blending" or "relationship" indicator
   on the chart when the join is risky.

It does **not** have a `count_distinct` type, and it does not protect you
from a grain mismatch. Those remain your responsibility.

### LookML

LookML is the language Looker uses to define its semantic layer. It is
small. The whole vocabulary is:

| LookML | What it is |
|---|---|
| `view` | A model — a table plus its fields |
| `explore` | A named starting point for querying |
| `dimension` | A grouping key |
| `measure` | An aggregation, with a type |
| `join` | A relationship, with a cardinality |
| `sql:` | The SQL that defines the view |
| `derive:` | A SQL expression over other fields |
| `timeframe:` | The date grains a time dimension supports |
| `filters:` | A measure's or dimension's filters |
| `explore` → `join:` | Which joins are available from the explore |

A minimal but complete view:

```lookml
view: orders {
  label: "Orders"
  description: "One row per order line."
  sql: "select * from analytics.orders" ;

  dimension: line_id {
    label: "Order Line ID"
    type: string
    sql: ${line_id}
    description: "The unique order-line identifier. The grain."
  }

  dimension: created_at {
    label: "Order Date"
    type: time
    sql: ${created_at}
    timeframe: [raw, day, week, month, quarter, year]
    description: "When the order was placed."
  }

  measure: total_revenue {
    label: "Total Revenue"
    type: sum
    sql: ${total_amount}
    description: "Sum of order line revenue. Additive."
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

  join: customers {
    relationship: many_to_one
    sql_on: ${orders.customer_id} = ${customers.customer_id}
    description: "Many order lines to one customer. Safe to traverse."
  }
}

explore: orders {
  label: "Orders"
  join: [customers]
}
```

Three things to notice:

1. **`type: count_distinct`** and **`type: ratio`** are the whole reason to
   use Looker rather than Looker Studio. They let the tool know that these
   measures behave differently.
2. **`relationship: many_to_one`** is declared on the join, so the tool
   knows the direction and the risk.
3. **`${field}`** is LookML's reference syntax. A typo is a **build error**,
   not a runtime error — Looker refuses to compile the model. That is the
   safety net.

The course's linter checks the same thing locally:

```bash
python resources/audit_course.py
```

### dbt's semantic layer

dbt's models, tests and documentation map onto Chapter 01's vocabulary:

| Concept | dbt |
|---|---|
| Model | A model in `models/`, materialised as a table or view |
| Grain | The `description` on the model, plus the `unique` test on its key |
| Measure | A metric in the semantic layer, or a metric in the metrics layer |
| Dimension | A column with a `description` |
| Join | A `relationships:` test, plus a `relationships:` entry in `schema.yml` |
| Type | The metric's `type: sum \| count \| count_distinct \| ratio \| average` |

```yaml
# models/schema.yml
version: 2

models:
  - name: fct_orders
    description: >
      One row per order line. The grain. Every measure over this table
      is a measure over order lines, not over orders.
    columns:
      - name: line_id
        description: "The unique order-line identifier."
        data_tests:
          - unique
          - not_null
      - name: order_id
        description: "The order identifier. NOT unique."
      - name: customer_id
        data_tests:
          - relationships:
              to: ref('dim_customers')
              field: customer_id
      - name: created_at
        data_tests:
          - not_null
```

```yaml
# models/metrics.yml
semantic_models:
  - name: orders
    model: ref('fct_orders')
    defaults:
      agg_time_dimension: created_at

    entities:
      - name: customer
        type: primary
        expr: customer_id

    dimensions:
      - name: region
        type: categorical
        expr: region
      - name: order_date
        type: time
        type_params:
          time_granularity: day

    measures:
      - name: total_revenue
        agg: sum
        expr: total_amount
      - name: distinct_orders
        agg: count_distinct
        expr: order_id
```

The `unique` and `not_null` tests are the grain, **checked**. The
`relationships` test is the referential integrity, checked. A failing test
fails the build, so a broken model never reaches a dashboard.

This is the structural advantage of dbt over a UI-built semantic layer:
**the semantic layer is version-controlled, reviewed, and tested**.

---

## 🛠️ Hands-On

### The LookML round trip

The course ships a LookML reader and writer. The Python model is the source
of truth; the LookML file is a rendering of it.

```bash
cd data-engineering/data-Course/google/data-analysis
python project/local_bi.py lookml --with-explores
```

```python
import sys

sys.path.insert(0, "project/core")

from lookml import parse_view, render_view
from model import build_sales_model

model = build_sales_model()

# Render.
text = render_view(model)
print(text[:400])

# And read it back.
view = parse_view(text)
print("\nview:", view.name)
print("dimensions:", [d.name for d in view.dimensions])
print("measures:", [m.name for m in view.measures])
```

```
view: orders {
  label: "Orders"
  description: "One row per order line. Note the grain: a single order with three lines appears three times."
  # Grain: one row per order line
  sql: "select * from analytics.orders";

  dimension: order_id {
...
view: orders
dimensions: ['order_id', 'line_id', 'customer_id', 'region', 'channel', 'status', 'created_at', 'product_category']
measures: ['total_revenue', 'order_count', 'distinct_orders', 'average_order_value', 'gross_margin']
```

### The reference checker

Looker catches a broken `{{ }}` reference at build time. The course's linter
catches it locally:

```python
import sys

sys.path.insert(0, "project/core")

from lookml import collect_available_fields, find_broken_references
from model import build_sales_model, build_customer_model

models = [build_sales_model(), build_customer_model()]
available = collect_available_fields(models)

good = 'sql: "{{ orders.order_id }}"\nsql: "{{ customers.customer_segment }}"'
bad = 'sql: "{{ orders.order_id }}"\nsql: "{{ customers.nope }}"'

print("good:", find_broken_references(good, available))
print("bad: ", find_broken_references(bad, available))
```

```
good: []
bad:  ['customers.nope']
```

### The LookML for a ratio — the part Looker Studio cannot do

```lookml
measure: gross_margin {
  label: "Gross Margin"
  type: ratio
  sql: ${margin_amount} / nullif(${total_amount}, 0)
  description: "Margin over revenue. NOT the average of per-row margins."
}
```

And the Looker Studio equivalent, which you must write yourself:

```
SUM(margin_amount) / NULLIF(SUM(total_amount), 0)
```

Note that the Looker Studio version must spell out `SUM` twice. If you leave
it as `margin_amount / total_amount`, the metric's own aggregation is applied
to the *ratio*, and you get the average-of-ratios.

### Building the Looker Studio data source

The steps, for when you do need the cloud:

1. **Connect.** Looker Studio → *Create → Data source* → *BigQuery*.
2. **Choose the project**, then the dataset, then the table.
3. **Check the field types.** `Field Type` → the numeric fields must be
   `NUMBER` (or `FLOAT`), not `TEXT`.
4. **Set the aggregation.** `Metric Type` → `Revenue` must be `SUM`.
5. **Set the default aggregation table**, if you are using a custom query.
6. **Name the data source** after its grain: `Orders (line grain)`.

That last one is a tiny act with a large payoff. When somebody later asks
"which data source should I use?", the name answers it.

### A custom query data source

When the table is not quite right, a custom query is the answer — but it
needs a grain comment, because the grain is no longer visible in the
connector:

```sql
-- Data source: Orders (line grain)
-- One row per order line. An order with three lines has three rows.
-- Every measure over this data source is a measure over order LINES.
select
    line_id,
    order_id,
    customer_id,
    product_id,
    region,
    channel,
    status,
    created_at,
    total_amount,
    margin_amount
from `your-project.analytics.orders`
```

### The Looker development loop

```bash
# Edit the LookML in your project, then validate it.
lookml-validate --project YOUR_PROJECT_ID --lookml ./lookml

# Or, in a git repo with the Looker CLI installed:
lookml-validate
```

The loop is: edit → validate → push → Looker compiles on the branch → you
preview the explore in the browser → you merge.

The compile step is where the `{{ }}` typo and the type mismatch become
errors. That is the safety net, and it is why LookML is worth learning even
if you spend your time in Looker Studio.

### A dbt test for the grain

```sql
-- tests/assert_fct_orders_grain.sql
-- The grain of fct_orders is one row per order line. If this test
-- fails, every additive measure over the table is inflated.
select
    line_id,
    count(*) as occurrences
from {{ ref('fct_orders') }}
group by line_id
having count(*) > 1
```

```bash
dbt test --select fct_orders
```

---

## 🛠️ Common Errors and Fixes

### "My revenue is the average, not the sum"

The metric's aggregation is `AVG`. Check `Field Type → Metric Type` in
Looker Studio, or `type:` in LookML.

This is the single most common Looker Studio bug, and it is silent: the
chart renders, the axis is labelled "Total Revenue", and the number is
about 1/450th of the truth.

### "My revenue field is a string and concatenates instead of summing"

The field type is `TEXT`. Set it to `NUMBER` in the data source's schema,
or cast in the custom query:

```sql
cast(total_amount as float64) as total_amount
```

### "My calculated field returns the wrong number"

Almost always one of:

- the metric's aggregation is `Average` and the calculated field is a ratio
  (Chapter 02);
- the calculated field references a field that already has an aggregation
  applied, and you have applied a second one;
- the division has no `NULLIF` and a zero row breaks the query.

**The debugging technique:** strip the calculated field back to the raw
fields and add them one at a time. `SUM(a)` first. Then `SUM(b)`. Then
combine.

### "Looker Studio says 'This field is ambiguous'"

Two fields with the same name in the joined tables. Rename in the schema
panel, or use the qualified name `Orders.Region` vs `Customers.Region`.

### "My dbt test passes but the dashboard is still wrong"

dbt tests check the **model**. The dashboard's problem might be in the
**join** it does on top of the model — which dbt does not know about.

This is the case for the fan-out query from Chapter 03. dbt cannot test a
join that lives in the BI tool.

### "LookML compiles but the measure shows `No data`"

The `sql:` expression references a field that is not in the view's base
table, or the base table has a different column name. Looker's compiler
does not check *semantic* validity, only syntactic.

**The fix:** check the query in Looker's "Explore" panel before merging.

---

## 💡 Production Notes

### Looker Studio is not a modelling tool

You *can* build a semantic layer in Looker Studio's UI. What you cannot do
is:

- version-control it meaningfully (a data source is a database object, not
  a file in a repo);
- review a change to a measure;
- test it;
- reuse it across many reports without copying.

If the semantic layer is the strategic asset — and in a mature BI
organisation it is — it belongs in LookML or dbt, where it is code.

### The "one data source per grain" rule

Do not build one Looker Studio data source called `Orders` that joins
everything. Build one per grain:

| Data source | Grain |
|---|---|
| `Orders (line grain)` | one row per order line |
| `Orders (order grain)` | one row per order |
| `Customers` | one row per customer |
| `Products` | one row per product |

Then blend them deliberately. The names make the grain visible at the point
of use, which is where the grain matters.

### The BI engineer is now a data engineer

The job title did not change but the skill set did. The work that used to be
"ask the analytics team for a report" is now "write a metric, add a test,
open a pull request". The barrier to entry to the semantic layer dropped
from "learn Looker" to "write SQL and understand the grain".

### Looker Studio's sharing model is a feature

Looker Studio's data source permissions, row-level security, and sharing
model are good. A report shared with a team sees the same numbers as a
report embedded in a slide — which is the property that makes the semantic
layer trustworthy.

### Measure the cost of a dashboard

Every dashboard costs: the query, the compute, the maintenance, and the
**trust**. A dashboard nobody trusts has negative value — it causes bad
decisions, and it costs money.

The metric worth tracking is not "how many dashboards" but "how many
questions have been asked of a dashboard whose answer was later disputed".
That number is a direct measure of semantic-layer quality.

### Keep the LookML in git, even if you do not deploy it

A LookML file in a repository is documentation that cannot go stale, because
a test can check it. The course's `project/lookml/ecommerce.model.lookml` is
generated from a model and validated by a test — that is the pattern.

---

## 🔑 Key Takeaways

1. **The three tools sit at different layers.** Looker Studio consumes,
   Looker and dbt build.
2. **Looker Studio has no `count_distinct` type and no ratio type.** You
   write `SUM(x) / SUM(y)` yourself, and you check the default aggregation
   every time.
3. **A calculated field is evaluated after aggregation.** Always spell out
   `SUM(...)` inside it.
4. **LookML's `type:` is what makes the tool behave.** `count_distinct` and
   `ratio` are the two that matter most.
5. **`relationship:` on the join is the cardinality**, declared where the
   tool can see it.
6. **A `{{ }}` typo is a build error**, not a runtime error — Looker will
   not ship it.
7. **dbt's `unique` test is the grain, checked.** A failing test fails the
   build, so a broken model never reaches a dashboard.
8. **One data source per grain**, with the grain in the name.

---

## 📚 Practice Exercises

1. Take any Looker Studio data source you have access to. Check the
   aggregation on every numeric field. Write down which ones are wrong.
   This is the single highest-yield five minutes in BI.

2. Write the Looker Studio calculated field for a conversion rate, and
   explain — in a comment — why `NULLIF` is needed and what happens without
   it.

3. Write the equivalent LookML for the same conversion rate, using
   `type: ratio`, and explain what the tool does differently.

4. Write a dbt `schema.yml` for the course's three models, with `unique`,
   `not_null` and `relationships` tests, and the grain in each model's
   `description`.

5. Build a Looker Studio data source against the course's `orders` table
   with a custom query, set the schema types correctly, and set the
   aggregation on `total_amount` to `SUM`. Then repeat it for the
   `average_order_value` metric with `AVG`, and explain why the two need
   different aggregations.

6. Add a `count_distinct` measure and a `ratio` measure to the course's
   `core/model.py`, render the LookML, and verify that the renderer emits
   `type: count_distinct` and `type: ratio` respectively.

7. Write a short "semantic layer style guide" for your team: naming
   conventions for measures, what every description must contain, which
   aggregations are forbidden by default, and how a measure is deprecated.
   It is a small document that prevents most of the disputes in this course.

---

## 📖 Further Reading

- **Looker Studio documentation** — *Data sources*, *Calculated fields*,
  *Data blending*, *Relationship settings*. Google Cloud,
  `cloud.google.com/looker/docs/studio`.
- **LookML reference** — *Views*, *Measures*, *Joins*, *Explores*,
  *Timeframes*, *Filters*. `cloud.google.com/looker/docs/reference/lookml`.
- **dbt's semantic layer** — *Semantic models*, *Metrics*, *Entities*,
  *Relationships*, and the `relationships` and `unique` generic tests.
  `docs.getdbt.com`.
- **dbt's "Learning SQL"** — `docs.getdbt.com/learn-sql`. The clearest
  introduction to the dimensional grain, and it is free.
- **"BI: The Three-Layer Stack"** — a widely read article on the
  consumption/semantic/transformation split. Search for it; the exact title
  varies.
- **Looker's "Data Modeler" learning path** — Google Cloud's own
  LookML course, free with a Google Cloud account.
