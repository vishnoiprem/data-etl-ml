# Advanced Dimension Design Techniques

## Why this lesson

The foundational dimension design lesson (Lesson 21) gives you the anatomy of a dim. The SCD lesson (Lesson 22) gives you the temporal machinery. This lesson goes further: how do you *share* dims across facts (conformed), how do you *reuse* the same dim in multiple roles on one fact (role-playing), and how do you handle the awkward "exception" dims that don't fit the standard pattern (junk and degenerate)? We also cover multi-valued dims and the bridge-table pattern — the advanced techniques that show up in mid-to-senior interviews. By the end, you'll have the full dimension toolkit and be able to narrate the choices in 30 seconds.

---

## Conformed dimensions

A *conformed dimension* is one logical dimension that is
shared across multiple fact tables with the *same* key and
*same* semantics. The classic example is `dim_date`: every
fact table joins to `dim_date` on `date_key`, and the meaning
of "January 15" is the same in every fact.

Other examples:

- `dim_customer` shared across `fact_orders` and
  `fact_support_tickets` (same customer_id, same attributes).
- `dim_product` shared across `fact_orders` and
  `fact_returns`.
- `dim_geography` shared across sales and inventory.

The key property: a row in the conformed dim means the same
thing in every fact that joins to it. `dim_date.date_key =
20240115` means "January 15, 2024" everywhere.

### Why conformance matters

If `dim_date` is *not* conformed — i.e., if `fact_orders`
and `fact_support_tickets` each have their own `dim_date`
table — then the analyst can't join across the two facts
without a translation step. Conformed dims make the warehouse
*joinable* across facts.

In a real warehouse, conformance is enforced by:

1. **Same table** — the fact tables share a single physical
   `dim_date` table.
2. **Same key** — the `date_key` integer is the same in
   every fact.
3. **Same semantics** — the values in `dim_date` mean the
   same thing (e.g., `month = 1` always means January in
   UTC).

### The interview pattern

