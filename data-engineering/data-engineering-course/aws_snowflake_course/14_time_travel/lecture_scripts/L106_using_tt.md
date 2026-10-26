---
l_id: L106
title: Using time travel
duration: "10:00"
prereqs: ["L105 - What is Time Travel?"]
---

# L106 — Using time travel

> **Author:** Prem Vishnoi &lt;pvishnoi&commat;avilx.com&gt;
> **Section:** 14 — Time Travel
> **Duration:** 10:00

## Prereqs

A table you can mutate (`UPDATE`/`DELETE`/`TRUNCATE`) and a role
with the rights to do so. A scratch schema is the cleanest way to
practice.

## Lecture

The three `AT | BEFORE` forms are the heart of Time Travel. In
this lecture we run through each one on a real table.

### Setup — a scratch table

```sql
CREATE OR REPLACE SCHEMA scratch;
USE SCHEMA scratch;

CREATE OR REPLACE TABLE prices (
  product_id NUMBER,
  price      NUMBER(10,2),
  updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

INSERT INTO prices VALUES
  (1, 10.00, CURRENT_TIMESTAMP()),
  (2, 20.00, CURRENT_TIMESTAMP()),
  (3, 30.00, CURRENT_TIMESTAMP());
```

### Form 1 — `AT (TIMESTAMP => ...)`

Anchor a query to a specific UTC moment.

```sql
-- Capture a "before" moment
SELECT CURRENT_TIMESTAMP() AS before_ts;
-- 2024-06-15 14:30:00.123 -0700

-- Update the table
UPDATE prices SET price = price * 1.10 WHERE product_id = 1;

-- Query the past state
SELECT * FROM prices
AT (TIMESTAMP => '2024-06-15 14:30:00.123'::TIMESTAMP_NTZ)
ORDER BY product_id;
```

You should see the pre-update price (10.00) for product 1.

### Form 2 — `AT (OFFSET => -<n> <unit>)`

Anchor relative to "now".

```sql
-- 5 minutes ago
SELECT * FROM prices
AT (OFFSET => -5 MINUTES)
ORDER BY product_id;

-- 1 hour ago
SELECT * FROM prices
AT (OFFSET => -60 MINUTES)
ORDER BY product_id;
```

`OFFSET` is the easiest form for ad-hoc "what changed in the
last hour" queries.

### Form 3 — `BEFORE (STATEMENT => ...)`

Anchor to the state just before a specific query.

```sql
-- 1. Capture the query ID of the bad UPDATE
SET qid = LAST_QUERY_ID();

-- (or copy the ID from a worksheet history: SELECT LAST_QUERY_ID();)

-- 2. Query the state before that statement
SELECT * FROM prices
BEFORE (STATEMENT => '$qid'::STRING)
ORDER BY product_id;
```

`BEFORE (STATEMENT => ...)` is the right tool when a query ID
is the only handle you have. Snowflake keeps enough history
to resolve the statement (within the retention window).

### The full restore recipe (preview)

We'll use this in L107 — preview here:

```sql
-- "Undo" the bad update by cloning the past state into a new table
CREATE OR REPLACE TABLE prices_restored CLONE prices
  AT (OFFSET => -10 MINUTES);

-- Swap the restored table in
ALTER TABLE prices SWAP WITH prices_restored;

-- Verify
SELECT * FROM prices ORDER BY product_id;
```

`SWAP WITH` is the standard "atomic rollback" pattern —
covered in section 17 (Zero-Copy Cloning).

### Inspecting what's available

```sql
-- How far back can I go on this table?
SHOW TABLES LIKE 'prices';
-- DATA_RETENTION_TIME_IN_DAYS column

-- How much storage is being used by historical versions?
SELECT *
FROM TABLE(INFORMATION_SCHEMA.TABLE_STORAGE_METRICS(
  TABLE_NAME => 'scratch.prices'
));
```

The `TIME_TRAVEL_BYTES` column tells you the cost of keeping
the history. Tune it with the retention parameter in L109.

### Common gotchas

- **`AT (TIMESTAMP => ...)`** is in **UTC**, not your session
  timezone. Always specify `::TIMESTAMP_NTZ` or convert from
  your local time.
- **`OFFSET` can go past the retention window** — if you ask
  for `-100 DAYS` and retention is 1 day, you get an error.
- **Time Travel does not survive `TRUNCATE` on its own.** A
  `TRUNCATE` is logged as a metadata change, so you can still
  `AT | BEFORE` to recover rows, but only within retention.

## Key takeaways

- `AT (TIMESTAMP => ...)` for absolute moments.
- `AT (OFFSET => -n <unit>)` for relative offsets.
- `BEFORE (STATEMENT => ...)` for surgical rollback.
- All three work the same way in `SELECT`, `CREATE TABLE ...
  CLONE`, and `SHOW`.

## What's next

In **L107 — Restoring data** we use Time Travel to undo a real
bad `UPDATE` and a real bad `DELETE`.
