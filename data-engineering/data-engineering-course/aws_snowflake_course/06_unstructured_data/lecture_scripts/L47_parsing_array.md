---
l_id: L47
title: "Parsing & handling array"
duration: "8:00"
prereqs:
  - L46 (Handling nested data)
---

# L47 — Parsing & handling array

> **Section:** 6 — Loading unstructured data
> **Duration:** 8:00

## Prereqs

- L46 — Handling nested data

## Key terms

- **Array element access** — `raw:line_items[0]`, `raw:line_items[1]`.
  Snowflake uses **zero-based** indexing, like C / Java / JS.
- **`ARRAY_SIZE(...)`** — returns the number of elements in a JSON
  array.
- **`ARRAY_CONSTRUCT(...)`** — builds a JSON array from scalars.
- **`LATERAL FLATTEN`** — the operation that turns an array into
  rows. Covered in L48.

## Lecture

Arrays are the most interesting part of JSON. They are also where
people get stuck. This lecture is the **prerequisite** for
`LATERAL FLATTEN` — by the end of it you'll be able to read a single
element out of an array using `[N]`.

### Sample array

Our `raw_orders` JSON has:

```json
{
  "order_id": "ORD-1001",
  "line_items": [
    { "sku": "BK-001", "qty": 2, "price": 24.99 },
    { "sku": "PN-007", "qty": 1, "price": 99.99 }
  ]
}
```

`line_items` is an **array of objects**. Each element is one
purchase on the order.

### Reach a single element with `[N]`

Snowflake uses **zero-based** indexing:

```sql
SELECT
    raw:order_id::STRING                       AS order_id,
    raw:line_items[0].sku::STRING              AS first_sku,
    raw:line_items[0].qty::NUMBER(2, 0)        AS first_qty,
    raw:line_items[0].price::NUMBER(10, 2)     AS first_price,
    raw:line_items[1].sku::STRING              AS second_sku
FROM raw_orders;
```

Important: `line_items[0]` is the **first** element, not `[1]`. This
is a frequent source of off-by-one bugs for SQL Server / Oracle
backgrounds.

### Negative indexing is **not** supported

`raw:line_items[-1]` is **not** valid. To get the last element,
you need to compute its index:

```sql
SELECT
    raw:line_items[
        ARRAY_SIZE(raw:line_items) - 1
    ].sku::STRING  AS last_sku
FROM raw_orders;
```

In practice, you'll rarely do this — `LATERAL FLATTEN` (L48) gives
you access to every element with `seq` (sequence number) and
`index` columns.

### Useful array functions

`ARRAY_SIZE(v)` — number of elements:

```sql
SELECT
    raw:order_id::STRING                       AS order_id,
    ARRAY_SIZE(raw:line_items)                 AS line_count
FROM raw_orders;
```

`ARRAY_CONSTRUCT(...)` — build an array from scalars:

```sql
SELECT ARRAY_CONSTRUCT('a', 'b', 'c')          AS arr;
-- [ "a", "b", "c" ]  -- VARIANT
```

`ARRAY_CONTAINS(v, arr)` — membership test:

```sql
SELECT
    raw:order_id::STRING,
    ARRAY_CONTAINS('BK-001'::VARIANT, raw:line_items.sku) AS has_book
FROM raw_orders;
```

(Note: that `raw:line_items.sku` shorthand is an **implicit
flatten** — it works for scalar fields of an array's elements but
is easy to misread. We prefer the explicit `LATERAL FLATTEN` for
production code.)

### Returning the **whole array** as a `VARIANT`

Sometimes you want the array unflattened:

```sql
SELECT
    raw:order_id::STRING,
    raw:line_items                              AS line_items_v
FROM raw_orders;
```

`line_items_v` is a `VARIANT` containing the array. Useful for
"pass-through" tables and for storing arrays when the downstream
consumer knows how to flatten.

### Building a single-line-item curated row

Sometimes you want exactly **one row per order** — e.g. for a
summary table. Use `[0]` for the first line item, or aggregate:

```sql
SELECT
    raw:order_id::STRING                          AS order_id,
    raw:line_items[0].sku::STRING                 AS primary_sku,
    raw:line_items[0].qty::NUMBER(2, 0)           AS primary_qty,
    ARRAY_SIZE(raw:line_items)                    AS line_count,
    SUM(raw:line_items.price::NUMBER(10, 2))      AS line_total
FROM raw_orders
GROUP BY
    raw:order_id,
    raw:line_items[0].sku,
    raw:line_items[0].qty;
```

The `SUM(raw:line_items.price)` form is a **FLATTEN-style sum**
where Snowflake aggregates the array for you. Convenient, but
limited — for anything beyond "sum this column", use
`LATERAL FLATTEN`.

### When to use `[N]` vs `LATERAL FLATTEN`

The rule of thumb:

- **`[N]`** — when you want a specific, known-position element
  (e.g. "first line item").
- **`LATERAL FLATTEN`** — when you want **every element** as its own
  row, with the surrounding object fields repeated on each row.

We use `LATERAL FLATTEN` in L48 to build the canonical
`curated_line_items` table.

## Hands-on

Run the `ARRAY_SIZE` query above and confirm `line_count` matches
the array length for the first 5 orders. Try `raw:line_items[2]`
on an order that has only 2 items — you should see `NULL`.

## Quiz prep

- Is Snowflake's array indexing zero-based or one-based?
- What does `ARRAY_SIZE` return for an empty array?
- When do you use `[N]` vs `LATERAL FLATTEN`?

## Key takeaways

- Use `[N]` for **specific element** access; Snowflake is
  **zero-based**.
- `ARRAY_SIZE`, `ARRAY_CONSTRUCT`, and `ARRAY_CONTAINS` are the
  workhorse array helpers.
- Negative indexing is **not** supported.
- For "every element as a row", use `LATERAL FLATTEN` (L48).

## What's next

In **L48 — Flatten hierarchical data** we cover `LATERAL FLATTEN`
in depth — the operation that turns `line_items` into many rows,
each carrying the order's scalar fields.