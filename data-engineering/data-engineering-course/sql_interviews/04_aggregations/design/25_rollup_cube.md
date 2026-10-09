# Lesson 25 — ROLLUP and CUBE

> **Goal:** multi-level subtotals in a single query.

---

## ROLLUP

`ROLLUP(a, b, c)` is shorthand for `GROUP BY a, b, c` plus
subtotals for `(a, b)`, `(a)`, and `()` (the grand total).
The number of grouping levels is the number of columns plus
one.

```sql
SELECT
  region,
  product_category,
  SUM(revenue) AS revenue
FROM   Sales
GROUP BY ROLLUP(region, product_category)
ORDER BY region NULLS LAST, product_category NULLS LAST;
```

The output has:

- One row per (region, product_category) combination — the
  detail rows.
- One row per region with `product_category = NULL` — the
  region subtotals.
- One row with both `NULL` — the grand total.

You can identify the subtotal rows by checking for NULL on
the rolled-up column.

### Subtotal rows: how to spot them

The subtotal row has NULL where the aggregation level
"disappeared". To distinguish a subtotal NULL from a real
data NULL, use `GROUPING()`:

```sql
SELECT
  region,
  product_category,
  SUM(revenue) AS revenue,
  GROUPING(region)            AS region_is_subtotal,
  GROUPING(product_category)  AS cat_is_subtotal
FROM   Sales
GROUP BY ROLLUP(region, product_category);
```

`GROUPING(x)` returns 1 if `x` is NULL *because of the
rollup*, 0 otherwise. So a region subtotal has
`region_is_subtotal = 0` and `cat_is_subtotal = 1`. The
grand total has both = 1.

---

## CUBE

`CUBE(a, b, c)` is shorthand for every combination of
subtotals: `(a, b, c)`, `(a, b)`, `(a, c)`, `(b, c)`,
`(a)`, `(b)`, `(c)`, `()`. That's 2^n levels for n columns.

```sql
SELECT
  region,
  product_category,
  SUM(revenue) AS revenue
FROM   Sales
GROUP BY CUBE(region, product_category);
```

This is a strict superset of ROLLUP. ROLLUP gives a
hierarchy; CUBE gives all combinations. ROLLUP is what you
want for "region → category → total"; CUBE is what you
want for "any dimension vs any other dimension".

---

## Support

ROLLUP and CUBE are part of the SQL standard. Supported by:

- **PostgreSQL** — yes, with `GROUPING()`.
- **SQL Server** — yes, with `GROUPING()` and `GROUPING_ID()`.
- **Oracle** — yes.
- **Snowflake** — yes.
- **BigQuery** — yes.
- **MySQL** — `WITH ROLLUP` (limited) and `WITH CUBE` removed
  in 8.0. Use `UNION ALL` of separate GROUP BYs.
- **SQLite** — **not supported**. Use `UNION ALL` of separate
  GROUP BYs.

In SQLite:

```sql
SELECT region, product_category, SUM(revenue) AS revenue
FROM   Sales
GROUP BY region, product_category
UNION ALL
SELECT region, NULL, SUM(revenue)
FROM   Sales
GROUP BY region
UNION ALL
SELECT NULL, NULL, SUM(revenue)
FROM   Sales;
```

This is verbose but works everywhere. Lesson 26 covers
`GROUPING SETS`, which is the standard way to write this.

---

## When to use ROLLUP / CUBE

Use ROLLUP when you have a natural hierarchy (year → quarter
→ month, region → country → city) and want a report that
shows subtotals at each level.

Use CUBE when you have independent dimensions and want to see
totals along any axis.

In data engineering, both are often replaced by a BI tool
that computes subtotals on the client. The SQL form is for
when the subtotals need to live in the database result (e.g.
as a report table, an API response, a CSV export).

---

## Try it

Given `Sales(region, country, product_category, revenue)`:

1. Compute total revenue per (region, country, product_category),
   per (region, country), per region, and grand total. Use
   `ROLLUP` if your database supports it; otherwise use
   `UNION ALL` of separate GROUP BYs.
2. Add a `level` column that says `'detail'`, `'subtotal'`,
   or `'grand_total'` using `GROUPING()`.
3. Compute the same with `CUBE` and see the difference in
   row count.
