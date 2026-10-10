---
l_id: L148
title: Staleness of a stream
duration: "4:30"
prereqs: ["L147"]
---

# L148 — Staleness of a stream

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 2. Streams
> **Duration:** 4:30

## Prereqs

L147 — OFFSET in a stream.

## Key terms

- **Stale stream** — a stream whose offset is older than the
  table's Time Travel retention. The stream is no longer
  readable.
- **Stale-safe** — a property of consumers that handle the
  "stream is stale" case gracefully (typically by recreating
  the stream).
- **Drop-on-stale** — explicitly `DROP STREAM` and recreate it
  when you detect staleness.

## Lecture

Welcome back. Today's lecture is short but important: a stream
that you don't consume for a long time *can become stale*. Once
stale, the stream is unreadable — you have to recreate it. By
the end of this lecture you'll know how to detect and recover
from staleness.

### Why streams go stale

A stream records row-level changes against a table. Snowflake
uses the table's Time Travel retention to determine how far
back it can replay those changes. If the stream's offset is
older than the table's retention, Snowflake can no longer
reconstruct the change history — the stream is **stale**.

```text
Stream offset: 100
Table retention: 14 days
Time since last consumption: 30 days  ← stream is stale
```

Concretely: if a table has 1-day retention and you don't
consume the stream for 24 hours, the stream is at risk of
becoming stale on the next change.

### The "stale stream" error

When a stream is stale, querying it returns:

```text
Stream 'X' is stale and cannot be queried.
```

This is *not* an empty result — it's an error. The fix is to
recreate the stream.

### The recovery pattern

```sql
-- 1. Detect
SELECT SYSTEM$STREAM_IS_STALE('demo_db.public.src_stream');

-- 2. Recreate
DROP STREAM src_stream;
CREATE STREAM src_stream ON TABLE src;
```

After recreation, the stream is fresh: its offset starts at
"now" and any changes from this point forward will be
recorded.

### How to prevent staleness

Two practical patterns:

1. **Consume on a tight schedule.** A task that runs every 5
   minutes with `WHEN SYSTEM$STREAM_HAS_DATA(...)` consumes
   within seconds of any change. Staleness is impossible.
2. **Raise the table's retention.** A 90-day retention
   permanent table has 90 days of grace period before staleness.

The first is the right answer; the second is a backstop.

### The operational rule

> If a stream consumer is paused for more than the table's
> `DATA_RETENTION_TIME_IN_DAYS`, recreate the stream on resume.

This is the cleanest mental model. Build it into your runbook.

## Hands-on

Simulating staleness is tricky in a sandbox (it takes 1+ days).
For now:

```sql
-- Inspect retention
SHOW PARAMETERS LIKE 'DATA_RETENTION_TIME_IN_DAYS' IN ACCOUNT;

-- Per-table
SHOW TABLES LIKE 'SRC';
-- Check the "retention_time" column.

-- Check if a stream is stale
SELECT SYSTEM$STREAM_IS_STALE('demo_db.public.src_stream') AS is_stale;
```

The function returns `TRUE` / `FALSE`. Run it from your
monitoring dashboard on every stream.

## Key takeaways

- A stream is stale if its offset is older than the source
  table's Time Travel retention.
- Once stale, the stream errors on read; recreate to recover.
- `SYSTEM$STREAM_IS_STALE` is the detector.
- Consume on a tight schedule to prevent staleness.

## What's next

L149 — Minimal Set of Changes. We pull together the previous
lectures into the production-grade consumption pattern.