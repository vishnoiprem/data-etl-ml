# Lesson 15 — Date Functions: DATE_ADD, DATEDIFF, EXTRACT

> **Goal:** date arithmetic for ETL and reporting.

---

## The dialects

Date functions are the *least* portable part of SQL. The
same question ("days between two dates") has a different
answer in each database.

| Operation | PostgreSQL | MySQL | SQLite |
|---|---|---|---|
| Today | `CURRENT_DATE` | `CURDATE()` | `DATE('now')` |
| Now | `NOW()` | `NOW()` | `DATETIME('now')` |
| Add days | `d + INTERVAL '1 day'` | `DATE_ADD(d, INTERVAL 1 DAY)` | `DATE(d, '+1 day')` |
| Diff in days | `d2 - d1` | `DATEDIFF(d2, d1)` | `JULIANDAY(d2) - JULIANDAY(d1)` |
| Year | `EXTRACT(YEAR FROM d)` | `YEAR(d)` | `CAST(STRFTIME('%Y', d) AS INT)` |
| Month | `EXTRACT(MONTH FROM d)` | `MONTH(d)` | `CAST(STRFTIME('%m', d) AS INT)` |

We'll use standard SQL where possible and note the SQLite
workarounds for the practice modules.

---

## Current date and time

```sql
SELECT CURRENT_DATE;          -- 2026-10-09
SELECT CURRENT_TIMESTAMP;     -- 2026-10-09 14:30:00
```

`CURRENT_TIMESTAMP` returns the timestamp at the start of
the current transaction. In a long-running analysis, this
is stable; in a long-running interactive session, it changes
once per transaction.

---

## EXTRACT

Pull a single field (year, month, day, hour, ...) from a
date or timestamp.

```sql
SELECT EXTRACT(YEAR  FROM order_date) AS yr,
       EXTRACT(MONTH FROM order_date) AS mo,
       EXTRACT(DAY   FROM order_date) AS day
FROM   Orders;
```

This is the standard SQL way. PostgreSQL, Snowflake,
BigQuery, Oracle support it. MySQL uses `YEAR()`, `MONTH()`,
`DAY()`. SQLite uses `STRFTIME`.

In SQLite:

```sql
SELECT CAST(STRFTIME('%Y', order_date) AS INTEGER) AS yr,
       CAST(STRFTIME('%m', order_date) AS INTEGER) AS mo
FROM   Orders;
```

`STRFTIME` is SQLite's swiss-army-knife date formatter. The
format string is the same as C's `strftime`: `%Y` = 4-digit
year, `%m` = month, `%d` = day, `%H` = hour, `%M` = minute,
`%S` = second, `%j` = day of year, `%w` = day of week (0-6).

---

## DATE_ADD and DATE_SUB

Add or subtract an interval.

```sql
-- MySQL
SELECT DATE_ADD(order_date, INTERVAL 7 DAY) FROM Orders;

-- PostgreSQL
SELECT order_date + INTERVAL '7 days' FROM Orders;

-- SQLite
SELECT DATE(order_date, '+7 days') FROM Orders;
```

In standard SQL the `+ INTERVAL '7 day'` form is portable.
MySQL prefers its own syntax. SQLite has a quirky third-arg
form that takes a string like `'+7 days'` or `'-1 month'`.

---

## DATEDIFF

Difference between two dates.

```sql
-- MySQL
SELECT DATEDIFF(NOW(), order_date) FROM Orders;

-- PostgreSQL (returns days as integer)
SELECT NOW()::date - order_date FROM Orders;

-- SQLite
SELECT CAST(JULIANDAY('now') - JULIANDAY(order_date) AS INTEGER)
FROM   Orders;
```

`JULIANDAY` returns a real number; cast to integer for whole
days. Watch for negative numbers: `DATEDIFF(a, b)` in MySQL
is `a - b`; in PostgreSQL `a - b` is the same; in SQLite the
`JULIANDAY` subtraction is also the same. Stay consistent.

For "months between two dates", there's no portable function.
The common pattern is `EXTRACT(YEAR FROM age) * 12 +
EXTRACT(MONTH FROM age)` in PostgreSQL, or a custom
implementation in MySQL/SQLite.

---

## DATE_TRUNC

Truncate a date to the start of a period. The killer feature
for "revenue by month" queries.

```sql
-- PostgreSQL
SELECT DATE_TRUNC('month', order_date) AS month, SUM(total)
FROM   Orders
GROUP BY DATE_TRUNC('month', order_date);

-- SQLite
SELECT DATE(order_date, 'start of month') AS month, SUM(total)
FROM   Orders
GROUP BY DATE(order_date, 'start of month');
```

`DATE_TRUNC('month', ...)` returns the first day of the
month. `DATE_TRUNC('year', ...)` returns Jan 1. `DATE_TRUNC('week',
...)` returns the Monday of the week. Use these for any "by
period" report.

---

## Time zones

`TIMESTAMP` is a point in time. `TIMESTAMP WITH TIME ZONE`
(aka `timestamptz` in PostgreSQL) is the same point in time,
displayed in the session's time zone. This distinction is the
source of countless production bugs.

**Rule of thumb:** store everything as `timestamptz` (or its
equivalent) in UTC. Convert to local time only at display
time.

---

## Try it

Given `Orders(id, customer_id, total, order_date)`:

1. Find the number of orders per year, sorted by year.
2. Find the number of orders per (year, month) for 2024.
3. Find the average number of days between order_date and
   today. (Use `JULIANDAY` if SQLite; `DATEDIFF` or `-` if
   MySQL/PostgreSQL.)
