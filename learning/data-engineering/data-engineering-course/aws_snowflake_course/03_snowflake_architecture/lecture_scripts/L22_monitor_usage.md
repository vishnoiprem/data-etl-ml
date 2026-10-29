---
l_id: L22
title: Monitor usage
duration: "8:00"
prereqs: ["L21"]
downloads: []
---

# L22 — Monitor Usage

> **Author:** Prem Vishnoi <pvishnoi@avishnoi@avilx.com>
> **Section:** 3 — Snowflake Architecture
> **Duration:** ~8:00

## Prereqs

L21 — Data storage & transfer cost. This lecture covers
operational monitoring.

## Key terms

- **`ACCOUNT_USAGE` schema** — the historical metadata
  schema, in the `SNOWFLAKE` database. Retention: 1 year.
- **`ORGANIZATION_USAGE` schema** — same, but for the
  organization (multi-account deployments).
- **`READER_ACCOUNT_USAGE`** — usage from reader accounts
  (consumers of shares).
- **Latency** — `ACCOUNT_USAGE` views have up to **3 hours**
  of latency. For real-time, use `INFORMATION_SCHEMA` or the
  UI.

## Lecture

Snowflake exposes a rich set of metadata views in the
`ACCOUNT_USAGE` schema. They are the operational telemetry
you'll use to monitor cost, performance, and usage. This
lecture walks through the most useful views.

### `ACCOUNT_USAGE` vs `INFORMATION_SCHEMA`

Two parallel metadata surfaces:

| Aspect | `ACCOUNT_USAGE` | `INFORMATION_SCHEMA` |
|---|---|---|
| Retention | 1 year | 7 days |
| Latency | Up to 3 hours | Real-time |
| Scope | Whole account | Current database |
| Use case | Reporting, dashboards | Operational checks |

For monitoring dashboards, use `ACCOUNT_USAGE`. For "is this
table created yet?" checks, use `INFORMATION_SCHEMA`.

### The most useful views

**Compute / cost**

```sql
-- Per-warehouse credit usage
SELECT warehouse_name,
       DATE_TRUNC('day', start_time) AS day,
       SUM(credits_used) AS credits
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY 1, 2
ORDER BY day DESC, credits DESC;
```

**Query performance**

```sql
-- Top 20 longest queries in the last 24h
SELECT query_id, user_name, warehouse_name,
       total_elapsed_time / 1000 AS seconds,
       bytes_scanned / 1024 / 1024 AS mb_scanned
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE start_time >= DATEADD('hour', -24, CURRENT_TIMESTAMP())
ORDER BY total_elapsed_time DESC
LIMIT 20;
```

**Storage**

```sql
SELECT usage_date,
       database_name,
       average_database_bytes / 1024 / 1024 / 1024 AS gb
FROM SNOWFLAKE.ACCOUNT_USAGE.DATABASE_STORAGE_USAGE_HISTORY
ORDER BY usage_date DESC, database_name;
```

**Login / security**

```sql
-- Failed logins
SELECT user_name, event_timestamp, error_message
FROM SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY
WHERE event_timestamp >= DATEADD('day', -7, CURRENT_TIMESTAMP())
  AND event_type = 'LOGIN'
  AND is_success = 'NO'
ORDER BY event_timestamp DESC;
```

**Data transfer**

```sql
SELECT usage_date,
       source_cloud,
       target_cloud,
       source_region,
       target_region,
       bytes_transferred / 1024 / 1024 / 1024 AS gb
FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_TRANSFER_HISTORY
ORDER BY usage_date DESC;
```

### Building a cost dashboard

A common pattern is to build a daily cost dashboard in
Snowflake itself:

```sql
CREATE OR REPLACE VIEW DEMO.ANALYTICS.V_COST_DAILY AS
SELECT
  DATE_TRUNC('day', start_time)::DATE AS day,
  warehouse_name,
  SUM(credits_used) AS compute_credits
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD('day', -365, CURRENT_TIMESTAMP())
GROUP BY 1, 2;
```

Connect Power BI, Tableau, or Streamlit to the view to
visualize.

### Required privileges

By default, only the `ACCOUNTADMIN` role can query
`ACCOUNT_USAGE`. To grant access to other roles:

```sql
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE ANALYST;
```

The `IMPORTED PRIVILEGES` is a Snowflake-specific grant
type for shared databases.

## Hands-on

```sql
-- Show the top 5 most expensive warehouses in the last 7 days
USE ROLE ACCOUNTADMIN;

SELECT warehouse_name,
       SUM(credits_used) AS credits_7d,
       SUM(credits_used) * 3 AS approx_cost_usd
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD('day', -7, CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY credits_7d DESC
LIMIT 5;
```

## Quiz prep

- What is the retention of `ACCOUNT_USAGE` views? (1 year)
- What is the latency of `ACCOUNT_USAGE` views? (Up to 3
  hours)
- How do you grant a role access to query
  `ACCOUNT_USAGE`? (`GRANT IMPORTED PRIVILEGES ON DATABASE
  SNOWFLAKE TO ROLE <role>`)

## What's next

Next up is **L23 — Resource Monitors + Setting Up**, the
last lecture in section 3, where we set credit caps to
prevent runaway bills.
