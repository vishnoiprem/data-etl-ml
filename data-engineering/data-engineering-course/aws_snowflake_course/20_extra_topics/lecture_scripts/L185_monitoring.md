---
l_id: L185
title: Monitoring
duration: "5:00"
prereqs: ["L184"]
---

# L185 — Monitoring

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 7. Best Practices & Bonus
> **Duration:** 5:00

## Prereqs

L184 — Table design.

## Key terms

- **`QUERY_HISTORY`** — the canonical log of every
  query that ran.
- **`LOGIN_HISTORY`** — the canonical log of every
  login.
- **Resource monitor** — a Snowflake object that caps
  credit usage and triggers an action (suspend, notify).
- **`ACCESS_HISTORY`** — the canonical log of *which rows
  were read* by a query (PII auditing).

## Lecture

Welcome back. Today's lecture is the observability
playbook. By the end, you should know the four Snowflake
log tables and the three monitoring patterns every
production account needs.

### The four log tables

| Table | What it logs | Use for |
|---|---|---|
| `QUERY_HISTORY` | Every query | Performance, audit |
| `LOGIN_HISTORY` | Every login | Security, audit |
| `ACCESS_HISTORY` | Which rows/columns were read | PII audit |
| `TASK_HISTORY` | Every task run | Pipeline ops |

`QUERY_HISTORY` is the most useful. The columns you'll
filter on most often:

- `warehouse_name` — which warehouse ran the query.
- `user_name`, `role_name` — who ran it.
- `start_time`, `total_elapsed_time` — when and how long.
- `error_code`, `error_message` — what failed.

### A resource monitor

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE RESOURCE MONITOR monthly_cap
  WITH
    CREDIT_QUOTA = 1000
    FREQUENCY    = MONTHLY
    START_TIMESTAMP = IMMEDIATELY
    TRIGGERS
      ON 75 PERCENT DO NOTIFY
      ON 90 PERCENT DO SUSPEND_IMMEDIATE
      ON 100 PERCENT DO SUSPEND_IMMEDIATE;

ALTER ACCOUNT SET RESOURCE_MONITOR = monthly_cap;
```

This monitor caps the account at 1000 credits per month.
At 75% (750), it sends a notification. At 90% (900), it
suspends all warehouses. The "suspend" is the hard cap.

### A simple credit-by-warehouse report

```sql
SELECT warehouse_name,
       SUM(credits_used) AS credits
FROM   TABLE(INFORMATION_SCHEMA.METERING_HISTORY(
              DATE_RANGE_START => DATE_TRUNC('month', CURRENT_DATE()),
              DATE_RANGE_END   => CURRENT_DATE()))
WHERE  service_type = 'WAREHOUSE_METERING'
GROUP BY warehouse_name
ORDER BY credits DESC;
```

Run this weekly. If one warehouse is consistently using
50%+ of the credits, look at what's running on it.

### A slow-query report

```sql
SELECT query_text,
       warehouse_name,
       total_elapsed_time / 1000 AS seconds
FROM   TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE  start_time > DATEADD('day', -1, CURRENT_TIMESTAMP())
  AND  total_elapsed_time > 60000    -- > 1 minute
ORDER BY total_elapsed_time DESC
LIMIT 20;
```

Use this to find queries that need optimization or a
bigger warehouse.

### An ACCOUNTADMIN audit

```sql
SELECT user_name, role_name, query_text, start_time
FROM   TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE  role_name = 'ACCOUNTADMIN'
  AND  start_time > DATEADD('day', -7, CURRENT_TIMESTAMP())
ORDER BY start_time DESC;
```

A weekly review of `ACCOUNTADMIN` activity is a strong
security control.

### A failed-task alert

```sql
SELECT name, scheduled_time, error_code, error_message
FROM   TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE  state = 'FAILED'
  AND  scheduled_time > DATEADD('hour', -1, CURRENT_TIMESTAMP());
```

Run from a task every 15 minutes; pipe failures into
your alerting.

## Hands-on

```sql
-- Top 10 slowest queries in the last 24h
SELECT query_text, total_elapsed_time / 1000 AS seconds
FROM   TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE  start_time > DATEADD('hour', -24, CURRENT_TIMESTAMP())
ORDER BY total_elapsed_time DESC
LIMIT 10;
```

## Key takeaways

- Four log tables: `QUERY_HISTORY`, `LOGIN_HISTORY`,
  `ACCESS_HISTORY`, `TASK_HISTORY`.
- A resource monitor with a 75% notify, 90% suspend is
  the standard.
- Three weekly reports: credit by warehouse, slow
  queries, ACCOUNTADMIN activity.
- A failed-task alert is a 15-line task; run it every
  15 minutes.

## What's next

L186 — Retention period. The deeper dive on Time Travel
and Fail Safe retention.