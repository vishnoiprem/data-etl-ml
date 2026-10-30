# FAQ

> The questions that come up most, answered properly.

---

## Getting started

### Do I need a GCP account to do this course?

**No.** The course's semantic layer, aggregation engine, date spine, LookML
renderer and validation gate are all **pure standard library**. The test
suite runs in about two seconds with no credentials and no bill.

The optional BigQuery deployment section is the only part that needs an
account, and the DDL is written to run there unchanged.

### Why is the semantic layer written in Python rather than LookML?

Because **LookML is nearly impossible to unit-test** — rendering it requires
the Looker application. The same logic in a plain module is testable in
milliseconds, and you can assert things about it that no UI would let you
assert:

```python
def test_distinct_orders_is_not_additive_across_regions():
    """Distinct orders summed across regions exceeds the total."""
```

That is a positive test of a negative property — it documents a trap. The
LookML is then *generated* from the Python model, so it is a rendering, not a
second source of truth.

### Do I need to know SQL?

You need to read SQL comfortably and be able to write joins and aggregations.
The course's SQL is deliberately plain — no window functions beyond what is
explained, no dialect-specific tricks except the `IS DISTINCT FROM` that
BigQuery and Postgres both support.

### How long does the course take?

The chapters are about **60 minutes each** — seven of them, so roughly seven
hours of reading. The notebooks add another three or four hours of
experimentation. The interview bank is designed for a final review pass
rather than a first read.

---

## The semantic layer

### What if two teams want the same metric to mean different things?

**Find out what each one is actually measuring, because they are usually
measuring different things and both are right.**

This is where the description earns its keep. "Revenue" might mean gross
merchandise value for one team and net of refunds for another. The
resolution is rarely "one of you is wrong" — it is usually "you want two
measures, and they should have two names". Then the disagreement becomes a
naming problem, which is solvable, instead of a data problem, which is not.

### Should every measure be in the layer, or only the important ones?

**Only the ones that get reused or that people disagree about.** A semantic
layer with 200 measures and no hierarchy is worse than a small one, because
the report author now has to choose *and* they do not know the difference.

The discipline: a measure goes in the layer when it will be used more than
once, or when its definition is contested. If it is genuinely one-off, say
so explicitly and record that it is not a governed metric.

### How do I handle a metric nobody has defined yet?

**Define it properly in the layer** if it will be used more than once. If it
is genuinely one-off, say so explicitly and record that it is not a governed
metric.

The tempting failure is to say yes quickly — it is one calculated field. The
cost is that two months later there are four implementations of "active
customer" and nobody can say which one the board was shown.

### Who owns a semantic layer?

**A named person, not a team.** The layer encodes business rules that took
months to learn, and it is the only place they are written down.

The failure mode of "owned by the data team" is that no individual is
accountable for a measure being *correct* — only for the layer being
*available*.

### When should I *not* build a semantic layer?

**When there is one report, one author, and no disagreement.** The overhead
is real.

The signal that you have outgrown it: the same metric is computed in three
places and the numbers disagree, or a report author has asked you what a
column means. Both mean the definition is missing from the system.

The other signal: you are being asked to build it *before* there is a
disagreement. Layers built speculatively get abandoned, because nothing was
wrong and therefore nothing was solved.

---

## Measures and grain

### Why is my count of orders different from my count of rows?

**Because they count different things, and that is not a bug.**

`COUNT(*)` on a fact table at *order line* grain counts lines. There are 901
lines and 450 orders in this course's data — exactly two lines per order.
If you want orders, use `COUNT_DISTINCT(order_id)`.

The mistake is naming. `order_count` built on `COUNT(*)` is a lie that reads
like the truth. Name it `order_line_count`.

### Why is my margin rate lower than I expected?

**Almost always because it is being computed as the average of per-row
ratios.** The correct formula is `SUM(numerator) / SUM(denominator)`, and the
naive one is always biased low.

On this course's data, the correct global margin is **0.5125** and the
average-of-ratios is **0.4816** — a 3.1 point gap, on £1.1M of revenue.

In Looker Studio specifically, check whether the calculated field is written
as `SUM(x) / SUM(y)` and not `x / y`. Calculated fields run after
aggregation.

### Can I sum a distinct count?

**No.** Summing distinct counts across a breakdown double-counts any entity
that appears in more than one bucket.

In this course's data, the regional `distinct_orders` sum to **799** against
a global **450** — a 77.6% inflation.

### What is a "safe" join, and why is grain mismatch worse?

A join is "safe" when it does not fan out — a `many_to_one` join from the
fact side. Grain mismatch is worse because it happens through a join that
*is* safe: the row count does not change, so nothing looks wrong, but a
measure is counted at the wrong level.

### How do I find fan-out in an existing dashboard?

Compare the measure computed on the fact table alone against the same
measure computed after the join. In this course:

```python
print("baseline :", total_revenue(orders))        # 1128941.37
print("duplicated:", total_revenue(orders + orders))  # 2257882.74
```

Duplicating the fact table is equivalent to joining it to a table with two
copies of every row — which is exactly what a badly-modelled dimension
produces.

---

## Dates

### Why do I need a date spine if I can just group by the date?

**Because grouping by the date only produces the rows that exist.** A day
with no sales has no row, so it never appears in a group-by at all.

The spine is generated, left-joined to the facts, with `COALESCE` on the
measures. It turns "no row" into "a row with zero".

### Why does my week start on Monday when the business expects Sunday?

**Because ISO weeks start on Monday.** `2026-03-15` truncates to week
`2026-03-09`.

Decide the convention, write it in the model's description, and put it in
the runbook. A weekly number that silently changes definition between two
dashboards cannot be reconciled — which is worse than a number that is
consistently wrong, because it at least can be compared.

