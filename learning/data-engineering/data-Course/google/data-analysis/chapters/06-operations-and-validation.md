# Chapter 06 — Operations: Validation, Reconciliation and Freshness

> **Module 3.2** · ~50 minutes · No cloud account required

---

## 🎯 What you will learn

- The **four checks** every BI model needs, and why each one catches a
  failure no chart can reveal.
- **Freshness** — why a stale pipeline looks exactly like a business event,
  and how to tell them apart.
- **Reconciliation** — comparing *values* rather than counts, and why a
  count comparison is worse than no comparison.
- The **reconciliation query** in three parts: the grain check, the fan-out
  check, and the freshness check.
- **SLOs for a dashboard** — what to measure, what to alert on, and what not
  to alert on.
- The **runbook**: the order of investigation when a number is questioned.

---

## 🧠 Concept

### The dashboard is a promise

Every dashboard makes a claim. "Revenue is up 12% this quarter" is a claim
that some number, computed some way, means something.

The claim breaks in ways nobody can see from the chart:

| Failure | What the chart shows |
|---|---|
| A fan-out join | Revenue doubled — looks like growth |
| A stale extract | Revenue flat — looks like a market event |
| A schema change | Revenue zero — looks like a catastrophe |
| A grain mismatch | Revenue slightly high — looks like inflation |
| A duplicate key | Revenue slightly high — looks like demand |

Every one of these is a **normal-looking chart**. That is the problem. A
chart cannot tell you that it is wrong, because a wrong chart is still a
chart.

So the checks have to happen outside the chart, before the number reaches
anybody.

### The four checks

**1. Grain.** Is the primary key actually unique?

```sql
SELECT line_id, COUNT(*) FROM analytics.orders
GROUP BY line_id HAVING COUNT(*) > 1;
```

One duplicated key inflates every additive measure over the table by the
duplicate factor. This is the root cause of most fan-outs, so it is the
first thing to check.

**2. Referential integrity.** Do the foreign keys resolve?

```sql
SELECT COUNT(*) FROM analytics.orders o
LEFT JOIN analytics.customers c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL;
```

An unresolved foreign key is usually a **timing** problem — the fact
arrived before the dimension row did. In a left-join BI tool it produces a
blank label, and the row still counts towards the total. **The total is
right and the breakdown is wrong**, which is worse than either being wrong
alone, because nobody checks the parts when the whole looks right.

**3. Completeness.** Are the required fields populated?

```sql
SELECT
    COUNTIF(region IS NULL) AS null_region,
    COUNTIF(status IS NULL) AS null_status
FROM analytics.orders;
```

A missing dimension value does not remove a row from a total. It collects
the row under a "None" bucket, and the breakdown silently loses a
category.

**4. Freshness.** Is the data recent enough to be believed?

```sql
SELECT
    MAX(created_at) AS newest_row,
    TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(created_at), HOUR) AS age_hours
FROM analytics.orders;
```

This is the check that saves the most time, because its failure mode is the
most confusing.

### Freshness: the check that pays for itself

Here is the scenario, and it happens every quarter.

The pipeline breaks on the 15th. The dashboard shows revenue flattening
after the 14th. The business interprets the flat line as "sales are down".
A regional director says their region is fine. The VP asks why EMEA is
down. Two people spend a day investigating a sales problem that does not
exist.

The data was three weeks old. The chart was correct about the data and
completely wrong about the business.

**Freshness is the check that distinguishes "the number went down" from
"the number stopped moving".**

The distinction is subtle but decisive:

- A **real** decline has *data* — the pipeline ran, and the value is
  smaller.
- A **stale** pipeline has *no data* — the pipeline stopped, and the last
  value is being repeated, or the chart simply ends.

The chart looks identical in both cases. Only the freshness check tells them
apart.

The fix is not technical. It is a **label on the dashboard**:

> Data as of 2026-03-14 03:00 UTC

