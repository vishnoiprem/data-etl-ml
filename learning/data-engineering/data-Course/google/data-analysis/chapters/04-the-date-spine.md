# Chapter 04 — The Date Spine and Timeframes

> **Module 2.2** · ~45 minutes · No cloud account required

---

## 🎯 What you will learn

- Why a chart with **gaps** is a modelling problem, not a display problem.
- The **date spine**: a generated table with one row per day, and how it
  turns a gap into a zero.
- **Timeframes** — the date grains, why the week starts on Monday, and why
  two dashboards disagree by one week when one of them starts on Sunday.
- How to build a spine **without** a date table — the `GENERATE_DATE_ARRAY`
  trick, and the join that fills the gaps.
- Date **filters** and the off-by-one-day bug that hides inside them.
- **Period over period**, and why "this month versus last month" needs the
  last day of the previous month, not "30 days ago".

---

## 🧠 Concept

### A gap is not a zero

Here is the fact:

```
2026-03-01   142 orders
2026-03-02    98 orders
2026-03-03     0 orders   ← there is no row here
2026-03-04   131 orders
```

Plot that and the chart has a **gap** at 3 March. Plot it and the line
*breaks*. The reader sees three separate shapes, and the natural
interpretation is "we have no data for the 3rd" — a data quality problem, an
ingestion failure, something to investigate.

The truth is "we had no sales on the 3rd", which is a **zero**. Nothing went
wrong. A weekend with no orders is not an incident.

This distinction is not cosmetic. It is the difference between:

- *"our pipeline broke on the 3rd"* — and somebody spends a day on it, and
  finds nothing, and the dashboard loses trust;
- *"we didn't sell anything on the 3rd"* — and nobody looks twice.

Both look identical on a chart. Only one of them is true.

### The date spine

The fix is a **date spine**: a table with one row per day, covering a range,
generated rather than loaded. You join it to the fact table, and the missing
days appear with null measures.

```sql
SELECT
    d.calendar_date,
    COUNT(o.line_id)      AS order_lines,
    COALESCE(SUM(o.total_amount), 0) AS revenue
FROM analytics.date_spine AS d
LEFT JOIN analytics.orders AS o
    ON DATE(o.created_at) = d.calendar_date
GROUP BY d.calendar_date
ORDER BY d.calendar_date;
```

The `LEFT JOIN` is the important word. A `LEFT JOIN` keeps every spine row
and matches what it can. An `INNER JOIN` would throw away the empty days and
you would be back where you started.

The `COALESCE` is the second important word. A null measure is not a zero —
nulls propagate through charts in ways that confuse readers, and some
charting tools will not plot them at all. `COALESCE(SUM(...), 0)` turns the
null into a zero, and the chart draws a flat line.

### Generating the spine without a table

In BigQuery you do not need a loaded table:

```sql
WITH spine AS (
    SELECT DATE(calendar_date) AS calendar_date
    FROM UNNEST(
        GENERATE_DATE_ARRAY(
            DATE '2026-01-01',
            DATE '2026-12-31',
            INTERVAL 1 DAY
        )
    ) AS calendar_date
)
SELECT
    spine.calendar_date,
    COALESCE(COUNT(o.line_id), 0) AS order_lines,
    COALESCE(SUM(o.total_amount), 0) AS revenue
FROM spine
LEFT JOIN analytics.orders AS o
    ON DATE(o.created_at) = spine.calendar_date
GROUP BY spine.calendar_date
ORDER BY spine.calendar_date;
```

In Looker Studio the equivalent is a **Data Blended** source or a
calculated field with `DATE()`. In Looker it is a `date_spine` view generated
with a `generate_series`-style SQL, or a `date_spine` **table** in your
warehouse, which Looker then joins automatically.

### Timeframes

A **timeframe** is a granularity: `raw`, `day`, `week`, `month`, `quarter`,
`year`. Dragging a date dimension into a chart and picking "Month" means:
truncate every date to the first of its month, then group.

```
2026-03-04  →  2026-03-01
2026-03-15  →  2026-03-01
2026-03-28  →  2026-03-01
              ──────────
              three rows, one bucket: March
```

