---
l_id: L121
title: Zero-Copy Cloning recap
duration: "4:00"
prereqs: ["L120"]
---

# L121 — Zero-Copy Cloning recap

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 17 — Zero-Copy Cloning
> **Duration:** 4:00

## Prereqs

L120 — Swapping tables + Hands-on. This is the recap lecture; if any
of the prior five confused you, restart from L116.

## Key terms

- **Zero-copy clone** — a metadata-only copy. Instant, free at clone
  time, costs storage only on divergence.
- **Clone + time travel** — fork from a historical point in time.
- **`ALTER TABLE ... SWAP WITH`** — atomic rename for zero-downtime
  ELT.

## Lecture

Welcome back. Section 17 covered three features that, together, are
the operational backbone of almost every production Snowflake
pipeline: **zero-copy cloning**, **clone with time travel**, and
**table swap**. This lecture is a tight recap — one view, three
takeaways, and a couple of patterns worth committing to muscle
memory.

### The one-view summary

| Feature | Statement | Storage at creation | Use case |
|---|---|---|---|
| Clone table | `CREATE TABLE x CLONE y` | 0 | dev, ELT backup, snapshot |
| Clone schema/db | `CREATE SCHEMA ... CLONE`, `CREATE DATABASE ... CLONE` | 0 | full-env refresh |
| Clone with time travel | `CLONE ... AT (TIMESTAMP => ...)` | 0 | forensic, finance close |
| Swap | `ALTER TABLE x SWAP WITH y` | unchanged | zero-downtime deploy |

### The three production patterns

**1. ELT swap-and-drop.**

```sql
CREATE TABLE staging.orders_v2 CLONE prod.orders;
-- transform against staging
ALTER TABLE prod.orders SWAP WITH staging.orders_v2;
DROP TABLE staging.orders;
```

Atomic, reversible, cheap. The single most-used pattern in the
course.

**2. Daily dev refresh.**

```sql
CREATE OR REPLACE DATABASE dev_clone CLONE prod;
```

Run as a single task at 7am. Dev gets a fresh copy of production
without anyone copying data.

**3. Forensic clone.**

```sql
CREATE TABLE orders_at_incident CLONE orders
  AT (OFFSET => -3600);
```

Clone from an hour ago, investigate, drop when done.

### A few things to remember

- **Zero-copy ≠ free forever.** Storage accrues as the source and
  clone diverge.
- **Grants are not inherited** by clones; re-grant when needed.
- **Tasks are paused** in a clone; streams reset to "now".
- **Retention governs clone depth.** A 1-day retention table can be
  cloned at most 1 day into the past.

### What's next

Section 18 is **Data Sharing** — the third Snowflake superpower
that comes for free once you have zero-copy cloning and
columnar storage. You'll share data with other Snowflake accounts,
non-Snowflake consumers, and reader accounts *without* duplicating a
single byte.

## Key takeaways

- Cloning is a metadata operation. It's instant and free at clone
  time.
- Combine clone with Time Travel to fork the past.
- Use `SWAP WITH` to deploy ELT changes atomically.
- Three patterns to remember: ELT swap-and-drop, daily dev refresh,
  forensic clone.

## What's next

L122 — Understanding data sharing. We turn clones into the most
powerful distribution model in cloud data warehousing.