---
l_id: L143
title: Tasks with condition
duration: "4:30"
prereqs: ["L142"]
---

# L143 — Tasks with condition

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 1. Tasks
> **Duration:** 4:30

## Prereqs

L142 — Task history & error handling.

## Key terms

- **`WHEN`** — a boolean predicate on a task. If it evaluates
  to `FALSE`, the task skips that run.
- **SYSTEM$STREAM_HAS_DATA** — a built-in function that returns
  `TRUE` if a stream has new data. The most common `WHEN`
  predicate.
- **Self-skipping** — the property that a task decides *not to
  run* on its own, without a human intervention.

## Lecture

Welcome back. The last lecture in the Tasks sub-group covers
**conditional execution** — a task that decides for itself
whether to run. This is the difference between "I run on a
schedule" and "I run when there's actually work to do".

### The `WHEN` clause

```sql
CREATE TASK consume_stream
  WAREHOUSE = etl_wh
  SCHEDULE  = '5 MINUTE'
  WHEN      SYSTEM$STREAM_HAS_DATA('my_stream')
AS
  INSERT INTO target
  SELECT * FROM my_stream;
```

`WHEN` is a boolean expression evaluated at runtime. If
`SYSTEM$STREAM_HAS_DATA('my_stream')` is `TRUE`, the task runs;
otherwise it skips and waits for the next scheduled tick.

This is the canonical pattern for stream consumption: the task
fires every 5 minutes, but only does work when the stream has
new data.

### Other useful predicates

```sql
-- Skip if the source table is empty
WHEN (SELECT COUNT(*) FROM source) > 0

-- Skip on weekends
WHEN DAYNAME(CURRENT_TIMESTAMP()) NOT IN ('Sat', 'Sun')

-- Skip on the 29th-31st of the month
WHEN DAY(CURRENT_TIMESTAMP()) < 29

-- Combine: only run if both are true
WHEN SYSTEM$STREAM_HAS_DATA('s1') AND DAYNAME(CURRENT_TIMESTAMP()) <> 'Sat'
```

`WHEN` accepts any expression that returns a boolean. Subqueries
are allowed but expensive — Snowflake will run them every tick.

### The order of evaluation

`WHEN` is checked *after* the task's predecessor succeeds (for
child tasks) but *before* the warehouse is woken up. If `WHEN`
is `FALSE`, the warehouse is not billed for that tick. This is
the operational reason to use `WHEN` instead of an `IF` inside
the body.

### When NOT to use `WHEN`

- **Multi-tenant SLAs.** If your task must run on a hard
  schedule for compliance reasons, don't add a `WHEN` predicate.
- **Complex logic that hides in the body.** If the decision
  involves 10 inputs, it's clearer to put the logic inside the
  task body and let it return early.

## Hands-on

```sql
-- Create a stream and a conditional consumer
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE TABLE SOURCE_TBL (n NUMBER);
INSERT INTO SOURCE_TBL VALUES (1);

CREATE OR REPLACE STREAM source_stream ON TABLE SOURCE_TBL;

CREATE OR REPLACE TABLE TARGET_TBL (n NUMBER);

CREATE OR REPLACE TASK consume_when_ready
  WAREHOUSE = compute_wh
  SCHEDULE  = '1 MINUTE'
  WHEN      SYSTEM$STREAM_HAS_DATA('DEMO_DB.PUBLIC.SOURCE_STREAM')
AS
  INSERT INTO TARGET_TBL SELECT n FROM SOURCE_STREAM;

ALTER TASK consume_when_ready RESUME;

-- Wait one tick. No rows in stream yet -> task SKIPPED.
SELECT state FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE name = 'CONSUME_WHEN_READY'
ORDER BY scheduled_time DESC LIMIT 3;

-- Now insert into source
INSERT INTO SOURCE_TBL VALUES (2), (3);

-- Wait one tick. Stream has data -> task SUCCEEDED, 2 rows in target.
SELECT * FROM TARGET_TBL;
```

## Key takeaways

- `WHEN` predicates let a task skip a run without a human
  decision.
- `SYSTEM$STREAM_HAS_DATA` is the canonical predicate for
  CDC-style tasks.
- Skipped ticks do not wake the warehouse; no bill.
- Don't over-use — the body is the right place for complex
  logic.

## What's next

We move on to **Streams** (L144–L154), the change-data-capture
primitive that pairs naturally with `WHEN`-gated tasks.