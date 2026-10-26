---
l_id: L154
title: Changes clause
duration: "4:30"
prereqs: ["L153"]
---

# L154 — Changes clause

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 2. Streams
> **Duration:** 4:30

## Prereqs

L153 — Append-only streams.

## Key terms

- **`CHANGES`** — a SQL clause that lets you query a table's
  change history directly, without creating a stream.
- **`PREDICATES`** — optional filters inside `CHANGES`.
- **One-shot CDC** — using `CHANGES` for a single ad-hoc query
  rather than maintaining a stream.

## Lecture

Welcome to the final lecture in the streams sub-group. The
`CHANGES` clause is the on-demand alternative to streams:
instead of creating a stream and consuming it, you query a
table's change history directly inside a `SELECT`. Useful for
debugging, ad-hoc audits, and one-off backfills.

### The syntax

```sql
SELECT *
FROM   SRC
CHANGES (INFORMATION => APPEND_ONLY)
AT (TIMESTAMP => :ts)
WHERE  id > 1000;
```

Three things going on:

- `CHANGES` — query the change history, not the current state.
- `INFORMATION => APPEND_ONLY` — only show `INSERT`s. Other
  values: `DEFAULT` (full history).
- `AT (TIMESTAMP => :ts)` — query as of a specific time, same
  syntax as Time Travel.

### When to use `CHANGES` instead of streams

- **One-off audit.** "What changed in the last hour?"
- **Ad-hoc backfill.** "Re-derive the last 7 days of data."
- **Debugging.** "What does the change log look like around
  this time?"
- **No pipeline.** You don't want to maintain a stream just to
  ask one question.

`CHANGES` requires no setup. The data is already in the
table's Time Travel history.

### The full example

```sql
-- All changes in the last hour
SELECT *
FROM   orders
CHANGES (INFORMATION => DEFAULT)
AT (OFFSET => -3600);

-- Just the inserts
SELECT id, customer, amount
FROM   orders
CHANGES (INFORMATION => APPEND_ONLY)
AT (OFFSET => -3600)
WHERE  amount > 1000;
```

### The INFORMATION options

| Value | What you get |
|---|---|
| `DEFAULT` | All DML types: INSERT, UPDATE (old + new), DELETE |
| `APPEND_ONLY` | Only INSERTs |
| `VARIANT` | Same as DEFAULT, but with extra columns for `VARIANT` columns |

In practice `DEFAULT` is the most useful; it matches the
default stream's data.

### Limitations

- **`CHANGES` does not advance an offset.** Every query reads
  the entire history between the start and `AT` time. If you
  run `CHANGES` twice, you get the same rows both times.
- **No stream metadata columns.** `CHANGES` returns
  `METADATA$ACTION` and `METADATA$ISUPDATE` (matching the
  stream view), but not `METADATA$OFFSET`.
- **Retention-bounded.** Like Time Travel, `CHANGES` is bounded
  by the table's `DATA_RETENTION_TIME_IN_DAYS`.

## Hands-on

```sql
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE TABLE SRC (id NUMBER, val VARCHAR);
INSERT INTO SRC VALUES (1, 'a'), (2, 'b');
UPDATE SRC SET val = 'A' WHERE id = 1;
DELETE FROM SRC WHERE id = 2;

-- All changes (default)
SELECT METADATA$ACTION, METADATA$ISUPDATE, id, val
FROM   SRC
CHANGES (INFORMATION => DEFAULT)
AT (OFFSET => -60);

-- Inserts only
SELECT id, val
FROM   SRC
CHANGES (INFORMATION => APPEND_ONLY)
AT (OFFSET => -60);
```

## Key takeaways

- `CHANGES` is a one-shot, on-demand query of a table's change
  history.
- Use it for ad-hoc audits and debugging; use streams for
  pipeline-style consumption.
- `INFORMATION => DEFAULT` matches the default stream's data.
- `CHANGES` is bounded by Time Travel retention.

## What's next

We move on to **Materialized Views** (L155–L160), the
precomputed-query alternative to on-demand aggregations.