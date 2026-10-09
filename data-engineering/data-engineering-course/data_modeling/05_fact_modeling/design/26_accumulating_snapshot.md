# Lesson 26 — Accumulating Snapshot Fact Tables

> **What you'll learn:** the right fact-table type for
> processes with milestones (an order that progresses
> from ordered to paid to shipped to delivered). By the
> end of this lesson you'll be able to draw an
> accumulating snapshot, pick the milestones, and defend
> the choice.

---

## What an accumulating snapshot is

An accumulating snapshot fact table has one row per
*lifecycle* of an entity. The lifecycle is a known
sequence of milestones; as the entity progresses, the
row is *updated* to set the milestone dates.

The defining properties:

- **One row per entity, updated as it progresses.**
- **Milestone dates as columns.** Each milestone has a
  date (or NULL if it hasn't happened yet).
- **Lag measures.** Days between milestones (e.g.,
  `days_to_pay`, `days_to_ship`).

The classic example is an order: ordered → paid → shipped
→ delivered. The row is inserted at order time (with
`order_date_key` set), and updated as the order moves
through the pipeline.

---

## The grain: one row per lifecycle

The grain is *one row per entity, throughout its
lifetime*. The entity has a defined start, a known set
of milestones, and a defined end.

Examples:

- An **order**: ordered → paid → shipped → delivered
  (or cancelled).
- A **job application**: applied → screened → interviewed
  → offered → hired (or rejected).
- A **patient visit**: arrived → triaged → treated →
  discharged.
- A **loan application**: submitted → reviewed → approved
  → funded (or rejected).
- A **support ticket**: opened → assigned → responded →
  resolved (Lesson 19 had a similar pattern, but
  modeled as event-grain).

The lifecycle must be **known and finite**. If the
milestones are unpredictable, an event-grain fact is
the right call (Lesson 19's support ticket pattern).

---

## The columns: a date per milestone

Each milestone gets a column. The column is a FK to
`dim_date` (since `dim_date` is conformed, it can be
reused for every milestone).

For an order:

```sql
CREATE TABLE fact_order_accumulating_snapshot (
    order_key         INTEGER PRIMARY KEY,
    order_id          INTEGER NOT NULL,
    customer_key      INTEGER NOT NULL,
    order_date_key    INTEGER NOT NULL,
    paid_date_key     INTEGER,
    ship_date_key     INTEGER,
    delivery_date_key INTEGER,
    days_to_pay       INTEGER,
    days_to_ship      INTEGER,
    days_to_deliver   INTEGER,
    total_amount      REAL NOT NULL,
    ...
);
```

The `*_date_key` columns are role-playing FKs to
`dim_date`. They're NULL until the milestone happens.

### The "lag" measures

The `days_to_pay`, `days_to_ship`, `days_to_deliver`
columns are *lag measures* — the time between
milestones. They're computed at load time and stored on
the fact. Why store them? Because the analyst will
filter and group by them constantly, and computing them
on every query is wasteful.

The convention varies:
- **Days from order** (e.g., `days_to_pay` is the time
  from `order_date` to `paid_date`).
- **Days from previous milestone** (e.g., `days_to_pay`
  is the time from `order_date` to `paid_date`, but
  `days_to_ship` is from `paid_date` to `ship_date`).

The second convention is more common — it answers
"how long did this step take?" rather than "how long
has it been since the order?"

---

## Update semantics: append, then mutate

The accumulating snapshot is the *one* fact type that
gets updated. New rows are inserted at lifecycle start
(order placed). Existing rows are updated as the
lifecycle progresses (paid, shipped, delivered).

The two implications:

1. **Late updates.** A row that was "shipped" yesterday
   might be "delivered" today. The `delivery_date_key`
   gets set, the row is updated. The fact table has
   no audit trail of the change — if you need that,
   pair the snapshot with a transactional event log.
2. **Replay risk.** If the loader re-runs, it might
   *overwrite* a milestone date with a different value.
   The fix: use upsert semantics (`MERGE` or
   `INSERT ... ON CONFLICT UPDATE`) and only update
   dates that are later than the stored value.

In a real warehouse, accumulating snapshots are often
backed by an event log: the snapshot is a *projection*
of the event log onto one row per entity. The event log
is the source of truth; the snapshot is the
query-optimized view.

---

## The "unknown milestones" problem

A row that hasn't reached a milestone yet has NULL in
that column. The "delivered" column is NULL until the
order is actually delivered.

This is fine — NULL means "not yet." But it raises a
subtle issue: how do you count *active* orders? You
filter `WHERE delivery_date_key IS NULL`. This is a
hot path; index it.

For the analyst, the trick is *cohorts*: how many
orders placed in March are still in transit 30 days
later? The query:

```sql
SELECT
    COUNT(*) AS still_in_transit
FROM fact_order_accumulating_snapshot
WHERE order_date_key BETWEEN 20240301 AND 20240331
  AND delivery_date_key IS NULL;
```

---

## When to use

An accumulating snapshot is the right choice when:

- The entity has a *known, finite lifecycle* with
  distinct milestones.
- The questions are about *how long* the entity
  spends in each stage.
- The milestones are *predictable* — you know in
  advance what the columns are.

Order fulfillment, loan processing, hiring pipeline,
patient flow, claim processing, manufacturing
pipeline — all accumulating snapshot.

## When *not* to use

- The lifecycle is *unpredictable* (any event can
  happen in any order) — use event-grain
  transactional (Lesson 19's support ticket
  pattern).
- The question is *just* "what happened?" — use
  transactional (Lesson 24).
- The question is *state at end of period* — use
  periodic snapshot (Lesson 25).

---

## Tradeoffs to call out

1. **Why accumulating snapshot, not transactional?**
   "The lifecycle is known and finite. The accumulating
   snapshot makes the *duration in each stage* a
   first-class measure, which is the whole point of the
   question."
2. **Why are `days_to_pay`, etc. computed at load
   time?** "The analyst filters and groups by these
   lags constantly. Computing them on every query is
   wasteful."
3. **Why are the milestone dates nullable?** "An order
   that's still in transit has no `delivery_date`. NULL
   means 'not yet' — it's the right semantic."
4. **How do you handle late updates?** "The loader
   uses upsert semantics. A late 'delivered' event
   updates the row only if the new date is later than
   the stored date."

---

## The example: `fact_order_accumulating_snapshot`

The schema in `code/fact_tables.py`:

```sql
CREATE TABLE fact_order_accumulating_snapshot (
    order_key         INTEGER PRIMARY KEY,
    order_id          INTEGER NOT NULL,
    customer_key      INTEGER NOT NULL,
    order_date_key    INTEGER NOT NULL,
    paid_date_key     INTEGER,
    ship_date_key     INTEGER,
    delivery_date_key INTEGER,
    days_to_pay       INTEGER,
    days_to_ship      INTEGER,
    days_to_deliver   INTEGER,
    total_amount      REAL NOT NULL
);
```

Sample data (3 orders at different stages):

| order_id | order_date | paid_date | ship_date | delivery_date | days_to_pay | days_to_ship | days_to_deliver |
|---|---|---|---|---|---|---|---|
| 1001 | Jan 1 | Jan 2 | Jan 3 | Jan 5 | 1 | 1 | 2 |
| 1002 | Jan 3 | Jan 5 | Jan 8 | Jan 10 | 2 | 3 | 2 |
| 1003 | Jan 5 | Jan 8 | Jan 10 | NULL | 3 | 2 | NULL |

Order 1003 is still in transit (no `delivery_date`).
The lag columns are computed relative to the previous
milestone.

---

## Sample queries

### Average time to deliver

```sql
SELECT
    AVG(days_to_pay) AS avg_days_to_pay,
    AVG(days_to_ship) AS avg_days_to_ship,
    AVG(days_to_deliver) AS avg_days_to_deliver
FROM fact_order_accumulating_snapshot
WHERE delivery_date_key IS NOT NULL;
```

### Orders still in transit, by cohort

```sql
SELECT
    d.month,
    d.year,
    COUNT(*) AS in_transit_count
FROM fact_order_accumulating_snapshot f
JOIN dim_date d ON f.order_date_key = d.date_key
WHERE f.delivery_date_key IS NULL
GROUP BY d.year, d.month
ORDER BY d.year, d.month;
```

---

## Try it

Open
[`code/fact_tables.py`](../code/fact_tables.py) and read
`build_accumulating_snapshot_fact`. Then:

1. State the grain: "one row per order, throughout its
   lifetime."
2. Identify the milestone dates (order, paid, ship,
   delivery) and the lag measures.
3. Find the row that's still in transit (no
   `delivery_date_key`).
4. Run the test:

```bash
python3 -m unittest data_modeling/05_fact_modeling/tests/test_facts.py
```

The test verifies that the lag measures are correct
and the still-in-transit row has a NULL delivery.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
