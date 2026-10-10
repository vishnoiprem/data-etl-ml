---
l_id: L113
title: Different table types
duration: "4:00"
prereqs: ["L112"]
---

# L113 — Different table types

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 16 — Types of tables
> **Duration:** 4:00

## Prereqs

L112 — Fail Safe storage. You need to know the *why* before this
lecture's *what*.

## Key terms

- **Permanent table** — default Snowflake table. Time Travel +
  Fail Safe. For production data.
- **Transient table** — Time Travel only, max 1 day (Enterprise).
  No Fail Safe. For staging / ETL scratch.
- **Temporary table** — session-scoped, dropped at session end.
  No Fail Safe. For ad-hoc work.
- **Retention period** — the number of days Time Travel is active
  before data moves to Fail Safe (permanent) or is deleted
  (transient / temporary).

## Lecture

Welcome back. The whole reason we spent the last two lectures on
Time Travel and Fail Safe was so this one could fit on a single slide.
Here is the entire decision you need to make for every table you
create:

```text
                  Time Travel   Fail Safe   Lifetime
                  -----------   --------   ---------
 Permanent          1–90 days     YES       Persistent
 Transient        ≤ 1 day         NO        Persistent
 Temporary        ≤ 1 day         NO        Session
```

That table is the section. If you memorize it, you can answer almost
every "which table type should I use?" question you'll be asked for
the rest of the course.

### Permanent

The default. When you write `CREATE TABLE foo (...)` you get a
permanent table. Snowflake gives you the full safety net: the Time
Travel retention you configure (up to 90 days on Enterprise), plus
the 7-day Fail Safe window after that. The trade-off is storage cost
— every byte in Time Travel and Fail Safe is billed at the standard
on-demand rate.

### Transient

A permanent table without Fail Safe. Time Travel still works, but it
caps at **1 day on Enterprise** and **0 days on Standard**. After
that, historical versions are *deleted*, not moved. Transient tables
are perfect for ETL staging, dev/test sandboxes, and any data that
can be cheaply rebuilt from source.

### Temporary

A transient table with an even shorter life. Temporary tables are
**bound to the session** that created them — log out (or end the
worksheet session) and the table is gone. They show up nowhere in
your schema, and Snowflake gives them 0–1 day of Time Travel, no
Fail Safe. Use them for one-off queries, data exploration, and
exploratory joins you don't want to commit to disk.

### The decision rule

A simple mental model: ask "if this table is corrupted tomorrow, how
painful is it to rebuild?"

- **Painful** (production fact tables, audit logs, financial data) → permanent.
- **Annoying but cheap** (ELT staging, vendor drop zones) → transient.
- **Trivial** (one-shot exploration, scratch joins) → temporary.

## Hands-on

```sql
-- Three tables, three types
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE TABLE PERM_TEST  (id NUMBER);  -- permanent
CREATE OR REPLACE TRANSIENT TABLE TRAN_TEST (id NUMBER);
CREATE OR REPLACE TEMPORARY TABLE TEMP_TEST (id NUMBER);

-- Show what you got
SHOW TABLES IN SCHEMA DEMO_DB.PUBLIC;
-- The "kind" column reads: PERMANENT, TRANSIENT, TEMPORARY
```

## Key takeaways

- Three table types: **permanent, transient, temporary**.
- Only permanent tables go to Fail Safe.
- Transient and temporary cap Time Travel at 1 day max.
- Temporary tables are session-scoped; transient and permanent are not.

## What's next

L114 zooms in on **permanent tables and databases** — the default
you'll reach for 90% of the time.