Every serious BI tool has this. Looker Studio has a "Data freshness"
annotation on the chart. Looker has a `data freshness:` parameter on the
explore. Every dashboard should have it.

### Reconciliation: values, not counts

The nightly question is: **does the dashboard still tell the truth?**

The naive check compares row counts:

```sql
-- The wrong check.
SELECT
    (SELECT COUNT(*) FROM source) AS source_rows,
    (SELECT COUNT(*) FROM dashboard) AS dashboard_rows;
```

Two tables can have the same number of rows and completely different
contents. One row says `EMEA` and the other says `APAC` — same count,
different data. The count check says "everything is fine" and produces a
green tick on a broken number.

**A count comparison that passes when the data is wrong is worse than no
comparison at all**, because it converts an unknown into a false assurance.

The right check compares **values**, three ways:

```sql
SELECT
    CASE
        WHEN source.line_id IS NULL THEN 'EXTRA'
        WHEN dashboard.line_id IS NULL THEN 'MISSING'
        WHEN source.total_amount IS DISTINCT FROM dashboard.total_amount
          OR source.region        IS DISTINCT FROM dashboard.region
        THEN 'VALUE_MISMATCH'
        ELSE 'OK'
    END AS difference,
    COUNT(*) AS rows
FROM source
FULL OUTER JOIN dashboard ON source.line_id = dashboard.line_id
GROUP BY difference;
```

Three outcomes:

- **MISSING** — in the source, not in the dashboard's output. Something
  dropped it: a filter, a join, a late-arriving row.
- **EXTRA** — in the dashboard's output, not in the source. Something
  invented it: a fan-out, a duplicate.
- **VALUE_MISMATCH** — in both, but the values differ. Something transformed
  it: a wrong expression, a currency conversion, a stale cache.

### `IS DISTINCT FROM`, not `<>`

This detail matters and is easy to miss.

```sql
-- NULL-unsafe: returns NULL (not TRUE) when either side is NULL.
WHERE source.total_amount <> dashboard.total_amount

-- NULL-safe: two NULLs are not distinct; a NULL and a value are.
WHERE source.total_amount IS DISTINCT FROM dashboard.total_amount
```

With `<>`, a row where the dashboard's value is NULL and the source's is 500
produces `NULL <> 500` → `NULL` → the row is **filtered out** and the
mismatch is never reported. `IS DISTINCT FROM` returns TRUE and the
mismatch is caught.

**Every reconciliation query should use `IS DISTINCT FROM`.** It is the
single most valuable SQL habit in this chapter.

### The three queries worth running nightly

**The grain check.**

```sql
SELECT line_id, COUNT(*) AS occurrences
FROM analytics.orders
GROUP BY line_id
HAVING COUNT(*) > 1;
```

**The fan-out check.**

```sql
WITH standalone AS (
    SELECT SUM(total_amount) AS revenue, COUNT(*) AS lines
    FROM analytics.orders
),
joined AS (
    SELECT SUM(o.total_amount) AS revenue, COUNT(*) AS lines
    FROM analytics.orders AS o
    LEFT JOIN analytics.customers AS c ON o.customer_id = c.customer_id
)
SELECT
    standalone.revenue, joined.revenue,
    joined.revenue - standalone.revenue AS difference,
    CASE WHEN joined.revenue = standalone.revenue
         THEN 'OK' ELSE 'FAN-OUT' END AS verdict
FROM standalone, joined;
```

**The freshness check.**

```sql
SELECT
    MAX(created_at) AS newest_row,
    TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(created_at), HOUR) AS age_hours,
    CASE
        WHEN MAX(created_at) IS NULL THEN 'NO DATA'
        WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(created_at), HOUR) > 48
        THEN 'STALE' ELSE 'OK'
    END AS verdict
FROM analytics.orders;
```

All three are in `sql/reconciliation.sql` in this course. All three run in
seconds. All three catch mistakes that cost quarters.

