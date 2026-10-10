---
l_id: L156
title: Using materialized views
duration: "4:30"
prereqs: ["L155"]
---

# L156 — Using materialized views

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 3. Materialized Views
> **Duration:** 4:30

## Prereqs

L155 — Understand materialized views.

## Key terms

- **Query the MV like a table** — `SELECT * FROM mv_name;`
- **`SHOW MATERIALIZED VIEWS`** — list of all MVs in scope.
- **Materialized view catalog** — `INFORMATION_SCHEMA.MATERIALIZED_VIEWS`.

## Lecture

Welcome back. Today's lecture is the practical mechanics: how
to query a materialized view, how to inspect it, and how to
verify it's serving the latest data.

### Reading the MV

A materialized view is queryable like any other table:

```sql
SELECT * FROM MV_REGION_TOTALS;
```

You can also join it to other tables, filter on it, aggregate
on it — Snowflake's query planner treats the MV as a regular
table for reads. The result is precomputed; no recomputation on
read.

### Filtering

```sql
-- Same as a normal table
SELECT *
FROM   MV_REGION_TOTALS
WHERE  total > 1000;
```

The filter is applied *after* the precomputed result is read.
There's no maintenance cost on this read; it's just a `SELECT`
over a stored result.

### Inspecting the MV

```sql
SHOW MATERIALIZED VIEWS IN SCHEMA PUBLIC;
```

The output columns include:

- `name` — the MV's name.
- `database_name`, `schema_name` — where it lives.
- `text` — the SQL definition of the MV.
- `is_secure` — whether the MV is a secure view.
- `refreshed_on` — the timestamp of the last successful refresh.
- `compilation_state` — `OK`, `ERROR`, etc.

For deep introspection, the
`INFORMATION_SCHEMA.MATERIALIZED_VIEWS` view is the same data in
a queryable form.

### When the MV is stale

By default, a materialized view refreshes *automatically* on a
schedule (frequently — every few seconds, typically). The
`refreshed_on` column tells you when the last refresh
completed. If you need to know *now*, run the query — Snowflake
will trigger a refresh if it has been too long.

### The read latency

There's a small delay between a source `INSERT` and the MV
reflecting it — typically a few seconds. For real-time use cases,
that's too slow. For dashboards, it's fine.

## Hands-on

```sql
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE TABLE SRC (id NUMBER, region VARCHAR, amount NUMBER);
INSERT INTO SRC VALUES (1, 'NA', 100), (2, 'EU', 200);

CREATE OR REPLACE MATERIALIZED VIEW MV_SRC AS
  SELECT region, SUM(amount) AS total
  FROM   SRC
  GROUP BY region;

SHOW MATERIALIZED VIEWS;
SELECT * FROM MV_SRC;

INSERT INTO SRC VALUES (3, 'NA', 50);
-- Wait a few seconds
SELECT * FROM MV_SRC;
```

## Key takeaways

- Query an MV with `SELECT`; the result is precomputed.
- `SHOW MATERIALIZED VIEWS` lists MVs in the scope.
- The `refreshed_on` column tells you the last refresh time.
- Refresh lag is typically a few seconds.

## What's next

L157 — Refresh materialized views. We dig into how refresh
works and how to force a refresh.