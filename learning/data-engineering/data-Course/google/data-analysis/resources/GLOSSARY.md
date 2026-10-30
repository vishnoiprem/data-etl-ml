# Glossary

> Every term in the course, defined once. Terms are grouped by the layer they
> belong to.

---

## The semantic layer

**Semantic layer**
A shared, machine-readable definition of the metrics an organisation reports
on. Holds models, measures, dimensions and explores — and, critically, the
grain of every table. Looker's LookML and dbt's semantic layer are both
implementations of the same idea.

**Model**
A table plus what it means: its grain, its primary key and its description.
The place where the contract lives.

**Measure**
A number with an aggregation: `SUM(total_amount)`,
`COUNT_DISTINCT(order_id)`, `SUM(margin) / SUM(revenue)`. What a report
author drags onto a chart.

**Dimension**
A grouping key with a type: `string`, `number`, `time` or `boolean`. A `time`
dimension supports timeframes.

**Explore**
A starting point for a report author: a base model plus the joins available
from it, with the fan-out risk of each join made explicit.

**View**
The LookML name for a model. A LookML `view` block is one model.

**Entity**
dbt's concept for a join key. Declares a key and its role — `primary`,
`foreign` or `natural` — and the tool uses those declarations to work out
the joins, exactly as Looker uses `relationship:`.

---

## Grain

**Grain**
The answer to "one row per what?" The level of detail a table records. The
single most important property of a table, and the thing that determines its
primary key, its join cardinalities and which questions it can answer.

**Fact table**
A table at a fine grain, recording transactions or events. Usually has
measures and a surrogate or business key.

**Dimension table**
A table at a coarser grain, describing entities. Usually has descriptive
attributes and no measures.

**Factless fact table**
A table with no measures, recording the *occurrence* of something rather
than an amount. The canonical example is a **cohort table** — one row per
customer per acquisition month.

**Degenerate dimension**
A dimension that is really the fact's primary key stored as a dimension — the
order number, the invoice number. Grouping by it is much cheaper than
grouping by a surrogate key and joining back.

**Grain mismatch**
Aggregating a measure at a grain coarser than the grain you are joining at.
The rows are correct; the measure is counted at the wrong level. The
subtlest and most common of the BI errors.

---

## Additivity and aggregation

**Additive**
A measure whose parts sum to the whole: `SUM(revenue)`, `COUNT(*)` on a
fact table.

**Non-additive**
A measure that does not roll up: `COUNT_DISTINCT`, `AVG`. Summing the parts
double-counts.

**Ratio**
A measure of the form `SUM(numerator) / SUM(denominator)`. Looks additive,
is not, and must be recomputed at every grain.

**Ratio problem**
Computing a ratio as the average of per-row ratios instead of sum-over-sum.
The two weight the data differently, and the naive answer is always
**biased low**.

**Additivity**
Whether a measure can be summed over a finer breakdown and still equal the
coarser value.

**Aggregation**
The SQL function a measure uses: `sum`, `count`, `count_distinct`, `avg`,
`min`, `max`.

**Measure type**
The semantic contract about how a measure behaves: `sum`, `count`,
`count_distinct`, `average`, `ratio`. Distinct from the aggregation, and
read by downstream tools.

---

## Joins

**Join cardinality**
How many rows of one table match one row of the other: `one_to_one`,
`many_to_one`, `one_to_many`, `many_to_many`.

**Fan-out**
The row multiplication that happens when a join matches more than one row
on the far side. The most consequential BI bug, because it produces no error
— just a number that is too large and looks like growth.

**Fan-out check**
Comparing a measure computed with and without a join. If they differ, the
join changed the number.

**Relationship**
LookML's declaration of a join's cardinality. Used by the tool to rewrite
the join so it cannot fan out.

**Many-to-many join**
A join that multiplies rows on both sides. Safe only when the measures
across it are non-additive — typically distinct counts.

**Bridge table**
The intermediate table in a many-to-many join, holding one row per
combination.

**Conformed dimension**
A dimension with the same definition — same name, same values, same grain —
shared across every fact that uses it. What lets you compare across facts.

**Star schema**
A fact table with foreign keys to conformed dimensions, rather than a wide
table with repeated descriptive columns.

