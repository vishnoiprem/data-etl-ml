---
l_id: L157
title: Refresh materialized views
duration: "4:30"
prereqs: ["L156"]
---

# L157 — Refresh materialized views

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 3. Materialized Views
> **Duration:** 4:30

## Prereqs

L156 — Using materialized views.

## Key terms

- **Automatic refresh** — Snowflake's default; MVs are kept in
  sync without manual intervention.
- **Manual refresh** — a forced re-computation; rarely needed.
- **Refresh lag** — the time between a source change and the
  MV reflecting it.
- **`ALTER MATERIALIZED VIEW ... SUSPEND / RESUME`** — pause
  and resume automatic refresh.

## Lecture

Welcome back. Today's lecture is the *refresh mechanics* of a
materialized view. By default, Snowflake keeps MVs in sync
automatically; understanding when to override that behavior is
the goal of this lecture.

### Automatic refresh

Snowflake's default is automatic. After every change to the
underlying tables, Snowflake schedules a background refresh
that recomputes the affected portion of the MV. The refresh is
*incremental* where possible — only the changed rows are
re-aggregated.

```text
source INSERT → Snowflake detects → schedules MV refresh → 1-5s later, MV is current
```

In the typical case, the lag is one to five seconds. For a
heavily-used MV with constant source churn, the lag can be
higher.

### When to manually refresh

In production, the answer is "almost never". The two cases
where a manual refresh is useful:

1. **A bulk load.** You just inserted 100M rows. The automatic
   refresh will catch up, but you want to validate that the
   MV is current before a downstream job runs. A manual refresh
   makes that synchronous.
2. **A schema change.** Renaming a column or changing a UDF
   used by the MV. Sometimes Snowflake needs a manual nudge to
   pick up the change.

```sql
-- Force a refresh
ALTER MATERIALIZED VIEW MV_REGION_TOTALS REFRESH;
```

The `REFRESH` keyword triggers a synchronous refresh. The
statement blocks until the refresh is complete.

### Suspending refresh

If you know the source is going to be heavily mutated in the
near future, you can pause the MV's refresh to save compute:

```sql
ALTER MATERIALIZED VIEW MV_REGION_TOTALS SUSPEND;
-- Source is now free to change; MV becomes stale.
-- Do your bulk load.
ALTER MATERIALIZED VIEW MV_REGION_TOTALS RESUME;
-- The MV catches up on the next automatic refresh.
```

A suspended MV can still be queried — but the data is stale.
Most production MVs run continuously; suspension is reserved
for big loads.

### Inspecting refresh state

```sql
SHOW MATERIALIZED VIEWS LIKE 'MV_REGION_TOTALS';
-- Look at: "behind_by" (in seconds) and "refreshed_on"
```

The `behind_by` column tells you the current lag in seconds. A
production dashboard should alert if `behind_by` exceeds your
SLA.

### When refresh is too costly

If a refresh consumes more compute than the read savings, you
have two options:

1. **Re-architect.** The MV is too aggressive — try a smaller
   `WHERE` clause or fewer grouping columns.
2. **Replace with a streaming pipeline.** Materialized views
   are great for occasional refreshes; for constant source
   changes, a task-driven pipeline is often cheaper.

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

-- Force a refresh
ALTER MATERIALIZED VIEW MV_SRC REFRESH;

-- Suspend, insert, query stale result, resume
ALTER MATERIALIZED VIEW MV_SRC SUSPEND;
INSERT INTO SRC VALUES (3, 'NA', 999);
SELECT * FROM MV_SRC;  -- still 2 rows
ALTER MATERIALIZED VIEW MV_SRC RESUME;
SELECT * FROM MV_SRC;  -- now 3 rows
```

## Key takeaways

- Snowflake refreshes MVs automatically — usually every few
  seconds.
- `ALTER MATERIALIZED VIEW ... REFRESH` forces a synchronous
  refresh.
- `SUSPEND` / `RESUME` pause and resume automatic refresh.
- If refresh is too costly, re-architect or use a task.

## What's next

L158 — Maintenance costs. The detailed cost model for MVs.