---
l_id: L146
title: UPDATE operation
duration: "5:00"
prereqs: ["L145"]
---

# L146 — UPDATE operation

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 2. Streams
> **Duration:** 5:00

## Prereqs

L145 — INSERT operation.

## Key terms

- **Old image** — the row's state *before* the UPDATE. The
  stream records this with `METADATA$ACTION = 'DELETE'` and
  `METADATA$ISUPDATE = TRUE`.
- **New image** — the row's state *after* the UPDATE. The
  stream records this with `METADATA$ACTION = 'INSERT'` and
  `METADATA$ISUPDATE = TRUE`.

## Lecture

Welcome back. Updates are the trickiest stream operation, because
Snowflake records *both* the old and the new image of an updated
row. Today's lecture is the one place in the course where you
have to think about *two* rows for one logical change.

### What an UPDATE looks like in the stream

```sql
CREATE OR REPLACE TABLE SRC (id NUMBER, val VARCHAR);
INSERT INTO SRC VALUES (1, 'a');

CREATE OR REPLACE STREAM src_stream ON TABLE SRC;
UPDATE SRC SET val = 'A' WHERE id = 1;

SELECT METADATA$ACTION, METADATA$ISUPDATE, id, val
FROM   src_stream;
```

You get *two* rows:

```text
ACTION  ISUPDATE  id  val
DELETE  TRUE       1   a    -- old image
INSERT  TRUE       1   A    -- new image
```

The "old image" lets you undo the change; the "new image" lets
you replay it. By default both are returned, so you have to
filter carefully.

### Filtering for "the new image only"

```sql
SELECT id, val
FROM   src_stream
WHERE  METADATA$ACTION = 'INSERT'
  AND  METADATA$ISUPDATE = TRUE;
```

The `ISUPDATE = TRUE` filter keeps only the new image. Without
it, you'd also see the new image of any *fresh* insert (with
`ISUPDATE = FALSE`).

### Consuming an update

```sql
MERGE INTO TGT t
USING (SELECT * FROM src_stream
       WHERE METADATA$ACTION = 'INSERT'
         AND METADATA$ISUPDATE = TRUE) s
ON     t.id = s.id
WHEN MATCHED THEN UPDATE SET t.val = s.val
WHEN NOT MATCHED THEN INSERT (id, val) VALUES (s.id, s.val);
```

`MERGE` is the right tool: it handles both "row existed, update
it" and "row is new, insert it" in one statement. The
`WHEN MATCHED` branch corresponds to UPDATEs; `WHEN NOT
MATCHED` to "net new" inserts.

### Why MERGE is essential

If you used `INSERT INTO TGT SELECT ... FROM src_stream` for
updates, you would get duplicate key errors on the next pass
through an already-updated row. `MERGE` is the *only* way to
consume updates without producing duplicates.

### A common bug: forgetting `ISUPDATE = TRUE`

If you consume both images:

```sql
INSERT INTO TGT
SELECT id, val FROM src_stream WHERE METADATA$ACTION = 'INSERT';
```

You would *insert* both the old (with `val = 'a'`) and the new
(with `val = 'A'`) images of the updated row, ending up with
two rows in `TGT` for `id = 1`. The `ISUPDATE = TRUE` filter is
what skips the old image.

## Hands-on

```sql
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE TABLE SRC (id NUMBER, val VARCHAR);
CREATE OR REPLACE TABLE TGT (id NUMBER, val VARCHAR);

CREATE OR REPLACE STREAM src_stream ON TABLE SRC;
INSERT INTO SRC VALUES (1, 'a');
UPDATE SRC SET val = 'A' WHERE id = 1;

SELECT METADATA$ACTION, METADATA$ISUPDATE, id, val
FROM   src_stream;

-- Consume with MERGE
MERGE INTO TGT t
USING (SELECT * FROM src_stream
       WHERE METADATA$ACTION = 'INSERT'
         AND METADATA$ISUPDATE = TRUE) s
ON     t.id = s.id
WHEN MATCHED THEN UPDATE SET t.val = s.val
WHEN NOT MATCHED THEN INSERT (id, val) VALUES (s.id, s.val);

SELECT * FROM TGT;  -- 1 row, val = 'A'
```

## Key takeaways

- An UPDATE produces two rows in the stream: old and new.
- Filter `METADATA$ACTION = 'INSERT' AND METADATA$ISUPDATE = TRUE`
  to keep the new image.
- Use `MERGE` to consume updates; `INSERT` would duplicate.
- The `ISUPDATE` column is what distinguishes a real insert from
  a new image of an update.

## What's next

L147 — OFFSET in a stream. We explore the offset column and how
to read the stream at a specific point.