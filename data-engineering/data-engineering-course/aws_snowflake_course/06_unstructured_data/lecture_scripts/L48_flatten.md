---
l_id: L48
title: "Flatten hierarchical data"
duration: "9:00"
prereqs:
  - L47 (Parsing & handling array)
---

# L48 — Flatten hierarchical data

> **Section:** 6 — Loading unstructured data
> **Duration:** 9:00

## Prereqs

- L47 — Parsing & handling array

## Key terms

- **`LATERAL FLATTEN`** — table function that turns one row with an
  array (or object) into **N rows**, one per element.
- **`seq`** — output column from `FLATTEN`; the index of the
  element within the array (1-based, regardless of how the array
  itself is indexed).
- **`index`** — output column from `FLATTEN`; same as `seq` for
  array inputs.
- **`value`** — output column from `FLATTEN`; the current element
  itself (still a `VARIANT` for array-of-object inputs).
- **`path`** — output column from `FLATTEN`; the JSON path to the
  element.

## Lecture

`LATERAL FLATTEN` is the single most useful function in this
section. It is what turns **one order row with an array of line
items** into **N rows**, each carrying the order's scalar fields.
Every Snowflake JSON pipeline you'll ever write uses it.

### The minimal example

```sql
SELECT
    raw:order_id::STRING                       AS order_id,
    f.value:sku::STRING                        AS sku,
    f.value:qty::NUMBER(2, 0)                  AS qty,
    f.value:price::NUMBER(10, 2)               AS price,
    f.seq                                      AS line_seq
FROM raw_orders,
     LATERAL FLATTEN(input => raw:line_items) f;
```

What just happened?

- For every row in `raw_orders`, the `LATERAL FLATTEN` produces
  one row per element of `raw:line_items`.
- The `f` alias is the **flattened row** — it has `value`, `seq`,
  `index`, `path`, `key` columns.
- The order's scalar fields (`order_id`, `customer.*`, …) are
  repeated on each of those rows.

### The comma in the `FROM` clause is `CROSS JOIN`

`FROM raw_orders, LATERAL FLATTEN(...) f` is a `CROSS JOIN
LATERAL` — every row of `raw_orders` is paired with every row of
the flattened array. The keyword `LATERAL` is required; without it
Snowflake won't let you reference `raw_orders` columns inside the
function call.

### What the function's output columns mean

For an **array** input:

| Column | Meaning |
|---|---|
| `seq` | 1-based index (1, 2, 3, …) |
| `index` | Same as `seq` for arrays |
| `value` | The current array element (`VARIANT`) |
| `path` | `[0]`, `[1]`, `[2]`, … |
| `key` | NULL for arrays |
| `this` | The input `ARRAY` itself |

For an **object** input (when `mode = 'object'`):

| Column | Meaning |
|---|---|
| `seq` | 1-based field index |
| `key` | The field's name (e.g. `'id'`) |
| `value` | The field's value (`VARIANT`) |
| `path` | `['id']`, `['name']`, … |

### Working with `f.value`

`f.value` is a `VARIANT`. To reach into the array element's fields,
use `:` on it (no alias needed):

```sql
SELECT
    raw:order_id::STRING,
    f.value:sku::STRING                       AS sku,
    f.value:qty::NUMBER(2, 0)                 AS qty,
    f.value:price::NUMBER(10, 2)              AS price
FROM raw_orders,
     LATERAL FLATTEN(input => raw:line_items) f;
```

If the array element is itself an object, `f.value` is the object.
If the element is a scalar (a list of strings), `f.value::STRING`
gives you the scalar directly.

### Filtering inside the `FLATTEN`

`LATERAL FLATTEN` accepts `WHERE` clauses just like any other FROM
clause:

```sql
SELECT
    raw:order_id::STRING,
    f.value:sku::STRING                       AS sku,
    f.value:qty::NUMBER(2, 0)                 AS qty
FROM raw_orders,
     LATERAL FLATTEN(input => raw:line_items) f
WHERE f.value:qty::NUMBER(2, 0) >= 2;
```

That `WHERE` runs **after** the flatten — the rows that fail the
condition are dropped, not the elements that produce them. To
filter the array **before** flattening (cheaper for big arrays),
push the predicate into a subquery or CTE.

### Empty arrays

If `raw:line_items` is `[]` (empty), `FLATTEN` produces **zero
rows**. The order **disappears** from the result.

To keep empty-array orders, use `OUTER => TRUE`:

```sql
SELECT
    raw:order_id::STRING,
    f.value:sku::STRING                       AS sku,
    f.seq                                      AS line_seq
FROM raw_orders,
     LATERAL FLATTEN(input => raw:line_items, OUTER => TRUE) f;
```

`OUTER => TRUE` makes the join behave like a `LEFT JOIN` — the
`raw_orders` row is preserved with `f.*` all `NULL`.

### Building a curated line-items table

Putting it together — the shape you almost always want for a
reporting warehouse:

```sql
CREATE OR REPLACE TABLE curated_line_items AS
SELECT
    raw:order_id::STRING                       AS order_id,
    raw:customer.id::STRING                    AS customer_id,
    raw:order_ts::TIMESTAMP_LTZ                AS order_ts,
    f.value:sku::STRING                        AS sku,
    f.value:qty::NUMBER(2, 0)                  AS qty,
    f.value:price::NUMBER(10, 2)               AS price,
    f.value:price::NUMBER(10, 2) * f.value:qty::NUMBER(2, 0) AS line_total,
    raw:currency::STRING                       AS currency
FROM raw_orders,
     LATERAL FLATTEN(input => raw:line_items) f;
```

That table is now the canonical fact table for "what sold and to
whom", joinable per-order against any order-level table.

## Hands-on

Run the `curated_line_items` `CREATE TABLE AS SELECT` and verify
that the row count is `SUM(ARRAY_SIZE(raw:line_items))` across
your `raw_orders`. Then run `SELECT * FROM curated_line_items
LIMIT 5;`.

## Quiz prep

- What does `LATERAL` mean in `LATERAL FLATTEN`?
- What's the difference between `seq` and `index` for arrays?
- How do you keep orders with empty arrays?

## Key takeaways

- `LATERAL FLATTEN` is **the** operation for "explode array into
  rows".
- `f.value` is the current element; `f.seq` is its 1-based index.
- `OUTER => TRUE` keeps rows whose array is empty.
- The order's scalar fields are **repeated** on every flattened
  row — perfect for fact-table joins.

## What's next

In **L49 — Insert final data** we'll write the `INSERT INTO
curated_orders SELECT …` that consumes the parsed result and
materializes the analytics-ready table.