# Slowly Changing Dimensions (SCDs)

## Why this lesson

This is the most-asked dimension topic in the data modeling interview. A dim is *slowly changing* if its attributes change over time but the changes are rare compared to the fact events: a user changes country every 3 years, a product gets re-categorized every quarter, a city's rate card changes every year. The schema has to *decide* what to do with each change — overwrite, expire-and-insert, or add a previous column. Each decision has a query implication. Without an SCD strategy, your historical facts will silently re-attribute to current values, and your cohort analysis will be wrong. This lesson is the deep dive on SCD Type 1, 2, and 3 — the three types that cover 99% of interview scenarios.

---

## What "slowly changing" means

A dimension is *slowly changing* if its attributes can change
over time, but the changes are rare compared to the fact
events. A user changes country once every 3 years; a product
gets re-categorized once a quarter; a city's rate card
changes once a year. The changes are infrequent enough that
we don't need to capture them in the fact table — but we
*do* need to handle them in the dim.

The Kimball taxonomy gives us three SCD types, named for the
historical depth they preserve. There's also a Type 4
(history table) and a Type 6 (hybrid), but the three covered
here are 99% of what you'll see in interviews.

---

## SCD Type 1 — overwrite (no history)

The simplest. When an attribute changes, *overwrite* the old
value with the new one. No history is kept.

```sql
-- Before: Alice is in US.
-- User changes country to UK.
UPDATE dim_customers
SET country = 'UK'
WHERE customer_id = 100;
-- After: Alice is in UK. The old value (US) is gone forever.
```

### When to use

- The change is non-historical (a typo in a display name).
- The analytics team only cares about the *current* value
  (e.g., a free-text comment that was edited).
- The change is a correction, not a meaningful event (e.g.,
  a data-entry error).

### Why it's right

Type 1 is *simple*. One row per natural key, no
effective/expiry dates, no temporal joins. The dim is a
flat lookup table.

### Why it's wrong

Type 1 *loses history*. If the analyst asks "what was
Alice's country when she placed this order in March?", you
can't answer — Alice is in UK now, and the March order
would join to the UK row. The historical fact is wrong.

---

## SCD Type 2 — add a new row, expire the old (full history)

The most common. When an attribute changes, *expire* the old
row (set `is_current = 0`, set `expiry_date`) and *insert* a
new row with the new value (set `is_current = 1`, set
`effective_date`).

```sql
-- Before:
-- id=1, customer_id=100, country=US, effective=2024-01-01,
-- expiry=9999-12-31, is_current=1
-- User changes country to UK on 2024-06-15.
-- Step 1: expire the old row.
UPDATE dim_customers
SET expiry_date = '2024-06-14', is_current = 0
WHERE customer_id = 100 AND is_current = 1;
-- Step 2: insert the new row.
INSERT INTO dim_customers
VALUES (2, 100, 'UK', '2024-06-15', '9999-12-31', 1);
-- After: two rows for customer_id=100, the old one expired,
-- the new one current.
```

The Python in
[`code/scd.py`](../code/scd.py) (`scd2_insert`) does this in
one call.

### When to use

- The change is *meaningful* and the analytics team needs
  historical attribution.
- The change is *rare enough* that doubling the row count
  of the dim is acceptable.
- The "current" view of the dim is still a hot path
  (`WHERE is_current = 1`).

### The schema

Every Type 2 dim has these extra columns:

| Column | Purpose |
|---|---|
| `effective_date` | When this version became active. |
| `expiry_date` | When this version was superseded. `'9999-12-31'` for current. |
| `is_current` | 1 for the current row, 0 for expired. |

Plus a *surrogate key* (`customer_key`) that's distinct from
the natural key (`customer_id`). The natural key has many
rows; the surrogate key has one row each.

### The temporal join

The reason SCD 2 is the right choice is the *temporal join*.
Given a fact row with `date_key = 20240615`, the analyst can
find the customer's *historical* country at that date:

```sql
SELECT f.order_id, c.country
FROM fact_orders f
JOIN dim_customers c
  ON f.customer_key = c.customer_key
WHERE f.date_key = 20240615
  AND c.effective_date <= '2024-06-15'
  AND c.expiry_date   >  '2024-06-15';
```

This is the most-asked interview question on SCD: "how do
you get the right version of the customer at the right
time?" The answer is the temporal join.

The modern equivalent uses a date-dim join:

```sql
JOIN dim_customers c
  ON f.customer_key = c.customer_key
JOIN dim_date d
  ON d.date = '2024-06-15'
WHERE d.date >= c.effective_date
  AND d.date <  c.expiry_date;
```

---

## SCD Type 3 — add a "previous" column (one level of history)

The middle ground. When an attribute changes, store the *new*
value in the original column and the *old* value in a new
"previous" column.

```sql
-- Before: Alice in US, no previous_country.
-- User changes country to UK.
ALTER TABLE dim_customers ADD COLUMN previous_country TEXT;
UPDATE dim_customers
SET previous_country = country,  -- 'US'
    country = 'UK'
WHERE customer_id = 100;
-- After: country = 'UK', previous_country = 'US'.
```

