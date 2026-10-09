# Lesson 24 — Transactional Fact Tables

> **What you'll learn:** the most common fact-table type — one
> row per atomic event. By the end of this lesson you'll
> know when to use it, when not to, and how to defend the
> choice.

---

## What a transactional fact is

A transactional fact table has one row per *atomic event*.
The event is a discrete, time-stamped occurrence: an order
placed, a click recorded, a payment processed, a workout
started.

The defining properties:

- **Append-only.** New rows are inserted; old rows are
  never updated or deleted.
- **High volume.** Transactional facts are the largest
  tables in a warehouse.
- **Sparse dimensions.** Most events touch a small
  subset of dimensions.

The classic example is `fact_order_items` (Lesson 16): one
row per order line item, with the order id, customer, product,
and date as dimensions and `quantity`, `gross_amount`,
`net_amount` as measures.

---

## The grain: one row per what?

The grain is *the single most important decision* in any
fact-table design. For a transactional fact, the grain is
typically:

- "one row per order line item" (e-commerce)
- "one row per workout session" (fitness app)
- "one row per click" (web analytics)
- "one row per page view" (engagement)
- "one row per transaction" (financial)

The rule: pick the *smallest* unit that still has the
information the analytics team needs. If the smallest unit
loses information, you've gone too fine. If the smallest
unit still has all the information, you can always
aggregate up.

### The "one event, one row" rule

A common trap: putting multiple events in one row. E.g., a
"session" fact with a "view_count" and a "click_count"
column. The problem: the analyst can't break out "view-only"
users from "click-only" users without an aggregate, and the
grain of the row is ambiguous (is it a session or a
view?).

The right move: one row per *view*, with a `session_id`
column to group them. The analyst can aggregate to session
level at query time; they can never disaggregate a session
row.

---

## The measures

A transactional fact has *atomic* measures — measurements
at the grain of one event. They are typically *additive*:
you can sum them across rows.

| Measure | Additive? | Notes |
|---|---|---|
| `quantity` | yes | sum across orders = total units sold |
| `gross_amount` | yes | sum = total revenue |
| `discount_amount` | yes | sum = total discounts |
| `net_amount` | yes | sum = net revenue |
| `tax_amount` | yes | sum = total tax |
| `unit_price` | no | average across orders is meaningful, sum is not |
| `duration_minutes` | yes | sum = total minutes |

Non-additive measures (like `unit_price`) can still be on
the fact — you just don't sum them. The schema doesn't
enforce this; the analyst has to know.

Some measures are *semi-additive*: they can be summed in
some dimensions but not others. `account_balance` is
semi-additive: sum across accounts is meaningful, sum
across time is not (you'd be double-counting). The interview
heuristic: if a measure can be summed *at the grain of
the fact*, it's additive; if it can only be summed in
*some* dimensions, it's semi-additive.

---

## The dimensions

A transactional fact typically joins to 3–7 dimensions:

- **`dim_date`** (conformed, role-playing) — every fact
  has a date. Sometimes multiple (e.g., `order_date`,
  `ship_date`).
- **`dim_customer`** (often SCD 2) — the "who" of the
  event.
- **`dim_product`** (often SCD 2) — the "what" of the
  event.
- **`dim_location`** — the "where" (city, country,
  region).
- **`dim_promotion`** (junk-ish) — the "why" (a
  promotional campaign that drove the event).
- **`dim_device_type`** — the "how" (mobile, web, etc.).

A common mistake: too many dimensions. If a dim has only
one row (e.g., `dim_environment` with `production` and
`staging`), it's a flag, not a dim. Use a junk dim or a
column on the fact.

---

## The example: `fact_order_items` (recap from Module 03)

```sql
CREATE TABLE fact_order_items (
    order_item_key   INTEGER PRIMARY KEY,
    customer_key     INTEGER NOT NULL,
    product_key      INTEGER NOT NULL,
    order_key        INTEGER NOT NULL,
    order_date_key   INTEGER NOT NULL,
    quantity         INTEGER NOT NULL DEFAULT 1,
    unit_price       REAL    NOT NULL,
    gross_amount     REAL    NOT NULL,
    discount_amount  REAL    NOT NULL DEFAULT 0,
    net_amount       REAL    NOT NULL,
    tax_amount       REAL    NOT NULL DEFAULT 0,
    FOREIGN KEY (customer_key)   REFERENCES dim_customers(customer_key),
    FOREIGN KEY (product_key)    REFERENCES dim_products(product_key),
    FOREIGN KEY (order_key)      REFERENCES dim_orders(order_key),
    FOREIGN KEY (order_date_key) REFERENCES dim_date(date_key)
);
```

Five dimensions, six measures, all at the line-item grain.
The `order_item_key` is a synthetic primary key. The four
FKs are the dimensions.

This is the canonical transactional fact. The grain is
stated: "one row per order line item." The measures are
all atomic. The dimensions are all conformed or
domain-specific.

---

## When to use

A transactional fact is the right choice when:

- Each event is a *discrete, atomic* action with a clear
  time stamp.
- The events are *append-only* — no row is ever updated.
- The questions the warehouse must answer are about
  *what happened*, not *what's the state*.

E-commerce sales, web clicks, page views, ad impressions,
fitness workouts, support tickets, transactions, payments,
shipments — all transactional.

## When *not* to use

A transactional fact is the *wrong* choice when:

- The question is about *state at a moment in time* (use
  a periodic snapshot — Lesson 25).
- The entity has a *lifecycle with milestones* (use an
  accumulating snapshot — Lesson 26).
- There are *no measures* — the question is just "did
  this happen?" (use a factless fact — Lesson 27).

The trap: making everything a transactional fact. A
"customer state" or "inventory level" question doesn't fit
this pattern; it fits periodic snapshot.

---

## Tradeoffs to call out

In the interview, after drawing a transactional fact, name
2–3 tradeoffs:

1. **Why transactional, not snapshot?** "Each event is
   atomic and append-only. There are no state transitions
   we need to capture over time."
2. **Why this grain (e.g., line item, not order)?** "Order
   grain loses the per-product breakdown. Line-item grain
   lets us answer 'most popular product' questions."
3. **Why these dimensions (e.g., SCD 2 on customers)?**
   "Customer attributes change and we need historical
   attribution for accurate cohort analysis."
4. **Why not include `running_total` or
   `lifetime_revenue`?** "Those are derived metrics.
   Computing them at query time is cheaper and avoids
   staleness."

---

## Try it

Open
[`code/fact_tables.py`](../code/fact_tables.py) and read
`build_transactional_fact`. Then:

1. State the grain out loud: "one row per order line
   item."
2. Identify which measures are additive vs non-additive.
3. Run the test and verify the additive measures sum
   correctly:

```bash
python3 -m unittest data_modeling/05_fact_modeling/tests/test_facts.py
```

The test asserts that `SUM(net_amount) = 320.0` for the
sample data. If you can explain why (100 + 70 + 150 = 320),
you understand additive measures.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
