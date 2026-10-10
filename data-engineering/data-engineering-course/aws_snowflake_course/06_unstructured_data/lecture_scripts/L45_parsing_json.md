---
l_id: L45
title: "Parsing JSON"
duration: "8:00"
prereqs:
  - L44 (Load raw JSON)
---

# L45 — Parsing JSON

> **Section:** 6 — Loading unstructured data
> **Duration:** 8:00

## Prereqs

- L44 — Load raw JSON

## Key terms

- **`:` (colon)** — the path-navigation operator. `raw:customer` is a
  `VARIANT` that contains the entire `customer` object.
- **`::TYPE`** — explicit cast. `raw:total::NUMBER(10, 2)` converts
  the `VARIANT` to `NUMBER`.
- **`GET_PATH(...)`** — function form of `:`. Useful for dynamic
  paths or paths with special characters.
- **`NULL` propagation** — if any segment of the path is missing or
  `NULL`, the whole expression is `NULL`. No error is raised.

## Lecture

Now that the file is loaded, the real work begins: turning a single
`VARIANT` column into 5, 10, or 50 typed columns. Snowflake gives
us three operators for that — `:` to navigate, `::` to cast, and
`get_path()` when `:` isn't flexible enough.

### The `:` operator — reach into a JSON object

```sql
SELECT
    raw:order_id                            AS order_id_variant,
    raw:order_id::STRING                    AS order_id_str,
    raw:currency                            AS currency_variant,
    raw:total::NUMBER(10, 2)                AS total_num
FROM raw_orders
LIMIT 5;
```

Notice:

- `raw:order_id` (no cast) is still a `VARIANT`. You almost always
  want to cast it.
- `::STRING` / `::NUMBER(10, 2)` / `::TIMESTAMP_LTZ` etc. are
  standard SQL casts.
- The path is **case-sensitive**: `raw:order_id` is not the same as
  `raw:Order_Id`.

### The `:.` shortcut — navigate and cast in one step

Snowflake has a `:.` shorthand that combines navigation and cast:

```sql
SELECT
    raw:order_id::STRING                    AS order_id,
    raw:total::NUMBER(10, 2)                AS total,
    raw:order_ts::TIMESTAMP_LTZ             AS order_ts,
    raw:currency::STRING                   AS currency
FROM raw_orders;
```

The `::TYPE` suffix is what turns `:.` into a one-step operation.
Use `:.` for the common case (one path, one cast) and the long
form when you need to do **two things** — e.g. parse a string,
trim, and lowercase — in a single expression.

### Multi-segment paths — into nested objects

`raw:customer.email` reaches into the `customer` object:

```sql
SELECT
    raw:customer.id::STRING                 AS customer_id,
    raw:customer.name::STRING               AS customer_name,
    raw:customer.email::STRING              AS customer_email
FROM raw_orders;
```

You can chain as deep as you like: `raw:a.b.c.d::STRING` is valid.
The earlier the chain breaks (because the field is missing), the
more rows you'll see with `NULL`.

### `get_path()` — the function form

When the path is dynamic (built in a variable) or contains characters
that the `:` operator doesn't like (spaces, hyphens at the start of a
key, …), use `GET_PATH`:

```sql
SELECT
    GET_PATH(raw, 'customer.email')::STRING AS customer_email,
    GET_PATH(raw, 'line_items[0].sku')::STRING AS first_sku
FROM raw_orders;
```

This is functionally identical to `raw:customer.email::STRING`. The
advantage is that you can build the path with string concatenation.

### NULL propagation — the most important behaviour

Snowflake does **not** raise an error when a JSON path is missing:

```sql
SELECT
    raw:customer.email::STRING  AS email,
    raw:customer.phone::STRING  AS phone
FROM raw_orders
LIMIT 5;
```

If 3 orders have `customer.phone`, you'll get 3 non-null values and
2 `NULL`s. **That is the desired behaviour for the `raw` layer.** In
the curated table you decide: do you keep `NULL`, substitute a
default, or `IFF(raw:customer.phone IS NULL, 'unknown', …)`?

### Type-coercion pitfalls

A few JSON shapes that bite:

- **Numbers as strings** — `{"total": "149.97"}` will not
  `::NUMBER`. Use `::FLOAT` then `::NUMBER`, or fix the source.
- **Timestamps** — `{"ts": "2026-10-01T12:34:56Z"}` parses with
  `::TIMESTAMP_LTZ`. Without a timezone, use `::TIMESTAMP_NTZ`.
- **Booleans** — JSON `true` / `false` → `::BOOLEAN`. But
  `"true"` (string) does **not** cast to boolean; use
  `IFF(raw:active = 'true', TRUE, FALSE)`.
- **Empty arrays/objects** — `[]` and `{}` are valid `VARIANT`.
  Casting them to a scalar type yields `NULL`.

### Build a small parser query

Putting it together — a one-shot preview of what the curated table
will look like:

```sql
SELECT
    raw:order_id::STRING              AS order_id,
    raw:order_ts::TIMESTAMP_LTZ       AS order_ts,
    raw:customer.id::STRING           AS customer_id,
    raw:customer.name::STRING         AS customer_name,
    raw:total::NUMBER(10, 2)          AS total,
    raw:currency::STRING              AS currency
FROM raw_orders;
```

That `SELECT` is what L49 will turn into `INSERT INTO curated_orders
… SELECT … FROM raw_orders`.

## Hands-on

Run the parser query above against `raw_orders` and inspect 5 rows.
For each column, ask: "what does this look like when the path is
absent?" (`NULL`.)

## Quiz prep

- What is the difference between `:` and `:.`?
- What happens when a JSON path is missing?
- Name two type-coercion pitfalls and how you'd handle each.

## Key takeaways

- `:` reaches into a JSON path; `::TYPE` casts the result.
- `:.` is a one-step navigate-and-cast operator.
- Missing paths produce `NULL`, not an error.
- `GET_PATH` is the function form when you need dynamic paths.

## What's next

In **L46 — Handling nested data** we tackle the deeper problem of
objects inside objects (`customer` → `address` → `street`) and how
to extract them with multi-segment paths.