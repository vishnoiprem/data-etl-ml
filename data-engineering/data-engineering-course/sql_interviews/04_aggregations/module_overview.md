# Module 04 — Aggregations

> **7 lessons · 0 videos · ~1.5 hours**
>
> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

Aggregations are where SQL turns from "filter rows" to
"compute summaries". M04 covers the patterns you'll use to
build dashboards and reports: counting distinct things,
conditional aggregation, percentiles, and the rare ROLLUP /
CUBE / GROUPING SETS syntax.

By the end of M04 you should be comfortable converting any
"show me X by Y" question into a single query, and any
"show me X by Y for some condition Z" into a conditional
aggregate inside the same query.

---

## What this module covers

| # | Lesson | What you'll learn |
|---|---|---|
| [21](design/21_count_distinct.md) | COUNT vs COUNT(DISTINCT) | When each is right. |
| [22](design/22_sum_avg_group_by.md) | SUM, AVG with GROUP BY | The basic "stats by group" shape. |
| [23](design/23_having_vs_where.md) | HAVING vs WHERE | Filters before vs after aggregation. |
| [24](design/24_conditional_agg.md) | Conditional aggregation with CASE inside aggregates | The pivot query. |
| [25](design/25_rollup_cube.md) | ROLLUP and CUBE | Multi-level subtotals. |
| [26](design/26_grouping_sets.md) | GROUPING SETS | Explicit multi-level aggregation. |
| [27](design/27_percentile_median.md) | Percentile and median approximations | Approximations in SQLite; exact in PostgreSQL. |

---

## How to read this module

M04 builds on M02. If you haven't done M02, do that first.
The lessons are short and dense — read each, type out the
example, then move on.
