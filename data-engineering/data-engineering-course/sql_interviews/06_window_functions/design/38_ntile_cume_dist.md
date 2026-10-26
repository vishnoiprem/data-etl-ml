# Lesson 38 — NTILE, CUME_DIST, PERCENT_RANK

> **Goal:** bucketing and cumulative distribution. The
> less-famous window functions, but very useful in
> production.

---

## NTILE

`NTILE(n)` divides the rows of a window into `n` buckets
(approximately equal size) and returns the bucket number
(1 to n) for each row.

```sql
SELECT
  name, salary,
  NTILE(4) OVER (ORDER BY salary DESC) AS quartile
FROM   Employee;
```

Divides employees into 4 buckets by salary. The top 25%
(by salary) get quartile = 1. The bottom 25% get quartile = 4.

If the number of rows isn't divisible by n, the first
buckets get the extra rows. For 10 rows and NTILE(4):
buckets 1, 2, 3 have 3 rows each, bucket 4 has 1 row.

### Use cases

- **Quartile/decile analysis.** `NTILE(4)` for quartiles,
  `NTILE(10)` for deciles, `NTILE(100)` for percentiles.
- **A/B bucketing.** `NTILE(2)` over a random order
  gives you two random groups.
- **Stratified sampling.** `NTILE(10)` and take all rows
  in bucket 1 for a 10% sample.

### Quartile math

Quartile is just `NTILE(4)`. To get the *boundary* values
(Q1, Q2, Q3), use `PERCENTILE_CONT` (PostgreSQL) or a
window function trick (Lesson 27).

---

## CUME_DIST

`CUME_DIST()` returns the cumulative distribution of a
value within a window: the proportion of rows with values
less than or equal to the current row's value.

```sql
SELECT
  name, salary,
  CUME_DIST() OVER (ORDER BY salary) AS cum_dist
FROM   Employee;
```

For the lowest salary, cum_dist is `1/n` (the row itself
counts). For the highest, it's 1.0. For ties, all tied
rows get the same cum_dist (the value of the last tied
row).

`CUME_DIST` is the empirical CDF. Useful for "what fraction
of values is at most X?".

### Example: "What percentile is this salary at?"

```sql
SELECT
  name, salary,
  CUME_DIST() OVER (ORDER BY salary) AS percentile
FROM   Employee
WHERE  name = 'Alice';
```

A value of 0.85 means "85% of salaries are at most Alice's".

---

## PERCENT_RANK

`PERCENT_RANK()` returns the relative rank of a row: the
rank minus 1, divided by the total number of rows minus 1.

```sql
SELECT
  name, salary,
  PERCENT_RANK() OVER (ORDER BY salary) AS pct_rank
FROM   Employee;
```

For the lowest salary, pct_rank is 0. For the highest, it's
1. Tied rows get the same value.

| Function | Range | For n rows |
|---|---|---|
| `CUME_DIST` | (0, 1] | 1/n to 1 |
| `PERCENT_RANK` | [0, 1] | 0 to 1 |
| `RANK / n` | (0, 1] | 1/n to 1 (similar to CUME_DIST but with gaps) |

The difference: `CUME_DIST` and `RANK / n` differ on ties
because `CUME_DIST` uses cumulative count (≤) while `RANK`
uses distinct-then-tied. For most uses they're close enough
that you can pick either.

---

## When to use each

| Function | Use case |
|---|---|
| `NTILE(n)` | Bucket into n groups (quartiles, A/B). |
| `CUME_DIST` | Empirical CDF; "fraction of values at most X". |
| `PERCENT_RANK` | Relative rank, normalized to [0, 1]. |

In interviews, the most common of these is `NTILE` (for "top
N%" questions). The other two are less common but show up
in "what percentile is this value at?" questions.

---

## NTILE pattern: top 10% of earners

```sql
WITH bucketed AS (
  SELECT
    name, salary,
    NTILE(10) OVER (ORDER BY salary DESC) AS decile
  FROM   Employee
)
SELECT name, salary
FROM   bucketed
WHERE  decile = 1;
```

Returns the top 10% of earners. The bucket is
"approximately 10%" — exactly 10% if the row count is
divisible by 10, otherwise off by one.

---

## A worked example

> "Show the salary distribution: for each salary value, the
> number of employees at or below it."

```sql
SELECT
  salary,
  COUNT(*)                                       AS n_at_or_below,
  CUME_DIST() OVER (ORDER BY salary)             AS cum_frac
FROM   Employee
GROUP BY salary
ORDER BY salary;
```

The CUME_DIST gives you the "fraction of the population
that earns at most this much". A small multiple of this
table is the basis of a salary-distribution chart.

---

## Try it

Given `Employee(id, name, salary, department_id)`:

1. Assign each employee to one of 4 quartiles by salary
   (company-wide). Use `NTILE(4)`.
2. Same, but per department. Use `PARTITION BY`.
3. For each employee, compute their `CUME_DIST` (fraction
   of the company earning less than or equal to them).
4. Same, per department.
