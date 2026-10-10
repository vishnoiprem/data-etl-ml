---
l_id: L137
title: Creating tasks
duration: "5:00"
prereqs: ["L136"]
---

# L137 — Creating tasks

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 1. Tasks
> **Duration:** 5:00

## Prereqs

L136 — Understanding tasks.

## Key terms

- **`CREATE TASK`** — the DDL for tasks.
- **`WAREHOUSE`** — explicit warehouse, or `USER_TASK_MANAGED_*`
  for serverless.
- **`SCHEDULE`** — `N MINUTE` for intervals, `'CRON expr'` for
  cron-style, or omitted if it's a child task.
- **`SUSPEND / RESUME`** — control commands.

## Lecture

Welcome back. Today we walk the full `CREATE TASK` syntax, the
parameter options that matter, and the most common production
gotchas (especially around suspended-by-default and the
`ALLOW_OVERLAPPING_EXECUTION` flag).

### The full syntax

```sql
CREATE [ OR REPLACE ] TASK [ IF NOT EXISTS ] <name>
  WAREHOUSE              = <wh>
  [ SCHEDULE             = '<interval or CRON>' ]
  [ ALLOW_OVERLAPPING_EXECUTION = TRUE | FALSE ]
  [ USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE = '<X-SMALL|...|X-LARGE>' ]
  [ USER_TASK_TIMEOUT_MS = <ms> ]
  [ COMMENT               = '<text>' ]
AS
  <single SQL statement>;
```

### `WAREHOUSE` vs serverless

The `WAREHOUSE` parameter is required unless you opt into
**serverless tasks**:

```sql
-- User-managed (you size and pay for the warehouse)
CREATE TASK t1 WAREHOUSE = compute_wh SCHEDULE = '60 MINUTE'
AS INSERT INTO log VALUES ('tick');

-- Serverless (Snowflake sizes and bills per execution)
CREATE TASK t2
  USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE = 'MEDIUM'
  SCHEDULE = '60 MINUTE'
AS INSERT INTO log VALUES ('tick');
```

Serverless is great for sporadic or unpredictable tasks; user-
managed is cheaper for steady, predictable workloads.

### Suspended by default

**Tasks are created in the suspended state.** This is intentional:
Snowflake doesn't want a brand-new task to fire on its own. You
must explicitly `RESUME`:

```sql
ALTER TASK demo_task RESUME;
```

In a production deployment, `CREATE TASK ... RESUME` is the
common pattern to skip the manual `ALTER`:

```sql
CREATE OR REPLACE TASK demo_task
  WAREHOUSE = compute_wh
  SCHEDULE  = '60 MINUTE'
AS
  INSERT INTO log VALUES ('tick');

ALTER TASK demo_task RESUME;
```

### `ALLOW_OVERLAPPING_EXECUTION`

By default, a task cannot run two instances of itself at the same
time. If a run takes longer than the schedule interval, the next
run is *skipped*, not queued. This is a back-pressure mechanism.
If you need overlapping runs (e.g. a 5-minute task scheduled every
minute), set:

```sql
ALTER TASK demo_task SET ALLOW_OVERLAPPING_EXECUTION = TRUE;
```

### Timeouts

`USER_TASK_TIMEOUT_MS` defaults to 60 minutes (1 hour). A task
that runs longer is cancelled. Increase the limit if you have a
known long-running workload.

### Common pitfalls

- **Multiple SQL statements.** A task body is *one* statement. If
  you need many, wrap them in a stored procedure (L141).
- **Time zone.** `SCHEDULE = 'CRON ...'` uses UTC unless you
  specify `TIMEZONE`.
- **Permissions.** The role running the task must have the
  privileges the task body needs (`INSERT` on the target table,
  `USAGE` on the warehouse, etc.).

## Hands-on

```sql
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE TABLE TICK_LOG (ts TIMESTAMP_NTZ, body VARCHAR);

CREATE OR REPLACE TASK tick_task
  WAREHOUSE = compute_wh
  SCHEDULE  = '1 MINUTE'
  COMMENT   = 'Append a row every minute'
AS
  INSERT INTO TICK_LOG VALUES (CURRENT_TIMESTAMP(), 'tick');

ALTER TASK tick_task RESUME;

SHOW TASKS;
-- Confirm "state" is "started".

-- Wait 2 minutes
SELECT * FROM TICK_LOG ORDER BY ts DESC LIMIT 5;

ALTER TASK tick_task SUSPEND;
```

## Key takeaways

- `CREATE TASK` requires a warehouse (or serverless sizing).
- Tasks are created suspended; explicitly `RESUME`.
- `ALLOW_OVERLAPPING_EXECUTION = FALSE` (default) prevents backlogs.
- The body is a single SQL statement; use a stored procedure for
  multi-statement logic.

## What's next

L138 — Using CRON. We swap the simple `'N MINUTE'` for proper
`CRON` expressions.