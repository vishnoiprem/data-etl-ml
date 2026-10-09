# Lesson 25 — Periodic Snapshot Fact Tables

> **What you'll learn:** when the question is "what's the
> state at a moment in time?" — a periodic snapshot is the
> answer. By the end of this lesson you'll know the
> pattern, the grain, and the tradeoffs.

---

## What a periodic snapshot is

A periodic snapshot fact table has one row per
**(entity, time period)**. The grain captures the
*state* of an entity at the end of each period.

The defining properties:

- **Rebuilt each period.** At the end of each period, a
  new row is appended for every active entity. Old rows
  stay (you have history).
- **State measures.** The measures are *state values* at
  the end of the period, not events that happened during
  the period.
- **Period-over-period comparison.** The whole point is
  to compare period N to period N-1.

The classic example is `fact_subscriptions_monthly` from
Lesson 09: one row per customer-month, with `mrr` and
flags (`is_active`, `is_new`, `is_churned`) as measures.

---

## The grain: one row per (entity, period)

The grain is the *single most important decision*. For a
periodic snapshot, the grain is a pair:

- The **entity** — customer, product, account, server,
  warehouse.
- The **period** — month, week, day, hour, quarter.

The combination. One row per (customer, month). One row
per (server, hour). One row per (product, week).

### How to pick the period

The period is driven by the *question*, not the data:

- "MRR at end of month" → monthly.
- "Inventory at end of day" → daily.
- "Follower count at end of week" → weekly.
- "DAU" → daily (or even hourly if the question is about
  intra-day).

The finer the period, the more rows. Pick the coarsest
period that still answers the question. Daily for MRR
would be 30× the rows of monthly, and the analyst
typically doesn't care.

### The "one period" rule

A common trap: a periodic snapshot that has *multiple*
periods in one row. E.g., a `fact_customer_quarterly`
with `q1_mrr`, `q2_mrr`, `q3_mrr`, `q4_mrr`. The row is
ambiguous (is it a Q1, Q2, Q3, or Q4 row?), and the
grain is broken.

The right move: one row per (customer, quarter) with
`mrr` as the measure. The analyst aggregates to
quarterly-by-quarter-by-quarter at query time if needed.

---

## The measures

The measures in a periodic snapshot are *state values*
at the end of the period. They are typically
*semi-additive* — you can sum them across entities, but
not across time.

| Measure | Type | Notes |
|---|---|---|
| `mrr` | semi-additive | sum across customers = total MRR; sum across time = meaningless |
| `is_active` | flag | 0/1 — was the customer active at end of period? |
| `is_new` | flag | 0/1 — was this the customer's first period? |
| `is_churned` | flag | 0/1 — did the customer churn this period? |
| `inventory_units` | semi-additive | sum across products = total inventory; sum across time = meaningless |

The flags are useful: they let the analyst answer
"how many *new* customers this month?" without a join to
the subscription event log.

---

## The dimensions

A periodic snapshot has the *same* dimensions as the
underlying event log:

- `dim_customer` (SCD 2 — we want the customer's
  attributes *at end of period*, not current).
- `dim_plan` (SCD 2).
- `dim_date` (conformed).

The date dim here is *role-playing* in a specific way:
it represents the *period*, not an event. A `dim_month`
or `dim_date` filtered to month-ends is the right shape.

---

## The example: `fact_subscriptions_monthly` (recap from Lesson 09)

```sql
CREATE TABLE fact_subscriptions_monthly (
    snapshot_key     INTEGER PRIMARY KEY,
    customer_key     INTEGER NOT NULL,
    plan_key         INTEGER NOT NULL,
    period_date_key  INTEGER NOT NULL,
    mrr              REAL    NOT NULL DEFAULT 0,
    is_active        INTEGER NOT NULL DEFAULT 0,
    is_new           INTEGER NOT NULL DEFAULT 0,
    is_churned       INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (customer_key)    REFERENCES dim_customers(customer_key),
    FOREIGN KEY (plan_key)        REFERENCES dim_plans(plan_key),
    FOREIGN KEY (period_date_key) REFERENCES dim_date(date_key)
);
```

