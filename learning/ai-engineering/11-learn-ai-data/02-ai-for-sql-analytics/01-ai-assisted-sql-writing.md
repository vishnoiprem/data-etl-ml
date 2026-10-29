# Lesson 1 — AI-Assisted SQL Writing

> **Type:** Article · Module 2 · AI for SQL & Analytics
> How to write production-grade SQL faster with AI as a copilot — and the verification rituals that make it safe.

---

## What this lesson covers

AI assistance for SQL is the **highest-ROI** daily activity for a DE. The gain is real (3–5× on complex queries, from Lesson 2). The failure modes are real too. This lesson gives you the working patterns: the prompt template, the verification checklist, and the specific silent bugs to watch for.

---

## The SQL-writing loop with AI

```
   ┌──────────────────────────────────────────────────────────┐
   │  THE 5-STEP SQL LOOP                                     │
   │                                                          │
   │   1. SPEC     what question, what grain, what timeframe  │
   │   2. DRAFT    AI produces first cut                      │
   │   3. READ     you read every line                        │
   │   4. VERIFY   row count + sample + EXPLAIN               │
   │   5. SHIP     commit + monitor for 24 hours              │
   └──────────────────────────────────────────────────────────┘
```

If you skip step 1, you re-do work. If you skip step 3 or 4, you ship the silent bug.

---

## The SQL prompt template (DE-flavored)

```text
ROLE: senior analytics engineer at {COMPANY}.
DIALECT: {Snowflake | BigQuery | Databricks SQL | Postgres}
SCHEMA: @schema.md (or paste the relevant CREATE TABLE)
CONVENTIONS:
  - lowercase keywords, 4-space indent, snake_case
  - explicit JOINs, no comma joins
  - CTEs over nested subqueries
  - always alias columns
  - date columns end in _at (UTC) or _date (DATE)
  - always handle NULL explicitly

TASK: {the business question, with grain and timeframe}

CONSTRAINTS:
  - no SELECT *
  - handle NULL {field} explicitly
  - respect {business rule}
  - return only the SQL + verification

FORMAT:
  1. SQL in a ```sql block
  2. 2-line explanation of choices
  3. 2 sample row-check queries

VERIFICATION:
  - expected row count: {N}
  - NULL check on {field}
  - {specific edge case for this query}