---

## Dates

**Date spine**
A generated table with one row per calendar day, left-joined to the facts so
that days with no activity become explicit zeros.

**Timeframe**
A truncation of a date to a reporting grain: raw, day, week, month,
quarter, year.

**ISO week**
A week starting on **Monday**, with the week number derived from the
Thursday of that week. Differs from the US convention, which starts on
Sunday.

**Date filter bounds**
The two dates a filter covers. Must be computed on the **raw** dates before
any truncation, and an inverted range must raise rather than swap.

**Fiscal calendar**
A business's own accounting calendar, which may not start in January. Best
expressed as a dimension with a validity window, not as date arithmetic.

**Period over period**
Comparing a period against the immediately preceding period of the same
length and grain. The previous *year* is 2025, not 2024 — the off-by-one
lives here.

---

## Slowly changing dimensions

**Slowly changing dimension (SCD)**
A dimension whose attributes change over time, while facts keep recording
what was true at the time.

**SCD Type 1**
Overwrite the attribute in place. History is lost; cohort analysis is
impossible.

**SCD Type 2**
Insert a new row with a new key and a validity window. History is preserved;
the dimension now has more rows than entities.

**SCD Type 3**
Add a new column for the new value. History is preserved in the column
names; the table widens with every change.

**Validity window**
The `valid_from` / `valid_to` range during which a Type 2 dimension row is
current. A join must respect it, or a customer who changed tier on the
order date matches two rows.

**Surrogate key**
An artificial unique identifier on a dimension row. Exists because Type 2
dimensions make the business key non-unique.

**Business key**
The natural identifier of an entity — the customer number, the product SKU.
Unique in Type 1 dimensions, not in Type 2.

---

## Operations

**Validation gate**
An automated set of checks that runs before a number is allowed to reach a
dashboard. Turns "we trust the data" from a habit into an enforced property.

**Grain check**
A check that two systems agree on the *level of detail*, not just the
values. The same total can come from completely different row structures.

**Reconciliation**
Comparing the dashboard's numbers against the source of truth, at the level
of individual values.

**`IS DISTINCT FROM`**
A null-safe inequality. `NULL <> NULL` is `NULL`, not `TRUE`, so a `<>`
comparison silently drops exactly the rows where the problems hide.

**MISSING / EXTRA / VALUE_MISMATCH**
The three outcomes of a reconciliation. The third is the one a row-count
comparison can never see.

**Freshness SLO**
A stated maximum age for the newest row in a model, in hours, with an owner.
Set it from the business's tolerance for being wrong, not from the pipeline's
current performance.

**Runbook**
The deliverable that keeps a semantic layer maintainable: the grain of every
table, the fan-out risk of every join, the freshness expectation for every
model, the exact queries to run when a number is questioned, and who to page.

**Query cost**
The bytes scanned by a query. Compare a dashboard's bytes against the fact
table's bytes — a large ratio means a join is multiplying work.

---

## The tools

**Looker Studio**
Google's consumer BI tool. Dashboard builder with no shared semantic layer:
every report author defines their own calculated fields, joins and filters.

**Calculated field**
A Looker Studio expression evaluated **after** aggregation. The source of
the ratio trap — always write `SUM(x) / SUM(y)`, and guard the denominator
with `NULLIF`.

**Looker**
Google's enterprise BI tool with a semantic layer. Metric definitions live
in LookML, versioned and reviewed like code.

**LookML**
Looker's modelling language. `view` blocks hold dimensions, measures and
joins; `explore` blocks name the starting points.

**`{{ }}` reference**
A field reference into another view, resolved when the model is compiled. A
reference to a non-existent field is a **build error**, not a runtime error.

**dbt**
A transformation framework. Builds and tests the tables; its semantic layer
now covers metric definitions as well.

**dbt test**
An assertion about a model — `unique`, `not_null`, `relationships`, or a
custom SQL test. The dbt equivalent of the course's grain tests.

**Metric store**
An execution engine that turns metric definitions into optimised queries —
column pruning, pre-aggregation, caching. MetricFlow and Cube are examples.
A metric store serves a semantic layer; it is not one.
