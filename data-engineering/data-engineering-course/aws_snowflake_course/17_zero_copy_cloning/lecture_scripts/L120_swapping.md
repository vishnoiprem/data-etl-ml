---
l_id: L120
title: Swapping tables + Hands-on
duration: "5:00"
prereqs: ["L119"]
---

# L120 — Swapping tables + Hands-on

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 17 — Zero-Copy Cloning
> **Duration:** 5:00

## Prereqs

L119 — Cloning with time travel.

## Key terms

- **`ALTER TABLE x SWAP WITH y`** — atomic metadata swap of two table
  names. To other sessions, the old `x` disappears and the new `x`
  appears in a single instant.
- **ELT swap-and-drop pattern** — load data into a stage table,
  swap it with the production table, drop the old production table
  in the background.
- **Zero-downtime deploy** — the property that no query sees an
  empty table during a deploy, because the swap is atomic.

## Lecture

Welcome back. Today we finish the cloning story with a feature that
looks unrelated but is actually the perfect partner: **table swap**.
Where cloning lets you *copy*, swapping lets you *replace* — in a
single atomic operation.

### The syntax

```sql
ALTER TABLE prod.public.orders  SWAP WITH staging.public.orders_v2;
```

What just happened? Snowflake renamed `orders` to `orders_v2` and
`orders_v2` to `orders`. From the perspective of any query running
at the same time, this is *one* rename event — there is no
"half-renamed" intermediate state. A `SELECT * FROM prod.public.orders`
either sees the old table or the new one, never empty.

### The ELT swap-and-drop pattern

Combine cloning, swap, and drop to get a bulletproof ELT deploy:

```sql
-- 1. Clone the current production table to a staging name
CREATE TABLE staging.public.orders_v2 CLONE prod.public.orders;

-- 2. Run your heavy transformations against the clone only
UPDATE staging.public.orders_v2
SET    amount = ROUND(amount * 1.10, 2);

-- 3. Atomic swap
ALTER TABLE prod.public.orders SWAP WITH staging.public.orders_v2;

-- 4. Drop the old version in the background
DROP TABLE staging.public.orders;
```

Three properties make this pattern win:

1. **Atomic.** Consumers never see an empty table.
2. **Reversible.** If the new table misbehaves, swap again to
   roll back.
3. **Zero extra storage during transformation** if the clone is the
   staging table, because it shares partitions until you mutate it.

### Hands-on: a full mini-pipeline

```sql
USE ROLE SYSADMIN;
CREATE DATABASE IF NOT EXISTS DEMO_SWAP;
USE SCHEMA DEMO_SWAP.PUBLIC;

-- Source of truth
CREATE OR REPLACE TABLE ORDERS (id NUMBER, amount NUMBER);
INSERT INTO ORDERS VALUES (1, 100), (2, 200), (3, 300);

-- Step 1: clone
CREATE OR REPLACE TABLE ORDERS_NEW CLONE ORDERS;

-- Step 2: transform the clone only
UPDATE ORDERS_NEW SET amount = amount * 2 WHERE id = 2;

-- Step 3: swap
ALTER TABLE ORDERS SWAP WITH ORDERS_NEW;

-- Step 4: inspect — should show the transformed row
SELECT * FROM ORDERS ORDER BY id;

-- Step 5: drop the old one
DROP TABLE ORDERS_NEW;
```

### Common pitfalls

- **Both tables must be of the same type.** You can't swap a
  permanent with a transient.
- **Both tables must be in the same database.** Schema swap is
  not allowed.
- **Grants**: by default, the swapped tables retain their own
  grants. If you want the production grants to follow, re-grant after
  the swap.

## Key takeaways

- `ALTER TABLE x SWAP WITH y` is an atomic rename between two
  tables in the same database.
- The classic ELT pattern is clone → transform → swap → drop.
- Swap gives zero-downtime, reversible deploys.
- Both tables must be of the same type and in the same database.

## What's next

L121 is the **recap** for section 17 — one tight summary of zero-copy
cloning, time-travel clones, and swap before we move on to data
sharing.