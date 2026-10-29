---
l_id: L118
title: Cloning schemas & databases
duration: "4:00"
prereqs: ["L117"]
---

# L118 — Cloning schemas & databases

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 17 — Zero-Copy Cloning
> **Duration:** 4:00

## Prereqs

L117 — Cloning tables. You should be comfortable with the table-level
syntax before extending it to larger containers.

## Key terms

- **Schema clone** — clones all tables, views, stages, file formats,
  sequences, pipes, and tasks inside a schema in one statement.
- **Database clone** — clones every schema inside a database, and
  therefore every object inside every schema.
- **Clone privileges** — you need `OWNERSHIP` on the source object
  *or* `CREATE <object> ... CLONE` privileges on the target.

## Lecture

Welcome back. If L117 made you think "I can clone a table in one
line", L118 is "you can clone an entire database in one line". The
syntax is identical, only the object type changes.

### Cloning a schema

```sql
CREATE SCHEMA prod_clone CLONE prod.public;
```

A schema clone captures:

- every table (permanent, transient, temporary? — only permanent and
  transient; temporary tables can't be cloned because they're
  session-scoped)
- views (regular and materialized — though materialized views may need
  re-grants)
- stages, file formats, sequences
- pipes, streams, tasks (with caveats — tasks are paused on the clone)

The clone is fully independent from the schema it was cloned from.
Mutations on either side don't affect the other.

### Cloning a database

```sql
CREATE DATABASE prod_clone CLONE prod;
```

A database clone is the largest unit Snowflake clones in one
statement. It is also one of the most common operations in
production: every morning, many teams run a single line like this to
create a point-in-time copy of their production database for dev
workloads.

```sql
-- Schedule this as a Snowflake task at 7am
CREATE DATABASE dev_clone CLONE prod;
```

The clone is *writable*. You can immediately start running
`UPDATE`/`DELETE`/`INSERT` statements against `dev_clone.public.*`
without ever touching `prod`.

### Privileges required

To clone an object you need either:

- `OWNERSHIP` on the source, **or**
- a global privilege such as `CREATE <object> ... CLONE` on the
  target container.

Forgetting this is the most common reason a clone statement fails
with an "insufficient privileges" error. As a rule of thumb, the role
that creates the clone should be `SYSADMIN` or a custom role modeled
after it.

### Caveats

- **Tasks**: cloned as **suspended**. Resuming them would mean both
  the source and clone try to run the same workload.
- **Streams**: cloned as **active**, but the offset is reset to
  "now". We'll cover this in section 20.
- **Materialized views**: cloned, but may need a manual refresh
  before serving queries efficiently.

## Hands-on

```sql
-- Build a small source db
CREATE OR REPLACE DATABASE SRC;
USE SCHEMA SRC.PUBLIC;

CREATE TABLE ORDERS    (id NUMBER);
CREATE TABLE CUSTOMERS (id NUMBER);
INSERT INTO ORDERS    VALUES (1), (2), (3);
INSERT INTO CUSTOMERS VALUES (10), (20);

-- Schema clone
CREATE SCHEMA SRC.RAW CLONE SRC.PUBLIC;
SELECT * FROM SRC.RAW.ORDERS;     -- same data

-- Database clone
CREATE DATABASE DST CLONE SRC;
SELECT * FROM DST.PUBLIC.ORDERS;  -- same data
```

## Key takeaways

- `CREATE SCHEMA x CLONE y;` clones every supported object in the
  schema in one statement.
- `CREATE DATABASE x CLONE y;` clones every schema in the database.
- Cloned tasks are paused; cloned streams reset to "now".
- You need `OWNERSHIP` on the source, or the appropriate
  `CREATE ... CLONE` privilege.

## What's next

L119 combines clone with **time travel** — clone *and* pick the
historical moment to fork at, in a single statement.