# Lesson 18 — Aliases and the AS Keyword

> **Goal:** name your columns and tables so the query reads
> like English.

---

## Column aliases

```sql
SELECT
  salary * 12            AS annual_salary,
  UPPER(name)            AS display_name,
  EXTRACT(YEAR FROM hire_date) AS hire_year
FROM   Employee;
```

`AS` is the standard. Some dialects accept the bare form
(`salary * 12 annual_salary`) but `AS` is clearer and more
portable.

Aliases can contain spaces if quoted:

```sql
SELECT salary * 12 AS "Annual Salary" FROM Employee;
```

This is non-portable and ugly. Don't do it. Use snake_case.

---

## Table aliases

```sql
SELECT e.id, e.name, d.department_name
FROM   Employee   AS e
JOIN   Department AS d ON e.department_id = d.id;
```

A table alias lets you write `e.id` instead of `Employee.id`.
This is essential for joins and self-joins.

**Convention:** short aliases for frequently-used tables
(`e` for Employee, `o` for Orders). Longer aliases for
one-off tables (`recent_orders`, `top_customers`).

The keyword `AS` is optional for table aliases too:
`FROM Employee e` works. Use `AS` for clarity in interview
answers.

---

## Aliases can be referenced in ORDER BY

```sql
SELECT salary * 12 AS annual_salary
FROM   Employee
ORDER BY annual_salary DESC;
```

The SELECT alias is visible to ORDER BY (because ORDER BY is
the last step in the query plan). It is *not* visible to
WHERE, GROUP BY, or HAVING in most databases. To use an
expression in those clauses, repeat the expression or wrap
in a CTE.

---

## Aliases can be referenced in GROUP BY (in some databases)

PostgreSQL, MySQL, and SQLite allow `GROUP BY` to reference
SELECT aliases. The standard says no; the engines permit it
as an extension.

```sql
-- Works in PostgreSQL, MySQL, SQLite
SELECT department_id, COUNT(*) AS n
FROM   Employee
GROUP BY department_id
ORDER BY n DESC;
```

Don't rely on this for portability. If you have to write SQL
that runs on multiple engines, repeat the expression:
`ORDER BY COUNT(*) DESC`.

---

## Aliases and JOIN: the same table twice

A self-join requires an alias because you reference the same
table twice. Without the alias the database can't tell which
"Employee" you mean.

```sql
-- Pairs of employees in the same department
SELECT a.name AS emp1, b.name AS emp2
FROM   Employee a
JOIN   Employee b ON a.department_id = b.department_id
                 AND a.id < b.id;
```

`a.id < b.id` ensures each pair appears once (not twice) and
excludes self-pairs. This is the canonical "find pairs"
pattern.

---

## The AS keyword and column names

`AS` does not rename the column in the table — it renames
it in the *result set* of this query. Other queries that
select from this one will see the original column name.

```sql
SELECT id AS employee_id FROM Employee;   -- result column: employee_id
```

```sql
-- Other query, sees the original
SELECT * FROM (SELECT id AS employee_id FROM Employee) sub;
-- The outer query references the alias, not 'id', from this derived table
```

This distinction matters when you nest queries.

---

## Try it

Given `Orders(id, customer_id, total, order_date, status)`:

1. Write a query that returns the total revenue per
   customer, with the customer_id aliased as `cust_id` and
   the sum aliased as `lifetime_value`.
2. Write a self-join that finds pairs of customers who
   placed an order on the same date.
3. Use a CTE to compute a derived column (`revenue =
   total * 1.1`) and reference the alias from the outer
   query's WHERE.
