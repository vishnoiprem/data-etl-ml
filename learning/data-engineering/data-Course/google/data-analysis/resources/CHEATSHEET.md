# Semantic Layer & BI Cheat Sheet

> One page per topic. Keep it open in a tab.

---

## The layer in one picture

```text
   analytics.orders          analytics.customers
   one row per order LINE   one row per customer
        │                          │
        │  many_to_one             │  one_to_many
        └──────────────────────────┘
                    │
              MODEL = grain + keys
                    │
        ┌───────────┴───────────┐
        │                       │
   MEASURES                 DIMENSIONS
   "what number"           "what grouping"
   SUM / COUNT /            string / number
   COUNT_DISTINCT /         time (with timeframes)
   AVG / RATIO
        │
        ▼
    EXPLORE = base model + joins (with fan-out warnings)
```

---

## The grain — the one sentence

```text
analytics.orders      one row per order LINE
analytics.customers   one row per customer
analytics.products    one row per product
analytics.date_spine  one row per CALENDAR DAY
```

**Record it in three places:** the DDL comment, the model description, and
the test. The test is the one that matters.

---

## Additivity — the three kinds of measure

| Kind | Aggregation | Rolls up? | Example |
|---|---|---|---|
| **Additive** | `sum`, `count` | yes | total revenue |
| **Non-additive** | `count_distinct`, `avg` | no | distinct orders |
| **Ratio** | `sum(n) / sum(d)` | no | margin rate |

```text
ADDITIVE       sum of parts = whole
NON-ADDITIVE   sum of parts ≠ whole  (distinct counts double-count)
RATIO          never sum a ratio; recompute it at the new grain
```

---

## The ratio problem

```text
CORRECT      SUM(numerator) / SUM(denominator)
WRONG        AVG(numerator / denominator)      ← always biased LOW
```

Looker Studio calculated fields run **after** aggregation:

```
margin_rate = SUM(margin_amount) / NULLIF(SUM(total_amount), 0)
```

> The `NULLIF` matters: a zero denominator becomes `NULL`, which charts
> render as a gap, rather than a divide-by-zero.

---

## Join cardinality

| Cardinality | Reads | Fan-out? | Safe to traverse? |
|---|---|---|---|
| `one_to_one` | one ↔ one | no | yes |
| `many_to_one` | many ↔ one | no | yes |
| `one_to_many` | one ↔ many | **yes** | no |
| `many_to_many` | many ↔ many | **yes** | no |

> **Fan-out happens when you traverse from the "one" side to the "many"
> side.** `orders → customers` is safe. `customers → orders` is not.

---

## The two wrong numbers

### Fan-out — the rows multiply

```sql
-- The check: compare the measure with and without the join
SELECT
  (SELECT SUM(total_amount) FROM analytics.orders) AS alone,
  (SELECT SUM(o.total_amount)
     FROM analytics.orders o
     JOIN analytics.customers c ON o.customer_id = c.customer_id) AS after_join;
```

### Grain mismatch — the measure is counted at the wrong level

```sql
-- WRONG: a customer-level measure over a line-level join
SELECT SUM(c.lifetime_value)
FROM customers c JOIN orders o ON c.customer_id = o.customer_id;

-- RIGHT: aggregate at the order grain FIRST
SELECT SUM(total_amount) FROM (
  SELECT order_id, SUM(total_amount) AS total_amount
  FROM order_lines GROUP BY order_id
) t;
```

> **Never aggregate a measure at a grain coarser than the grain you are
> joining at.**

---

## The date spine

```sql
WITH spine AS (SELECT date FROM analytics.date_spine),
daily AS (
  SELECT DATE(created_at) AS date,
         COUNT(*)          AS order_lines,
         SUM(total_amount) AS revenue
  FROM analytics.orders GROUP BY 1
)
SELECT s.date,
       COALESCE(d.order_lines, 0) AS order_lines,
       COALESCE(d.revenue, 0)     AS revenue
FROM spine s
LEFT JOIN daily d ON d.date = s.date;
```