The truncation is what makes the rollup possible. Once every row in March
carries the same truncated date, grouping by it is a plain `GROUP BY`.

The course implements this in `project/core/date_helpers.py`:

```python
from date_helpers import truncate_date

truncate_date("2026-03-15", "month")    # date(2026, 3, 1)
truncate_date("2026-03-15", "quarter")  # date(2026, 1, 1)
truncate_date("2026-03-15", "year")     # date(2026, 1, 1)
truncate_date("2026-03-15", "week")     # date(2026, 3, 9)  ← Monday
```

### Why the week starts on Monday

2026-03-15 is a Sunday. Truncating it to its week gives **Monday 9 March**,
not Sunday 15 March.

This is the ISO 8601 convention, and it is what Looker does. It is *not*
what some other tools do, and that is a genuine source of disagreement
between two dashboards that should agree.

The failure mode: dashboard A groups the week 9–15 March under "week of
9 March" (ISO). Dashboard B groups Sunday 15 March with the *following*
week (Sunday-start weeks), so B's "week of 15 March" contains 15–21 March.
The two dashboards report **different revenue for the same seven days**, and
both are internally consistent.

If you have both, pick one. This course uses ISO, because that is what
Looker does, and because ISO is the international standard.

### The off-by-one-day bug in date filters

This one is subtle and it hides.

A date filter "March 2026" should mean **1 March to 31 March inclusive**. Get
it wrong and you lose the last day — or the first — of every month.

The bug is easy to write because the filter's bounds are *displayed* as
"1 March" and "31 March" but are *applied* as ">= 1 March" and "<= 1 March"
(the truncated start of the bucket), with the end exclusive.

```python
from date_helpers import date_filter_bounds

bounds = date_filter_bounds("2026-03-01", "2026-03-01", "month")
bounds.start   # date(2026, 3, 1)
bounds.end     # date(2026, 3, 31)   ← the last day, not the first
```

And February, which is 28 days in 2026 and 29 in 2028:

```python
date_filter_bounds("2026-02-01", "2026-02-01", "month").end   # date(2026, 2, 28)
date_filter_bounds("2028-02-01", "2028-02-01", "month").end   # date(2028, 2, 29)
```

The course computes the end of the bucket with `calendar.monthrange`, so
February is right in both years, and a quarter filter ends on the last day
of the quarter:

```python
date_filter_bounds("2026-02-10", "2026-02-10", "quarter").end   # date(2026, 3, 31)
date_filter_bounds("2026-03-11", "2026-03-11", "week").end      # date(2026, 3, 15)
```

The last one is worth pausing on: a week filter on Wednesday 11 March covers
**Monday 9 to Sunday 15**. That is the whole week, not Monday to Wednesday.

### Period over period

"This month versus last month" is a two-line requirement and a one-day
subtraction in the wrong direction.

The current month might be 1 to 31 March. The previous month is **1 to 28
February** — not 28 March to 28 April, and not "30 days ago".

```python
from date_helpers import previous_period

previous_period("2026-03-01", "2026-03-31", "month")
# DateRange(start=date(2026, 2, 1), end=date(2026, 2, 28))

previous_period("2028-03-01", "2028-03-31", "month")
# DateRange(start=date(2028, 2, 1), end=date(2028, 2, 29))   ← leap year
```

The leap-year case is the one that catches people. A report that hardcodes
"28 days in February" is wrong once every four years, and it is wrong in a
way nobody notices until the annual comparison is off by a day.

And the percentage change, which is undefined when the denominator is zero:

```python
from date_helpers import period_over_period

period_over_period(125, 100)   # 0.25
period_over_period(100, 0)     # None — undefined, not infinite
```

`None` renders as a gap on a chart. `float("inf")` renders as an axis that
goes to infinity, which is a very expensive mistake.

### Timeframes and additivity, together

One thing connects this chapter to Chapter 02: **a rolled-up measure is only
correct if the tool re-aggregates it.**

Rolling up from day to month changes the grain. Revenue is additive, so
summing the days gives the month. The margin *rate* is not additive, so the
month's rate must be recomputed from the month's numerator and denominator —
not averaged from the days.