The Python in
[`code/scd.py`](../code/scd.py) (`scd3_add_column`) does this
in one call.

### When to use

- The change is *very rare* and you only need one level of
  history ("was she on the free plan before she upgraded?").
- The cost of SCD 2 (extra rows, complex joins) is not
  justified.
- The analysis is *simple* (yes/no was the customer on the
  previous plan).

### Why it's limited

Type 3 only keeps *one* level of history. If a customer
upgrades from free → pro → enterprise, the third change
overwrites "pro" with "enterprise" in the new column, and
the original "free" is lost. The chain is not preserved.

For 95% of interview scenarios, you want Type 2, not Type 3.
Type 3 is a niche tool for a specific question.

---

## The decision rule

When the interviewer asks "what SCD type for `dim_X`?":

```
                  ┌─────────────────────────────────┐
                  │ Does the analytics team need    │
                  │ the historical value at a       │
                  │ specific point in time?         │
                  └────────────┬────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │ Yes                         │ No
                ▼                             ▼
   ┌──────────────────────┐      ┌──────────────────────┐
   │ Type 2               │      │ Is the change a      │
   │ (effective_date,     │      │ correction (typo,    │
   │  expiry_date,        │      │ data-entry error)?   │
   │  is_current)         │      └──────────┬───────────┘
   └──────────────────────┘                 │
                                  ┌─────────┴──────┐
                                  │ Yes            │ No
                                  ▼                ▼
                          ┌──────────┐   ┌─────────────┐
                          │ Type 1   │   │ Type 2 (still)│
                          │ overwrite│   │ but call out │
                          └──────────┘   │ the trade-off│
                                         └─────────────┘
```

In practice, the answer is **Type 2** about 80% of the time.
Type 1 is for typos and corrections. Type 3 is rare.

The interview rule: default to Type 2, then call out the
tradeoff. The candidate who says "Type 2 because the
attribute changes and we need historical attribution" is
4/4. The candidate who says "Type 1" without justification
is 1/4.

---

## Worked example — user plan changes

A SaaS user moves from free → pro → enterprise over 3 years.

| date | plan | SCD 1 | SCD 2 (effective/expiry) | SCD 3 |
|---|---|---|---|---|
| 2022-01-01 | free | free, 2022 | (free, 2022-01-01, 2023-06-30, expired) | (free, null) |
| 2023-07-01 | pro | pro, 2023 | (pro, 2023-07-01, 2024-12-31, expired) | (pro, free) |
| 2025-01-01 | enterprise | enterprise, 2025 | (enterprise, 2025-01-01, 9999-12-31, current) | (enterprise, pro) |

- **SCD 1** lost the history. We can't answer "what plan
  was this user on in 2023?"
- **SCD 2** kept all three versions. The temporal join
  returns the right plan for any date.
- **SCD 3** kept the most-recent change. We can answer
  "did this user upgrade?" but not "what plan was she on
  in 2023?"

The interview call: "Type 2 — the plan changes are
meaningful and the analytics team needs historical
attribution for accurate cohort analysis. The row-count
cost is small (one extra row per change) and the
effective/expiry dates are well-understood."

---

## How to draw SCD 2 on the whiteboard

A common whiteboard pattern:

```
dim_customers
┌────┬─────────────┬───────┬───────────────┬───────────────┬───────────┐
│key │customer_id  │country│effective_date │expiry_date    │is_current │
├────┼─────────────┼───────┼───────────────┼───────────────┼───────────┤
│ 1  │ 100         │ US    │ 2022-01-01    │ 2023-06-30    │ 0         │
│ 2  │ 100         │ UK    │ 2023-07-01    │ 9999-12-31    │ 1         │
│ 3  │ 101         │ DE    │ 2022-03-15    │ 9999-12-31    │ 1         │
└────┴─────────────┴───────┴───────────────┴───────────────┴───────────┘
```

Show the surrogate key (`key`) is distinct from the natural
key (`customer_id`). The same `customer_id = 100` has two
rows with different `key` values — one expired, one
current.

The fact table joins on the *surrogate* key (`f.customer_key
= c.key`), not the natural key. This is what makes the
temporal join work — the fact is bound to a *specific
version* of the customer, not to the customer in general.

---

## Try it

For each of the 5 star schemas in
[`code/star_schemas.py`](../../03_high_level_diagrams/code/star_schemas.py),
write down:

1. Which dimensions are SCD 1, SCD 2, or SCD 3.
2. Why, in one sentence.
3. What the temporal join would look like for the SCD 2
   dims.

If you can do this in 10 minutes, you understand the
SCD 2 pattern. Move to Lesson 21 (the foundational lesson
on dimension table design).

---

## In the interview, you would say...

> "Default to **SCD Type 2** for any dimension attribute that
> changes and that the analytics team needs to attribute
> historically — country, plan, category, status. Add
> `effective_date`, `expiry_date`, `is_current`, and a surrogate
> key. Use the temporal join
> (`effective_date <= event_date < expiry_date`) to reconstruct
> history. Type 1 only for typos and corrections; Type 3 almost
> never."

---

*Author: Prem Vishnoi <pvishnoi@avilx.com>*
