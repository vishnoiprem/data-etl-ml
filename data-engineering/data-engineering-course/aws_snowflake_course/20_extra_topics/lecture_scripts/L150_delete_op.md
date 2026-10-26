---
l_id: L150
title: DELETE operation
duration: "4:30"
prereqs: ["L149"]
---

# L150 — DELETE operation

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 2. Streams
> **Duration:** 4:30

## Prereqs

L149 — Minimal Set of Changes.

## Key terms

- **`METADATA$ACTION = 'DELETE'`, `METADATA$ISUPDATE = FALSE`** —
  a real delete from the source.
- **`WHEN MATCHED ... THEN DELETE`** — the MERGE branch that
  removes a row from the target.

## Lecture

Welcome back. Today's lecture zooms in on the third and last DML
operation: `DELETE`. A real delete in the source shows up in
the stream as `METADATA$ACTION = 'DELETE'` with
`METADATA$ISUPDATE = FALSE` — distinct from the "old image of an
update" which is `DELETE` with `ISUPDATE = TRUE`.

### What a real delete looks like

```sql
CREATE OR REPLACE TABLE SRC (id NUMBER, val VARCHAR);
CREATE OR REPLACE STREAM src_stream ON TABLE SRC;
INSERT INTO SRC VALUES (1, 'a');
DELETE FROM SRC WHERE id = 1;

SELECT METADATA$ACTION, METADATA$ISUPDATE, id, val
FROM   src_stream;
```

You get:

```text
ACTION  ISUPDATE  id  val
DELETE  FALSE      1   a
```

A real delete: `ACTION = 'DELETE'`, `ISUPDATE = FALSE`. This
single row is what should drive a `DELETE` from your target
table.

### Consuming a delete

```sql
DELETE FROM TGT
WHERE id IN (SELECT id
             FROM   src_stream
             WHERE  METADATA$ACTION = 'DELETE'
               AND  METADATA$ISUPDATE = FALSE);
```

Or, more idiomatically, inside the minimal-set `MERGE` from
L149:

```sql
WHEN MATCHED
     AND s.action = 'DELETE' AND s.is_update = FALSE
     THEN DELETE
```

Both work. The `MERGE` is preferred because it handles all
three DML types in one statement.

### Why the `ISUPDATE = FALSE` filter matters

A naive filter (`ACTION = 'DELETE'`) would also match the old
image of an update. The old image has the row *before* the
update; if you `DELETE` on it, you'd delete the row in the
target — even though the user *updated* it, not deleted it.

```sql
-- Bad: catches both real deletes and old images of updates
WHERE METADATA$ACTION = 'DELETE'

-- Good: real deletes only
WHERE METADATA$ACTION = 'DELETE'
  AND METADATA$ISUPDATE = FALSE
```

### The full picture

| Stream row | Filter to use | Action in TGT |
|---|---|---|
| Real insert | `ACTION='INSERT' AND ISUPDATE=FALSE` | INSERT |
| New image of update | `ACTION='INSERT' AND ISUPDATE=TRUE` | UPDATE |
| Real delete | `ACTION='DELETE' AND ISUPDATE=FALSE` | DELETE |
| Old image of update | (skip) | (skip) |

Three "real" change types, four stream rows. The
`ISUPDATE` column is how you tell the four apart.

## Hands-on

```sql
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE TABLE SRC (id NUMBER, val VARCHAR);
CREATE OR REPLACE TABLE TGT (id NUMBER, val VARCHAR);
CREATE OR REPLACE STREAM src_stream ON TABLE SRC;

INSERT INTO SRC VALUES (1, 'a'), (2, 'b'), (3, 'c');
DELETE FROM SRC WHERE id = 2;

-- Consume with a focused DELETE
DELETE FROM TGT
WHERE id IN (SELECT id
             FROM   src_stream
             WHERE  METADATA$ACTION = 'DELETE'
               AND  METADATA$ISUPDATE = FALSE);

SELECT * FROM TGT;
```

## Key takeaways

- A real delete is `ACTION='DELETE' AND ISUPDATE=FALSE`.
- Always pair the filter with `ISUPDATE=FALSE` to skip the
  old image of an update.
- Use the `MERGE` pattern from L149 to handle all DML in one
  statement.

## What's next

L151 — Process all data changes. We tie INSERT, UPDATE, and
DELETE into one clean production pattern.