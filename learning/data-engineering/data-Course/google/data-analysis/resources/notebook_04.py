#!/usr/bin/env python3
"""
notebook_04.py — build notebook 04, The Date Spine.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_notebooks import code, md, notebook  # noqa: E402


def build() -> dict:
    """Build notebook 04.

    Returns:
        The notebook dict.
    """
    return notebook([
        md("""
# 04 · The Date Spine

> **Module 1 · Foundations · Lecture 1.4**

In this notebook you will:

- Build a **date spine** — one row per calendar day — and see why it exists
- Fill the gaps a raw time series leaves behind
- Master the **timeframes**: day, week, month, quarter, year
- Get the **date filter** right, including the leap-year edge case
- Compute **period over period** without an off-by-one

Everything here runs with **no GCP account, no credentials and no bill**.
"""),
        code("""
import csv
import sys
from datetime import date, timedelta
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
## 1. The problem: a chart that lies by omission

Plot revenue by day against only the days that had sales, and a slow week
looks like a cliff. The days with no sales are simply **not on the chart** —
the line connects Tuesday straight to Friday, and the reader sees a decline
that did not happen.

This is not a rendering bug. It is the absence of a row.

The fix is a **date spine**: a table with one row per calendar day over the
range you care about, left-joined to the facts. The gaps become explicit
zeros, and the chart becomes honest.
"""),
        code("""
from model import aggregate, build_sales_model

model = build_sales_model()
orders = list(csv.DictReader(open(COURSE_ROOT / "sample_data" / "orders.csv")))

# Which days have data?
days_with_data = sorted({row["created_at"] for row in orders})
print(f"order lines            : {len(orders):,}")
print(f"distinct dates in data : {len(days_with_data)}")
print(f"first date             : {days_with_data[0]}")
print(f"last date              : {days_with_data[-1]}")
"""),
        code("""
# The gaps. These dates have no rows, so a raw chart skips them.
start = date.fromisoformat(days_with_data[0])
end = date.fromisoformat(days_with_data[-1])
span = (end - start).days + 1

missing = []
cursor = start
while cursor <= end:
    if cursor.isoformat() not in set(days_with_data):
        missing.append(cursor.isoformat())
    cursor += timedelta(days=1)

print(f"calendar days in range : {span}")
print(f"days with data         : {len(days_with_data)}")
print(f"days with NO data      : {len(missing)}")
print()
for day in missing:
    print("  gap:", day)
"""),
        md("""
Nine missing days out of 177. On a chart, that is nine invisible collapses
in the line — each one reading as a revenue crash.

## 2. Building the spine

The spine is generated, not derived from the data. That distinction matters:
a spine derived from the data would have exactly the gaps you are trying to
fill.
"""),
        code("""
from date_helpers import build_date_spine, fill_missing_periods

spine = build_date_spine("2026-01-01", "2026-06-29")
print(f"spine rows            : {len(spine)}")
print(f"first                 : {spine[0].date}")
print(f"last                  : {spine[-1].date}")
print(f"fields                : year, quarter, month, week, day_of_week, "
      f"year_month, year_quarter")
"""),
        code("""
# Fill the gaps: group the facts by day, then walk the calendar.
filled = fill_missing_periods(
    orders,
    date_field="created_at",
    timeframe="day",
)

print(f"filled buckets: {len(filled)}")
print()
print(f"{'date':<12} {'lines':>7} {'revenue':>14}")
for bucket in filled[:10]:
    rows = bucket["rows"]
    revenue = sum(float(r["total_amount"]) for r in rows)
    print(f"{bucket['date']!s:<12} {len(rows):>7} {revenue:>14,.2f}")
"""),
        md("""
There it is: **2026-01-03 with zero lines and £0.00**. The gap is now a
fact on the chart rather than an absence.

## 3. The SQL

The Python above is a teaching model. The SQL is what you ship.

```sql
WITH spine AS (
    SELECT date FROM analytics.date_spine
),
daily AS (
    SELECT
        DATE(created_at) AS date,
        COUNT(*)          AS order_lines,
        SUM(total_amount) AS revenue
    FROM analytics.orders
    GROUP BY 1
)
SELECT
    s.date,
    COALESCE(d.order_lines, 0) AS order_lines,
    COALESCE(d.revenue, 0)     AS revenue
FROM spine AS s
LEFT JOIN daily AS d ON d.date = s.date
```

Two details that are easy to get wrong:

- **`LEFT JOIN`, not `INNER JOIN`.** An inner join throws away exactly the
  spine rows you built the spine to keep.
- **`COALESCE` the measures to zero.** Without it the gap is `NULL`, and a
  chart renders `NULL` as a gap — you have achieved nothing.
"""),
        md("""
## 4. Timeframes

A timeframe is a truncation of a date to a reporting grain. The six the
course supports:

| Timeframe | Truncates to | Notes |
|---|---|---|
| `raw` | the value as-is | no truncation |
| `day` | the day | |
| `week` | the Monday | ISO weeks start Monday |
| `month` | the 1st | |
| `quarter` | the 1st of Jan/Apr/Jul/Oct | |
| `year` | the 1st of January | |
"""),
        code("""
