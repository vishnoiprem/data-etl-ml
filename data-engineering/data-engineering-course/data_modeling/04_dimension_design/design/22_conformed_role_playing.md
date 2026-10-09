# Lesson 22 — Conformed Dimensions and Role-Playing Dimensions

> **What you'll learn:** the two patterns for sharing
> dimensions across fact tables — conformed (same dim,
> multiple facts) and role-playing (same dim, multiple
> roles in one fact). By the end of this lesson you'll be
> able to recognize both patterns and apply them correctly.

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

## How to narrate this in the interview

After drawing the star schema, say:

> "I'm using `dim_date` as both a conformed dimension
> (shared across all the facts in the warehouse) and a
> role-playing dimension on `fact_orders` — order date,
> ship date, and delivery date are all FKs to the same
> physical `dim_date`."

That's two sentences. The interviewer is now satisfied that
you know the patterns. Move on.

---

## Try it

For each of the 5 star schemas in
[`code/star_schemas.py`](../../03_high_level_diagrams/code/star_schemas.py):

1. List the conformed dimensions.
2. List any role-playing dimensions.
3. If a fact had multiple dates (e.g., `dim_date` as
   `signup_date` and `churn_date`), how would you model it?

Time yourself: 10 minutes.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