---

## 🛠️ Hands-On: The Validation Gate

The course ships the four checks as a runnable gate.

### Run it

```bash
cd data-engineering/data-Course/google/data-analysis
python resources/sample_data.py --output-dir ./sample_data
python project/local_bi.py validate --input ./sample_data/orders.csv
```

```
Validation report
----------------------------------------------------
  source            : ./sample_data/orders.csv
  rows checked      : 901
  result            : FAIL
  findings:
    [ERROR  ] grain.not_unique: primary key 'line_id' is not unique: 1 value(s) repeat. Every measure over this table is inflated. (1 rows)
    [ERROR  ] freshness.stale: newest row in 'created_at' is 126 day(s) old; the limit is 2. The numbers are not current — say so on the dashboard. (1 rows)
    [WARNING] value.negative: 1 row(s) have a negative 'total_amount'. Legitimate for refunds; suspicious for a sign-flip bug. (1 rows)
```

Three findings, and each one is a planted defect in the sample data:

| Finding | Severity | Why |
|---|---|---|
| `grain.not_unique` | ERROR | A duplicated order line — a re-delivered event |
| `freshness.stale` | ERROR | The extract stopped 4 days before the end of the range |
| `value.negative` | WARNING | A refund — legitimate, but worth a look |

**The exit code is 1.** That is what makes it usable in CI.

### The severity rules

Not every finding is equally serious, and the difference matters:

- **ERROR** — the number is wrong, or the number is not current. Fail the
  build, fail the pipeline, block the dashboard.
- **WARNING** — the number is probably right but something is worth
  looking at. A negative revenue row is a refund most of the time; it is
  also the signature of a sign-flip bug.
- **INFO** — the check ran and passed. "primary key is unique and
  populated" is not a problem, but it is worth recording that you checked.

```python
from validate import ERROR, WARNING, INFO
```

### The checks in isolation

```python
import csv
import sys

sys.path.insert(0, "project/core")

from validate import (
    check_grain,
    check_referential_integrity,
    check_completeness,
    check_freshness,
    check_no_negative_revenue,
)

rows = list(csv.DictReader(open("sample_data/orders.csv")))
customers = list(csv.DictReader(open("sample_data/customers.csv")))

print("grain:")
print(check_grain(rows, "line_id").to_text())

print("\nreferential integrity:")
print(
    check_referential_integrity(
        rows, "customer_id", customers, "customer_id"
    ).to_text()
)

print("\nfreshness:")
print(
    check_freshness(
        rows, "created_at", max_age_days=2, today="2026-06-30"
    ).to_text()
)
```

The referential check finds the planted `c9999`:

```
Validation report
----------------------------------------------------
  rows checked      : 901
  result            : FAIL
  findings:
    [ERROR  ] referential.unresolved: foreign key 'customer_id' has 1 value(s) with no matching 'customer_id'. Those rows will show a blank label but still count towards totals. (1 rows)
```

### The gate as a test

```python
def test_the_gate_catches_a_duplicated_key():
    """A duplicated primary key must fail the gate."""
    model = build_sales_model()
    rows = [
        {
            "line_id": "l1",
            "customer_id": "c1",
            "created_at": "2026-03-15",
            "total_amount": 100.0,
        },
        {
            "line_id": "l1",          # the duplicate
            "customer_id": "c1",
            "created_at": "2026-03-15",
            "total_amount": 100.0,
        },
    ]

    report = validate_dataset(rows, model, today=date(2026, 3, 15))

    assert not report.passed
    assert any(f.code == "grain.not_unique" for f in report.errors)
```

### A negative test — the gate must not cry wolf

