# Lesson 23 — Junk Dimensions and Degenerate Dimensions

> **What you'll learn:** the two "exception" dimension types —
> junk dims (low-cardinality flags collected into one
> table) and degenerate dims (transaction IDs that live on
> the fact). By the end of this lesson you'll be able to
> recognize each pattern and know when to apply it.

---

## Junk dimensions

A *junk dimension* is a collection of low-cardinality flags
and attributes that don't deserve their own dimension each.
The pattern: pull them all into one "junk" dim and let the
fact FK to it.

The classic example is a `dim_order_flags` that holds:

- `is_first_order` (yes/no)
- `is_gift` (yes/no)
- `payment_method` (credit_card, paypal, apple_pay, …)
- `has_promo_code` (yes/no)
- `shipping_speed` (standard, expedited, overnight)

Each of these is a low-cardinality attribute (2–10 distinct
values). Putting each in its own dim would create 5 tiny
dims with 2–10 rows each, all of which the fact has to FK
to. The "junk" pattern pulls them into one dim with one row
per *combination*:

```
dim_order_flags
┌────────────────┬─────────┬─────────┬──────────────┬───────────────┐
│ flags_key      │is_first │is_gift  │payment_method│shipping_speed │
├────────────────┼─────────┼─────────┼──────────────┼───────────────┤
│ 1              │ yes     │ no      │ credit_card  │ standard      │
│ 2              │ no      │ yes     │ paypal       │ expedited     │
│ 3              │ no      │ no      │ apple_pay    │ overnight     │
│ …              │ …       │ …       │ …            │ …             │
└────────────────┴─────────┴─────────┴──────────────┴───────────────┘

fact_orders
┌────────┬──────────────┐
│order_id│ flags_key    │
├────────┼──────────────┤
│ 1001   │ 1            │
│ 1002   │ 2            │
│ 1003   │ 3            │
└────────┴──────────────┘
```

The fact has *one* FK to the junk dim. The analyst joins
once and gets all the flags.

### Why this works

- **One FK, one join.** The fact doesn't need 5 separate
  joins for 5 low-cardinality attrs.
- **Stable cardinality.** The junk dim has a known max
  cardinality (the product of all the per-attribute
  cardinalities), so its row count is bounded.
- **Easy to add flags.** When a new flag is needed, you add
  it to the junk dim and let the loader populate the new
  combinations.

### When to use

- The flags are *low-cardinality* (each is 2–10 distinct
  values).
- The flags are *correlated* (they tend to appear in the
  same combinations — e.g., free shipping always pairs with
  gift orders).
- The dim is *small* even at the product cardinality
  (say, < 10,000 rows).

### When *not* to use

- One of the attributes has *high cardinality* (>50 values).
  Then it deserves its own dim.
- The flags are *uncorrelated* (every combination appears).
  Then the product cardinality is huge and the junk dim
  becomes as large as the fact.

### How to draw on the whiteboard

```
                ┌──────────────────┐
                │ dim_order_flags  │
                │ (junk)           │
                └────────┬─────────┘
                         │ flags_key
                         ▼
              ┌────────────────────┐
              │    fact_orders     │
              └────────────────────┘
```

One dim, one FK. The dim is wider than a typical dim (5–10
columns) but has the same number of rows as a typical dim
(10–1000).

---

## Degenerate dimensions

A *degenerate dimension* is a transaction ID that lives on
the fact table itself, rather than in its own dim. The
classic example is `order_id` on `fact_orders`.

```
fact_orders
┌──────────┬──────────┬────────────┐
│ order_id │customer  │ …          │
│ (deg dim)│ _key     │            │
├──────────┼──────────┼────────────┤
│ 1001     │ 5        │ …          │
│ 1002     │ 7        │ …          │
│ 1003     │ 5        │ …          │
└──────────┴──────────┴────────────┘
```

`order_id` is a "dimension" in the sense that it identifies
a transaction, but it has no attributes — there's no
`dim_order` table that holds `order_id = 1001` plus more
columns. The ID is *just* an ID, and it lives on the fact.

### Why this is the right call

- The transaction ID is a *natural key* for the fact. It
  already exists on every row.
- There are no additional attributes to attach (no
  `order_date_utc`, no `order_origin`, no `order_channel`
  that don't already have their own dim).
- Creating a `dim_order` table that just has `order_id`
  and nothing else is overhead with no benefit.

The degenerate dim is a way of saying "this is a
dimension-key, but it has no attributes of its own — it
lives on the fact."

### When to use

- The "dimension" is a *single-column key* (no attributes).
- The key has *high cardinality* (one per fact row).
- The key is *meaningful* — the analyst will filter on it
  ("show me order 1001").

### When *not* to use

- You find yourself wanting to attach attributes to it
  (e.g., "the order's IP address"). Then it's a real dim.
- The key has *low cardinality* (only 5 distinct values).
  Then it might be a flag in a junk dim.

### How to draw on the whiteboard

```
              ┌────────────────────┐
              │    fact_orders     │
              │                    │
              │  order_id (deg)    │
              │  customer_key      │
              │  product_key       │
              │  …                 │
              └────────────────────┘
```

The degenerate dim is *part of* the fact. You don't draw a
separate box; you put a label on the fact's column.

---

## The two patterns side-by-side

| Pattern | Definition | Cardinality | When to use |
|---|---|---|---|
| **Junk dim** | A collection of low-cardinality flags. | Small (10s–1000s of rows). | Many low-card flags, no obvious hierarchy. |
| **Degenerate dim** | A transaction ID on the fact. | High (1 per fact row). | A key with no attributes, just an ID. |

The interview rule:

- A handful of low-cardinality flags → junk dim.
- A single high-cardinality ID → degenerate dim.
- A real entity with attributes → real dim.

---

## Tradeoffs to call out

### For junk dim

- **Why not just put the flags on the fact?** "We could,
  but then the fact has 5 extra columns of low-cardinality
  data, and the analyst has to filter on each one
  separately. The junk dim lets them join once and get all
  the flags."
- **Why not split each flag into its own dim?** "We'd have
  5 tiny dims with 2–10 rows each, all FK'd from the fact.
  The query would be 5 joins instead of 1."

### For degenerate dim

- **Why not create a `dim_order` table?** "The order_id
  has no attributes. A dim with one column is overhead
  with no benefit. The degenerate dim is the right call
  when the 'dim' is just an ID."
- **What if we need to attach attributes later?** "We
  promote the degenerate dim to a real dim. The order_id
  becomes a FK, and the new dim has the columns."

---

## Try it

For each of the 5 star schemas in
[`code/star_schemas.py`](../../03_high_level_diagrams/code/star_schemas.py):

1. Identify any junk-dim candidates (low-cardinality
   flags that should be collected).
2. Identify any degenerate-dim candidates (transaction
   IDs that live on the fact).
3. State whether each is a junk or degenerate dim in
   one sentence.

Time yourself: 10 minutes.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
