# Lesson 26 — GROUPING SETS

> **Goal:** explicit multi-level aggregation. The most
> general form of ROLLUP / CUBE.

---

## The idea

`GROUPING SETS` lets you list exactly which aggregation
levels you want. It's the explicit form; `ROLLUP` and `CUBE`
are abbreviations for particular sets of levels.

```sql
SELECT
  region,
  country,
  product_category,
  SUM(revenue) AS revenue
FROM   Sales
GROUP BY GROUPING SETS (
  (region, country, product_category),  -- detail
  (region, country),                    -- per (region, country)
  (region),                             -- per region
  ()                                    -- grand total
);
```

This is exactly the same as the ROLLUP example in Lesson 25,
written explicitly. ROLLUP and CUBE are convenience syntax
for the most common patterns; GROUPING SETS is the general
form.

---

## Equivalences

```sql
-- ROLLUP(a, b) == GROUPING SETS ((a, b), (a), ())
-- CUBE(a, b)   == GROUPING SETS ((a, b), (a), (b), ())
```

So ROLLUP is a hierarchical subset, and CUBE is the full
power set. GROUPING SETS is whatever you want.

If you want a non-hierarchical, non-full-cube set of
aggregation levels, GROUPING SETS is the only option.

```sql
-- Revenue by region AND revenue by category, in one query
SELECT
  region,
  product_category,
  SUM(revenue) AS revenue
FROM   Sales
GROUP BY GROUPING SETS (
  (region),
  (product_category)
);
```

The result has rows with `product_category = NULL` (region
subtotals) and rows with `region = NULL` (category
subtotals), plus any row that satisfies both (which is
impossible here, so we don't see detail rows).

---

## Support

Same as ROLLUP / CUBE: PostgreSQL, SQL Server, Oracle,
Snowflake, BigQuery, DuckDB. **Not** MySQL, **not** SQLite.

For SQLite / MySQL, fall back to `UNION ALL` of separate
queries, one per aggregation level.

---

## Practical use case: a report query

Imagine a report that needs:

1. Total revenue per (region, country, category) — detail.
2. Total revenue per region — one level up.
3. Grand total — top level.

You'd write:

```sql
SELECT
  COALESCE(region, 'ALL REGIONS')          AS region,
  COALESCE(country, 'ALL COUNTRIES')       AS country,
  COALESCE(product_category, 'ALL CATS')   AS product_category,
  SUM(revenue)                              AS revenue
FROM   Sales
GROUP BY GROUPING SETS (
  (region, country, product_category),
  (region),
  ()
)
ORDER BY region NULLS LAST, country NULLS LAST, product_category NULLS LAST;
```

`COALESCE` replaces the subtotal NULLs with human-readable
strings. This is the report-row pattern.

---

## `GROUPING_ID` and `GROUPING`

Same as in ROLLUP / CUBE:

- `GROUPING(col)` — 1 if `col` is NULL due to rollup, 0
  otherwise.
- `GROUPING_ID(a, b, c)` — bitmask of which columns are
  rolled up. For a (region, country) subtotal, it's
  binary `001 = 1`. For grand total, `111 = 7`.

`GROUPING_ID` is useful as a sort key: it gives a stable
ordering of "level" rows.

---

## Try it

Given `Sales(region, country, product_category, revenue)`:

1. Compute revenue per (region, country) and per
   product_category, in one query. Use `GROUPING SETS` if
   your database supports it.
2. Add a column that labels each row as `'detail'`,
   `'region_country'`, or `'category'`, based on which
   columns are NULL.
3. Same as 1, but write the equivalent `UNION ALL` form
   that works in SQLite.
