---
l_id: L109
title: Retention time
duration: "8:00"
prereqs: ["L108 - UNDROP tables"]
---

# L109 — Retention time

> **Author:** Prem Vishnoi &lt;pvishnoi&commat;avilx.com&gt;
> **Section:** 14 — Time Travel
> **Duration:** 8:00

## Prereqs

`ACCOUNTADMIN` (or a role with the `MODIFY` privilege on
warehouses/databases). A table you can experiment on.

## Lecture

`DATA_RETENTION_TIME_IN_DAYS` is the dial that controls how far
back Time Travel can see. Default is 1 day; Enterprise and above
let you push to 90. Tune it to match your recovery SLA — but be
aware that every extra day is real storage cost.

### Where the parameter lives

Four scopes:

| Scope | What it sets |
|---|---|
| **Account** | Default for new objects. |
| **Database** | Default for new objects in the database. |
| **Schema** | Default for new objects in the schema. |
| **Table** | The actual retention for that table. |

The most-specific setting wins. So you can set account-level
"1 day" for cost, and override to "30 days" on the finance
schema where audit is critical.

### Set at the account level

```sql
ALTER ACCOUNT SET DATA_RETENTION_TIME_IN_DAYS = 1;
```

Standard edition is locked at 1. Enterprise and above can go up
to 90.

### Set at the database / schema level

```sql
ALTER DATABASE finance SET DATA_RETENTION_TIME_IN_DAYS = 30;
ALTER SCHEMA finance.audit SET DATA_RETENTION_TIME_IN_DAYS = 90;
```

### Set at the table level

```sql
ALTER TABLE finance.audit.transactions
  SET DATA_RETENTION_TIME_IN_DAYS = 90;
```

### Inspect current retention

```sql
SHOW TABLES IN SCHEMA finance.audit;
-- Look for the retention column

-- Or programmatically
SELECT table_name,
       retention_days,
       created,
       COMMENT
FROM INFORMATION_SCHEMA.TABLES
WHERE table_schema = 'AUDIT';
```

### Cost: how much does 30 vs 90 cost?

Every historical version is stored in micro-partitions. Tune the
parameter; check the bill:

```sql
SELECT table_name,
       active_bytes,
       time_travel_bytes,
       failsafe_bytes,
       (time_travel_bytes + failsafe_bytes) AS historical_bytes
FROM TABLE(INFORMATION_SCHEMA.TABLE_STORAGE_METRICS(
  TABLE_NAME => 'finance.audit.transactions'
));
```

A common rule of thumb:

- **Hot tables** (small, high write rate): Time Travel cost
  approaches 0 because the historical partitions roll off
  quickly.
- **Cold tables** (large, low write rate): Time Travel cost can
  exceed the active storage cost, especially with 90-day
  retention on a terabyte-scale fact table.

### Transient and temporary tables

- **Transient tables** have `DATA_RETENTION_TIME_IN_DAYS = 1`
  and **no Fail Safe** (section 15). Use them for staging.
- **Temporary tables** are scoped to the session and have no
  retention at all. (Covered in section 16.)

### Decision framework

| Need | Recommended retention |
|---|---|
| Dev / sandbox | 0 (transient) |
| Production staging | 1 (default) |
| Production core | 7 |
| Regulated / audit | 30–90 |

When in doubt, start with the default (1) and bump only the
tables that need it.

## Key takeaways

- `DATA_RETENTION_TIME_IN_DAYS` is settable at account, database,
  schema, and table scopes. Most-specific wins.
- Time Travel storage shows up as `time_travel_bytes` in
  `TABLE_STORAGE_METRICS`.
- Transient and temporary tables give you cheaper, shorter
  retention — covered in section 16.

## What's next

In **L110 — Time travel cost** we look at the bill side: how to
estimate the cost of retention, and how to keep it from
ballooning.
