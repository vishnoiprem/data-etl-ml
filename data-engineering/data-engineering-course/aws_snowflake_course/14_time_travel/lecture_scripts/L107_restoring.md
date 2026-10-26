---
l_id: L107
title: Restoring data
duration: "9:00"
prereqs: ["L106 - Using time travel"]
---

# L107 — Restoring data

> **Author:** Prem Vishnoi &lt;pvishnoi&commat;avilx.com&gt;
> **Section:** 14 — Time Travel
> **Duration:** 9:00

## Prereqs

The scratch `prices` table from L106. A role with `OWNERSHIP` on
the schema.

## Lecture

The two production disasters Time Travel solves cleanly are the
"bad `UPDATE`" and the "bad `DELETE`". In both cases the right
pattern is **clone the past state, swap it in** — never `INSERT`
back from a past version (it rewrites micro-partitions and
double-bills you on storage).

### Disaster 1 — bad UPDATE

```sql
-- Oops: scaled everything by 0.01 instead of 1.10
UPDATE prices SET price = price * 0.01;
SELECT * FROM prices;  -- all 0.10, 0.20, 0.30

-- Recover
CREATE OR REPLACE TABLE prices_undo CLONE prices
  AT (OFFSET => -10 MINUTES);

ALTER TABLE prices SWAP WITH prices_undo;
DROP TABLE prices_undo;

SELECT * FROM prices;  -- 10, 20, 30
```

`SWAP WITH` is atomic: in the time it takes Snowflake to rename
the two tables, no other query can see the in-between state.

### Disaster 2 — bad DELETE

```sql
DELETE FROM prices WHERE product_id = 2;
SELECT * FROM prices;  -- 1 and 3

-- Recover — clone before the DELETE
CREATE OR REPLACE TABLE prices_undo CLONE prices
  BEFORE (STATEMENT => '<query_id_of_the_delete>'::STRING);

ALTER TABLE prices SWAP WITH prices_undo;
DROP TABLE prices_undo;
```

The `BEFORE (STATEMENT => ...)` form is critical here — you
want the version **just before** the DELETE, which is exactly
what the statement ID resolves to.

### Disaster 3 — bad TRUNCATE

```sql
TRUNCATE TABLE prices;
SELECT COUNT(*) FROM prices;  -- 0

-- Recover (within retention)
CREATE OR REPLACE TABLE prices_undo CLONE prices
  AT (OFFSET => -5 MINUTES);

ALTER TABLE prices SWAP WITH prices_undo;
DROP TABLE prices_undo;
```

`TRUNCATE` is a metadata operation, so the rows are still
recoverable for the duration of the retention window.

### Disaster 4 — wrong WHERE in a MERGE

```sql
MERGE INTO prices tgt
USING (SELECT * FROM prices WHERE product_id = 1) src
ON tgt.product_id = src.product_id
WHEN MATCHED THEN UPDATE SET price = 0.00;  -- yikes

-- Recover: clone the state before the MERGE
CREATE OR REPLACE TABLE prices_undo CLONE prices
  BEFORE (STATEMENT => LAST_QUERY_ID()::STRING);

ALTER TABLE prices SWAP WITH prices_undo;
DROP TABLE prices_undo;
```

### Why not `INSERT INTO ... SELECT ... AT | BEFORE ...`?

You can, but it has two downsides:

1. It rewrites every micro-partition of the target table —
   billing you storage twice for the new state.
2. The "old" rows still exist in Time Travel history, so you
   pay for them twice.

Cloning the past state is **zero-copy** — the clone references
the same micro-partitions as the historical version. You only
pay the storage delta when you `SWAP` and the new table is
garbage-collected.

### When SWAP is not enough

- If the bad statement created a *different* table and you
  want to roll back that table, the same pattern works on any
  table.
- If the bad statement modified *multiple* tables, do the clone
  + swap on each one.
- If you need the entire database at a past state, the cleanest
  approach is `CREATE DATABASE ... CLONE ... AT | BEFORE ...`
  (covered in section 17) and then `SWAP WITH` at the database
  level.

## Key takeaways

- The right pattern is `CLONE ... AT | BEFORE ...` + `SWAP
  WITH`, not `INSERT ... SELECT`.
- `BEFORE (STATEMENT => ...)` is the surgical tool when you
  have the bad query ID.
- `SWAP WITH` is atomic — no torn state.

## What's next

In **L108 — UNDROP tables** we cover the other half of the
recovery story: when the table itself is gone.