### My date filter is returning the wrong number. Where do I look?

**At the truncation order.** The bounds must be computed on the raw dates
*before* truncating.

Truncating the end of a March filter to the month turns 31 March into
1 March, and the filter silently loses 30 days. And truncating *both* ends
before comparing them can mask an inverted range — 31 March and 1 March both
truncate to 1 March and look valid.

### Why did the previous period come out as 2024 instead of 2025?

**The year-grain off-by-one.** The previous year for 2026 is 2025.

This is exactly the kind of bug that lives in `previous_period`, and it is
why the course has a test asserting it.

---

## Validation and operations

### Why does the validation gate fail on the sample data?

**Because the sample data is deliberately imperfect.** It plants, on purpose:

| Defect | Caught by | Severity |
|---|---|---|
| A duplicated order line | `grain.not_unique` | ERROR |
| An unresolved `customer_id` | `referential.unresolved` | ERROR |
| A null `product_id` | `completeness.missing` | WARNING |
| A negative revenue row | `value.negative` | WARNING |
| A stale extract (126 days old) | `freshness.stale` | ERROR |

Every one of those is a real defect the gate exists to catch. The gate exits
**1**, which is correct.

### How strict should the gate be?

**ERROR only for things that make the number wrong or not current.**
WARNING for things worth a look. INFO for things that passed.

And: **never fail a build on a check that has fired before without a human
deciding what to do.** A gate that fires on good data gets switched off
within a week, and then it protects nothing.

### Should reconciliation compare values or row counts?

**Values.** Row counts are a weak signal — two systems can have identical
counts and entirely different contents. The outcome that matters is
`VALUE_MISMATCH`, and a count comparison can never see it.

Use `IS DISTINCT FROM`, not `<>`. `NULL <> NULL` is `NULL`, not `TRUE`, so
`<>` silently drops exactly the rows where the problems hide.

### How often should I reconcile?

**Nightly, automatically, at the level of individual rows** for the measures
that matter.

The level is the decision that determines whether it is useful. A single
aggregate tells you *that* something is wrong; row-level tells you *which*
rows, which is the difference between an investigation and a guessing game.

### What is a freshness SLO, and how do I pick the number?

**A stated maximum age for the newest row in a model, in hours, with an
owner.**

Set it from the business's tolerance for being wrong, not from the pipeline's
current performance. If the daily report goes out at 8am, the SLO is 6am —
even though the pipeline currently delivers at 4am. A performance measurement
is not a requirement.

---

## The tools

### Should I use Looker Studio or Looker?

**Looker Studio for dashboards, Looker for metrics.** The deciding factor is
whether the definitions need to be reviewable.

Looker Studio has no shared semantic layer. Every author defines their own
calculated fields and joins, so two dashboards about revenue are two
unrelated implementations that will eventually disagree.

If the metrics matter — if they go to a board, a regulator or a customer —
they belong in LookML or dbt, where they are versioned and reviewed.

### When is dbt's semantic layer the right answer instead of LookML?

**When the transformation and the metric definitions belong to the same
team.** dbt's semantic layer lets the team that builds the tables also
define the metrics, with the tests sitting next to the definitions.

The dbt model has one addition LookML lacks as a first-class concept: the
**entity**, which declares a key and its role (`primary`, `foreign`,
`natural`) and lets the tool work out the joins.

### What is a metric store, and how is it different from a semantic layer?

**A semantic layer defines metrics; a metric store serves them.**

A metric store — MetricFlow, Cube, Transform's hosted metrics — is an
execution engine that turns definitions into optimised queries: column
pruning, pre-aggregation, caching, partition pruning.

Most metric stores are built *on* a semantic layer. The definitions live in
one; the metric store makes them fast.

The practical question: do you need the definitions to be reviewable and
portable, or the queries to be fast? Those are different products, and the
answer is usually "both, in that order".

### My LookML fails to build with "undefined field". What now?

**A `{{ }}` reference to a field that does not exist.** Good news: it is a
build error, so it never reached a dashboard.

The course reproduces this check locally:

```python
from lookml import collect_available_fields, find_broken_references

available = collect_available_fields([sales_model, customer_model])
broken = find_broken_references(lookml_text, available)
```

---

## Working with people

### How do I get people to migrate off a spreadsheet?

**Do not argue about the spreadsheet. Give them the number they need, faster
and with the caveat they care about.**

Most spreadsheet resistance is not about trust in the pipeline; it is about
control, and about the spreadsheet having one extra column they built
themselves. A migration that removes that capability will fail, correctly.

The successful migrations put the governed number next to the spreadsheet
number, let them see they match, and keep the ability to slice the
spreadsheet for one-off analysis. The spreadsheet becomes a scratchpad
rather than a source of truth.

### How do I tell "the dashboard is broken" from "the metric is wrong"?

**Does the number change when you use a different chart or filter?** If yes,
the dashboard is at fault. If no, the definition is.

Teams that skip this distinction rebuild dashboards when the metric is wrong
— and the rebuilt dashboard is still wrong, and now there are two of them.

### My semantic layer was built and nobody uses it. What went wrong?

**It is a design problem, not a marketing problem.** The layer usually makes
the *hard* questions easy and the *easy* questions slightly harder. A report
author who wants "revenue by region" must pick the right explore and the
right measure — and if the wrong choice is also available, they will pick it,
because they do not know the difference.

The three fixes:

- **Name things so the right choice is obvious.** `order_line_count` versus
  `order_count`. The name is the documentation.
- **Make the wrong thing hard to do.** Do not put a non-additive measure in a
  view a report author will find first.
- **Make the right thing the default.** The explore most people want should
  be the one with the safe joins.

The team that shipped a layer with 40 measures and 3% adoption fixed it by
*deleting* measures and renaming the rest. Adoption went up.
