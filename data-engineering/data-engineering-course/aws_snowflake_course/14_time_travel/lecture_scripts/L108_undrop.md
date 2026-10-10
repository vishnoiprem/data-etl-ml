---
l_id: L108
title: UNDROP tables
duration: "7:00"
prereqs: ["L107 - Restoring data"]
---

# L108 — UNDROP tables

> **Author:** Prem Vishnoi &lt;pvishnoi&commat;avilx.com&gt;
> **Section:** 14 — Time Travel
> **Duration:** 7:00

## Prereqs

A role with `OWNERSHIP` on the schema (or `CREATE TABLE` plus
the right to undrop objects). A scratch schema is fine.

## Lecture

When the disaster is "I dropped the table", you don't need a
clone — you need `UNDROP`. Snowflake retains the dropped object's
metadata (and its data, within the retention window) so you can
restore it in one statement.

### The most common case: drop a table, undrop it

```sql
USE SCHEMA scratch;
DROP TABLE prices;
-- Whoops. The table is gone.

-- One statement:
UNDROP TABLE prices;

SELECT * FROM prices;  -- back
```

`UNDROP` restores the table with the same name, schema, columns,
and data as of the moment before the drop. Grants, comments, and
clustering keys are preserved; tasks and streams attached to the
table are *not* automatically reattached.

### Undrop a schema

```sql
DROP SCHEMA scratch;
-- oops
CREATE SCHEMA scratch;  -- recreate empty schema

UNDROP SCHEMA scratch;
-- wait — that fails because the schema we just created has
-- a different object ID. Drop the empty one first:
DROP SCHEMA scratch;
UNDROP SCHEMA scratch;
```

The "recreate the empty stub so we can `UNDROP`" pattern is a
common gotcha. If you `DROP SCHEMA` and try to `UNDROP` without
the empty stub, it works. If you already created a new schema
with the same name, drop the stub and then `UNDROP`.

### Undrop a database

```sql
DROP DATABASE sandbox;
UNDROP DATABASE sandbox;
```

Same pattern, same caveat about an existing empty stub.

### What `UNDROP` does NOT do

- It does **not** restore `DROP TABLE ... CASCADE` cleanly —
  dependent views and tasks are still gone.
- It does **not** restore the object after the retention
  window. After Time Travel ends, the metadata is purged.
- It does **not** restore dropped roles, users, or warehouses.
  Those are account-scoped, not database objects.

### Recovering a dropped column or table structure

There is no `UNDROP COLUMN`. If you `ALTER TABLE ... DROP
COLUMN my_col`, the data is gone for that column. The workarounds:

1. **Time Travel + clone** — `CREATE TABLE prices_undo CLONE
   prices BEFORE (STATEMENT => '<alter_id>'::STRING); ALTER TABLE
   prices SWAP WITH prices_undo;`
2. **Stream + clone** — if you have an `APPEND_ONLY = TRUE`
   stream on the table, you can replay the column from the
   stream's offset. (Streams are in section 20.)

### The "oops, I ran the wrong script" drill

Set yourself up for a successful recovery in advance:

1. Make sure every dev/prod database has
   `DATA_RETENTION_TIME_IN_DAYS = 7` (or whatever the SLA
   needs).
2. Practice `UNDROP` on a scratch table so the muscle memory
   is there.
3. Keep a one-pager: "If you dropped X, run `UNDROP X`; if
   you ran an `UPDATE`/`DELETE`, find the query ID, run the
   clone + swap recipe from L107."

## Key takeaways

- `UNDROP TABLE|SCHEMA|DATABASE <name>` recovers a dropped
  object within retention.
- If you've already recreated the empty stub, drop it before
  you `UNDROP`.
- For "wrong `UPDATE`/`DELETE`", clone + swap is the recipe;
  for "dropped the whole thing", `UNDROP` is the recipe.

## What's next

In **L109 — Retention time** we tune
`DATA_RETENTION_TIME_IN_DAYS` and look at the storage cost of
keeping history.