A tool that gets this wrong produces a chart whose total does not match the
sum of its parts, and that mismatch is visible to any reader who checks.
Looker gets it right because the measure's type says it is a ratio.

---

## 🛠️ Hands-On: Filling the Gaps

### Find the gaps

```bash
cd data-engineering/data-Course/google/data-analysis
python resources/sample_data.py --output-dir ./sample_data
python project/local_bi.py spine --input ./sample_data/orders.csv --timeframe day
```

```
Date spine
----------------------------------------------------
  source            : ./sample_data/orders.csv
  timeframe         : day
  buckets           : 177
  buckets with data : 168
  empty buckets     : 9

  The empty buckets — these are the gaps a raw chart shows:
    2026-01-03
    2026-01-31
    2026-02-22
    2026-02-28
    2026-03-08
    2026-04-11
    ... and 3 more
```

Nine days out of 177 have no orders. On a chart, that is nine gaps.

### Fill them and write the result

```bash
python project/local_bi.py spine \
    --input ./sample_data/orders.csv \
    --timeframe day \
    --output ./out/spine.csv
```

```
Wrote out/spine.csv
```

```bash
head -5 out/spine.csv
```

```
date,order_lines,revenue
2026-01-01,8,8923.74
2026-01-02,2,2100.44
2026-01-03,0,0
2026-01-04,2,1730.84
```

2026-01-03 has `0, 0` — a real row with a zero, rather than a gap. The
chart now draws a flat line.

### The spine in Python

```python
import csv
import sys

sys.path.insert(0, "project/core")

from date_helpers import fill_missing_periods

rows = list(csv.DictReader(open("sample_data/orders.csv")))

filled = fill_missing_periods(rows, timeframe="day")

print(f"buckets        : {len(filled)}")
print(f"with data      : {sum(1 for b in filled if b['rows'])}")
print(f"empty          : {sum(1 for b in filled if not b['rows'])}")

for bucket in filled:
    revenue = sum(float(r["total_amount"] or 0) for r in bucket["rows"])
    print(
        bucket["date"].isoformat(),
        len(bucket["rows"]),
        round(revenue, 2),
    )
```

```
buckets        : 177
with data      : 168
empty          : 9
2026-01-01 8 8923.74
2026-01-02 2 2100.44
2026-01-03 0 0
...
```

### The timeframe truncation, one by one

```python
from date_helpers import truncate_date, describe_timeframe

for timeframe in ("day", "week", "month", "quarter", "year"):
    print(
        f"{timeframe:9}",
        truncate_date("2026-03-15", timeframe).isoformat(),
        "—", describe_timeframe(timeframe),
    )
```

```
day       2026-03-15 — the calendar day
week      2026-03-09 — the Monday of the ISO week
month     2026-03-01 — the first day of the calendar month
quarter   2026-01-01 — the first day of the calendar quarter
year      2026-01-01 — the first of January
```

### The date filter bounds

```python
from date_helpers import date_filter_bounds, previous_period

# "March 2026" — the whole month.
march = date_filter_bounds("2026-03-01", "2026-03-01", "month")
print(march.start, "to", march.end)
print(march.to_sql("created_at"))
```

```
2026-03-01 to 2026-03-31
created_at >= DATE('2026-03-01') AND created_at <= DATE('2026-03-31')
```

### The leap year, and the previous period

```python
from date_helpers import previous_period

previous_period("2026-03-01", "2026-03-31", "month")
previous_period("2028-03-01", "2028-03-31", "month")
previous_period("2026-04-01", "2026-06-30", "quarter")
previous_period("2026-01-01", "2026-06-30", "year")
```

```
DateRange(start=date(2026, 2, 1), end=date(2026, 2, 28), timeframe='month')
DateRange(start=date(2028, 2, 1), end=date(2028, 2, 29), timeframe='month')
DateRange(start=date(2026, 1, 1), end=date(2026, 3, 31), timeframe='quarter')
DateRange(start=date(2025, 1, 1), end=date(2025, 12, 31), timeframe='year')
```

### The spine as a test

A test that asserts the spine fills the gaps — and one that asserts the
totals do not change when it does:

