---
l_id: L119
title: Cloning with time travel
duration: "5:00"
prereqs: ["L118"]
---

# L119 — Cloning with time travel

> **Author:** Prem Vishnoi &lt;pvishnoi@pvishnoi.com&gt;
> **Section:** 17 — Zero-Copy Cloning
> **Duration:** 5:00

## Prereqs

L118 — Cloning schemas & databases. Plus the L105–L109 series on Time
Travel (`AT`, `BEFORE`, retention).

## Key terms

- **`AT (TIMESTAMP => ...)`** — point-in-time clause on a clone.
- **`AT (OFFSET => ...)`** — "N seconds ago" syntax.
- **`BEFORE (STATEMENT => ...)`** — fork from just before a given
  query ID (advanced).
- **Forensic clone** — a clone used to investigate the state of a
  table at some past moment.

## Lecture

Welcome back. The two Snowflake features you've already learned —
**zero-copy cloning** and **time travel** — combine cleanly into
something more powerful than the sum of the parts: clone *and* pick
the moment in time you want the clone to fork from. One statement,
instantaneous, historical snapshot of your data.

### The syntax

```sql
-- Clone as of a timestamp
CREATE TABLE orders_yesterday CLONE orders
  AT (TIMESTAMP => '2026-10-09 12:00:00'::TIMESTAMP_NTZ);

-- Clone as of N seconds ago
CREATE TABLE orders_5min_ago CLONE orders
  AT (OFFSET => -300);

-- Clone just before a statement ran
CREATE TABLE orders_before_bad_update CLONE orders
  BEFORE (STATEMENT => '01a4f5e6-0000-abcd-0000-0000abc12345');
```

The `AT` / `BEFORE` clauses are the same ones you used with
`SELECT` in L106. They sit at the end of the `CLONE` statement and
they tell Snowflake: *treat the source object as if it were the
version from this moment*, then clone *that*.

### Why this is so powerful

Time travel on its own lets you query the past. Cloning on its own
lets you copy the present. Combined, you can:

1. **Investigate incidents.** "What did the `customers` table look
   like at 02:14 UTC, just before that bad ETL job ran?" — clone it,
   inspect the clone, throw it away.
2. **Reproduce finance-close data.** Every month, clone the fact
   tables as of the close timestamp; you get an immutable snapshot
   for free.
4. **Test "what if we had done this earlier?"** Clone the production
   table as of last quarter, run a hypothetical migration against
   the clone, throw it away.

### Things to remember

- The retention period on the **source** governs how far back you
  can clone. Permanent table with 90-day retention = 90-day history.
- Cloning the past creates a new live table that you can mutate.
  The clone is not read-only.
- The clone still inherits the source's table type — clone a
  transient table, get a transient table.

### Combining with schema/database clones

The same `AT` clause works at every level:

```sql
CREATE SCHEMA prod_clone_yesterday CLONE prod.public
  AT (TIMESTAMP => '2026-10-09 00:00:00'::TIMESTAMP_NTZ);

CREATE DATABASE dev_snapshot CLONE prod
  AT (OFFSET => -86400);  -- 24h ago
```

A whole-database clone with time travel is the classic
"end-of-day snapshot" pattern for dev environments.

## Hands-on

```sql
USE SCHEMA DEMO_DB.PUBLIC;

CREATE TABLE EVENTS (id NUMBER, payload VARCHAR, ts TIMESTAMP_NTZ);
INSERT INTO EVENTS VALUES (1, 'first',  CURRENT_TIMESTAMP);
INSERT INTO EVENTS VALUES (2, 'second', CURRENT_TIMESTAMP);
INSERT INTO EVENTS VALUES (3, 'third',  CURRENT_TIMESTAMP);

-- Clone as of one minute ago — only the first two rows survive
CREATE TABLE EVENTS_PAST CLONE EVENTS
  AT (OFFSET => -120);

SELECT * FROM EVENTS_PAST ORDER BY id;
```

## Key takeaways

- Clone + Time Travel = point-in-time fork of any object.
- Use `AT (TIMESTAMP => ...)` for absolute time, `OFFSET` for
  relative, `BEFORE (STATEMENT => ...)` for forensic clones.
- The source's retention period is the maximum historical depth
  you can clone.
- Whole-database historical clones are the standard pattern for
  dev/test environments.

## What's next

L120 introduces `ALTER TABLE ... SWAP WITH` — the atomic rename trick
that turns a zero-copy clone into a zero-downtime ELT deploy.