Two things that are easy to get wrong:

- **`LEFT JOIN`**, not `INNER JOIN` — an inner join throws away the rows the
  spine exists for.
- **`COALESCE`** the measures — without it the gap is `NULL` and the chart
  shows a gap.

---

## Timeframes

| Timeframe | Truncates to |
|---|---|
| `raw` | the value as-is |
| `day` | the day |
| `week` | the **Monday** (ISO) |
| `month` | the 1st |
| `quarter` | Jan / Apr / Jul / Oct |
| `year` | 1 January |

> **ISO weeks start on Monday.** Decide the convention, write it down.

---

## Date filters

```python
# CORRECT order: parse → validate → truncate
raw_start = parse_date(start)
raw_end   = parse_date(end)
if raw_end < raw_start:
    raise ValueError("inverted range")     # raise, never swap
start = truncate_date(raw_start, timeframe)
end   = truncate_date(raw_end,   timeframe)
```

> Truncating first can mask an inverted range: 31 March and 1 March both
> truncate to 1 March.

---

## The validation gate

```text
ERROR    makes the number wrong or not current   → fails the build
WARNING  worth a look                            → does not fail
INFO     passed                                  → recorded
```

```text
grain.not_unique       primary key is not unique — every measure is inflated
referential.unresolved foreign key has no match — blank label, right total
completeness.missing    required field is empty
freshness.stale        newest row is older than the limit
value.negative         negative revenue — refund, or a sign-flip bug
```

> **Never fail a build on a check that has fired before without a human
> deciding what to do.** A gate that fires on good data gets switched off
> within a week.

---

## Reconciliation

```sql
-- NULL-safe value comparison
WHERE source_value IS DISTINCT FROM dashboard_value
```

> `NULL <> NULL` is `NULL`, not `TRUE` — a `<>` comparison silently drops
> exactly the rows where the problems hide.

Three outcomes: **MISSING**, **EXTRA**, **VALUE_MISMATCH**.

---

## LookML

```lookml
view: orders {
  sql: SELECT * FROM ${analytics.orders} ;;

  measure: total_revenue {
    type: sum
    sql: ${total_amount} ;;
    description: "Sum of order line revenue."
  }

  dimension: created_at {
    type: time
    sql: ${created_at} ;;
    timeframe: [raw, day, week, month, quarter, year]
  }

  join: customers {
    relationship: many_to_one
    sql_on: ${orders.customer_id} = ${customers.customer_id} ;;
    description: "One customer per order line. Safe to traverse."
  }
}

explore: orders {
  base: orders
  join: customers {
    relationship: many_to_one
    sql_on: ${orders.customer_id} = ${customers.customer_id} ;;
  }
}
```

> `type:` on a measure is what tells the tool how to aggregate. Getting it
> wrong doubles the number.
>
> `relationship:` on a join is what stops the join fanning out.

---

## The CLI

```bash
python project/local_bi.py describe
python project/local_bi.py explores
python project/local_bi.py query --input ./sample_data/orders.csv \
    --dimensions region --measures total_revenue,distinct_orders
python project/local_bi.py validate --input ./sample_data/orders.csv
python project/local_bi.py spine --input ./sample_data/orders.csv --timeframe day
python project/local_bi.py lookml --with-explores
```

---

## The numbers in this course

| Figure | Value |
|---|---:|
| Order lines | 901 |
| Distinct orders | 450 |
| Distinct customers | 121 |
| Lines per order | 2.00 |
| Total revenue | £1,128,941.37 |
| Average order value | £2,508.76 |
| Revenue after duplicating the fact | £2,257,882.74 |
| Regional `distinct_orders` sum | 799 (vs 450 — 77.6% inflated) |
| Correct gross margin | 0.5125 |
| Average-of-ratios margin | 0.4816 (3.1 points low) |
| Days with no orders | 9 of 177 |
| Newest row in the sample data | 126 days old |

---

## The one-sentence version

> **Know the grain, state it in three places, make the measures say what
> they exclude, and check that the numbers are still true every day.**
