---
l_id: L145
title: INSERT operation
duration: "4:30"
prereqs: ["L144"]
---

# L145 — INSERT operation

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 2. Streams
> **Duration:** 4:30

## Prereqs

L144 — Understanding streams.

## Key terms

- **`METADATA$ACTION = 'INSERT'`** — the metadata column that
  identifies a row as a fresh insert.
- **Consuming an INSERT** — the pattern of copying new rows
  from the stream into a target table.

## Lecture

Welcome back. Today we focus on the simplest stream operation:
**INSERT**. New rows in the source appear in the stream with
`METADATA$ACTION = 'INSERT'`. Consuming them is just a `SELECT`
followed by an `INSERT INTO target`.

### What an INSERT looks like in the stream

```sql
CREATE OR REPLACE TABLE SRC (id NUMBER, val VARCHAR);
INSERT INTO SRC VALUES (1, 'a'), (2, 'b');

CREATE OR REPLACE STREAM src_stream ON TABLE SRC;
INSERT INTO SRC VALUES (3, 'c');

SELECT METADATA$ACTION, METADATA$ISUPDATE, id, val
FROM   src_stream;
-- INSERT    FALSE    3   c
```

The new row appears in the stream with `METADATA$ACTION = 'INSERT'`
and `METADATA$ISUPDATE = FALSE`. The two metadata columns are
the only difference between a stream and the underlying table.

### The consumer pattern

```sql
CREATE OR REPLACE TABLE TGT (id NUMBER, val VARCHAR);

-- Consume the stream once
INSERT INTO TGT
SELECT id, val
FROM   src_stream
WHERE  METADATA$ACTION = 'INSERT';

SELECT * FROM TGT;     -- has 1 row (id=3, val='c')
SELECT * FROM src_stream;  -- empty; the offset advanced
```

After the `INSERT INTO TGT`, the stream's offset advances and
`SELECT * FROM src_stream` returns no rows. The next change to
`SRC` will appear in the next read.

### Why filter by `METADATA$ACTION = 'INSERT'`?

A default stream also contains `UPDATE` and `DELETE` rows. If
you don't filter, the consumer will try to `INSERT` the metadata
columns too — which fail because `TGT` doesn't have
`METADATA$ACTION`. Filter to keep the SQL clean.

```sql
-- Bad: tries to insert all metadata columns
INSERT INTO TGT SELECT * FROM src_stream;

-- Good: project only the source columns, filter to INSERTs
INSERT INTO TGT
SELECT id, val
FROM   src_stream
WHERE  METADATA$ACTION = 'INSERT';
```

### Idempotency

If the consumer fails between consuming the stream and committing
the result, a re-run will see the same rows again and
re-insert them. Two ways to make INSERTs idempotent:

1. **Use a primary key + MERGE.** `MERGE INTO tgt USING
   src_stream ON key ...` — duplicates overwrite.
2. **Commit the stream offset explicitly.** Use a *finalizer*
   task (L152) to consume the stream only after the main task
   succeeds.

## Hands-on

```sql
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE TABLE SRC (id NUMBER, val VARCHAR);
CREATE OR REPLACE TABLE TGT (id NUMBER, val VARCHAR);

CREATE OR REPLACE STREAM src_stream ON TABLE SRC;

INSERT INTO SRC VALUES (1, 'a'), (2, 'b');
INSERT INTO SRC VALUES (3, 'c');

-- Read the stream and verify
SELECT METADATA$ACTION, id, val FROM src_stream;

-- Consume
INSERT INTO TGT SELECT id, val FROM src_stream WHERE METADATA$ACTION = 'INSERT';
SELECT * FROM TGT;          -- 3 rows
SELECT * FROM src_stream;   -- empty
```

## Key takeaways

- INSERTs in the stream show as `METADATA$ACTION = 'INSERT'`.
- Filter the stream to INSERTs to project the right columns.
- The stream's offset advances after the consumer reads it.
- Make consumers idempotent with primary keys or finalizer
  tasks.

## What's next

L146 — UPDATE operation. Updates are trickier because the stream
records both the old and the new image.