---
l_id: L142
title: Task history & error handling
duration: "5:00"
prereqs: ["L141"]
---

# L142 — Task history & error handling

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 1. Tasks
> **Duration:** 5:00

## Prereqs

L141 — Calling a stored procedure.

## Key terms

- **`TASK_HISTORY`** — a Snowflake table function that returns
  one row per task run, including state, error code, and
  duration.
- **State** — `SUCCEEDED`, `FAILED`, `SKIPPED`, `CANCELLED`.
- **SUSPEND_TASK_ON_ERROR** — a task parameter; if `TRUE`, the
  task is automatically suspended after a failure.

## Lecture

Welcome back. Tasks fail. Warehouses run out of credit, source
tables are missing, columns get renamed, secrets rotate. The
operational question is: *how do I know, and what do I do?*
Today's lecture is the two halves of that answer: `TASK_HISTORY`
for visibility, and the error-handling patterns that keep a
single failure from spiraling.

### Reading `TASK_HISTORY`

```sql
SELECT name,
       scheduled_time,
       state,
       error_code,
       error_message,
       query_id,
       completed_time - scheduled_time AS duration
FROM   TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
              SCHEDULED_TIME_RANGE_START => DATEADD('hour', -24, CURRENT_TIMESTAMP()),
              SCHEDULED_TIME_RANGE_END   => CURRENT_TIMESTAMP()))
ORDER BY scheduled_time DESC;
```

A typical row:

```text
NAME                SCHEDULED_TIME  STATE       ERROR_CODE  ERROR_MESSAGE         DURATION
NIGHTLY_ETL         2026-10-10 02:00  SUCCEEDED   NULL        NULL                  00:00:42
NIGHTLY_ETL         2026-10-09 02:00  FAILED      100058      Object 'X' not found  00:00:05
```

You read this to answer: which runs succeeded, which failed, and
what was the error.

### The "stop the bleeding" pattern

By default, a failing task *does not* suspend itself; it will
keep trying on its next scheduled run. If the failure is
persistent (missing column), the task will fail on every run and
fill your `TASK_HISTORY` with errors.

The fix:

```sql
ALTER TASK nightly_etl SET SUSPEND_TASK_ON_ERROR = TRUE;
```

With this, a single failure automatically suspends the task. You
get one email / one Slack alert / one PagerDuty incident instead
of 60 failures an hour.

### Recovery: where the run left off

There is no built-in "resume from this offset" — Snowflake's
model is "the next run starts from a clean state". For idempotent
tasks, that's fine. For non-idempotent tasks, the safe pattern
is:

1. Suspend the chain.
2. Fix the upstream bug.
3. Manually `CALL` the procedure or `INSERT` to backfill the
   missing data.
4. Resume the chain bottom-up.

### Common error codes

| Code | Meaning |
|---|---|
| 100058 | Object not found (renamed, dropped) |
| 002038 | Authentication / network |
| 002140 | Warehouse suspended or insufficient credit |
| 100071 | SQL compilation error (typo in task body) |
| 100051 | Runtime exception (NULL, divide-by-zero) |

A small set of codes accounts for 95% of production failures.
Wire them into your alerting.

### Alerting pattern

The most common production setup is a task that *observes*
`TASK_HISTORY`:

```sql
-- Pseudo-code
SELECT *
FROM   TABLE(INFORMATION_SCHEMA.TASK_HISTORY(...))
WHERE  state = 'FAILED'
  AND  scheduled_time > DATEADD('hour', -1, CURRENT_TIMESTAMP());
```

Run this from a separate monitoring task, and pipe failures into
Slack / PagerDuty / email.

## Hands-on

```sql
-- Force a failure: drop a column the task uses
ALTER TABLE TICK_LOG DROP COLUMN body;  -- If body is the column the task inserts

-- Wait for the next scheduled run, then:
SELECT name, state, error_code, error_message
FROM   TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE  name = 'PROC_TASK'
ORDER BY scheduled_time DESC
LIMIT 5;
```

## Key takeaways

- `INFORMATION_SCHEMA.TASK_HISTORY()` is the canonical place to
  read task run state.
- Set `SUSPEND_TASK_ON_ERROR = TRUE` for tasks that should stop
  after a single failure.
- Tasks don't have built-in retry offsets; design for
  idempotency.
- Pipe `TASK_HISTORY` failures into your alerting.

## What's next

L143 — Tasks with condition. We add `WHEN` predicates so a task
self-skips when its data is not yet ready.