Three dimensions, four measures, all at the
customer-month grain. The `period_date_key` points to
the end-of-month date.

Sample data (from the module's `fact_tables.py`):

| snapshot_key | customer | plan | period | mrr | is_active | is_new | is_churned |
|---|---|---|---|---|---|---|---|
| 1 | Alice | pro | 2024-01-31 | 50.0 | 1 | 0 | 0 |
| 2 | Alice | pro | 2024-02-29 | 50.0 | 1 | 0 | 0 |
| 3 | Alice | free | 2024-03-31 | 0.0 | 0 | 0 | 1 |
| 4 | Bob | free | 2024-01-31 | 0.0 | 1 | 1 | 0 |
| 5 | Bob | pro | 2024-02-29 | 50.0 | 1 | 0 | 0 |
| 6 | Bob | pro | 2024-03-31 | 50.0 | 1 | 0 | 0 |
| 7 | Carol | pro | 2024-03-31 | 50.0 | 1 | 1 | 0 |

Notice the flags: Alice is `is_churned = 1` in March; Bob
is `is_new = 1` in January; Carol is `is_new = 1` in
March. These flags make the snapshot self-describing.

---

## When to use

A periodic snapshot is the right choice when:

- The question is *state at end of period* ("MRR at end
  of month").
- The state is *slowly changing* relative to the period
  (a customer's MRR doesn't change 100×/day).
- The analyst needs *period-over-period comparison*
  ("how did March compare to February?").

Subscription metrics, inventory levels, account balances,
follower counts, employee headcount, warehouse stock —
all periodic snapshot.

## When *not* to use

A periodic snapshot is the *wrong* choice when:

- The events are *atomic and high-volume* (use a
  transactional fact — Lesson 24).
- The entity has a *lifecycle with milestones* (use an
  accumulating snapshot — Lesson 26).
- The state is *the same every period* (you don't need
  history; use a flat dim).

---

## The "rebuild" workflow

A periodic snapshot is typically rebuilt at the end of
each period. The flow:

1. At end of month, the loader iterates over all
   currently-active customers.
2. For each, it computes the state at end of month
   (current MRR, plan, is_churned flag).
3. It inserts a new row in the snapshot for that
   (customer, month).
4. Old rows stay. The snapshot grows by one row per
   active customer per period.

The snapshot's row count grows linearly with the number
of entities × the number of periods. For 100k active
customers × 36 months = 3.6M rows. Manageable.

The "rebuild" cost is the price of periodic snapshots.
It's higher than a transactional fact (which just
appends). The trade-off: the snapshot is fast to query
(`WHERE period_date_key = X` is a single-partition scan).

---

## Tradeoffs to call out

1. **Why periodic snapshot, not transactional?** "We need
   state at end of month. A transactional fact
   (subscription events) would require a complex
   aggregation to reconstruct the state. The snapshot
   makes the state a single row."
2. **Why monthly, not weekly?** "MRR doesn't change
   weekly in our business. Monthly captures the
   meaningful transitions (new, upgrade, churn) without
   the noise of intra-month changes."
3. **Why include `is_churned` and `is_new` flags?**
   "Without them, the analyst has to join to the
   subscription event log to figure out if a customer
   is new or churned. The flags make the snapshot
   self-describing."
4. **Why SCD 2 on `dim_customer`?** "We need the
   customer's *historical* plan and segment at the end
   of the period, not the current value. SCD 2 + the
   temporal join from Lesson 21."

---

## Try it

Open
[`code/fact_tables.py`](../code/fact_tables.py) and read
`build_periodic_snapshot_fact`. Then:

1. State the grain: "one row per (customer, month)."
2. Identify the semi-additive measure (`mrr`).
3. Run the test and verify that `is_churned` corresponds
   to `mrr = 0`.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
