---
l_id: L147
title: OFFSET in a stream
duration: "4:30"
prereqs: ["L146"]
---

# L147 — OFFSET in a stream

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 2. Streams
> **Duration:** 4:30

## Prereqs

L146 — UPDATE operation.

## Key terms

- **`METADATA$OFFSET`** — a numeric column on the stream that
  records the order in which changes were captured.
- **Time-ordered** — Snowflake guarantees offset values are
  monotonically increasing per stream.
- **Time travel of a stream** — you can read the stream `AT` a
  specific offset.

## Lecture

Welcome back. Today's lecture is the technical deep-dive on
**`METADATA$OFFSET`**: a numeric column that records *when* each
change was captured. The offset is the anchor of every CDC
workflow in Snowflake — it tells you exactly where in the change
log you are, and gives you a way to read the stream at a
specific point.

### What the offset looks like

```sql
SELECT METADATA$ACTION,
       METADATA$ISUPDATE,
       METADATA$OFFSET,
       id,
       val
FROM   src_stream;
```

You'd see:

```text
ACTION  ISUPDATE  OFFSET       id  val
DELETE  TRUE      1000000001   1   a
INSERT  TRUE      1000000002   1   A
INSERT  FALSE     1000000003   2   b
```

The `OFFSET` values are 64-bit integers, monotonically increasing
per stream. They're not timestamps (although they correlate with
commit time) and they are not contiguous for unrelated changes.

### The key property: order of operations

For a single change, the *old* image has a smaller offset than
the *new* image. So in an `UPDATE`, `OFFSET(old) < OFFSET(new)`.
This is what lets you reason about ordering inside a single
change.

Across changes, offsets are also strictly increasing. If you
process the stream in offset order, you see changes in the order
they were committed.

### The "consume from offset X" pattern

The most useful thing you can do with offsets is save the
"highest offset I have processed" and pass it back to the next
consumer run. Snowflake has a built-in helper for this:

```sql
SELECT SYSTEM$STREAM_GET_OFFSET('SRC_STREAM');
```

The function returns the stream's current end offset. You can
record it in a metadata table and use it as a checkpoint.

A more practical pattern uses *streams on streams* — we won't
cover that in this lecture, but it's the foundation of the
"finalizer" pattern in L152.

### Time travel of a stream

```sql
-- Read the stream as of one minute ago
SELECT *
FROM   src_stream AT (OFFSET => -60);
```

The `AT` clause on a stream reads the stream's *change log* as of
the offset that was current one minute ago. This is rarely used
in production but useful for debugging.

### Common pitfalls

- **Offset is not a timestamp.** Don't compare to
  `CURRENT_TIMESTAMP`.
- **Offset is unique per stream, not across streams.** Two
  streams on different tables can have the same offset value.
- **Offset is monotonic, not dense.** Gaps in the sequence are
  normal and indicate periods of no change.

## Hands-on

```sql
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE TABLE SRC (id NUMBER, val VARCHAR);
CREATE OR REPLACE STREAM src_stream ON TABLE SRC;
INSERT INTO SRC VALUES (1, 'a');
INSERT INTO SRC VALUES (2, 'b');

-- Read offsets
SELECT METADATA$OFFSET, METADATA$ACTION, id, val
FROM   src_stream
ORDER BY METADATA$OFFSET;

-- Get the current end offset
SELECT SYSTEM$STREAM_GET_OFFSET('DEMO_DB.PUBLIC.SRC_STREAM') AS end_offset;
```

## Key takeaways

- `METADATA$OFFSET` is a 64-bit integer, monotonically increasing
  per stream.
- The old image of an update has a smaller offset than the new
  image.
- `SYSTEM$STREAM_GET_OFFSET` returns the stream's current end
  offset.
- Offsets are not timestamps; treat them as opaque checkpoints.

## What's next

L148 — Staleness of a stream. A stream that is not consumed
becomes "stale"; we learn what that means and what to do.