from date_helpers import TIMEFRAMES, describe_timeframe, truncate_date

print("timeframes:", ", ".join(TIMEFRAMES))
print()
for timeframe in TIMEFRAMES:
    print(f"  {timeframe:<9} {describe_timeframe(timeframe)}")
"""),
        code("""
# Truncation, on a single awkward date.
sample = "2026-03-15"
print(f"{sample} (a {date.fromisoformat(sample).strftime('%A')})")
print()
for timeframe in TIMEFRAMES:
    if timeframe == "raw":
        # `raw` means no truncation at all.
        print(f"  {timeframe:<9} -> {sample}  (no truncation)")
        continue
    truncated = truncate_date(sample, timeframe)
    print(f"  {timeframe:<9} -> {truncated}")
"""),
        md("""
Note that `week` gives **2026-03-09** — the Monday. ISO weeks start on
Monday, and Sunday belongs to the *previous* week. This is the single most
common source of "why is Friday in last week?" in weekly reporting, and it
differs from the US convention, where the week starts on Sunday.

**Decide your convention, write it down, and put it in the model
description.** A weekly number that silently changes definition between two
dashboards is worse than a number that is consistently wrong, because it
cannot be reconciled.
"""),
        md("""
## 5. Date filters

A date filter needs two bounds, and the bounds must be computed on the
**raw** dates before any truncation. Truncating first is how you get a
filter that includes a day it should not.
"""),
        code("""
from date_helpers import date_filter_bounds

for start, end, timeframe in [
    ("2026-03-01", "2026-03-31", "month"),
    ("2026-03-01", "2026-03-31", "day"),
    ("2026-01-01", "2026-12-31", "quarter"),
    ("2024-02-01", "2024-02-29", "day"),
]:
    bounds = date_filter_bounds(start, end, timeframe)
    print(f"{start} .. {end}  [{timeframe:<8}] -> {bounds.start} .. {bounds.end}")
"""),
        code("""
# The leap-year edge case.
bounds = date_filter_bounds("2024-02-01", "2024-02-29", "day")
print("Feb 2024 bounds:", bounds.start, "..", bounds.end)
print("includes 29 Feb 2024:", bounds.contains("2024-02-29"))
print("excludes 01 Mar 2024:", not bounds.contains("2024-03-01"))

# And the inverted filter, which must raise rather than silently swap.
try:
    date_filter_bounds("2026-03-31", "2026-03-01", "day")
except ValueError as exc:
    print()
    print("inverted filter raises:", exc)
"""),
        md("""
An inverted date filter must **raise**, not silently swap the bounds. A
silently-swapped filter returns a plausible-looking number for the wrong
period, and nobody ever notices.

## 6. Period over period

Comparing this month to last month is a very common request and a very
common off-by-one.

The previous period for March 2026 is February 2026 — but for a *year*
grain, it is 2025, not 2024.
"""),
        code("""
from date_helpers import previous_period

for start, end, timeframe in [
    ("2026-03-01", "2026-03-31", "month"),
    ("2026-01-01", "2026-01-31", "month"),
    ("2026-01-01", "2026-03-31", "quarter"),
    ("2026-01-01", "2026-12-31", "year"),
    ("2026-03-01", "2026-03-31", "day"),
]:
    current = date_filter_bounds(start, end, timeframe)
    previous = previous_period(start, end, timeframe)
    print(f"{current.start} .. {current.end} [{timeframe:<8}] "
          f"-> previous {previous.start} .. {previous.end}")
"""),
        code("""
# The year case, which is where the off-by-one usually lives.
previous = previous_period("2026-01-01", "2026-12-31", "year")
print("current : 2026-01-01 .. 2026-12-31")
print("previous:", previous.start, "..", previous.end)
assert previous.start.year == 2025, "the previous year is off by one"
print("✓ previous year is 2025")
"""),
        md("""
## 7. Why the spine earns its keep

The spine is not only about gaps in a chart. It is the thing that makes
these possible:

- **Week-over-week comparisons** that line up on the same weekday.
- **Cohort analysis** — you need every month between acquisition and the
  measurement date, including the ones with no activity.
- **Fiscal calendars** — a spine that knows your fiscal year starts in
  February is worth more than a month arithmetic function.
- **Safe date filters** — the filter is a join against the spine, not a
  `BETWEEN` on a string column.

## Takeaways

1. A missing row and a zero row are different things. The spine makes them
   the same thing.
2. Generate the spine; never derive it from the facts.
3. `LEFT JOIN` and `COALESCE` — an inner join throws away the rows you
   built the spine for.
4. ISO weeks start on **Monday**. Write the convention down.
5. Compute date filter bounds on the **raw** dates, before truncating.
6. An inverted date filter must raise.
7. The previous *year* is 2025, not 2024. The off-by-one lives here.
"""),
    ])
