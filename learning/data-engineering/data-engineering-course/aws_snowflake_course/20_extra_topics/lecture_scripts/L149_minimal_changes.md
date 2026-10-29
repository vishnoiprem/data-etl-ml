---
l_id: L149
title: Minimal Set of Changes
duration: "5:00"
prereqs: ["L148"]
---

# L149 — Minimal Set of Changes

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 2. Streams
> **Duration:** 5:00

## Prereqs

L148 — Staleness of a stream.

## Key terms

- **Minimal set of changes** — the smallest possible query that
  correctly handles all three DML operations in a default
  stream.
- **Pattern** — a reusable SQL shape for stream consumption.
- **`MERGE` with a CASE branch** — the most common minimal-set
  pattern.

## Lecture

Welcome back. So far we've handled `INSERT` and `UPDATE` in
isolation. Today's lecture is the production-grade pattern that
handles **all three DML operations in one statement**:
`MERGE` keyed on the primary key, with the right `WHEN MATCHED`
branches for `UPDATE` and `DELETE`.

### The minimal pattern

```sql
MERGE INTO TGT t
USING (
  -- Project just the columns we need; filter to "live" rows only
  SELECT id, val,
         METADATA$ACTION        AS action,
         METADATA$ISUPDATE      AS is_update
  FROM   src_stream
) s
ON t.id = s.id
WHEN MATCHED
     AND s.action = 'DELETE'
     AND s.is_update = FALSE
     THEN DELETE
WHEN MATCHED
     AND s.action = 'INSERT'
     AND s.is_update = TRUE
     THEN UPDATE SET t.val = s.val
WHEN NOT MATCHED
     AND s.action = 'INSERT'
     AND s.is_update = FALSE
     THEN INSERT (id, val) VALUES (s.id, s.val);
```

That single `MERGE` handles every change type:

- `WHEN MATCHED + DELETE + is_update = FALSE` → a true delete
  from the source; remove the row from `TGT`.
- `WHEN MATCHED + INSERT + is_update = TRUE` → the new image of
  an update; apply it.
- `WHEN NOT MATCHED + INSERT + is_update = FALSE` → a true
  insert; add the row.

The `is_update` filter is what makes this *minimal* — without
it, you would process the old image of an update (a `DELETE`
that isn't really a delete) and end up deleting rows you
should keep.

### Why one statement

Three reasons:

1. **Atomic.** All changes apply or none do.
2. **Idempotent.** Re-running with the same stream contents
   produces the same `TGT` state.
3. **Cheap.** Snowflake optimizes `MERGE` heavily; it doesn't
   do a full table scan.

### How to test it

In a sandbox, run a sequence of operations and check `TGT`:

```sql
INSERT INTO SRC VALUES (1, 'a');
INSERT INTO SRC VALUES (2, 'b');
UPDATE SRC SET val = 'A' WHERE id = 1;
DELETE FROM SRC WHERE id = 2;

-- Run the MERGE
SELECT * FROM TGT;  -- 1 row, id=1, val='A'
```

Re-run the same operations; the stream is empty; re-running
the `MERGE` is a no-op. Idempotency, achieved.

### What to leave out

The pattern deliberately *skips* the old image of an update
(`DELETE + is_update = TRUE`) and the new image of a net-new
insert. The `WHEN MATCHED + DELETE` branch is only for *true*
deletes.

## Hands-on

```sql
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE TABLE SRC (id NUMBER, val VARCHAR);
CREATE OR REPLACE TABLE TGT (id NUMBER, val VARCHAR);
CREATE OR REPLACE STREAM src_stream ON TABLE SRC;

INSERT INTO SRC VALUES (1, 'a'), (2, 'b');
UPDATE SRC SET val = 'A' WHERE id = 1;
DELETE FROM SRC WHERE id = 2;

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

SELECT * FROM TGT ORDER BY id;  -- 1 row: (1, 'A')
```

## Key takeaways

- A single `MERGE` with three `WHEN` branches handles all DML
  operations.
- The `is_update` filter is what makes the set *minimal*.
- The pattern is atomic and idempotent.
- Always test against a sequence of all three DML types.

## What's next

L150 — DELETE operation. We cover the delete-specific branches
in detail.