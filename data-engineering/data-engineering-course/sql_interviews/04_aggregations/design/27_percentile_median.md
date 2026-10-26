# Lesson 27 — Percentile and Median Approximations

> **Goal:** compute percentiles and medians in SQL. Know
> the difference between exact and approximate answers.

---

## The exact way: PostgreSQL

PostgreSQL has built-in ordered-set aggregate functions:

```sql
SELECT
  percentile_cont(0.5) WITHIN GROUP (ORDER BY salary) AS median_salary,
  percentile_disc(0.5) WITHIN GROUP (ORDER BY salary) AS median_salary_disc,
  percentile_cont(0.95) WITHIN GROUP (ORDER BY salary) AS p95,
  percentile_cont(0.99) WITHIN GROUP (ORDER BY salary) AS p99
FROM   Employee;
```

- `percentile_cont(f)` — returns a value that *interpolates*
  between data points. The median of {1, 2, 3, 4} is 2.5.
- `percentile_disc(f)` — returns an *actual* data point. The
  median of {1, 2, 3, 4} is 2 or 3 (engine-dependent).

`WITHIN GROUP (ORDER BY col)` is the standard syntax. Snowflake
and Oracle support it; MySQL and SQLite do not.

---

## The standard way: window function

For a per-group median, you need a window function. The
canonical pattern in PostgreSQL:

```sql
SELECT DISTINCT
  department_id,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY salary)
    OVER (PARTITION BY department_id) AS median_salary
FROM   Employee;
```

`percentile_cont` is a special aggregate that can be used as
a window function with `OVER (PARTITION BY ...)`. The
`DISTINCT` is needed because the aggregate is computed for
each row and produces duplicates; `DISTINCT` collapses them.

---

## The SQLite way: manual

SQLite has no built-in percentile. The classic pattern:

```sql
WITH ranked AS (
  SELECT
    salary,
    ROW_NUMBER() OVER (ORDER BY salary) AS rn,
    COUNT(*)    OVER ()                  AS n
  FROM   Employee
)
SELECT AVG(salary) AS median_salary
FROM   ranked
WHERE  rn IN ((n + 1) / 2.0, (n + 2) / 2.0);
```

This is the standard "average the two middle values" median.
If `n` is odd, the two expressions round to the same value
and we average one row. If `n` is even, we average the two
middle rows.

For per-group median, add a `PARTITION BY` to the window:

```sql
WITH ranked AS (
  SELECT
    department_id,
    salary,
    ROW_NUMBER() OVER (PARTITION BY department_id ORDER BY salary) AS rn,
    COUNT(*)    OVER (PARTITION BY department_id)                  AS n
  FROM   Employee
)
SELECT
  department_id,
  AVG(salary) AS median_salary
FROM   ranked
WHERE  rn IN ((n + 1) / 2.0, (n + 2) / 2.0)
GROUP BY department_id;
```

This is the pattern M09 (Hard) uses for "median salary by
department".

---

## Approximations

For very large tables, the exact median is expensive. Common
approximations:

- **t-digest** (PostgreSQL's `percentile_cont` uses this for
  large inputs). Approximate but accurate to a few percent.
- **Reservoir sampling**. Keep a fixed-size random sample;
  compute the median on the sample.
- **Sorted histogram**. Bin the data, then look up the
  median bin.

The simplest approximation: take a 1% random sample and
compute the median on it. For p50, the error is O(1/sqrt(n))
on the sample, so a 10,000-row sample gives ~1% accuracy.

```sql
SELECT AVG(salary) AS approx_median
FROM   (
  SELECT salary
  FROM   Employee
  WHERE  RANDOM() < 0.01   -- 1% sample
  ORDER BY salary
  LIMIT 10000
)
WHERE  ... (same IN-trick as above)
```

This is good enough for dashboards. For SLOs and finance
reports, use the exact answer.

---

## Interview expectations

If the question is "what's the median salary per
department" and you're in an interview:

1. State the dialect and the function. "PostgreSQL has
   `percentile_cont(0.5) WITHIN GROUP (ORDER BY salary)`."
2. Show the per-group version using a window function or
   GROUP BY.
3. Mention the SQLite / MySQL workaround if relevant.
4. If the table is huge, mention the approximation
   (t-digest or sample).

---

## Try it

Given `Employee(id, name, salary, department_id)`:

1. Compute the company-wide median salary.
2. Compute the per-department median salary.
3. Compute the p95 salary per department.

If your database has `percentile_cont`, use it. If not,
write the window-function equivalent.
