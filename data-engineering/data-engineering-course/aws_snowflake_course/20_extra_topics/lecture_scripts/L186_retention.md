---
l_id: L186
title: Retention period
duration: "4:30"
prereqs: ["L185"]
---

# L186 — Retention period

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 7. Best Practices & Bonus
> **Duration:** 4:30

## Prereqs

L185 — Monitoring.

## Key terms

- **`DATA_RETENTION_TIME_IN_DAYS`** — the parameter that
  controls Time Travel length.
- **Default 1** — Snowflake's default for new accounts.
- **Max 90** — Enterprise Edition max for permanent
  tables; 1 for transient.

## Lecture

Welcome back. Today's lecture is the retention playbook.
By the end, you should be able to set the right retention
for every table in your account, balancing the cost of
storage against the value of historical access.

### The retention hierarchy

```text
Account level (default 1 day)
   ↓
   Database level (overrides account)
   ↓
   Schema level (overrides database)
   ↓
   Table level (overrides schema)
```

The most specific setting wins, bounded by the parent.
If the account is set to 1, no table can exceed 1.

### Set the right value

```sql
-- Account-wide default
ALTER ACCOUNT SET DATA_RETENTION_TIME_IN_DAYS = 1;

-- A specific table that needs longer
ALTER TABLE finance.audit.transactions
  SET DATA_RETENTION_TIME_IN_DAYS = 90;
```

The 1-day default is appropriate for most tables. Raise
retention for:

- **Audit logs** (90 days is a typical compliance
  requirement).
- **Financial close** tables (the last 30 days might be
  needed for re-runs).
- **Regulated data** (PII may have explicit retention
  rules).

### The cost trade-off

A higher retention costs more in storage. The numbers:

- 1-day retention ≈ 5% of the active table size.
- 7-day retention ≈ 15% of the active table size.
- 90-day retention ≈ 30% of the active table size.

(These are rough averages for tables with continuous
mutation. Tables that are mostly read have lower Time
Travel cost.)

### The transient override

A transient table caps at 1 day even on Enterprise:

```sql
ALTER TABLE staging.events SET DATA_RETENTION_TIME_IN_DAYS = 7;
-- ERROR: transient tables cap at 1 day
```

The cap is intentional. If you need longer retention,
the table should be permanent.

### Operational pattern: the "audit-table" layout

In a regulated account, a common pattern:

```sql
-- Audit: 90 days
ALTER TABLE audit.events SET DATA_RETENTION_TIME_IN_DAYS = 90;

-- Production: 7 days
ALTER TABLE prod.orders  SET DATA_RETENTION_TIME_IN_DAYS = 7;

-- Staging: 1 day (transient)
ALTER TABLE staging.raw_orders SET DATA_RETENTION_TIME_IN_DAYS = 1;

-- Everything else: account default (1 day)
```

The 90-day audit table is a small fraction of the total
storage; the rest of the account stays cheap.

### Inspecting retention

```sql
SHOW TABLES IN SCHEMA prod.public;
-- The "retention_time" column shows the effective value.

-- Per-table
SELECT table_name, retention_time
FROM   TABLE(INFORMATION_SCHEMA.TABLES(...))
WHERE  table_schema = 'PUBLIC';
```

### The cost of `UNDROP`

`UNDROP` works within the retention period. If a table
is dropped at day 5 and retention is 1, `UNDROP` fails
("data not recoverable"). Plan retention around the
`UNDROP` window you need.

## Hands-on

```sql
-- Inspect the retention for one schema
SHOW TABLES IN SCHEMA prod.public;

-- Set retention for an audit table
ALTER TABLE prod.audit.events
  SET DATA_RETENTION_TIME_IN_DAYS = 90;
```

## Key takeaways

- Default retention is 1 day. Raise selectively for
  audit / regulated / financial data.
- The cost scales with retention; 90 days is ~30% of
  the active table size.
- Transient tables cap at 1 day; promote to permanent
  for longer.
- Always inspect `retention_time` on critical tables.

## What's next

L187 — Bonus lecture. The course wrap-up.