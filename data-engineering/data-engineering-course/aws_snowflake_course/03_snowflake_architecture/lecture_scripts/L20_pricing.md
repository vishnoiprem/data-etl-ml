---
l_id: L20
title: Snowflake pricing
duration: "9:00"
prereqs: ["L19"]
downloads: []
---

# L20 — Snowflake Pricing

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 3 — Snowflake Architecture
> **Duration:** ~9:00

## Prereqs

L19 — Snowflake editions. This lecture breaks down the credit
model and per-second billing.

## Key terms

- **Credit** — Snowflake's unit of compute. 1 credit = 1 hour
  of an X-Small warehouse. Larger warehouses consume credits
  proportionally.
- **Per-second billing** — warehouses bill per second while
  running, with a 60-second minimum.
- **Storage** — billed per average compressed TB per month.
- **Cloud services** — billed per credit when monthly cloud
  services usage exceeds 10% of the corresponding warehouse
  compute. In practice, services are usually free.

## Lecture

Snowflake's pricing model has two main cost drivers —
**compute** (warehouse credits) and **storage** (per-TB) — plus
a small cloud services component. This lecture breaks down each
so you can model your monthly bill.

### The credit model

A **credit** is the unit of compute. 1 credit = 1 hour of an
X-Small warehouse running.

| Warehouse size | Credits per hour | Per credit × size |
|---|---|---|
| X-Small | 1 | 1× |
| Small | 2 | 2× |
| Medium | 4 | 4× |
| Large | 8 | 8× |
| X-Large | 16 | 16× |
| 2X-Large | 32 | 32× |
| 3X-Large | 64 | 64× |
| 4X-Large | 128 | 128× |

Each step doubles the credit cost. A 4X-Large running for 1
hour costs 128 credits.

### Per-second billing

Warehouses bill per second while running, with a **60-second
minimum**. A query that takes 8 seconds on an X-Small bills:

```text
60 seconds × (1 credit / 3600 seconds) ≈ 0.0167 credits
```

The 60-second minimum exists because spinning up a cluster has
a fixed cost. After the first minute, billing is precisely
proportional to the time the warehouse is active.

### Auto-suspend — why it matters

Without auto-suspend, a warehouse left running overnight
consumes credits continuously. Auto-suspend at 60 seconds means
a warehouse that finishes a query at 17:01:00 suspends by
17:02:00 — you pay for 1 minute of idle time, not 14 hours.

> **Rule.** Always set `AUTO_SUSPEND` to a non-null value. The
> default is 60s; many production setups use 60–300s.

### Storage pricing

Storage is billed per **average compressed TB per month**.
Pricing varies by region and edition but is in the cents-per-GB
range.

For example (Standard edition, US regions):

- On-demand: ~$23 / compressed TB / month
- Capacity (pre-purchased): ~$40 / TB / month upfront discount

The compression is significant: Snowflake typically achieves
5–10× compression on structured data, so a 1 TB raw CSV
becomes 100–200 GB stored. Your bill is on the **stored** size,
not the raw size.

### Cloud services

Cloud services are billed per credit, but **only when monthly
cloud services usage exceeds 10% of the corresponding warehouse
compute**. In practice, services are usually under 10% and
therefore free.

If you generate huge amounts of metadata churn (DDL every
minute, for example), the 10% threshold can be exceeded and
you'll see services charges. This is rare.

### Modelling a monthly bill

Example: a small analytics team.

```text
Workload:
  - ETL:        Large warehouse, 4 hours/day, 22 days/month
                = 8 credits/hour × 4 hours × 22 = 704 credits
  - Reporting:  Small warehouse, 8 hours/day, 22 days/month
                = 2 credits/hour × 8 hours × 22 = 352 credits
  - Ad-hoc:     X-Small, 4 hours/day, 22 days/month
                = 1 credit/hour × 4 hours × 22 = 88 credits

Total compute: 1,144 credits/month
At $3/credit (Enterprise): $3,432 / month

Storage: 5 TB compressed × $23 = $115 / month

Cloud services: $0 (under 10%)

Total: ~$3,547 / month
```

### Capacity vs on-demand

Snowflake offers two payment options:

- **On-demand** — pay-as-you-go, monthly billing. Higher per-
  credit price. Good for unpredictable workloads.
- **Capacity** — pre-purchase credits at a discount (typically
  20–30% off). Good for predictable workloads.

Most production accounts use a mix: capacity for baseline
usage, on-demand for spikes.

## Hands-on

```sql
-- Estimate your own warehouse usage
SELECT warehouse_name,
       SUM(credits_used) AS credits_30d
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY credits_30d DESC;

-- Storage usage
SELECT usage_date,
       average_database_bytes / 1024 / 1024 / 1024 AS avg_gb
FROM SNOWFLAKE.ACCOUNT_USAGE.DATABASE_STORAGE_USAGE_HISTORY
ORDER BY usage_date DESC
LIMIT 30;
```

## Quiz prep

- What is 1 credit equivalent to? (1 hour of an X-Small
  warehouse)
- What is the per-second billing minimum? (60 seconds)
- When are cloud services billed? (Only when monthly
  services usage exceeds 10% of corresponding warehouse
  compute)

## What's next

Next up is **L21 — Data Storage & Transfer Cost**, where we
drill into storage billing and cross-region/cloud transfer
costs.
