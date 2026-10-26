# Lesson 19 — INSERT, UPDATE, DELETE

> **Goal:** write data. The DML (Data Manipulation Language)
> statements that round out the SQL toolkit.

---

## INSERT

Add one or more rows to a table.

### Single row

```sql
INSERT INTO Employee (id, name, salary, department_id)
VALUES (101, 'Alice', 90000, 3);
```

The column list is good practice — it makes the SQL
self-documenting and survives schema changes (adding a
nullable column won't break this INSERT).

### Multiple rows

```sql
INSERT INTO Employee (id, name, salary, department_id)
VALUES
  (102, 'Bob',   80000, 3),
  (103, 'Carol', 95000, 5),
  (104, 'Dan',   70000, 5);
```

### INSERT ... SELECT

Insert the result of a query:

```sql
INSERT INTO Employee_archive (id, name, salary, dept_id, archived_at)
SELECT id, name, salary, department_id, CURRENT_TIMESTAMP
FROM   Employee
WHERE  hire_date < '2020-01-01';
```

This is the standard "archive" pattern: copy some rows to
another table, optionally then delete them from the source.

### INSERT ... ON CONFLICT (upsert)

```sql
INSERT INTO Employee (id, name, salary)
VALUES (101, 'Alice', 90000)
ON CONFLICT (id) DO UPDATE
SET name = excluded.name,
    salary = excluded.salary;
```

If the row already exists (by primary key), update it.
Otherwise insert. PostgreSQL and SQLite support this
directly; MySQL has `INSERT ... ON DUPLICATE KEY UPDATE`
which is similar.

### REPLACE

`REPLACE INTO Employee (...) VALUES (...)` is a SQLite /
MySQL shortcut: delete the conflicting row, then insert.
This is dangerous because it triggers `ON DELETE` cascades.
Prefer `ON CONFLICT DO UPDATE`.

---

## UPDATE

Change existing rows.

```sql
UPDATE Employee
SET    salary = salary * 1.05
WHERE  department_id = 3;
```

The `WHERE` is critical. **Always include a WHERE clause.**
`UPDATE Employee SET salary = 0` updates every row in the
table. This is the #1 cause of "I just deleted the
production data" stories.

### UPDATE with a join

In MySQL and SQLite you can `UPDATE` joined tables:

```sql
UPDATE Employee
SET    salary = salary * 1.10
FROM   Department
WHERE  Employee.department_id = Department.id
  AND  Department.location = 'NY';
```

In PostgreSQL the syntax is `UPDATE ... FROM`:

```sql
UPDATE Employee e
SET    salary = salary * 1.10
FROM   Department d
WHERE  e.department_id = d.id
  AND  d.location = 'NY';
```

---

## DELETE

Remove rows.

```sql
DELETE FROM Employee
WHERE  department_id = 99;
```

Same warning: **always include a WHERE.** `DELETE FROM
Employee` with no WHERE removes every row.

### DELETE with a join

```sql
DELETE FROM Employee
WHERE  id IN (
  SELECT id FROM Employee WHERE hire_date < '2010-01-01'
);
```

Or, in MySQL/SQLite:

```sql
DELETE e FROM Employee e
JOIN   ArchiveBatch a ON e.id = a.employee_id
WHERE  a.batch_id = 7;
```

### TRUNCATE

`TRUNCATE TABLE Employee` removes every row, faster than
`DELETE FROM Employee` (no per-row triggers, no transaction
log per row). Most databases cannot `TRUNCATE` a table that
is referenced by a foreign key. SQLite does not support
`TRUNCATE` — use `DELETE FROM`.

---

## RETURNING (PostgreSQL, SQLite)

```sql
INSERT INTO Employee (name, salary)
VALUES ('Alice', 90000)
RETURNING id;
```

Returns the inserted row. Useful for getting the auto-generated
ID without a second query.

```sql
DELETE FROM Employee WHERE id = 101 RETURNING *;
```

---

## Transactions

DML statements are wrapped in transactions. The default is
"autocommit" — every statement is its own transaction. To
make multiple statements atomic:

```sql
BEGIN;
  UPDATE Account SET balance = balance - 100 WHERE id = 1;
  UPDATE Account SET balance = balance + 100 WHERE id = 2;
COMMIT;
-- or ROLLBACK; to undo
```

In a Python `QueryRunner`, every `execute()` commits
immediately. To start a transaction, use `q.conn.execute()`
and `q.conn.commit()` directly.

---

## Try it

Given `Customer(id, name, email, country)`:

1. Insert three new customers in a single statement.
2. Update every customer in `'US'` to have a `country` of
   `'USA'` (just to feel the difference).
3. Delete every customer whose `email` ends with
   `@example.com`. Use `LIKE`.

For each statement, run it in a transaction, verify the row
count, then ROLLBACK to leave the table clean.
