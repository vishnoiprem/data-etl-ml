# Lesson 01 — Introduction to SQL and Its History

> **Goal:** understand what SQL is, where it came from, and why
> it has outlasted every "SQL killer" of the last four decades.

---

## What SQL is

**SQL** stands for **Structured Query Language**. It is a
declarative language for talking to *relational* databases. You
describe *what* you want, not *how* to get it. The database
engine figures out the access path.

A single SELECT statement can be answered in many different
ways — a sequential scan, an index lookup, a hash join, a
merge join. The engine picks one based on statistics, indexes,
and the structure of the query. The application code never
sees that decision.

This is why SQL has survived where other query languages have
not. The relational model is a thin, principled layer over sets
and predicates. Add or remove an index, double the data, swap
the storage engine — the same SQL keeps working.

---

## Where it came from

- **1970** — Edgar F. Codd publishes *"A Relational Model of
  Data for Large Shared Data Banks"*. The idea: data should be
  organized as *relations* (tables) and queried with a
  mathematical algebra.
- **1974** — Donald Chamberlin and Raymond Boyce at IBM
  design **SEQUEL** (Structured English QUEry Language) to
  implement Codd's algebra. Renamed to **SQL** for trademark
  reasons.
- **1979** — Oracle ships the first commercial implementation.
- **1986** — ANSI standardizes SQL. The standard is revised in
  1989, 1992, 1999, 2003, 2006, 2008, 2011, 2016, 2019, and
  2023. Every revision adds features; very few are removed.
- **Today** — every major database (PostgreSQL, MySQL, SQLite,
  SQL Server, Oracle, Snowflake, BigQuery, Databricks, DuckDB)
  speaks some dialect of SQL. The core is identical.

---

## Why "SQL killer" languages lose

Every decade, a new query language is proposed as a SQL
replacement: object-oriented SQL, XML query, LINQ, MongoDB's
aggregation pipeline, GraphQL. None of them have unseated SQL.

The reason is the **relational closure property**: every SQL
query takes a relation (or several) as input and produces a
relation as output. You can chain queries without breaking the
abstraction. The output of one SELECT is the input of the next.

```sql
WITH high_earners AS (
  SELECT * FROM Employee WHERE salary > 100000
)
SELECT department_id, COUNT(*)
FROM high_earners
GROUP BY department_id;
```

`high_earners` is a relation. The outer query treats it exactly
like a table. This composability is what declarative languages
are good at and imperative languages are bad at.

---

## Dialects you will meet

In data engineering interviews the dialect is almost always
**standard SQL** with one of these two flavors:

- **PostgreSQL flavor** — cleanest window-function syntax,
  `INTERVAL '1 day'`, `GENERATE_SERIES`, recursive CTEs.
- **MySQL flavor** — `DATE_ADD`, `DATEDIFF`, slightly different
  string functions (`CONCAT` instead of `||`).

The practice modules in this course use **SQLite** because it is
embedded, deterministic, and ships with Python. SQLite supports
about 80% of the SQL you will ever need in an interview: window
functions, CTEs, all standard joins, most string/date functions.
It does **not** support `FULL OUTER JOIN` or `GROUPING SETS`
natively — we work around that in the relevant lessons.

---

## Try it

Open a Python REPL and run:

```python
from common import QueryRunner
with QueryRunner(":memory:") as q:
    q.execute("CREATE TABLE hello (msg TEXT)")
    q.execute("INSERT INTO hello VALUES ('hi from sqlite')")
    print(q.query_all("SELECT * FROM hello"))
```

You just ran a real SQL query against a real (in-memory)
database. The rest of this track is that, with bigger
questions.
