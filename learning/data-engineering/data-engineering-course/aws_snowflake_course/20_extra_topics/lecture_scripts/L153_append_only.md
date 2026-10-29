---
l_id: L153
title: Append-only streams
duration: "4:30"
prereqs: ["L152"]
---

# L153 — Append-only streams

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 2. Streams
> **Duration:** 4:30

## Prereqs

L152 — Combine streams & tasks.

## Key terms

- **Append-only stream** — a stream that tracks only `INSERT`
  operations. Cheaper and simpler than a default stream.
- **`APPEND_ONLY = TRUE`** — the parameter on `CREATE STREAM`.
- **Use case** — fact tables that only grow, never update or
  delete.

## Lecture

Welcome back. The default stream tracks `INSERT`, `UPDATE`, and
`DELETE`. But many tables in practice are **append-only** —
events, logs, fact rows that are never updated or deleted after
they're written. For those, the full default stream is overkill.
Today's lecture is the lighter alternative: **append-only
streams**.

### The syntax

```sql
CREATE OR REPLACE STREAM src_stream
  ON TABLE src
  APPEND_ONLY = TRUE;
```

That's the only change from the default stream. Now the stream
records only `INSERT` operations. `UPDATE` and `DELETE` on the
source table are *silently skipped* — they don't appear in the
stream at all.

### When to use

- **Event tables** — append-only by design.
- **Audit logs** — written once, never updated.
- **Logs from external systems** — already immutable by the
  time they reach Snowflake.

### When NOT to use

- **Mutable tables** — any table that supports `UPDATE` or
  `DELETE` against a meaningful subset of rows. Skipping those
  operations would silently drop changes.
- **Slowly changing dimensions** — if the table has type-2
  SCD history, you need a default stream.

### The consumer pattern

Append-only streams are simpler to consume — no
`METADATA$ISUPDATE` filtering, no `MERGE` branches:

```sql
INSERT INTO tgt (id, val)
SELECT id, val
FROM   src_stream;
```

That's it. The stream contains only new rows; an `INSERT INTO`
is the right consumer.

### Performance

Append-only streams are cheaper than default streams. Because
they don't track `UPDATE`/`DELETE` image pairs, they store less
metadata per change. For very high-volume event tables, this
is a measurable storage and latency win.

### Caveats

- An `UPDATE` on the source is **not** an error — it's just not
  recorded. Verify the source is truly append-only before
  enabling this.
- A `DELETE` on the source is also silently dropped. If your
  retention policy is to "delete after 90 days", you need a
  default stream (or to recreate the stream and reset the
  consumer).

## Hands-on

```sql
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE TABLE EVENT_LOG (id NUMBER, evt VARCHAR, ts TIMESTAMP_NTZ);
CREATE OR REPLACE STREAM event_stream ON TABLE EVENT_LOG APPEND_ONLY = TRUE;

INSERT INTO EVENT_LOG VALUES (1, 'click',  CURRENT_TIMESTAMP);
INSERT INTO EVENT_LOG VALUES (2, 'view',   CURRENT_TIMESTAMP);

-- Stream shows both inserts
SELECT * FROM event_stream;

-- Try an UPDATE
UPDATE EVENT_LOG SET evt = 'CLICK' WHERE id = 1;

-- Stream is unchanged — the UPDATE is silently skipped
SELECT * FROM event_stream;
```

## Key takeaways

- `APPEND_ONLY = TRUE` makes the stream track only `INSERT`s.
- Cheaper than a default stream.
- Use only when the source is truly append-only; otherwise
  you silently lose changes.
- The consumer is a single `INSERT INTO ... SELECT`.

## What's next

L154 — Changes clause. We close the streams sub-group with
`CHANGES`, the SQL keyword for ad-hoc CDC queries.