```python
def test_the_spine_does_not_change_the_total():
    """Filling the gaps must not change the revenue.

    A spine adds rows for days with no facts. Every one of those rows
    has a zero measure. If the total changed, the spine was joined
    wrongly — probably an inner join, which drops the empty days
    instead of filling them.
    """
    model = build_sales_model()
    rows = load_rows()

    before = aggregate(model, rows, [], ["total_revenue"])
    filled = fill_missing_periods(rows, timeframe="day")
    after = aggregate(model, filled, [], ["total_revenue"])

    assert (
        after.rows[0].measures["total_revenue"]
        == before.rows[0].measures["total_revenue"]
    )
```

That test is worth writing, because the most common way to "add a spine" is
to get the join type wrong, and the symptom — the total staying the same —
looks like success.

---

## 🛠️ Common Errors and Fixes

### "My chart has gaps but the data is fine"

The data is fine and the chart is telling the truth: there were no facts for
those periods. You need a spine. Chapter 04, above.

### "My monthly total is missing the last day of the month"

A date filter whose end bound is truncated rather than expanded. "March 2026"
is being applied as `<= 1 March` instead of `<= 31 March`.

**The fix:** always compute the end of the bucket explicitly, and use `>=`
and `<=` (inclusive) rather than a half-open range unless the database's
date type makes that awkward.

### "My week number is different from finance's"

Different week-start conventions. ISO (Monday) versus Sunday-start versus
the US federal fiscal year. Pick one and document it. This course uses ISO
because Looker does.

### "The period-over-period comparison is off by a day at the end of the month"

The previous period was computed as "the same number of days before today"
rather than "the previous calendar bucket". At the end of March, "30 days
before" lands in late February and misses a day; in February it lands in
January.

**The fix:** compute the previous bucket from the calendar, as
`previous_period()` does.

### "My YoY chart has an empty first three months"

The current year has no data yet. A chart comparing January–June 2026 with
January–June 2025 shows a gap for the months that have not happened.

**The fix:** either truncate the current period to what has actually
happened, or mark the future as "not yet" with a zero and a footnote. A
zero and a "no data yet" are different claims.

### "My `DATE(created_at)` join to the spine is slow"

It is, on a big table, because the function is applied to the fact table on
every scan. Two fixes:

- **BigQuery:** partition the fact table by `DATE(created_at)` and join on
  the partition column.
- **Everywhere:** join on a pre-computed date column rather than a function
  of a timestamp.

```sql
-- Slow: the function is applied per row.
LEFT JOIN spine ON DATE(o.created_at) = d.calendar_date

-- Fast: the function was applied once, at load time.
LEFT JOIN spine ON o.order_date = d.calendar_date
```

---

## 💡 Production Notes

### The spine belongs in the warehouse, not the chart

If the spine lives in the BI tool, every chart author has to remember to
join it, and the first one who forgets ships a chart with gaps. If it lives
in the warehouse — as a table, or as a `date_spine` view that Looker joins
automatically — every chart gets it right by default.

In Looker, a view named `date_spine` with a column named `date` is
**automatically joined** to any date dimension on any explore. That is
Looker's most useful BI-automation feature and it is not well known.

### Choose one time zone, once, and document it

A timestamp stored in UTC, truncated to a date in UTC, is a different day
than the same timestamp truncated in local time. For a business in one
timezone this is irrelevant; for a business in three, it is the difference
between a revenue figure and a different revenue figure.

The rule: **truncate dates in the timezone the business operates in**, and
store the timezone with the data. `DATE(created_at, 'Australia/Sydney')` in
BigQuery; `created_at AT TIME ZONE 'Australia/Sydney'` in Postgres.

Never truncate in UTC and call it a business date unless the business is in
UTC.

### Fiscal periods need their own dimension

If the business reports on fiscal quarters, do not compute them from calendar
quarters in the chart. Build a **date dimension with a fiscal calendar** —
one row per date, with the fiscal year, fiscal quarter, fiscal period and
fiscal week as columns.

