---
l_id: L46
title: "Handling nested data"
duration: "8:00"
prereqs:
  - L45 (Parsing JSON)
---

# L46 — Handling nested data

> **Section:** 6 — Loading unstructured data
> **Duration:** 8:00

## Prereqs

- L45 — Parsing JSON

## Key terms

- **Multi-segment path** — `raw:customer.address.city` reaches
  through three object levels.
- **Flattening object** — turning a nested object into its own set
  of columns in the curated table. Each leaf becomes one column.
- **Object literal vs path** — `raw:customer` is a path; the value
  is still a `VARIANT` containing the object.

## Lecture

Most real-world JSON is **hierarchical** — a `customer` object has
an `address` object, which has a `city` field. Snowflake handles
this naturally: you just chain the `:` operators. The mental model
you want is *"the whole object tree is reachable from `raw`, one
colon at a time"*.

### A deeper customer object

Let's say our orders JSON now has a 3-level nested customer:

```json
{
  "order_id": "ORD-1001",
  "customer": {
    "id": "C-42",
    "name": "Ada Lovelace",
    "address": {
      "street": "10 Downing St",
      "city": "London",
      "postcode": "SW1A 2AA",
      "country": "UK"
    }
  }
}
```

### Reach into nested fields

```sql
SELECT
    raw:order_id::STRING                       AS order_id,
    raw:customer.id::STRING                    AS customer_id,
    raw:customer.name::STRING                  AS customer_name,
    raw:customer.address.street::STRING        AS street,
    raw:customer.address.city::STRING          AS city,
    raw:customer.address.postcode::STRING      AS postcode,
    raw:customer.address.country::STRING       AS country
FROM raw_orders;
```

Multi-segment paths are **left-to-right and case-sensitive**.
Each `:` is one level of nesting. Three colons = four levels deep.

### When to stop and flatten

There's a tension: the deeper your nesting, the longer the column
aliases get. The convention we follow in this course is:

- **≤ 3 levels deep**: use multi-segment paths.
- **> 3 levels deep**: extract the parent object into its own
  `VARIANT` column and add a downstream table for that leaf.

For example, if `customer.address` had a further nested
`coordinates.{ lat, lng }`, we'd put `raw:customer.address::VARIANT`
in one column and parse `coordinates` separately.

### Build the curated table — one column per leaf

```sql
CREATE OR REPLACE TABLE curated_orders AS
SELECT
    raw:order_id::STRING                       AS order_id,
    raw:order_ts::TIMESTAMP_LTZ                AS order_ts,
    raw:customer.id::STRING                    AS customer_id,
    raw:customer.name::STRING                  AS customer_name,
    raw:customer.address.street::STRING        AS street,
    raw:customer.address.city::STRING          AS city,
    raw:customer.address.postcode::STRING      AS postcode,
    raw:customer.address.country::STRING       AS country,
    raw:total::NUMBER(10, 2)                   AS total,
    raw:currency::STRING                       AS currency,
    raw:payment.method::STRING                 AS payment_method,
    raw:payment.last4::STRING                  AS payment_last4
FROM raw_orders;
```

That `AS` clause is doing double duty — naming the column **and**
declaring its Snowflake type from the cast. Snowflake infers
`STRING` / `NUMBER` / `TIMESTAMP_LTZ` from `::TYPE`.

### What to do with the **nested** object itself

Sometimes you want the whole nested object as a single `VARIANT`
column (for example, to share the data set later without exploding
it). Just **omit** the `::CAST`:

```sql
SELECT
    raw:order_id::STRING  AS order_id,
    raw:customer          AS customer_obj   -- still VARIANT
FROM raw_orders;
```

`customer_obj` is a `VARIANT` containing the entire `customer`
object. Useful for "I'll flatten this later" tables.

### Pitfalls with nested objects

- **Misspelling a parent** — `raw:customers.name` (plural) is
  `NULL` for every row. The path silently produces `NULL`, so
  always spot-check with a `LIMIT 5`.
- **Wrong case** — `raw:customer.Address.city` is `NULL`. JSON
  keys are case-sensitive in Snowflake.
- **Returning the parent** vs **a leaf** — `raw:customer` is a
  `VARIANT`; `raw:customer.name` is also a `VARIANT` until you
  `::STRING`. Forgetting the cast is the most common cause of
  "everything is a string" in the curated table.

### Verify with `LIMIT 5`

Always run the curated table preview before `INSERT`-ing:

```sql
SELECT * FROM curated_orders LIMIT 5;
```

Expected: every column populated, no obvious `NULL`s except where
the source JSON itself is missing a field.

## Hands-on

Add a `customer.address` block to your test JSON, reload the raw
table with `FORCE = TRUE`, and verify that all four address fields
appear in `curated_orders`.

## Quiz prep

- How deep can a `:` path be?
- What is the rule of thumb for when to flatten vs keep a nested
  object?
- Why does `raw:customer` (no `::CAST`) still return a `VARIANT`?

## Key takeaways

- Multi-segment paths (`raw:a.b.c`) reach into nested objects.
- The convention: ≤ 3 levels of paths, then break out a parent
  `VARIANT` column.
- Forgetting `::TYPE` leaves you with a `VARIANT`, not a typed
  column.
- Spot-check with `LIMIT 5` — path misses produce `NULL`, not
  errors.

## What's next

In **L47 — Parsing & handling array** we tackle the array half of
the problem: `line_items[]` is an array of objects, and the
curated table needs **one row per item**.