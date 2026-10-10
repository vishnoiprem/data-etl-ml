---
l_id: L53
title: "Create dedicated virtual warehouse"
duration: "6:00"
prereqs:
  - L52 (Performance Considerations in Snowflake)
---

# L53 — Create dedicated virtual warehouse

> **Section:** 7 — Performance optimization
> **Duration:** 6:00

## Prereqs

- L52 — Performance Considerations in Snowflake

## Key terms

- **Dedicated warehouse** — a warehouse reserved for one
  workload (loading, BI, ML, ELT) so it can't be starved by
  another workload on the same warehouse.
- **Resource monitor** — a budget cap that sends alerts and can
  suspend a warehouse when credit spend hits a threshold.
- **Auto-suspend / auto-resume** — turns the warehouse off when
  idle and back on when a query arrives. The single biggest
  cost-saving feature.
- **Statement timeout** — caps the wall-clock time of a single
  statement; useful for BI warehouses to avoid runaway scans.

## Lecture

The most common production mistake in Snowflake is **one
warehouse for everything**. A single `COMPUTE_WH` ends up
loading 50 GB at 2 AM, serving a dashboard at 9 AM, and running
an ad-hoc analyst query at 2 PM. The load and the dashboard
fight for the same resources; one of them waits. The fix is
**dedicated warehouses** — one per workload.

### The four warehouses we'll create

For our course pipeline we need four:

| Warehouse | Workload | Size | Auto-suspend |
|---|---|---|---|
| `loading_wh` | `COPY INTO`, ELT | Medium | 60 s |
| `transform_wh` | dbt, materialized views | Large | 60 s |
| `bi_wh` | dashboards, ad-hoc | Small | 60 s |
| `admin_wh` | user tasks, monitoring | X-Small | 60 s |

Two observations:

- **Loading wants a bigger warehouse** — `COPY INTO` benefits
  from parallelism and the time saving dwarfs the credit cost.
- **BI wants a smaller, snappy warehouse** — dashboards ask many
  small questions; the per-second cost matters.

### The `CREATE WAREHOUSE` template

```sql
CREATE OR REPLACE WAREHOUSE loading_wh
    WITH
        WAREHOUSE_SIZE       = 'MEDIUM'
        AUTO_SUSPEND         = 60
        AUTO_RESUME          = TRUE
        INITIALLY_SUSPENDED  = TRUE
        MIN_CLUSTER_COUNT    = 1
        MAX_CLUSTER_COUNT    = 1
        SCALING_POLICY       = 'STANDARD'
        RESOURCE_MONITOR     = monthly_budget;
```

`RESOURCE_MONITOR = monthly_budget` is optional but **strongly
recommended** — we'll cover it in L54.

### Auto-suspend — the single biggest cost saver

Every idle warehouse bills credits. `AUTO_SUSPEND = 60` means
"turn off after 60 seconds of no activity". You'll barely
notice the resume latency on the next query; you'll notice the
credit bill.

| AUTO_SUSPEND | Idle cost / hour |
|---|---|
| 600 s (10 min, default) | bills for the full 10 min |
| 60 s | bills for 1 min on average |
| 10 s | bills for 10 s on average |

For a 5-person team running BI queries 8 hours a day, dropping
`AUTO_SUSPEND` from 600 to 60 saves roughly **80% of idle cost**.

### Auto-resume

`AUTO_RESUME = TRUE` means Snowflake spins the warehouse back up
the moment a query arrives. There is no manual step. Combine
this with `INITIALLY_SUSPENDED = TRUE` and a fresh warehouse
doesn't bill anything until the first query.

### Scaling policy

`SCALING_POLICY = 'STANDARD'` (default) keeps a single cluster
sized for the average workload. `'ECONOMY'` favours cost over
latency (waits longer before adding a cluster). `'AGGRESSIVE'`
favours latency over cost (adds clusters immediately when the
queue grows). We use `STANDARD` in this course.

### Resource monitor

```sql
CREATE OR REPLACE RESOURCE_MONITOR monthly_budget
    WITH
        CREDIT_QUOTA = 100           -- 100 credits per month
        FREQUENCY    = MONTHLY
        START_TIMESTAMP = IMMEDIATELY
        NOTIFY_USERS = (ACCOUNTADMIN);
```

Then:

```sql
ALTER WAREHOUSE loading_wh SET RESOURCE_MONITOR = monthly_budget;
```

A resource monitor at 100% sends a notification; at 110% it
suspends the warehouse. This is how you avoid the "I left a
Medium warehouse running all weekend" surprise.

### Per-role access

By default, only `SYSADMIN` can create warehouses. We grant
`USAGE` to the roles that need them:

```sql
GRANT USAGE ON WAREHOUSE loading_wh  TO ROLE loader;
GRANT USAGE ON WAREHOUSE bi_wh      TO ROLE analyst;
GRANT USAGE ON WAREHOUSE transform_wh TO ROLE transformer;
```

Use a separate role for each workload class. It's the same
separation-of-concerns principle as a separate warehouse, just
one level up.

## Hands-on

Run the four `CREATE WAREHOUSE` statements. Open
**Account → Warehouses** in the UI and confirm all four appear
with `AUTO_SUSPEND = 60` and `INITIALLY_SUSPENDED = TRUE`.

## Quiz prep

- Why have one warehouse per workload?
- What is the single biggest credit-saving setting on a
  warehouse?
- What is the difference between `STANDARD`, `ECONOMY`, and
  `AGGRESSIVE` scaling policies?

## Key takeaways

- **One warehouse per workload** is the default for any
  non-trivial Snowflake deployment.
- `AUTO_SUSPEND = 60` is the single biggest cost-saving setting.
- `RESOURCE_MONITOR` caps monthly credit spend and sends
  alerts before suspending.
- Use **per-role grants** so a dashboard role can't accidentally
  burn the loading warehouse.

## What's next

In **L54 — Implement dedicated virtual warehouse** we'll wire
the four warehouses into the actual ETL pipeline (L51's
`COPY INTO` runs on `loading_wh`, not `COMPUTE_WH`).