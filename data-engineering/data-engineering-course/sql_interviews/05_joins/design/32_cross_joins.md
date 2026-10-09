# Lesson 32 — Cross Joins and Cartesian Products

> **Goal:** every-row-pairs joins. The right tool for
> building grids, the wrong tool for almost everything
> else.

---

## What CROSS JOIN does

Every row in the left table is paired with every row in the
right table. The result has `|A| × |B|` rows.

```sql
SELECT a.x, b.y
FROM   A CROSS JOIN B;
```

Equivalent to:

```sql
SELECT a.x, b.y
FROM   A, B;
```

Or:

```sql
SELECT a.x, b.y
FROM   A
JOIN   B ON 1 = 1;   -- always-true predicate
```

All three are the same. The explicit `CROSS JOIN` is the
most readable.

---

## When to use CROSS JOIN

### 1. Building a date × product grid

```sql
WITH dates AS (
  SELECT DISTINCT DATE(order_date) AS d FROM Orders
),
products AS (
  SELECT DISTINCT product_id FROM OrderItem
)
SELECT d.d, p.product_id
FROM   dates d
CROSS JOIN products p;
```

This gives you every (date, product) combination, even the
ones that didn't actually sell. Use it to find "missing"
combinations or to anchor a report.

### 2. Generating a sequence

```sql
SELECT 0 AS n
UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3
UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6
UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9
```

Or, more elegantly, a recursive CTE:

```sql
WITH RECURSIVE seq(n) AS (
  SELECT 0
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 9
)
SELECT * FROM seq;
```

`CROSS JOIN` this with another table to get a row per
sequence number per other row.

### 3. Pairwise comparisons

```sql
-- All pairs of products in the same category
SELECT a.id, a.name, b.id, b.name
FROM   Product a
CROSS JOIN Product b
WHERE  a.category = b.category
  AND  a.id < b.id;
```

This produces a row for every (unordered) pair of products
in the same category. `a.id < b.id` keeps each pair once.

### 4. Matrix multiplication (in SQL)

A CROSS JOIN plus aggregation is how you do matrix
multiplication in pure SQL. Rare in interviews; common in
specific domains (recommender systems, graph algorithms).

---

## When NOT to use CROSS JOIN

If you find yourself writing a CROSS JOIN and your query
takes more than a few seconds, you almost certainly wanted
an INNER JOIN with a predicate. CROSS JOINs blow up row
counts quadratically.

Rule of thumb: a CROSS JOIN of two 1000-row tables is
1,000,000 rows. A CROSS JOIN of two 100,000-row tables is
10,000,000,000 rows. The engine will scan all of them.

The one exception is when you `GROUP BY` afterwards and
collapse the result back down. Then the CROSS JOIN is a
way to express "consider every pair" before aggregating.

---

## The accidental cross join

A common bug: forgetting the join predicate.

```sql
-- WRONG: no ON clause
SELECT e.name, d.department_name
FROM   Employee e
JOIN   Department d;          -- implicit CROSS JOIN
```

Some databases (MySQL with certain configs) accept this
syntax. It returns every (employee, department) pair — a
Cartesian product. The result looks plausible but the
counts are wildly inflated.

Always include an ON clause for any JOIN that isn't an
explicit CROSS JOIN.

---

## CROSS JOIN with WHERE

```sql
SELECT a.x, b.y
FROM   A CROSS JOIN B
WHERE  a.x > b.y;
```

This is fine. The CROSS JOIN produces the Cartesian product;
the WHERE filters it down. The optimizer usually reorders
this into a more efficient plan, but for very large inputs
the CROSS JOIN first can be expensive. Prefer:

```sql
SELECT a.x, b.y
FROM   A
JOIN   B ON a.x > b.y;
```

Same result, but the predicate is visible in the JOIN and
the optimizer is more likely to push it down.

---

## Try it

Given `Product(id, name, category)` and `Customer(id, name,
country)`:

1. Build the full product × customer grid. (Don't run this
   on more than 10 rows of each.)
2. Find every (product, customer) pair where the product
   category matches the customer's country (just as an
   exercise in cross-join filtering).
3. Build a sequence of integers from 0 to 9 using a
   recursive CTE.
