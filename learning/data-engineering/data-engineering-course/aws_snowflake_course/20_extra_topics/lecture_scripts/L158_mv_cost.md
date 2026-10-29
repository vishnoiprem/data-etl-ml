---
l_id: L158
title: Maintenance costs
duration: "4:30"
prereqs: ["L157"]
---

# L158 — Maintenance costs

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 3. Materialized Views
> **Duration:** 4:30

## Prereqs

L157 — Refresh materialized views.

## Key terms

- **Compute cost** — the warehouse time Snowflake spends on
  automatic refreshes.
- **Storage cost** — the bytes the MV result occupies on disk.
- **Read savings** — the warehouse time you save on `SELECT`
  queries that hit the MV instead of the source.
- **Net cost** — `maintenance - read_savings`. The bottom line.

## Lecture

Welcome back. Today's lecture is the financial model of a
materialized view. By the end, you'll know exactly when an MV
pays for itself and when it doesn't.

### The cost components

A materialized view has three cost components:

1. **Compute (maintenance).** Every time the source changes,
   Snowflake spends warehouse time to refresh the MV. This is
   billed against your account's credit pool.
2. **Storage.** The MV stores its precomputed result on disk.
   This is billed at the standard on-demand rate.
3. **Read savings.** Every `SELECT` against the MV is faster
   than against the source, so you spend less on read compute.

The **net cost** is `maintenance + storage - read_savings`. If
this is positive, the MV is *costing* you money. If negative,
it's *saving* you money.

### Reading the cost from `METERING`

```sql
SELECT *
FROM   TABLE(INFORMATION_SCHEMA.METERING_HISTORY())
WHERE  service_type = 'MATERIALIZED_VIEW_REFRESH'
ORDER BY start_time DESC
LIMIT 100;
```

The `credits_used` column shows the credit cost of refresh
operations. Multiply by your credit price to get dollars.

### Reading the cost from `TABLE_STORAGE_METRICS`

```sql
SELECT  table_name,
        active_bytes,
        time_travel_bytes
FROM    TABLE(INFORMATION_SCHEMA.TABLE_STORAGE_METRICS(
            TABLE_NAME => 'MV_REGION_TOTALS'));
```

The MV's `active_bytes` is the storage cost.

### When the math works

A common rule of thumb: **if the source is queried 10× more
than it changes, an MV is usually a win**.

| Source changes per day | Reads per day | MV worth it? |
|---|---|---|
| 1,000 | 10 | No (read savings tiny) |
| 1,000 | 100,000 | Yes |
| 1,000,000 | 100,000 | No (refresh cost dominates) |
| 1,000,000 | 10,000,000 | Maybe — measure |

The metric to watch is *read savings* vs *refresh cost*. If
both are large, the net could be near zero; if reads dominate,
the MV is a clear win.

### The biggest cost driver

The single biggest cost driver for MVs is **source churn**.
A table that changes 1M times per day will spend a lot on
refreshes, even if the MV is small. The mitigation:

- **Filter the MV's `WHERE` clause** to a smaller slice of the
  source.
- **Use a streaming pipeline** for very high-churn sources.
- **Use multiple smaller MVs** instead of one large one — Snowflake
  refreshes incrementally; smaller MVs are cheaper to maintain.

## Hands-on

```sql
-- Inspect the cost of an MV you created earlier
SELECT * FROM TABLE(INFORMATION_SCHEMA.METERING_HISTORY())
WHERE  service_type = 'MATERIALIZED_VIEW_REFRESH'
ORDER BY start_time DESC
LIMIT 10;

SELECT table_name, active_bytes
FROM   TABLE(INFORMATION_SCHEMA.TABLE_STORAGE_METRICS(
           TABLE_NAME => 'MV_SRC'));
```

## Key takeaways

- A materialized view has compute, storage, and read-savings
  costs.
- Use `METERING_HISTORY` to read the compute cost.
- Use `TABLE_STORAGE_METRICS` to read the storage cost.
- If source churn dominates, MVs lose; consider a pipeline.

## What's next

L159 — When to use materialized views. The decision rules for
when an MV is the right tool.