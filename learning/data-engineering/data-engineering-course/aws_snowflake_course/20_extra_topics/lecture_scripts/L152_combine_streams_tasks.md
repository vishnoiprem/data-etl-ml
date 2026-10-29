---
l_id: L152
title: Combine streams & tasks
duration: "5:00"
prereqs: ["L151"]
---

# L152 — Combine streams & tasks

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 2. Streams
> **Duration:** 5:00

## Prereqs

L151 — Process all data changes.

## Key terms

- **Producer/consumer pipeline** — a source table → stream →
  consumer task → target table. The canonical pattern.
- **Finalizer task** — a task that runs after the consumer
  task, used to "commit" the stream by recreating it.
- **Idempotency via stream recreation** — drop and recreate the
  stream at the end of the consumer run; this is the equivalent
  of committing a transaction.

## Lecture

Welcome back. Today we put streams and tasks together into the
*end-to-end production pattern* — the one you'll see in 80% of
Snowflake ELT pipelines in the wild. Producer table → stream →
conditional task → consumer procedure → target table. Plus a
finalizer for guaranteed commit semantics.

### The full pattern

```sql
-- 1. Source
CREATE OR REPLACE TABLE src (id NUMBER, val VARCHAR);

-- 2. Stream
CREATE OR REPLACE STREAM src_stream ON TABLE src;

-- 3. Target
CREATE OR REPLACE TABLE tgt (id NUMBER, val VARCHAR);

-- 4. Consumer procedure
CREATE OR REPLACE PROCEDURE sp_consume()
RETURNS STRING LANGUAGE SQL AS
$$
BEGIN
  MERGE INTO tgt t
  USING (SELECT id, val,
                METADATA$ACTION   AS action,
                METADATA$ISUPDATE AS is_update
         FROM   src_stream) s
  ON t.id = s.id
  WHEN MATCHED AND s.action = 'DELETE' AND s.is_update = FALSE THEN DELETE
  WHEN MATCHED AND s.action = 'INSERT' AND s.is_update = TRUE  THEN UPDATE SET t.val = s.val
  WHEN NOT MATCHED AND s.action = 'INSERT' AND s.is_update = FALSE
       THEN INSERT (id, val) VALUES (s.id, s.val);
  RETURN 'OK';
END;
$$;

-- 5. Finalizer procedure
CREATE OR REPLACE PROCEDURE sp_finalize()
RETURNS STRING LANGUAGE SQL AS
$$
BEGIN
  -- Drop and recreate the stream to "commit" the consumption
  DROP STREAM src_stream;
  CREATE STREAM src_stream ON TABLE src;
  RETURN 'committed';
END;
$$;

-- 6. Consumer task (every minute, only if stream has data)
CREATE OR REPLACE TASK consume_task
  WAREHOUSE = etl_wh
  SCHEDULE  = '1 MINUTE'
  WHEN      SYSTEM$STREAM_HAS_DATA('demo_db.public.src_stream')
AS
  CALL sp_consume();

-- 7. Finalizer (after consumer succeeds)
CREATE OR REPLACE TASK finalize_task
  WAREHOUSE = etl_wh
  AFTER     consume_task
AS
  CALL sp_finalize();
```

### Resume order (bottom-up)

```sql
ALTER TASK finalize_task RESUME;
ALTER TASK consume_task  RESUME;
```

`finalize_task` runs only after `consume_task` succeeds. If the
consumer fails, the stream is *not* committed; the next
`consume_task` run will see the same rows and retry.

### Why drop-and-recreate

Recreating the stream is Snowflake's way of *committing* the
stream's offset. The next read starts at the new offset (now),
and the previously-processed rows are gone from the stream's
view. If the consumer is replayed, the rows it processed are
no longer in the stream — guaranteed idempotency.

This is the alternative to using `SYSTEM$STREAM_GET_OFFSET` as
a checkpoint. Both work; drop-and-recreate is simpler to
reason about.

### The operational dashboard

```sql
-- Streams and their staleness
SELECT TABLE_NAME, STALE, STALE_AFTER
FROM   TABLE(INFORMATION_SCHEMA.SHOW_STREAMS())
WHERE  TABLE_SCHEMA = 'PUBLIC';

-- Recent task runs
SELECT name, state, error_code, completed_time
FROM   TABLE(INFORMATION_SCHEMA.TASK_HISTORY(...));
```

## Hands-on

Build the full 7-step pattern above in a sandbox schema. Run a
mix of `INSERT`, `UPDATE`, and `DELETE` against `src`; confirm
`consume_task` picks them up and `tgt` matches.

## Key takeaways

- The canonical pattern is: source → stream → consumer task →
  finalizer task.
- `WHEN SYSTEM$STREAM_HAS_DATA` is the gate.
- Drop-and-recreate the stream in the finalizer to "commit"
  the consumption.
- Resume tasks bottom-up.

## What's next

L153 — Append-only streams. A simpler stream type that only
tracks `INSERT` operations, useful when you don't need to
handle updates or deletes.