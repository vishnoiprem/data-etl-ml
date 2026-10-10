---
l_id: L155
title: Understand materialized views
duration: "4:30"
prereqs: ["L154"]
---

# L155 — Understand materialized views

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 3. Materialized Views
> **Duration:** 4:30

## Prereqs

L154 — Changes clause. By now you've seen how to precompute work
with tasks, streams, and Time Travel. Materialized views are the
*declarative* version of "precompute this query".

## Key terms

- **Materialized view** — a view whose result is stored on disk
  and maintained automatically. Reads are fast; writes pay a
  maintenance cost.
- **Standard view** — a stored query that runs at read time.
  Always fresh; always re-executed.
- **Maintenance cost** — the storage and compute that Snowflake
  spends to keep the materialized view up to date.

## Lecture

Welcome to the materialized views sub-group. A **materialized
view** is a hybrid between a view and a table: it's a query whose
result is stored on disk, and Snowflake automatically keeps that
result in sync as the underlying tables change. Today we
introduce the concept and the trade-offs.

### View vs materialized view

```sql
-- A standard view: query re-runs on every SELECT
CREATE VIEW v_orders AS
  SELECT region, SUM(amount) AS total
  FROM   orders
  GROUP BY region;

-- A materialized view: result is stored; SELECTs are precomputed
CREATE MATERIALIZED VIEW mv_orders AS
  SELECT region, SUM(amount) AS total
  FROM   orders
  GROUP BY region;
```

The materialized view is *queryable like a table*:

```sql
SELECT * FROM mv_orders;  -- reads precomputed data
```

The cost: every change to `orders` triggers Snowflake to recompute
the affected portion of `mv_orders`. For a hot table, that
maintenance can be significant.

### The trade-off

| | Standard view | Materialized view |
|---|---|---|
| Freshness | Always current | Up to a few seconds behind |
| Read cost | Re-runs the query | Reads precomputed data |
| Write cost | None | Maintenance on the source |
| Storage | None | Stores the result |
| Best for | small/simple queries, ad-hoc | repeated heavy aggregations |

### When materialized views win

- A dashboard refreshes every minute with `SELECT region, SUM(amount)`.
  Without a materialized view, that aggregation runs every refresh.
  With one, it runs once per source change.
- A small set of BI users hits the same aggregate dozens of times
  per minute. Pre-compute once, read many.

### When materialized views lose

- The source changes constantly. The maintenance cost *exceeds*
  the read savings.
- The query is simple — Snowflake's normal caching (L57–L58)
  already serves it cheaply.
- The query is rare — a materialized view's maintenance is paid
  for every change, even if no one reads the result.

### An example

```sql
CREATE OR REPLACE TABLE ORDERS (id NUMBER, region VARCHAR, amount NUMBER);
INSERT INTO ORDERS
  SELECT SEQ4(), 'NA', UNIFORM(1, 1000, RANDOM()) FROM TABLE(GENERATOR(ROWCOUNT => 1000000));

CREATE MATERIALIZED VIEW MV_REGION_TOTALS AS
  SELECT region, SUM(amount) AS total
  FROM   ORDERS
  GROUP BY region;

-- Read it
SELECT * FROM MV_REGION_TOTALS;
```

After this, any `INSERT` into `ORDERS` triggers a recompute of
`MV_REGION_TOTALS`. Reads are O(1) — they hit the precomputed
result.

## Hands-on

```sql
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE TABLE ORDERS (id NUMBER, region VARCHAR, amount NUMBER);
INSERT INTO ORDERS VALUES (1, 'NA', 100), (2, 'EU', 200), (3, 'NA', 150);

CREATE MATERIALIZED VIEW MV_REGION_TOTALS AS
  SELECT region, SUM(amount) AS total
  FROM   ORDERS
  GROUP BY region;

SELECT * FROM MV_REGION_TOTALS;

INSERT INTO ORDERS VALUES (4, 'EU', 300);
-- After ~1s, MV reflects the new row.
SELECT * FROM MV_REGION_TOTALS;
```

## Key takeaways

- A materialized view stores the result of a query; reads are
  precomputed.
- Maintenance cost is paid on every source change.
- Use them for repeated, expensive aggregations.
- Avoid them for rarely-queried or constantly-changing tables.

## What's next

L156 — Using materialized views. The mechanics of reading,
querying, and inspecting a materialized view.