```

---

## The four silent SQL bugs to always check

### 1. Silent fan-out joins
**Symptom:** query returns 3× the rows you expect because of a 1-to-many join you didn't account for.

**Check:**
```sql
SELECT COUNT(*) FROM <result>;
-- compare to upstream fact row count, or to a known-good control query
```

**Fix:** switch INNER JOIN to LEFT JOIN, or aggregate before joining.

### 2. NULL exclusion in negation
**Symptom:** `WHERE region != 'APAC'` silently drops 8% of rows where region IS NULL.

**Check:**
```sql
SELECT region, COUNT(*) FROM orders GROUP BY region;
-- expect "NULL" to be its own row
```

**Fix:** `WHERE COALESCE(region, '') != 'APAC'` or `WHERE region IS DISTINCT FROM 'APAC'`.

### 3. Wrong window frame
**Symptom:** `LAST_VALUE()` returns the current row instead of the actual last value.

**Check:**
```sql
SELECT *, LAST_VALUE(x) OVER (PARTITION BY ... ORDER BY ...
       ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
FROM ...
```

**Fix:** always specify the frame explicitly.

### 4. Timezone drift
**Symptom:** report looks fine in dev (UTC), wrong in prod (IST). Off by one day at boundaries.

**Check:** print `CURRENT_TIMESTAMP()` and the user's expected timezone.

**Fix:** convert at the warehouse boundary, store in UTC, document the convention.

---

## Verification checklist (use before every commit)

- [ ] Row count matches the expected control
- [ ] 10-row sample by hand (read the actual values)
- [ ] EXPLAIN plan shows expected join order
- [ ] No full-table scans on large tables (unless intended)
- [ ] NULL handling explicit on every filter
- [ ] Date/timezone conversion is correct
- [ ] Window frame specified on every window function
- [ ] No `SELECT *`
- [ ] Cost estimate reasonable (Snowflake query profile, BigQuery dry-run)

---

## What AI is good at (the skeleton)

- CTE structure and naming
- Picking the right window function
- Choosing join order for readability
- Dialect-specific syntax (Snowflake vs BigQuery vs Postgres)
- Translating from one dialect to another
- First-draft coverage of edge cases when you explicitly name them

## What AI is bad at (the joints)

- Knowing your specific business rule for "active customer"
- Choosing grain when the spec is ambiguous
- SCD strategy
- Performance tuning on your actual data
- Joins that depend on undocumented org conventions

---

## Senior-level habit: the "explain the SQL back" prompt

After AI writes the SQL, ask it to **explain it back to you in plain English**. If the explanation doesn't match what you wanted, the SQL doesn't either.

```text
Explain the SQL above as if to a non-technical stakeholder.
Include:
- what each CTE does
- what each join's cardinality is (1:1, 1:many, many:many)
- what happens if column X is NULL
- what the final grain is (one row per ...)
```

If the AI's explanation is hand-wavy where the logic is subtle, the SQL is too. Push back.

---

## Worked Example — the cohort-retention query, all 4 silent bugs in one

> **Task:** *"Show me the top 3 products by revenue per category for users in the second-purchase cohort, last 90 days."*

### Step 1 — The first-draft query (AI)

```sql
WITH cohort AS (
  SELECT user_id, MIN(order_date) AS first_order_date
  FROM orders
  GROUP BY user_id
),
ranked AS (
  SELECT
    p.category,
    p.product_id,
    SUM(oi.revenue) AS revenue,
    ROW_NUMBER() OVER (
      PARTITION BY p.category
      ORDER BY SUM(oi.revenue) DESC
    ) AS rn
  FROM order_items oi
  JOIN orders o   ON o.order_id = oi.order_id
  JOIN products p ON p.product_id = oi.product_id
  JOIN cohort c   ON c.user_id = o.user_id
  WHERE o.order_date >= CURRENT_DATE - INTERVAL '90 days'
    AND o.order_date > c.first_order_date          -- "second purchase"
  GROUP BY p.category, p.product_id
)
SELECT category, product_id, revenue
FROM ranked
WHERE rn <= 3
ORDER BY category, rn;
```

### Step 2 — Read it line by line (5 minutes)

You scan it. Looks plausible. **Now check the 4 silent bugs.**

### Step 3 — Run the verification probes

```sql
-- Bug #1: silent fan-out?
-- Is order_items 1:1 with orders? No — an order has many items.
-- Did AI count an order's revenue N times if it had N items?
-- Probe:
SELECT 'orders_last_90d' AS what, COUNT(*) AS n FROM orders WHERE order_date >= CURRENT_DATE - 90
UNION ALL
SELECT 'order_items_last_90d', COUNT(*) FROM order_items oi JOIN orders o ON o.order_id = oi.order_id WHERE o.order_date >= CURRENT_DATE - 90;
-- If order_items >> orders, you have a fan-out if you SUM without careful grouping.

-- In our draft, we GROUP BY (category, product_id) and SUM revenue.
-- SUM(oi.revenue) per (category, product_id) is correct because we're
-- aggregating per item, not per order. OK. NO fan-out here.
-- BUT — many-to-many between products and orders (via order_items).
-- AI joined products to order_items. Cardinality: order_items 1:1 products.
-- No fan-out.

-- Bug #2: NULL exclusion
-- 'region' wasn't in this query. Skip.

-- Bug #3: window frame
-- ROW_NUMBER() with PARTITION BY + ORDER BY — no LAST_VALUE(). OK.

-- Bug #4: timezone drift
-- CURRENT_DATE assumes server timezone. If your server is UTC, "last 90 days"
-- is UTC. If it's EST, "last 90 days" is EST. The product owner said
-- "last 90 days" without saying which. AI picked server default.
-- FIX: explicit cast.
WHERE o.order_date >= DATE_TRUNC('day', CURRENT_TIMESTAMP() AT TIME ZONE 'UTC') - INTERVAL '90 days'
```

### Step 4 — Run on sample data + check row counts

```sql
-- Sample
SELECT * FROM (
  SELECT category, product_id, revenue, rn
  FROM ranked
  WHERE rn <= 3
)
ORDER BY category, rn;
-- Spot-check 5 rows. Compare to a hand-computed value for one user.

-- Row count sanity check
-- We expect ~3 rows per category that had orders in the window.
SELECT COUNT(DISTINCT category) AS cats_with_orders
FROM ranked;
-- Compare to "total active categories in 90 days" — should be ≤ this.
```

### Step 5 — Senior "explain it back" probe

You ask AI:

> "In this query, if a user has 5 orders and 30 order-items in the last 90 days, what is their contribution to `ranked.revenue`?"

The honest answer is: it depends on which items and which categories. `ranked.revenue` is per (category, product_id), summed across users, not per-user. So one user doesn't "contribute" a single value — they contribute rows to the aggregation.

If AI replies *"the user's revenue is the sum of all their items"*, that's the **per-user view**, not the **per-product view**. **The query is per-product, not per-user.** Push back on the answer and you'll see whether the AI actually understands the grain.

### Step 6 — The "right" version

```sql
WITH cohort AS (
  SELECT user_id, MIN(order_date) AS first_order_date
  FROM orders
  GROUP BY user_id
),
second_purchase_orders AS (
  SELECT o.*
  FROM orders o
  JOIN cohort c ON c.user_id = o.user_id
  WHERE o.order_date > c.first_order_date                       -- exclude the first
    AND o.order_date >= DATE_TRUNC('day', CURRENT_TIMESTAMP() AT TIME ZONE 'UTC') - INTERVAL '90 days'
),
scoped_items AS (
  SELECT oi.product_id, oi.revenue
  FROM order_items oi
  WHERE oi.order_id IN (SELECT order_id FROM second_purchase_orders)
),
ranked AS (
  SELECT
    p.category,
    si.product_id,
    SUM(si.revenue) AS revenue,
    ROW_NUMBER() OVER (
      PARTITION BY p.category
      ORDER BY SUM(si.revenue) DESC
    ) AS rn
  FROM scoped_items si
  JOIN products p ON p.product_id = si.product_id
  GROUP BY p.category, si.product_id
)
SELECT category, product_id, revenue
FROM ranked
WHERE rn <= 3
ORDER BY category, rn;
```

**What changed:**
- Made the second-purchase logic explicit in its own CTE (clearer).
- Pinned the time window to UTC.
- Made grain explicit at each step.
- Same correctness, much easier to audit.

### What this example shows

| AI gave you | You added |
|---|---|
| Reasonable structure | Explicit grain at each CTE |
| Correct `ROW_NUMBER()` usage | Timezone pinned |
| Correct aggregations | Row count + sample verification |
| Correct joins | "Explain it back" probe caught a framing error |
| Plausible-looking SQL | Documented *why* each step exists |

**The 5-step loop in action: SPEC → DRAFT → READ → VERIFY → SHIP.**
Without steps 3–4, you ship a query that looks right, runs fast, and answers the wrong question in production for 6 months.

---

## What Comes Next

> Lesson 2 — **Text-to-SQL** — the real accuracy of AI on a 200-table warehouse, the failure modes that drive the gap, and when text-to-SQL is the right tool vs. the wrong one.
