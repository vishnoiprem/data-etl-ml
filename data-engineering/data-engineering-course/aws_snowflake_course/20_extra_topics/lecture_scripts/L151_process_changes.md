---
l_id: L151
title: Process all data changes
duration: "5:00"
prereqs: ["L150"]
---

# L151 — Process all data changes

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 2. Streams
> **Duration:** 5:00

## Prereqs

L150 — DELETE operation.

## Key terms

- **End-to-end consumer** — the full pipeline that picks up
  every change from a source table and applies it to a target.
- **End-to-end pattern** — the union of L145, L146, and L150 in
  a single procedure.

## Lecture

Welcome back. Today is the wrap-up for the DML lecture trio
(INSERT / UPDATE / DELETE). We assemble the minimal-set pattern
from L149 into a single, reusable stored procedure, and we add
the **idempotency loop** that handles the common "consumer
re-runs after a partial failure" scenario.

### The full procedure

```sql
CREATE OR REPLACE PROCEDURE sp_consume_src()
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
  MERGE INTO TGT t
  USING (
    SELECT id, val,
           METADATA$ACTION   AS action,
           METADATA$ISUPDATE AS is_update
    FROM   src_stream
  ) s
  ON t.id = s.id
  WHEN MATCHED
       AND s.action = 'DELETE' AND s.is_update = FALSE
       THEN DELETE
  WHEN MATCHED
       AND s.action = 'INSERT' AND s.is_update = TRUE
       THEN UPDATE SET t.val = s.val
  WHEN NOT MATCHED
       AND s.action = 'INSERT' AND s.is_update = FALSE
       THEN INSERT (id, val) VALUES (s.id, s.val);

  RETURN 'OK';
END;
$$;
```

One procedure, three branches, one transaction. Calling it
consumes the stream.

### The idempotency loop

A re-run after a partial failure should produce the same result.
The key is to verify the source and target converge after the
`MERGE`:

```sql
-- Idempotency check (after MERGE)
SELECT COUNT(*) AS drift
FROM   TGT t
FULL OUTER JOIN SRC s ON t.id = s.id
WHERE  t.id IS NULL OR s.id IS NULL;

-- Drift should be 0
```

If `drift > 0`, the consumer missed something; re-run. In
practice the `MERGE` is atomic so this check is almost always
zero on the first try.

### Calling it from a task

```sql
CREATE OR REPLACE TASK consume_src_task
  WAREHOUSE = etl_wh
  SCHEDULE  = '5 MINUTE'
  WHEN      SYSTEM$STREAM_HAS_DATA('DEMO_DB.PUBLIC.SRC_STREAM')
AS
  CALL sp_consume_src();
```

This is the L143 + L152 combination. The task wakes up every
5 minutes, checks for stream data, runs the procedure, and
stops.

### When the source and target diverge

If you have an emergency and the consumer has been paused, the
stream may go stale (L148). The recovery is:

```sql
DROP STREAM src_stream;
CREATE STREAM src_stream ON TABLE SRC;
-- The new stream is empty; only future changes are recorded.
-- Backfill the target with a one-shot MERGE FROM SRC TO TGT.
```

After that, resume the consumer.

## Hands-on

```sql
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE TABLE SRC (id NUMBER, val VARCHAR);
CREATE OR REPLACE TABLE TGT (id NUMBER, val VARCHAR);
CREATE OR REPLACE STREAM src_stream ON TABLE SRC;

CREATE OR REPLACE PROCEDURE sp_consume()
RETURNS STRING LANGUAGE SQL AS
$$
BEGIN
  MERGE INTO TGT t
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

-- Generate a mix of changes
INSERT INTO SRC VALUES (1, 'a'), (2, 'b');
UPDATE SRC SET val = 'A' WHERE id = 1;
DELETE FROM SRC WHERE id = 2;

-- Consume
CALL sp_consume();

SELECT * FROM TGT ORDER BY id;  -- 1 row: (1, 'A')
```

## Key takeaways

- The minimal-set pattern handles all three DML operations
  in one `MERGE`.
- Wrap the `MERGE` in a procedure and call it from a
  `WHEN`-gated task for production CDC.
- If the stream goes stale, recreate it and backfill.
- The idempotency loop is `MERGE → re-run if drift > 0`.

## What's next

L152 — Combine streams & tasks. We tie it all together with a
real production task chain.