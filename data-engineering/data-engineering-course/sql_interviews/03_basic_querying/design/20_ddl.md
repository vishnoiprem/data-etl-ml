# Lesson 20 — CREATE TABLE, ALTER TABLE, DROP TABLE

> **Goal:** define and remove schema. The DDL (Data
> Definition Language) half of SQL.

---

## CREATE TABLE

The basic shape:

```sql
CREATE TABLE Employee (
    id            INTEGER       PRIMARY KEY,
    name          TEXT          NOT NULL,
    email         TEXT          UNIQUE,
    salary        REAL          CHECK (salary >= 0),
    department_id INTEGER       REFERENCES Department(id),
    hire_date     DATE          DEFAULT CURRENT_DATE
);
```

### Column constraints

| Constraint | What it does |
|---|---|
| `PRIMARY KEY` | Unique, NOT NULL. Usually indexed. |
| `NOT NULL` | Disallow NULL. |
| `UNIQUE` | No two rows can share this value. |
| `CHECK (cond)` | Per-row validation. |
| `DEFAULT val` | Value used if no value is provided. |
| `REFERENCES t(c)` | Foreign key to another table. |

### IF NOT EXISTS

`CREATE TABLE IF NOT EXISTS ...` is the idempotent form:
succeed if the table exists, create it otherwise. Used by
test setup scripts so they can run multiple times.

### TEMPORARY

`CREATE TEMP TABLE ...` creates a table visible only to the
current session. The data goes away when the connection
closes. Useful for intermediate steps in a long analysis.

### CTAS — CREATE TABLE AS

```sql
CREATE TABLE Employee_summary AS
SELECT department_id, COUNT(*) AS n, AVG(salary) AS avg_sal
FROM   Employee
GROUP BY department_id;
```

Creates a new table from a query. The new table has no
constraints (other than the types inferred from the query).
Common in ETL: materialize the result of a long-running
query as a new table.

---

## ALTER TABLE

Modify an existing table. The supported operations vary by
database.

### Add a column

```sql
ALTER TABLE Employee ADD COLUMN middle_name TEXT;
```

### Drop a column

```sql
ALTER TABLE Employee DROP COLUMN middle_name;
```

### Rename a column / table

```sql
ALTER TABLE Employee RENAME COLUMN name TO full_name;  -- SQLite
ALTER TABLE Employee RENAME TO Staff;                  -- SQLite
```

In PostgreSQL: `ALTER TABLE Employee RENAME COLUMN name TO
full_name;`. In MySQL: `ALTER TABLE Employee CHANGE name
full_name TEXT;` (you re-state the type — annoying).

### Modify a column's type

```sql
ALTER TABLE Employee ALTER COLUMN salary TYPE NUMERIC(12, 2);  -- PG
```

Changing a column's type can fail if existing data doesn't
fit the new type. Always check first.

---

## DROP TABLE

Remove a table and all its data.

```sql
DROP TABLE Employee;            -- error if doesn't exist
DROP TABLE IF EXISTS Employee;  -- silent if doesn't exist
```

`DROP TABLE` is irreversible. It also fails if other tables
have foreign keys to this one. The cascade form:

```sql
DROP TABLE Employee CASCADE;
```

In SQLite, foreign key constraints are not enforced by
default. To enforce them:

```sql
PRAGMA foreign_keys = ON;
```

---

## Indexes

An index is a separate data structure that lets the engine
find rows by a column value without scanning the whole
table. Create one with `CREATE INDEX`:

```sql
CREATE INDEX idx_employee_dept ON Employee(department_id);
CREATE UNIQUE INDEX idx_employee_email ON Employee(email);
```

Indexes have a cost: every write updates every index. Don't
index every column "just in case". Index the columns you
filter or join on.

In SQLite, `CREATE INDEX IF NOT EXISTS` is supported. In
PostgreSQL: same. In MySQL: same. The "IF NOT EXISTS"
extension is universal.

---

## Views

A view is a named query. It looks like a table but doesn't
store data.

```sql
CREATE VIEW high_earners AS
SELECT id, name, salary, department_id
FROM   Employee
WHERE  salary > 100000;
```

You can `SELECT * FROM high_earners` like a table. The
query runs every time the view is referenced. Some
databases have *materialized views* that store the result;
SQLite and MySQL do not (you'd use a table for that).

---

## Schema design checklist

When designing a new table, ask:

1. What's the primary key? (Immutable, integer, narrow.)
2. What are the foreign keys?
3. Which columns are NOT NULL?
4. Which columns need an index?
5. Are there CHECK constraints (e.g. `salary >= 0`)?
6. What's the default for each column?

The `common/schema.py` module in this course wraps these
into a `Table` and `Column` dataclass so you can write
schemas in Python and dump them as DDL.

---

## Try it

1. Create a `Project(id, name, owner_id, budget, start_date,
   end_date)` table with appropriate constraints.
2. Add a `status` column with default `'active'`.
3. Drop the `end_date` column.
4. Drop the entire `Project` table.

Use `QueryRunner` so you can verify each step.
