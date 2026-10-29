---
l_id: L160
title: Limitations + recap
duration: "4:00"
prereqs: ["L159"]
---

# L160 — Limitations + recap

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 3. Materialized Views
> **Duration:** 4:00

## Prereqs

L159 — When to use materialized views.

## Key terms

- **MV hard limit** — a constraint Snowflake imposes on the
  query that defines a materialized view. Some `SELECT`
  features cannot be used.
- **Dynamic table** — Snowflake's newer alternative to MVs
  with a more flexible query language.

## Lecture

Welcome to the last lecture in the materialized views sub-group.
Today we cover the hard limits — what a materialized view
*cannot* do — and recap the section.

### Hard limits

A materialized view's defining query has restrictions. The most
important:

- **No `JOIN` of multiple tables.** Single-table aggregations
  only.
- **No `UNION`.** Single query block.
- **No `MIN/MAX` as the only aggregate.** `SUM`, `COUNT`,
  `AVG` are fine; `MIN`/`MAX` is allowed only in combination
  with other aggregates.
- **No `LIMIT`.**
- **No `ORDER BY`.**
- **No non-deterministic functions** like `CURRENT_TIMESTAMP`,
  `RANDOM`, `SEQ4`.

In practice, this means a materialized view is best for
single-table `SUM/COUNT/AVG` aggregations. Anything more
complex should be a dynamic table or a task-driven pipeline.

### Performance considerations

- **Clustering.** Cluster the *source* table on the same
  columns the MV aggregates by. Refresh becomes cheaper.
- **Filter pushdown.** A `WHERE` clause in the MV definition
  reduces the data the MV must store; always filter when
  possible.

### When to upgrade to dynamic tables

Snowflake's **dynamic tables** are the modern alternative to
materialized views. They support:

- joins
- window functions
- arbitrary expressions
- explicit refresh scheduling

If your MV's query is hitting the hard limits above, a dynamic
table is the right next step. (Dynamic tables are out of scope
for this course; they're the natural follow-up.)

### The recap

| Lecture | Takeaway |
|---|---|
| L155 | MVs precompute a query's result; reads are O(1) |
| L156 | Query MVs like tables; `SHOW MATERIALIZED VIEWS` |
| L157 | Auto-refresh; manual `REFRESH`; `SUSPEND` / `RESUME` |
| L158 | Cost = refresh + storage − read savings |
| L159 | Use for stable, expensive, often-queried aggregates |
| L160 | Hard limits: single-table, no joins, simple aggregations |

### The one-slide summary

A materialized view is a "precomputed aggregate on a single,
moderately-changing table, queried often, in a stable way". If
your workload matches that profile, an MV is a clean win. If
not, pick a different tool.

## Hands-on

```sql
-- Try to create a multi-table MV (will fail)
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE TABLE A (id NUMBER, val NUMBER);
CREATE OR REPLACE TABLE B (id NUMBER, val NUMBER);
INSERT INTO A VALUES (1, 100);
INSERT INTO B VALUES (1, 200);

-- This will fail with a hard-limit error
CREATE MATERIALIZED VIEW MV_BAD AS
  SELECT A.id, SUM(A.val + B.val) AS total
  FROM A JOIN B ON A.id = B.id
  GROUP BY A.id;
```

## Key takeaways

- MVs are limited to single-table, simple aggregations.
- For multi-table joins, use a dynamic table or a pipeline.
- The recap: MVs win for stable, often-queried, expensive
  aggregates on moderately-changing sources.
- Always measure with `METERING_HISTORY`.

## What's next

We move on to **Data Masking** (L161–L165), the column-level
security primitive.