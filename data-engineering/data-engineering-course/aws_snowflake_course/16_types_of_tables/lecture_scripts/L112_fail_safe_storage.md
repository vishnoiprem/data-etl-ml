---
l_id: L112
title: Fail Safe storage
duration: "4:30"
prereqs: ["L111"]
---

# L112 — Fail Safe storage

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 16 — Types of tables
> **Duration:** 4:30

## Prereqs

L111 — Understanding Fail Safe. This lecture zooms in on the *storage*
side of Fail Safe: where those 7 days of backup live, how they show up
on your bill, and the one rule that catches most beginners.

## Key terms

- **Fail Safe** — 7-day backup window that activates *after* Time
  Travel retention expires. Non-configurable.
- **Fail Safe storage** — the on-disk bytes holding historical data
  inside that 7-day window. Billed at the standard storage rate.
- **ACCOUNTADMIN** — the only role that can interact with Fail Safe
  data; in practice only Snowflake Support uses it.
- **On-demand storage** — the per-TB-per-month cost for active +
  Time Travel + Fail Safe bytes.

## Lecture

Hi, and welcome back. In the last lecture we said that **Fail Safe** is
Snowflake's last-resort safety net: 7 days of historical data, locked
away from you, only accessible by Snowflake Support, only for true
disaster recovery. Today we zoom in on the *storage* half of that
sentence, because that 7-day window is the most expensive line item
most people miss on their first Snowflake bill.

### How Fail Safe storage works

When a table's data ages past its Time Travel retention period, the
historical versions don't just disappear. They move into a separate
storage tier — **Fail Safe storage** — where they sit for up to 7
more days. From your point of view, the data is invisible: you can't
query it, you can't `UNDROP` from it, you can't `SELECT` from it. The
only thing that can read it is a Snowflake support engineer after you
open a ticket.

That invisibility is the whole point. Time Travel is a *user-facing*
feature; Fail Safe is a *provider-facing* one. The contract is simple:
you get disaster recovery, Snowflake gets the bytes.

### How it shows up in billing

```sql
-- Inspect the storage breakdown for a table
SELECT  table_name,
        active_bytes,
        time_travel_bytes,
        failsafe_bytes,
        (active_bytes + time_travel_bytes + failsafe_bytes) AS total_bytes
FROM    TABLE(INFORMATION_SCHEMA.TABLE_STORAGE_METRICS(
            TABLE_NAME => 'ORDERS'));
```

The `failsafe_bytes` column is the number to watch. On a small dev
account it's tiny; on a multi-petabyte production warehouse it can be
the single largest line item. A common rule of thumb is **Fail Safe
adds ~10% on top of your Time Travel storage** for an actively
mutated table, and the percentage climbs the longer you keep data
mutated.

### The hard rule

> **Only permanent tables get Fail Safe.**

This is the bridge into L113. Transient and temporary tables do *not*
go to Fail Safe — when their Time Travel expires, the data is gone,
period. That single fact drives most of the cost-vs-resilience
decisions in the next two lectures.

## Hands-on

```sql
-- Create a sample table and watch the storage metrics move
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE TABLE ORDERS (
  id        NUMBER,
  amount    NUMBER(10,2),
  created   TIMESTAMP_NTZ
);

INSERT INTO ORDERS SELECT SEQ4(), UNIFORM(1, 1000, RANDOM()), CURRENT_TIMESTAMP()
FROM TABLE(GENERATOR(ROWCOUNT => 1000000));

-- Wait a few minutes, then re-run the TABLE_STORAGE_METRICS query
```

## Key takeaways

- Fail Safe storage is a 7-day, non-configurable backup tier.
- You cannot read Fail Safe data yourself; only Snowflake Support can.
- The cost shows up as `failsafe_bytes` in `TABLE_STORAGE_METRICS`.
- **Only permanent tables have Fail Safe** — keep that sentence in
  your head for L113.

## What's next

In L113 we line up the three table types — permanent, transient, and
temporary — so you can pick the cheapest one that still meets your
recovery requirements.
