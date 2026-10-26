# 18 — Slowly Changing Dimensions

> **Lesson 18 of 30 — Transformation**

Dimensions change. A user moves countries, an account upgrades
from free to pro, a product is recategorized. The warehouse has
to keep history *somehow* — and the choice is SCD1, SCD2, or
SCD3. This lesson is the *when to use which* decision.

---

## 1. The three types

**SCD1 (Type 1): overwrite.** The destination reflects the
*current* state only. No history.

```
Source timeline:        Destination (SCD1):
  US ───── UK              UK  (no history of US)
```

**SCD2 (Type 2): add a row.** The destination has one row per
*version* of the dimension. Full history.

```
Source timeline:        Destination (SCD2):
  US ───── UK              US  (valid 2022-01-01 to 2023-06-15)
                          UK  (valid 2023-06-15 to 9999-12-31)
```

**SCD3 (Type 3): add a column.** The destination has the current
value plus a fixed number of previous values.

```
Source timeline:        Destination (SCD3):
  US ───── UK              current=UK, previous=US
```

The senior move: know the three types, and know which one fits
which use case.

---

## 2. When to use SCD1

SCD1 is the right choice when:
- The history doesn't matter (e.g. typos in `email`).
- The dimension is *current-state only* (e.g. today's weather).
- Storage is at a premium.

The senior framing: "For dimensions where the past isn't
predictive of the future, SCD1 is fine. Email corrections,
name changes, address updates — overwrite."

The implementation:

```sql
-- The SCD1 pattern
UPDATE users
SET country = 'UK'
WHERE user_id = 12345;
```

---

## 3. When to use SCD2

SCD2 is the right choice when:
- The history matters (e.g. for ML feature engineering).
- You need point-in-time analysis ("what country was the user
  in when they placed this order?").
- The dimension changes occasionally and you want to track each
  change.

The senior framing: "For dimensions that drive point-in-time
analysis — user country, account tier, product category — SCD2
is the right call. ML models in particular need SCD2 to avoid
target leakage."

The implementation (Snowflake-style):

```sql
-- The SCD2 close-the-previous-row pattern
UPDATE dim_users_scd2 target
SET valid_to = source.valid_from
FROM (
  SELECT user_id, country, valid_from
  FROM dim_users_scd2_staging
  WHERE is_current = FALSE
) source
WHERE target.user_id = source.user_id
  AND target.is_current = TRUE
  AND target.valid_to = '9999-12-31';

-- Then insert the new row
INSERT INTO dim_users_scd2
SELECT user_id, country, valid_from, '9999-12-31', TRUE
FROM dim_users_scd2_staging
WHERE is_current = TRUE;
```

The senior move: the two-step pattern (close the previous row,
insert the new row) is *idempotent* if you do it in a single
transaction.

---

## 4. The SCD2 schema

The standard columns:

| Column | Meaning |
|---|---|
| `user_id` | Natural key (the dimension's primary key in the source) |
| `country` | The dimension attribute |
| `valid_from` | When this version became effective (timestamp) |
| `valid_to` | When this version was superseded (timestamp; `9999-12-31` for current) |
| `is_current` | Boolean: is this the latest version? |
| `surrogate_key` | Optional: a generated key for the row (often `hash(user_id, valid_from)`) |

The `is_current` flag is denormalization for query speed: the
common query "current state of user X" is a `WHERE is_current =
TRUE` instead of a `WHERE valid_to = '9999-12-31'`.

---

## 5. The point-in-time join

The SCD2 payoff is the point-in-time join:

```sql
-- The point-in-time pattern
SELECT
  o.order_id,
  o.order_date,
  u.country AS user_country_at_order
FROM orders o
LEFT JOIN dim_users_scd2 u
  ON o.user_id = u.user_id
  AND o.order_date >= u.valid_from
  AND o.order_date < u.valid_to;
```

For each order, this returns the user's country *at the time
they placed the order*. This is the canonical "no target
leakage" pattern for ML feature engineering.

The senior move: this pattern is the reason SCD2 exists. If you
can't describe it, you don't understand SCD2.

---

## 6. When to use SCD3

SCD3 is rare. Use it when:
- You only need to compare *current* to *immediately previous*
  (e.g. "did the user's country change since last month?").
- Storage is constrained and SCD2 is too expensive.
- The dimension changes very rarely.

The senior move: SCD3 is a niche. If you find yourself reaching
for it, you probably want SCD2 instead.

---

## 7. The dbt snapshot pattern

dbt has a built-in `snapshot` concept that implements SCD2:

```yaml
# dbt_project.yml
snapshots:
  - name: users_snapshot
    target_schema: snapshots
    strategy: timestamp
    unique_key: user_id
    updated_at: updated_at
```

```sql
-- snapshots/users_snapshot.sql
SELECT user_id, country, updated_at FROM {{ source('raw', 'users') }}
```

dbt runs the snapshot, diffs against the existing snapshot, and
emits the SCD2 close/insert pattern automatically. The senior
move: if you're using dbt, use `snapshots` for SCD2; don't
write the SQL by hand.

---

## 8. The interview answer

> "For dimensions that drive point-in-time analysis — user
> country, account tier, product category — I use SCD2. The
> destination has a row per version with `valid_from` /
> `valid_to` and an `is_current` flag. The point-in-time join
> returns the dimension value as of the event timestamp, which
> is essential for ML feature engineering to avoid target
> leakage. For dimensions where the past isn't predictive
> (email corrections, name changes) SCD1 is fine. SCD3 is
> niche. If I'm using dbt, I use the `snapshot` block to manage
> SCD2."

That single paragraph covers: when to use SCD2, the schema, the
point-in-time join, when to use SCD1, and the dbt pattern.
Senior answer in 30 seconds.

---

## Try it

Look at the most recent dimension table you've worked on. Is it
SCD1, SCD2, or SCD3? Does it have `valid_from` / `valid_to`?
Can you do a point-in-time join against it? If any answer is
"no," the dimension is either too simple for SCD2 or is
missing the history the business needs.
