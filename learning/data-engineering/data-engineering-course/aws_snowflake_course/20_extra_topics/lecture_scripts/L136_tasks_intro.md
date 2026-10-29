---
l_id: L136
title: Understanding tasks
duration: "4:00"
prereqs: ["L135"]
---

# L136 — Understanding tasks

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 1. Tasks
> **Duration:** 4:00

## Prereqs

L135 — Sampling data: Hands-on. The skills we built so far (clones,
swap, time travel, shares) need a scheduler to run automatically.
That's what tasks are for.

## Key terms

- **Task** — a Snowflake object that runs a single SQL statement on
  a schedule. Equivalent to a cron job, but stored inside
  Snowflake.
- **Schedule** — a `CRON` or `MINUTES` interval. Tasks can also
  run only on a "trigger" (no schedule).
- **Root task** — a task with no predecessor; it has a schedule.
- **Child task** — a task triggered by a predecessor's success.
- **Serverless tasks** — tasks whose compute is managed by
  Snowflake (you pay per execution, not by warehouse size).

## Lecture

Welcome to the extra topics section, and the first sub-group: tasks.
A **task** is a Snowflake-managed scheduled job. You define it in
SQL, give it a schedule, and Snowflake runs it — forever, or until
you `DROP` it — without any external scheduler. Tasks are the
glue that turns one-off SQL into a continuously running pipeline.

### What a task is

```sql
CREATE TASK my_task
  WAREHOUSE = compute_wh
  SCHEDULE  = '60 MINUTE'
AS
  INSERT INTO log_table VALUES (CURRENT_TIMESTAMP(), 'tick');
```

Three pieces:

- `WAREHOUSE` — which warehouse to use for the computation. (Use
  `USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE` for serverless tasks.)
- `SCHEDULE` — how often to run. `'60 MINUTE'` means once an hour.
- `AS` — the single SQL statement that runs each time.

That's the entire task. One `CREATE`, one `DROP`. Snowflake handles
the rest.

### Tasks vs Snowpipe

Both run things on a schedule, but they're not the same:

| | Task | Snowpipe |
|---|---|---|
| Trigger | cron / interval | S3/Azure/GCS file arrival |
| Use case | scheduled SQL | continuous file load |
| Idempotency | you write it | guaranteed by pipe |

If you want to "load data when a file lands", use Snowpipe (L79).
If you want to "transform the orders table every night at 2am",
use a task.

### The hierarchy: root and child tasks

A task can have a *predecessor*. The predecessor's successful
completion triggers the child. The child is then a **child task**.
The top of any tree is a **root task** that has a schedule; it
fires the chain.

```text
        root_task        (every night at 2am)
            │
            ▼
        stage_task       (after root succeeds)
            │
            ▼
        publish_task     (after stage succeeds)
```

This is the only way to express "run B, but only after A" inside
Snowflake without writing external orchestration. We'll see this in
L139–L140.

### Where tasks live

Tasks are schema-level objects. To create one, you need `CREATE
TASK` on the schema. The execution context is the role that
created the task (or whoever owns it at runtime).

## Hands-on

```sql
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

-- A simple task: append a row to a log table every minute
CREATE OR REPLACE TABLE TASK_LOG (ts TIMESTAMP_NTZ, msg VARCHAR);

CREATE OR REPLACE TASK demo_task
  WAREHOUSE = compute_wh
  SCHEDULE  = '1 MINUTE'
AS
  INSERT INTO TASK_LOG VALUES (CURRENT_TIMESTAMP(), 'tick');

-- Start it (tasks are created suspended by default)
ALTER TASK demo_task RESUME;

-- Wait a couple of minutes, then:
SELECT * FROM TASK_LOG ORDER BY ts DESC LIMIT 10;

-- Always clean up
ALTER TASK demo_task SUSPEND;
DROP TASK demo_task;
```

## Key takeaways

- A task is a scheduled SQL statement that lives inside Snowflake.
- It has a warehouse (or is serverless), a schedule, and a body.
- Tasks are created suspended; you must `ALTER TASK ... RESUME`.
- Tasks form a tree: root has a schedule, children follow.

## What's next

L137 — Creating tasks. We cover the full `CREATE TASK` syntax,
parameters, and the most common gotchas.