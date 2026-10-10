---
l_id: L139
title: Understand tree of tasks
duration: "4:30"
prereqs: ["L138"]
---

# L139 — Understand tree of tasks

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 1. Tasks
> **Duration:** 4:30

## Prereqs

L138 — Using CRON.

## Key terms

- **Predecessor** — the task that runs *before* (and triggers)
  the current task.
- **`AFTER`** — the parameter that attaches a child task to its
  predecessor.
- **Finalizer** — a task that runs *after* a stream consumer;
  used to commit a stream offset.
- **DAG** — directed acyclic graph. A task tree is a Snowflake
  DAG; the engine guarantees no cycles.

## Lecture

Welcome back. So far every task we've built has been a single
node with a CRON schedule. Real pipelines are not single nodes.
A nightly ELT usually has: extract → transform → publish → notify.
Each stage depends on the previous one, and a failure in the
middle should stop the rest. Tasks give you that orchestration
natively, with no Airflow, no Dagster, no external scheduler.

### A simple tree

```text
        root_task          (every night at 2am)
            │ AFTER
            ▼
        transform_task     (after root succeeds)
            │ AFTER
            ▼
        publish_task       (after transform succeeds)
```

In Snowflake terms:

```sql
-- 1. Root has a schedule, no predecessor
CREATE TASK root_task
  WAREHOUSE = etl_wh
  SCHEDULE  = 'USING CRON 0 2 * * * UTC'
AS INSERT INTO raw_events SELECT ...;

-- 2. Transform runs after root
CREATE TASK transform_task
  WAREHOUSE = etl_wh
  AFTER     root_task
AS INSERT INTO clean_events SELECT ... FROM raw_events;

-- 3. Publish runs after transform
CREATE TASK publish_task
  WAREHOUSE = etl_wh
  AFTER     transform_task
AS INSERT INTO marts.dim_customer SELECT ... FROM clean_events;
```

The keyword `AFTER` is what wires the tree together. Note that
the children have **no `SCHEDULE`** — they run only when the
predecessor succeeds.

### Resume order

When you suspend or resume a tree, the order matters. To resume
a 3-task chain, you resume from the *bottom up*:

```sql
-- 1. Make sure root is suspended
ALTER TASK root_task SUSPEND;
ALTER TASK transform_task SUSPEND;
ALTER TASK publish_task SUSPEND;

-- 2. Resume bottom-up
ALTER TASK publish_task    RESUME;
ALTER TASK transform_task  RESUME;
ALTER TASK root_task       RESUME;
```

Snowflake won't let you resume a child whose parent is still
suspended. This is intentional: it ensures you don't accidentally
trigger a partial pipeline.

### Failure semantics

If `transform_task` fails, `publish_task` is *not* triggered. The
root task's next scheduled run will try the chain again, but
the offset/state from the failure is preserved. This is the
"all-or-nothing per run" property that makes tasks a viable
orchestrator.

### Use cases

- ELT (extract → transform → publish).
- Data quality checks (validate → quarantine or promote).
- Notification (publish → Slack webhook via a stored proc).
- Stream consumption (consume → commit).

## Hands-on

```sql
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE TABLE STEP_A (id NUMBER);
CREATE OR REPLACE TABLE STEP_B (id NUMBER);
CREATE OR REPLACE TABLE STEP_C (id NUMBER);

CREATE OR REPLACE TASK t_a
  WAREHOUSE = compute_wh
  SCHEDULE  = 'USING CRON */2 * * * * UTC'
AS INSERT INTO STEP_A VALUES (SEQ4());

CREATE OR REPLACE TASK t_b
  WAREHOUSE = compute_wh
  AFTER     t_a
AS INSERT INTO STEP_B SELECT id FROM STEP_A;

CREATE OR REPLACE TASK t_c
  WAREHOUSE = compute_wh
  AFTER     t_b
AS INSERT INTO STEP_C SELECT id * 10 FROM STEP_B;

-- Resume bottom-up
ALTER TASK t_c RESUME;
ALTER TASK t_b RESUME;
ALTER TASK t_a RESUME;

-- Wait 4 minutes, then
SELECT 'A' AS step, COUNT(*) FROM STEP_A
UNION ALL SELECT 'B', COUNT(*) FROM STEP_B
UNION ALL SELECT 'C', COUNT(*) FROM STEP_C;
```

## Key takeaways

- A task tree is built with the `AFTER` parameter.
- Children have no `SCHEDULE`; they run when the predecessor
  succeeds.
- Resume tasks bottom-up; Snowflake rejects out-of-order
  resumes.
- Failures stop the chain — that is the right default for
  pipelines.

## What's next

L140 — Creating trees of tasks. We build a real production
pipeline and add the suspend-and-resume safety net.