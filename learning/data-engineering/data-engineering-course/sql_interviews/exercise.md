# Capstone — 5 Interview-Style SQL Questions

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

Five end-to-end interview questions to time yourself on. The
goal is to write each query in 15 minutes or less, run it
against a seeded SQLite, and walk through the answer as if
you were explaining it to an interviewer.

Each question has a starter schema in
`tests/fixtures/capstone.sql` (a hand-crafted minimal
fixture) and a reference answer in
`code/capstone_solutions.sql`. Time yourself. Don't peek.

---

## Question 1 — Top 3 spenders per country

> "Given `Customers(id, name, country)` and
> `Orders(id, customer_id, total, order_date)`, return the
> top 3 customers by total spend per country, with ties
> preserved."

Pattern: `DENSE_RANK` partitioned by country, ordered by
total spend desc.

---

## Question 2 — Month-over-month revenue growth

> "Given `Orders(id, customer_id, total, order_date)`,
> return each month's revenue and the percentage growth
> from the previous month. Order chronologically."

Pattern: `SUM(total) GROUP BY month` then `LAG` to get the
previous month's revenue, then a percentage calc.

---

## Question 3 — Users active 7 consecutive days

> "Given `Logins(user_id, login_date)`, return every user
> who has logged in on at least 7 consecutive days."

Pattern: identify runs by subtracting `ROW_NUMBER()` from
the date; group by (user, run) and check the run length.

---

## Question 4 — Pivoted cohort revenue

> "Given `Orders(id, customer_id, total, order_date)`,
> build a cohort table: rows = signup year, columns =
> order year, values = revenue. The signup year is the
> year of the customer's first order."

Pattern: build a CTE for signup year per customer, then
`SUM(CASE WHEN year = X THEN total END)` pivoted across
years.

---

## Question 5 — Anti-join: customers with no delivered orders

> "Given `Customers(id, name)` and `Orders(id, customer_id,
> status)`, return every customer who has never had a
> `status = 'delivered'` order. Use all three anti-join
> forms (`NOT IN`, `NOT EXISTS`, `LEFT JOIN ... IS NULL`)
> and explain which is correct when the subquery might
> return NULLs."

Pattern: write each form, run them, compare results,
explain.

---

## Running your answers

A minimal harness is in
`09_hard_practice/tests/fixtures/capstone.sql`. To test your
own query:

```python
from common import QueryRunner

with open("sql_interviews/09_hard_practice/tests/fixtures/capstone.sql") as f:
    schema_sql = f.read()

q = QueryRunner(":memory:")
for stmt in schema_sql.split(";"):
    if stmt.strip():
        q.execute(stmt)

# Replace with your query
rows = q.query_all("""
  SELECT ...
""")
print(rows)
```

When you're ready, compare against
`09_hard_practice/code/capstone_solutions.sql`.