```sql
CREATE TABLE analytics.dim_date (
    calendar_date   DATE NOT NULL,
    fiscal_year     INT64 NOT NULL,
    fiscal_quarter  INT64 NOT NULL,
    fiscal_period   INT64 NOT NULL,
    fiscal_week     INT64 NOT NULL,
    is_week_start   BOOL NOT NULL,
    PRIMARY KEY (calendar_date)
);
```

This is the difference between "the finance team can explain their numbers"
and "the finance team files a ticket".

### A spine is also a completeness check

A spine joined to the fact table tells you something the fact table alone
cannot: how many days have **no** data at all, as opposed to no *activity*.

```sql
SELECT
    COUNT(*) AS spine_days,
    COUNT(o.line_id) AS days_with_orders,
    COUNT(*) - COUNT(o.line_id) AS days_without_orders
FROM analytics.date_spine AS d
LEFT JOIN analytics.orders AS o
    ON DATE(o.created_at) = d.calendar_date;
```

If `days_without_orders` is suddenly 40 when it used to be 9, the pipeline
stopped. That is the freshness check from Chapter 06, in a more precise
form.

### Pre-compute the date column at load time

`DATE(created_at)` in a join predicate is computed on every scan. A
materialised `order_date` column costs one byte-ish of storage per row and
saves the computation forever. On a table with billions of rows this is the
difference between a 4-second dashboard and a 4-minute one.

---

## 🔑 Key Takeaways

1. **A gap is not a zero.** The chart cannot tell "no sales" from "no data",
   so the model has to.
2. **The date spine is a generated table with one row per day**, joined with
   a `LEFT JOIN` and `COALESCE`d.
3. **A timeframe is a truncation**, and truncation is what makes the rollup
   a plain `GROUP BY`.
4. **The week starts on Monday** (ISO), and so does Looker. Pick a
   convention and document it.
5. **A date filter must cover the whole bucket.** "March 2026" is 1 to 31
   March, and February is 28 or 29 days depending on the year.
6. **The previous period is the previous calendar bucket**, not "N days
   ago".
7. **A percentage change from zero is undefined.** Return `NULL`, not
   infinity.
8. **Put the spine in the warehouse**, and the timezone with the data.

---

## 📚 Practice Exercises

1. Build the date spine in BigQuery with `GENERATE_DATE_ARRAY`, join it to
   the orders table with a `LEFT JOIN`, and produce a daily revenue series
   with zeros for the empty days. Verify that the total matches the
   unspined total.

2. Write a test that asserts the spine produces one row per day in a range
   and that no day is missing. Then break the join deliberately (change it to
   an `INNER JOIN`) and confirm the test fails.

3. Extend `project/core/date_helpers.py` with a `fiscal_truncate` function
   that truncates to a fiscal quarter starting in July, and test it against
   the boundary dates 30 June and 1 July.

4. Write the SQL for a date dimension with fiscal columns, a fiscal-week
   number, and a `is_week_start` flag, and explain in a comment which
   queries use each column.

5. Compute the "last complete month" for any date, and write the function
   that returns it. Then write the SQL that uses it to build a
   month-over-month comparison that is never affected by the current,
   incomplete month.

6. Take the timezone question seriously: write the BigQuery expression that
   truncates a UTC timestamp to a Sydney business date, and the expression
   that does the reverse. Then explain what a dashboard looks like if the
   two are mixed.

---

## 📖 Further Reading

- **BigQuery's `GENERATE_DATE_ARRAY`** — the function behind the spine.
  `cloud.google.com/bigquery/docs/reference/standard-sql/date_functions`.
- **LookML's `timeframe` parameter** and **Looker's `date_spine` views** —
  `cloud.google.com/looker/docs/reference/lookml` and
  `cloud.google.com/looker/docs/admin/looker-core#date_spine`.
- **Kimball & Ross, *The Data Warehouse Toolkit*** (3rd ed., 2013) — chapter
  on the date dimension, and why it is the most important dimension in the
  warehouse.
- **ISO 8601 week dates** — the convention this course uses. The
  "Week 1 contains the first Thursday" rule is worth knowing, because it is
  why ISO weeks are sometimes 52 and sometimes 53.
- **"The Most Common BI Mistake"** — a widely circulated piece on the
  average-of-averages error; the same class of problem as the ratio mistake
  in Chapter 02.
