---
l_id: L144
title: Understanding streams
duration: "5:00"
prereqs: ["L143"]
---

# L144 — Understanding streams

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 2. Streams
> **Duration:** 5:00

## Prereqs

L143 — Tasks with condition. The `WHEN` clause introduced the idea
of "skip if no work". Streams give that idea its data.

## Key terms

- **Stream** — a Snowflake object that tracks row-level changes
  to a table. Effectively change-data-capture (CDC) inside
  Snowflake.
- **Default stream** — tracks `INSERT`, `UPDATE`, `DELETE`.
- **Append-only stream** — tracks `INSERT` only.
- **Offset** — a pointer inside the stream; the stream advances
  every time a change is recorded.
- **Consume** — read rows from a stream; the offset advances.

## Lecture

Welcome to the streams sub-group. A **stream** is a Snowflake
object that records the row-level changes happening to a table.
You can think of it as a CDC log — every `INSERT`, `UPDATE`, and
`DELETE` against the source table is recorded in the stream.
Reading from the stream "consumes" those changes; subsequent
reads see only newer changes.

### Why streams exist

Three real-world use cases:

1. **Incremental ELT.** A nightly job that processes only the
   rows that changed since the last run.
2. **Replication to another account or table.** Stream of
   changes in `PROD`; consumer mirrors them into `STAGE` or a
   downstream `MART`.
3. **Audit.** "Who changed this row, and when?" — answered by
   the stream's metadata.

Before streams, the answer to "what changed?" was "diff the table
against a snapshot". That's `O(n)` in table size. A stream
captures changes in `O(rows_changed)` — orders of magnitude
faster on a hot table.

### Creating a stream

```sql
CREATE OR REPLACE STREAM orders_stream ON TABLE orders;
```

A default stream tracks all three DML operations: `INSERT`,
`UPDATE`, `DELETE`. The stream is *schema-bound*: if the source
table adds a column, the stream inherits it.

### Reading from a stream

A stream is *queryable* like a table. It returns the changes
recorded so far:

```sql
SELECT *
FROM   orders_stream;
```

The first time you read the stream, you see *all* changes from
the stream's creation to now. Subsequent reads see only the
changes since the last read — the stream's *offset* advances
each time you query it.

### The metadata columns

Every stream row has three extra columns:

- `METADATA$ACTION` — `INSERT`, `UPDATE`, or `DELETE`.
- `METADATA$ISUPDATE` — `TRUE` if the row is the *new* image of
  an update; `FALSE` otherwise.
- `METADATA$ROW_ID` — a stable ID for the row.

We'll use these in the next few lectures to handle each DML
operation.

### Streams and tasks

Pair a stream with a `WHEN`-gated task (L143) and you have
auto-scaling CDC: the task wakes up on a schedule, checks if the
stream has data, and only runs if so. No polling cost when the
source is idle.

## Hands-on

```sql
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE TABLE STREAM_DEMO (id NUMBER, val VARCHAR);
INSERT INTO STREAM_DEMO VALUES (1, 'a'), (2, 'b');

CREATE OR REPLACE STREAM demo_stream ON TABLE STREAM_DEMO;

-- Stream is empty so far
SELECT COUNT(*) FROM demo_stream;

-- Now change the source
INSERT INTO STREAM_DEMO VALUES (3, 'c');
UPDATE STREAM_DEMO SET val = 'A' WHERE id = 1;
DELETE FROM STREAM_DEMO WHERE id = 2;

-- Stream now has 3 rows: 1 INSERT, 1 UPDATE, 1 DELETE
SELECT METADATA$ACTION, METADATA$ISUPDATE, id, val
FROM   demo_stream;
```

## Key takeaways

- A stream is a CDC log of row-level changes to a table.
- Default streams track `INSERT`, `UPDATE`, and `DELETE`.
- Streams advance their offset on every read.
- Pair with `WHEN SYSTEM$STREAM_HAS_DATA` for efficient
  scheduling.

## What's next

L145 — INSERT operation. We dig into the metadata columns and
learn how to consume `INSERT` rows.