```python
def test_the_gate_passes_on_clean_data():
    """Clean data must pass every check.

    A validation gate that fires on good data gets switched off. This
    test is what keeps it honest.
    """
    model = build_sales_model()
    rows = [
        {
            "line_id": "l1",
            "customer_id": "c1",
            "created_at": "2026-03-15",
            "total_amount": 100.0,
        },
        {
            "line_id": "l2",
            "customer_id": "c2",
            "created_at": "2026-03-15",
            "total_amount": 200.0,
        },
    ]

    report = validate_dataset(
        rows, model,
        required=["line_id", "customer_id"],
        today=date(2026, 3, 15),
    )

    assert report.passed, report.to_text()
```

The negative test is the more important of the two. A gate that fires on
good data gets ignored within a week, and then it protects nothing.

---

## 🛠️ Common Errors and Fixes

### "The number is right but the chart looks empty"

A filter is too aggressive, or a date filter excludes the boundary. Check
the filter's bounds with `date_filter_bounds` rather than by eye:

```python
from date_helpers import date_filter_bounds

bounds = date_filter_bounds("2026-03-01", "2026-03-01", "month")
print(bounds.to_sql("created_at"))
```

### "The dashboard is slow"

In order of likelihood:

1. **A fan-out join.** The query is joining a table at a much finer grain.
2. **No filter pushdown.** A filter applied *after* a join cannot reduce
   the scan. Filter the fact table first.
3. **`DATE(timestamp)` in a join predicate.** Compute the date column at
   load time.
4. **A `SELECT *` under the covers.** Looker Studio's default queries can
   select every column.

### "The reconciliation says MISSING but the row is there"

The reconciliation query joins on a key, and the two sides use different
key representations — a string `'1'` versus an integer `1`, or a date
versus a timestamp.

**The fix:** normalise the key in both sides before joining. This is a
data-modelling bug, and it will keep biting you.

### "The reconciliation says VALUE_MISMATCH on every row"

Almost always a float comparison. `0.1 + 0.2 != 0.3` in binary floating
point.

**The fix:** round both sides before comparing, or compare with a
tolerance:

```sql
WHERE abs(source.total_amount - dashboard.total_amount) > 0.01
```

For a money comparison, `ROUND(x, 2)` is usually right.

### "We got a page at 3am because the freshness check fired"

And the data was fine — the check ran at 03:00, before the day's load
finished. **Time your checks against your pipeline's schedule.** A freshness
check that runs at 03:00 needs a freshness threshold that accounts for a
load that starts at 02:00.

The better design: alert on the *pipeline's* success, not on the data's age.
The pipeline knows when it failed; the data does not.

---

## 💡 Production Notes

### Alert on the pipeline, not on the data

This is the single most important operational distinction in BI.

| | Data-based alerting | Pipeline-based alerting |
|---|---|---|
| Detects a broken extract | Yes, late | Yes, immediately |
| Knows a load is *supposed* to run | No | Yes |
| False positives | Many (a late load looks stale) | Few |
| Misses a silent schema change | No | Sometimes |

**The pipeline knows when it failed. The data does not.** A freshness check
is a useful backstop, but the primary signal should be the pipeline's own
success metric.

The freshness check earns its keep for the case the pipeline *thinks*
succeeded — a schema change that silently produces empty tables, a query
that returns zero rows and exits zero, a permission change that turns a
query into a filtered one.

### Put a freshness label on every dashboard

```
Data as of 2026-03-14 03:00 UTC
```

In Looker Studio: *Chart → Annotations → Add an annotation*, with the text
"Data as of {{data_as_of}}". In Looker: the `data freshness:` parameter on
the explore.

It costs one annotation and it converts a confusing chart into a
trustworthy one.

### Make the gate a CI job

```bash
python project/local_bi.py validate --input ./sample_data/orders.csv
```

Exit code 1 on failure. Put it in the pipeline's CI and a broken model
never gets deployed.

### Log the checks, not just the failures

A validation run that passes should leave a record. "Checked 901 rows, grain
unique, referential integrity clean, fresh as of 2026-06-26" is worth
storing, because when somebody asks "was this data ever broken?" the answer
is a log rather than a memory.

