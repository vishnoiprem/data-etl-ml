---
l_id: L13
title: Manage warehouses
duration: "8:00"
prereqs: ["L12"]
downloads: []
---

# L13 — Manage Warehouses

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 2 — Getting Started
> **Duration:** ~8:00

## Prereqs

L10–L12 — Setting up a warehouse. You should have at least one
warehouse created.

## Key terms

- **`ALTER WAREHOUSE`** — change size, scaling policy,
  auto-suspend, comment, or rename a warehouse.
- **`SHOW WAREHOUSES`** — list all warehouses and their
  properties.
- **Query History** — UI page listing every query that has
  run, with warehouse, bytes scanned, duration, and
  queued time.
- **WAREHOUSE_METERING_HISTORY** — account_usage view that
  shows credit usage per warehouse per hour.

## Lecture

This lecture covers the day-2 operations: resizing, restarting,
monitoring credit usage, and troubleshooting slow queries. Most
of this is information you can get from the UI; we'll also
show the SQL views for programmatic monitoring.

### Resizing — `ALTER WAREHOUSE`

```sql
-- Resize on the fly
ALTER WAREHOUSE LOADING_WH SET WAREHOUSE_SIZE = 'XLARGE';

-- Drop back down
ALTER WAREHOUSE LOADING_WH SET WAREHOUSE_SIZE = 'LARGE';
```

Resizing is **online**. Active queries finish on the current
cluster; new queries use the new size on the next start.

> **Watch out.** A warehouse that resizes up while running
> will stay at the larger size until you resize it back, even
> if the workload drops. The scaling policy controls
> multi-cluster behavior, not single-cluster resize.

### Suspend / resume

```sql
ALTER WAREHOUSE LOADING_WH SUSPEND;
ALTER WAREHOUSE LOADING_WH RESUME;
```

Manual suspend is useful when you want to guarantee a
warehouse won't be used — e.g. during a maintenance window.

### Monitoring credit usage

The most useful account_usage views:

```sql
-- Credit usage per warehouse per hour (last 30 days)
SELECT warehouse_name,
       DATE_TRUNC('hour', start_time) AS hr,
       SUM(credits_used) AS credits
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD('day', -7, CURRENT_TIMESTAMP())
GROUP BY 1, 2
ORDER BY hr DESC;
```

This is the view to put into a dashboard. Group by
`warehouse_name` and bucket by day or hour.

### Monitoring query performance

```sql
-- Top 20 longest-running queries in the last 24 hours
SELECT query_id,
       user_name,
       warehouse_name,
       total_elapsed_time / 1000  AS seconds,
       bytes_scanned / 1024 / 1024 AS mb_scanned,
       query_text
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE start_time >= DATEADD('hour', -24, CURRENT_TIMESTAMP())
ORDER BY total_elapsed_time DESC
LIMIT 20;
```

`QUERY_HISTORY` is the operational view you'll use most.
Combine with the Query Profile (UI) for deep dives.

### Common operational tasks

| Task | SQL |
|---|---|
| List warehouses | `SHOW WAREHOUSES;` |
| Describe a warehouse | `DESC WAREHOUSE my_wh;` |
| Resize | `ALTER WAREHOUSE my_wh SET WAREHOUSE_SIZE = 'XLARGE';` |
| Change auto-suspend | `ALTER WAREHOUSE my_wh SET AUTO_SUSPEND = 300;` |
| Suspend | `ALTER WAREHOUSE my_wh SUSPEND;` |
| Resume | `ALTER WAREHOUSE my_wh RESUME;` |
| Rename | `ALTER WAREHOUSE my_wh RENAME TO new_name;` |
| Drop | `DROP WAREHOUSE my_wh;` |

### Permissions needed

To manage a warehouse, your role needs:

- `OWNERSHIP` — full control (rename, drop)
- `OPERATE` — resume/suspend/abort
- `MONITOR` — see usage and query history
- `USAGE` — submit queries to the warehouse

`SYSADMIN` has all of these by default on the warehouses it
creates.

## Hands-on

```sql
-- Resize, suspend, resume, drop
USE ROLE SYSADMIN;

ALTER WAREHOUSE ANALYST_WH SET WAREHOUSE_SIZE = 'SMALL';
ALTER WAREHOUSE ANALYST_WH SUSPEND;
ALTER WAREHOUSE ANALYST_WH RESUME;

-- Look at recent credit usage
SELECT warehouse_name,
       SUM(credits_used) AS credits_30d
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY credits_30d DESC;
```

## Quiz prep

- Which view shows per-warehouse credit usage? (`SNOWFLAKE
  .ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY`)
- Which view shows query performance history?
  (`SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY`)
- Is resizing a warehouse online or does it require a
  restart? (Online — active queries finish, new ones use
  the new size on the next start)

## What's next

Next up is **L14 — Scaling policy**, where we cover the
scaling policy options for multi-cluster warehouses.