> "I'm using `dim_date` as a conformed dimension. Every fact
> table joins to it on `date_key`, and the meaning of
> `date_key = 20240115` is the same everywhere. This lets the
> analyst join across facts (e.g., 'orders and support tickets
> on the same day') without a translation step."

The interviewer is checking: do you know that `dim_date` is
the *canonical* conformed dim, and that conformance is
*required* for cross-fact queries?

### The conformance trap

A common mistake: the same dim is *re-implemented* in two
fact tables with slightly different attributes. E.g.,
`fact_orders.dim_date` has `month` and `quarter`, but
`fact_support.dim_date` has only `month`. The analyst can't
compare quarters across facts.

The fix: one physical `dim_date` table, with the union of
all attributes. Every fact joins to the same table.

---

## Role-playing dimensions

A *role-playing dimension* is one logical dim used in
multiple roles on the *same* fact table. The classic example
is `dim_date` playing the roles of `order_date`,
`ship_date`, and `delivery_date` on `fact_orders`.

```
fact_orders
┌──────────────┬─────────────┬─────────────┬─────────────┐
│ order_id     │order_date_  │ ship_date_  │ delivery_   │
│              │   key       │   key       │ date_key    │
├──────────────┼─────────────┼─────────────┼─────────────┤
│ 1001         │ 20240115    │ 20240116    │ 20240120    │
│ 1002         │ 20240115    │ 20240118    │ 20240125    │
└──────────────┴─────────────┴─────────────┴─────────────┘
                  │              │              │
                  └──────────────┴──────────────┘
                                 │
                                 ▼
                           dim_date
```

The same `dim_date` table is referenced three times on the
fact, each with a different foreign-key column and a
different *role*. The column name on the fact carries the
role.

### Why this works

- The dim is *physically* the same table (so it's
  conformed).
- The fact has *multiple* foreign keys, each with a
  different role-playing alias.
- The analyst joins the same `dim_date` three times, each
  time with a different alias:

```sql
SELECT
    od.date AS order_date,
    sd.date AS ship_date,
    dd.date AS delivery_date
FROM fact_orders f
JOIN dim_date od ON f.order_date_key  = od.date_key
JOIN dim_date sd ON f.ship_date_key   = sd.date_key
JOIN dim_date dd ON f.delivery_date_key = dd.date_key;
```

### When to use

Any time the same dim plays multiple roles in a single fact.
The most common:

- `dim_date` as `order_date`, `ship_date`, `delivery_date`,
  `cancel_date`, `refund_date`.
- `dim_employee` as `salesperson`, `manager`,
  `technical_lead`.
- `dim_geography` as `ship_from`, `ship_to`, `customer_location`.

### The interview pattern

> "I'm using `dim_date` as a role-playing dimension — once
> for each date on the order (order, ship, delivery). The
> fact has three foreign keys, each labeled with its role.
> The same physical dim is joined three times in queries,
> each with a different alias."

### The "duplicate the dim" anti-pattern

A common mistake: make three copies of `dim_date` —
`dim_order_date`, `dim_ship_date`, `dim_delivery_date`.
This breaks conformance and makes the dim three times as
expensive to maintain.

The fix: one `dim_date`, three FKs on the fact.

---

## The two patterns side-by-side

| Pattern | Definition | Example |
|---|---|---|
| **Conformed** | One dim, shared across *multiple* fact tables. | `dim_date` shared by `fact_orders` and `fact_tickets`. |
| **Role-playing** | One dim, used in *multiple roles* in one fact. | `dim_date` as `order_date`, `ship_date`, `delivery_date` on `fact_orders`. |

Both patterns share the same physical dim. The difference is
*how* it's referenced: across facts (conformed) or across
columns on a single fact (role-playing).

In practice, `dim_date` is almost always both: it's
conformed across all the facts AND role-playing on the
facts that have multiple dates.

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

## Multi-valued dimensions and the bridge table

A *multi-valued dimension* is one where a single fact row
corresponds to *multiple* dim rows. The classic example: a
single workout fact has *multiple* exercises. A single
order fact has *multiple* shipping addresses. A single
account fact has *multiple* contacts.

You cannot model this with a single FK on the fact — the
fact has one slot, and the dim has many. Three solutions:

### Solution 1 — Bridge table (preferred)

A *bridge table* sits between the fact and the multi-valued
dim. It holds:

- A FK to the fact (or to the parent dim, depending on
  cardinality).
- A FK to the multi-valued dim row.
- Any measure-on-the-relationship (e.g., `reps`, `weight`).

```
dim_exercises
┌─────────────┬────────────┐
│ exercise_key│ name       │
├─────────────┼────────────┤
│ 1           │ pushup     │
│ 2           │ squat      │
│ 3           │ pull-up    │
└─────────────┴────────────┘

fact_workouts         bridge_workout_exercise
┌──────────┬────────┐  ┌──────────┬─────────────┬──────┐
│workout_id│user_key│  │workout_id│exercise_key │ reps │
├──────────┼────────┤  ├──────────┼─────────────┼──────┤
│ 1001     │ 5      │  │ 1001     │ 1           │ 20   │
│ 1002     │ 7      │  │ 1001     │ 2           │ 15   │
└──────────┴────────┘  │ 1002     │ 3           │ 10   │
                       └──────────┴─────────────┴──────┘
```

The bridge resolves the many-to-many into a queryable
shape. The downside: aggregating across the bridge
distorts counts (a workout with 3 exercises is counted
3 times if you naively sum). Senior candidates call this
out and offer a `DISTINCT` or a weighted aggregation.

### Solution 2 — Denormalize into the fact

For *low-cardinality* multi-valued dims (e.g., a workout
has 1–5 exercises, never 50), you can denormalize into the
fact row as repeated columns or a JSON array:

```sql
fact_workouts
workout_id | exercise_1_key | exercise_2_key | exercise_3_key | ...
```

This is simple but doesn't scale past ~5 multi-values per
fact row.

### Solution 3 — Outrigger / snowflake

The multi-valued dim is a sub-dimension of a parent dim.
E.g., a customer has multiple addresses; `dim_address` is
an "outrigger" of `dim_customer`. The fact joins to the
parent dim, the parent dim has a 1-to-many to the
outrigger.

```
fact_orders ── dim_customer ── (1:N) ── dim_address
```

This is the snowflake pattern applied to multi-valued
dims.

### When to use which

| Pattern | When to use |
|---|---|
| **Bridge table** | Multi-valued dim is high-cardinality or unbounded; you need to query individual values. |
| **Denormalized columns** | Multi-valued dim is small (1–5 values per fact); simplicity matters. |
| **Outrigger (snowflake)** | Multi-valued dim is owned by a parent dim (e.g., addresses belong to a customer); hierarchical query is the main access pattern. |

The interview signal: the candidate names the multi-valued
dim, picks the right pattern, and calls out the
*aggregation distortion* problem with the bridge pattern.

---

## The two patterns (junk vs degenerate) side-by-side

| Pattern | Definition | Cardinality | When to use |
|---|---|---|---|
| **Junk dim** | A collection of low-cardinality flags. | Small (10s–1000s of rows). | Many low-card flags, no obvious hierarchy. |
| **Degenerate dim** | A transaction ID on the fact. | High (1 per fact row). | A key with no attributes, just an ID. |

The interview rule:

- A handful of low-cardinality flags → junk dim.
- A single high-cardinality ID → degenerate dim.
- A real entity with attributes → real dim.
- A multi-valued relationship → bridge table, denormalized
  columns, or outrigger.

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

### For bridge table

- **Aggregation distortion** — a single fact with 3
  exercises is counted 3 times if you SUM over the
  bridge. Solution: `COUNT(DISTINCT fact_id)` or pre-aggregated
  rollup.

---

## How to narrate this in the interview

After drawing the star schema, say:

> "I'm using `dim_date` as both a conformed dimension
> (shared across all the facts in the warehouse) and a
> role-playing dimension on `fact_orders` — order date,
> ship date, and delivery date are all FKs to the same
> physical `dim_date`. The low-cardinality flags
> (`is_first_order`, `is_gift`, `payment_method`,
> `shipping_speed`) go into a `dim_order_flags` junk dim
> with one FK on the fact. The `order_id` is a degenerate
> dim on the fact — no attributes, no separate table.
> The exercises on a workout are multi-valued, so I'm
> using a `bridge_workout_exercise` table between
> `fact_workouts` and `dim_exercises`, with a DISTINCT
> guard for aggregations."

That's 30 seconds that covers four advanced techniques. The
interviewer is now satisfied that you have the full
dimension toolkit.

---

## Try it

For each of the 5 star schemas in
[`code/star_schemas.py`](../../03_high_level_diagrams/code/star_schemas.py):

1. List the conformed dimensions.
2. List any role-playing dimensions.
3. Identify any junk-dim candidates (low-cardinality
   flags that should be collected).
4. Identify any degenerate-dim candidates (transaction
   IDs that live on the fact).
5. Identify any multi-valued dims and pick a pattern
   (bridge, denormalized, or outrigger).
6. State each decision in one sentence.

Time yourself: 15 minutes.

---

## In the interview, you would say...

> "Beyond the foundational anatomy and the SCD 2 temporal
> machinery, the advanced dimension toolkit has four pieces:
> **conformed** dims (shared across facts), **role-playing**
> dims (one dim, multiple roles in one fact), **junk** dims
> (low-cardinality flags collected into one), **degenerate**
> dims (transaction IDs on the fact), and **multi-valued
> dims** solved with a bridge table. Naming each, and the
> anti-pattern it solves, is the interview signal."

---

*Author: Prem Vishnoi <prem.vishnoi@example.com>*
