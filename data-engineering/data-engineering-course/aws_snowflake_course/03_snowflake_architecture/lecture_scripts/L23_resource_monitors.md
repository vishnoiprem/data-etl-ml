---
l_id: L23
title: Resource monitors + setting up
duration: "8:00"
prereqs: ["L22"]
downloads: []
---

# L23 — Resource Monitors + Setting Up

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 3 — Snowflake Architecture
> **Duration:** ~8:00

## Prereqs

L22 — Monitor usage. This lecture covers resource monitors —
the credit-cap system in Snowflake.

## Key terms

- **Resource monitor** — a Snowflake object that caps the
  credits a warehouse (or set of warehouses) can consume over
  a period.
- **Credit quota** — the maximum credits the monitor allows.
- **Trigger thresholds** — percentages at which the monitor
  notifies or suspends. Typical: 50% notify, 75% notify,
  100% suspend.
- **Notify / suspend / suspend immediately** — the action
  the monitor takes at each threshold.

## Lecture

A **resource monitor** is Snowflake's built-in cost guard. It
caps how many credits a warehouse (or set of warehouses) can
consume over a period and triggers actions at thresholds. This
is the single most important cost-control object you'll set up
in a production account.

### Anatomy of a resource monitor

```sql
CREATE RESOURCE MONITOR monthly_cap
  WITH CREDIT_QUOTA = 1000           -- max credits per period
       FREQUENCY       = 'MONTHLY'  -- reset period
       START_TIMESTAMP = '2024-01-01 00:00 UTC'
       TRIGGERS
         ON 50 PERCENT DO NOTIFY
         ON 75 PERCENT DO NOTIFY
         ON 100 PERCENT DO SUSPEND;
```

Components:

- **Credit quota** — total credits allowed per period.
- **Frequency** — `MONTHLY`, `WEEKLY`, `DAILY`, `YEARLY`, or
  `NEVER` (monitor but never reset).
- **Start timestamp** — when the first period begins.
- **Triggers** — actions at 1–100% thresholds. Available
  actions:
  - `NOTIFY` — sends an email to all users with the
    `MONITOR` privilege on the warehouse.
  - `SUSPEND` — suspends the warehouse (queries in flight
    complete; new ones fail).
  - `SUSPEND_IMMEDIATE` — aborts all queries and suspends.

### Attaching to a warehouse

```sql
ALTER WAREHOUSE LOADING_WH SET RESOURCE_MONITOR = 'monthly_cap';
```

A monitor can be attached to:

- A **single warehouse** — caps only that warehouse.
- **Multiple warehouses** — caps the total. Useful for
  account-level caps.

### Attaching to the account

```sql
ALTER ACCOUNT SET RESOURCE_MONITOR = 'account_cap';
```

> The account-level monitor caps total account consumption
> across all warehouses. This is the highest-priority
> safety net.

### Setting up a starter set of monitors

For a small production account, a reasonable starting setup:

```sql
-- Account-level cap: $10,000 / month
CREATE RESOURCE MONITOR account_cap
  WITH CREDIT_QUOTA = 3300       -- ~$10K at $3/credit
       FREQUENCY = 'MONTHLY'
       START_TIMESTAMP = '2024-01-01 00:00 UTC'
       TRIGGERS
         ON 50 PERCENT DO NOTIFY
         ON 80 PERCENT DO NOTIFY
         ON 100 PERCENT DO SUSPEND;

-- ETL warehouse cap: $5,000 / month
CREATE RESOURCE MONITOR etl_cap
  WITH CREDIT_QUOTA = 1700
       FREQUENCY = 'MONTHLY'
       START_TIMESTAMP = '2024-01-01 00:00 UTC'
       TRIGGERS
         ON 75 PERCENT DO NOTIFY
         ON 100 PERCENT DO SUSPEND;

ALTER ACCOUNT SET RESOURCE_MONITOR = 'account_cap';
ALTER WAREHOUSE LOADING_WH SET RESOURCE_MONITOR = 'etl_cap';
```

### Inspecting monitors

```sql
SHOW RESOURCE MONITORS;
```

The `SHOW` output includes the credit quota, frequency, and
attached warehouses.

### Modifying a monitor

```sql
ALTER RESOURCE MONITOR etl_cap SET CREDIT_QUOTA = 2000;
ALTER RESOURCE MONITOR etl_cap ADD TRIGGER ON 90 PERCENT DO NOTIFY;
```

### Common patterns

| Pattern | Threshold setup |
|---|---|
| Conservative | 50% notify, 75% notify, 90% suspend |
| Standard | 75% notify, 100% suspend |
| Aggressive | 50% suspend |
| Monitor-only (no cap) | 50% notify, 100% notify, no suspend |

### Dropping a monitor

```sql
DROP RESOURCE MONITOR etl_cap;
```

Dropping a monitor detaches it from all warehouses.

## Hands-on

```sql
USE ROLE ACCOUNTADMIN;

-- Create and attach
CREATE RESOURCE MONITOR demo_cap
  WITH CREDIT_QUOTA = 50
       FREQUENCY = 'MONTHLY'
       START_TIMESTAMP = '2024-01-01 00:00 UTC'
       TRIGGERS
         ON 50 PERCENT DO NOTIFY
         ON 100 PERCENT DO SUSPEND;

ALTER WAREHOUSE ANALYST_WH SET RESOURCE_MONITOR = 'demo_cap';

-- Inspect
SHOW RESOURCE MONITORS;
```

## Quiz prep

- What is the difference between `SUSPEND` and
  `SUSPEND_IMMEDIATE`? (SUSPEND lets in-flight queries
  finish; SUSPEND_IMMEDIATE aborts them)
- How do you set an account-level cap? (`ALTER ACCOUNT
  SET RESOURCE_MONITOR = '<name>'`)
- What frequency options are available for resource
  monitors? (MONTHLY, WEEKLY, DAILY, YEARLY, NEVER)

## Key takeaways

- **Resource monitors** cap credit consumption and trigger
  actions at thresholds.
- Three actions: `NOTIFY` (email), `SUSPEND` (graceful),
  `SUSPEND_IMMEDIATE` (hard).
- Always set an **account-level monitor** as a final
  safety net.
- Always set **per-warehouse monitors** for high-cost
  warehouses (ETL).

## What's next

Next up is **L24 — Roles in Snowflake**, the first lecture
in section 4. We shift from architecture to the access
control model and start loading data.
