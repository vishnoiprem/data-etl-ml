---
l_id: L42
title: "Understanding our data"
duration: "6:00"
prereqs:
  - L41 (High-level steps)
---

# L42 — Understanding our data

> **Section:** 6 — Loading unstructured data
> **Duration:** 6:00

## Prereqs

- L41 — High-level steps

## Key terms

- **JSON object** — `{ "key": value, … }`. Think of it as a Python
  `dict`.
- **JSON array** — `[ v1, v2, … ]`. Think of it as a Python `list`.
- **Path navigation** — Snowflake's `:` (object field) and `:.` (cast)
  operators. `raw:customer.name::STRING` reaches into the object.
- **Lateral flatten input** — any `ARRAY` or `OBJECT` you can "spread
  out" into multiple rows. The most common input is the
  `raw:line_items` array.

## Lecture

Before we touch `COPY INTO`, let's look at the file we'll be loading.
The `JSON` in this course is an **orders** file — one order per line,
each with a nested customer, a list of line items, and a payment
object. It is the kind of shape a real e-commerce API returns.

### Sample document

One row in our file looks like this:

```json
{
  "order_id": "ORD-1001",
  "order_ts": "2026-10-01T12:34:56Z",
  "currency": "USD",
  "total": 149.97,
  "customer": {
    "id": "C-42",
    "name": "Ada Lovelace",
    "email": "ada@example.com"
  },
  "line_items": [
    { "sku": "BK-001", "qty": 2, "price": 24.99 },
    { "sku": "PN-007", "qty": 1, "price": 99.99 }
  ],
  "payment": { "method": "card", "last4": "4242" }
}
```

Three things to notice:

1. **Scalars at the top** — `order_id`, `currency`, `total`.
2. **A nested object** — `customer.{ id, name, email }`.
3. **An array of objects** — `line_items[].{ sku, qty, price }`.

That combination — scalars + objects + arrays — is the JSON shape you
will see in 90% of real workloads.

### The four questions to ask of any JSON file

Before writing a single line of SQL, ask:

1. **What is the unit of one row?** (Here: one `order`.)
2. **Which fields are scalars?** (`order_id`, `total`, `currency`.)
3. **Which fields are nested objects?** (`customer`, `payment`.)
4. **Which fields are arrays?** (`line_items`.)

Answers drive two decisions: the columns of your **curated** table
(answer 2), and the `LATERAL FLATTEN` call (answer 4).

### Peek inside a `VARIANT` with `PARSE_JSON`

If you already have the JSON in a string column, you can convert it
to a `VARIANT` for inspection:

```sql
SELECT PARSE_JSON('{
  "order_id": "ORD-1001",
  "total": 149.97,
  "customer": { "id": "C-42", "name": "Ada" }
}') AS v;
```

`PARSE_JSON` is mostly used in ad-hoc debugging. In our pipeline the
`COPY INTO` into the `VARIANT` column does the parsing for us.

### Reach into the data with path operators

The two operators you'll type hundreds of times are `:` and `:.`:

```sql
SELECT
    raw:order_id::STRING            AS order_id,
    raw:total::NUMBER(10, 2)        AS total,
    raw:customer.name::STRING       AS customer_name,
    raw:customer.email::STRING      AS customer_email,
    raw:line_items[0].sku::STRING   AS first_sku
FROM raw_orders;
```

`:` gets the value (still `VARIANT`). `::TYPE` casts it. We will
deep-dive into the syntax in L45 — for now, just notice that
`raw:customer.name` reaches into the **object** and
`raw:line_items[0]` indexes into the **array**.

### Spot the array — it is the row-multiplier

`line_items` is an array. In the curated table, **one order → many
rows**. We will need `LATERAL FLATTEN(input => raw:line_items)` to
turn each element of that array into its own row. The non-array
fields (`order_id`, `customer.*`, `total`) get repeated on every
flattened row.

### Why we look at the file *first*

Looking at the JSON before writing SQL prevents two common mistakes:

- **Forgetting the array** — if you only know the scalar fields, you
  will quietly lose data when an order has more than one line item.
- **Mis-typing the path** — `raw:customer.name` is right;
  `raw:customer["name"]` is also right; `raw.customer.name` is
  **wrong** (those dots are SQL identifier separators, not JSON
  paths).

## Hands-on

Open the file we'll be using — `code/orders.json` in this section's
`code/` folder — and answer the four questions above for yourself.
Don't write any SQL yet; L43 is where we set up the stage.

## Quiz prep

- What is the difference between `:` and `::` in Snowflake?
- Why is `line_items` the array we will need to `FLATTEN`?
- What are the four questions to ask of any JSON file before
  loading it?

## Key takeaways

- Always **read the JSON file first** — note scalars, objects, and
  arrays.
- `:` navigates a path; `::TYPE` casts the result.
- Arrays are row-multipliers; **one order → many `line_items` rows**.
- `LATERAL FLATTEN` is how we turn an array into rows.

## What's next

In **L43 — Creating stage & raw table** we'll create the stage that
points at our JSON file and the `raw_orders` `VARIANT` table we'll
load into.