### Know which dashboards are load-bearing

Not every dashboard matters. Three of them probably drive decisions; the
other forty are reference material.

For the three that matter:

- reconcile them nightly, at the **value** level;
- page somebody when the reconciliation fails;
- review their measures when the underlying model changes.

### The incident runbook

When a number is questioned, the order of investigation is fixed:

1. **Grain.** What is one row of the source table?
2. **Freshness.** Is the data current? *Check this before anything else* —
   it is the cheapest and the most commonly the answer.
3. **Filters.** Which filters are applied, on which side of the join?
4. **Cardinality.** Does any join fan out? Run the check.
5. **Additivity.** Is the measure additive across the grouping?
6. **Values.** Only now, diff the rows with the reconciliation query.

Steps 1 to 5 are cheap and explain almost every discrepancy. Step 6 is
expensive and explains almost nothing on its own.

---

## 🔑 Key Takeaways

1. **A wrong chart looks exactly like a right one.** The checks have to
   happen outside the chart.
2. **The four checks:** grain, referential integrity, completeness,
   freshness.
3. **Freshness is the check that saves the most time** — a stale pipeline
   looks exactly like a business event.
4. **Reconcile values, not counts.** A count comparison that passes on
   broken data is worse than no comparison.
5. **Use `IS DISTINCT FROM`, never `<>`** — `<>` silently drops the
   NULL-mismatch rows, which are the ones you most need to see.
6. **Alert on the pipeline, not on the data.** The pipeline knows when it
   failed; the data does not.
7. **Put a freshness label on every dashboard.**
8. **Test the gate's negative case** — a gate that fires on good data gets
   switched off.

---

## 📚 Practice Exercises

1. Write the four checks as BigQuery SQL and run them against the course's
   `sql/create_analytics.sql` schema. Add the `IS DISTINCT FROM`
   reconciliation query and explain, in a comment, why `<>` would miss rows.

2. Extend `project/core/validate.py` with a check for **unusual row counts**
   — a day-over-day change larger than a threshold. Write the test that
   catches a 50% drop, and explain why this check is noisy and should be a
   warning rather than an error.

3. Add a `data_as_of` field to the validation report, and write the code
   that formats it as "Data as of 2026-06-26 03:00 UTC". Then write the
   Looker Studio annotation text that uses it.

4. Build a dbt test that reconciles the modelled table against the raw
   table at the value level, using `IS DISTINCT FROM`. Run it against a
   deliberately broken model and confirm it fails.

5. Write the incident runbook for your own dashboards — the five or six
   queries somebody runs when a number is questioned, in order, with a
   one-line explanation of each. Put it next to the dashboards.

6. Add a `reconciliation` subcommand to the CLI that compares two data
   files at the value level and reports MISSING, EXTRA and VALUE_MISMATCH.
   Test it with a file that has one row changed, one row missing and one
   row added.

7. Design an alerting policy for a set of dashboards: what pages, what
   tickets, what is only logged. Write down the freshness threshold for
   each and justify it against the pipeline's schedule.

---

## 📖 Further Reading

- **Google Cloud's "Data quality" documentation** — the BigQuery
  approach to data quality, and the `DATA QUALITY` error codes in
  pipeline jobs. `cloud.google.com/bigquery/docs`.
- **dbt's data tests** — `unique`, `not_null`, `relationships`,
  `accepted_values`, and `dbt-expectations` for the custom ones.
  `docs.getdbt.com`.
- **"Data Contracts"** — the emerging practice of making the schema and
  the semantics of a table an explicit contract between producers and
  consumers. Relevant because it is the formal version of "write down the
  grain".
- **Monteiro's "Data Observability"** — the practice of treating a
  dataset's health the way you treat a service's health: with SLIs, SLOs
  and alerts.
- **The course's own `sql/reconciliation.sql`** — the three nightly queries
  in one file, ready to copy.
