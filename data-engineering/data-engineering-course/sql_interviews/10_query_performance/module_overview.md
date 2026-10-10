# Module 10 — Query Performance & Optimization

> **4 lessons · 0 videos · ~2 hours**
>
> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

The module that turns a SQL candidate into a SQL engineer. Every
L5+ interview round includes some version of "this query is
slow — how do you fix it?" The only honest answer is "I've done
it, and I can explain the plan, the indexes, the joins, and the
rewrite." This module is that experience, in compressed form.

M10 is the bridge between "I can write correct SQL" and "I can
make SQL run at scale." The four lessons cover the four levers
you have: **read the plan** (M10-01), **choose the indexes**
(M10-02), **order the joins** (M10-03), and **rewrite the
query** (M10-04). Master all four and you can answer any
performance question the interviewer throws at you.

---

## What this module covers

| # | Lesson | What you'll learn |
|---|---|---|
| [40](design/01_explain_plans.md) | Reading EXPLAIN / EXPLAIN ANALYZE | Operators, red flags, worked plans in Postgres / MySQL / Snowflake / BigQuery. |
| [41](design/02_index_strategy.md) | Index Strategy | B-tree, hash, bitmap, partial, covering, composite; when each wins. |
| [42](design/03_join_optimization.md) | Join Optimization | Join order, algorithms, broadcast vs shuffle, common join bugs. |
| [43](design/04_query_rewrites.md) | Query Rewrites | The 10 most-asked "rewrite this slow query" patterns. |

---

## How to read this module

Read the lessons in order — each builds on the previous. The
EXPLAIN lesson teaches you what to look for. The indexes
lesson teaches you what to add. The joins lesson teaches you
how to order. The rewrites lesson teaches you what to change
in the query itself. Together they cover ~80% of the
performance problems you'll see in interviews and in real
pipelines.

The worked examples in each lesson are deliberately real —
Postgres plans from `pg_stat_statements`, BigQuery
`EXPLAIN`-style JSON, MySQL `EXPLAIN FORMAT=JSON`. Read them
slowly and try to predict what the plan will look like before
reading the answer.
