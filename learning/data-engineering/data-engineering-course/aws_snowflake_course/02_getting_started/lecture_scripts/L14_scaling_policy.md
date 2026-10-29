---
l_id: L14
title: Scaling policy
duration: "7:00"
prereqs: ["L13"]
downloads: []
---

# L14 — Scaling Policy

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 2 — Getting Started
> **Duration:** ~7:00

## Prereqs

L13 — Manage warehouses. This lecture introduces multi-cluster
warehouses and the scaling policy.

## Key terms

- **Multi-cluster warehouse** — a warehouse that can run
  multiple clusters of the same size. Each cluster can run a
  query independently. Enterprise+ edition only.
- **Scaling policy** — controls how clusters spin up/down:
  `STANDARD` (responsive) or `ECONOMY` (cost-optimized).
- **Scale factor** — `SCALE_OUT` (1 cluster per concurrent
  query) or `SCALE_OUT_2X` (1 cluster per 2 concurrent queries).
- **Min/max cluster count** — the range of clusters the
  warehouse can scale to.

## Lecture

Single-cluster warehouses handle concurrency poorly: if 10
queries arrive at the same time, 9 of them queue behind the
one cluster. The fix is a **multi-cluster warehouse** — the
warehouse spins up additional clusters to run queries in
parallel.

### When to use multi-cluster

Use multi-cluster when:

- **Many concurrent users** are submitting queries (BI tools,
  ad-hoc analysts).
- Workload is **read-heavy and bursty** (e.g. Monday morning
  dashboards).
- The same warehouse is shared across many teams and you want
  predictable performance.

Don't use multi-cluster when:

- Workload is **ETL/batch** — single large queries, not
  concurrent. Just size up.
- Workload is **predictable and small** — single cluster
  handles it.

### Scaling policies

```sql
CREATE WAREHOUSE ANALYST_WH
  WITH WAREHOUSE_SIZE       = 'MEDIUM'
       MIN_CLUSTER_COUNT    = 1
       MAX_CLUSTER_COUNT    = 10
       SCALING_POLICY       = 'STANDARD'
       AUTO_SUSPEND         = 60
       AUTO_RESUME          = TRUE;
```

- **STANDARD** — spin up clusters aggressively to keep wait
  times low. When queries queue, a new cluster starts within
  ~30 seconds. When load drops, clusters scale back over a
  few minutes.
- **ECONOMY** — only spin up additional clusters when the
  existing ones have been busy for a sustained period. Cheaper
  but with longer wait times during spikes.

> **Rule of thumb.** Pick `STANDARD` for interactive BI
> workloads; `ECONOMY` for batch-ish or budget-sensitive
> workloads.

### Scale factor

The scale factor controls how aggressive the scaling is:

- `SCALE_OUT` (default) — one cluster per concurrent query.
  Maximum concurrency, maximum cost.
- `SCALE_OUT_2X` — one cluster per two concurrent queries.
  Half the cost, half the concurrency.

```sql
ALTER WAREHOUSE ANALYST_WH SET SCALING_POLICY = 'ECONOMY';
ALTER WAREHOUSE ANALYST_WH SET MAX_CLUSTER_COUNT = 5;
```

### Cost implications

Multi-cluster warehouses are billed per **cluster-second**,
not per warehouse. A 3-cluster warehouse at Medium (4
credits/hour each) costs 12 credits/hour when fully scaled
out. Set `MAX_CLUSTER_COUNT` carefully — a runaway spike can
multiply your compute bill.

### An alternative — separate warehouses per workload

A common alternative to multi-cluster is to give each team its
own warehouse:

```sql
-- Three single-cluster warehouses, no multi-cluster
CREATE WAREHOUSE BI_WH     WITH WAREHOUSE_SIZE = 'MEDIUM' AUTO_SUSPEND = 60;
CREATE WAREHOUSE DS_WH     WITH WAREHOUSE_SIZE = 'XLARGE' AUTO_SUSPEND = 60;
CREATE WAREHOUSE ETL_WH    WITH WAREHOUSE_SIZE = 'LARGE'  AUTO_SUSPEND = 60;
```

This gives you explicit cost attribution per team and avoids
the runaway-cluster risk. Many production setups prefer
multiple single-cluster warehouses over one multi-cluster.

## Hands-on

```sql
USE ROLE SYSADMIN;

-- Create a multi-cluster warehouse
CREATE OR REPLACE WAREHOUSE ANALYST_MC_WH
  WITH WAREHOUSE_SIZE    = 'MEDIUM'
       MIN_CLUSTER_COUNT = 1
       MAX_CLUSTER_COUNT = 5
       SCALING_POLICY    = 'STANDARD'
       AUTO_SUSPEND      = 60;

-- Show scaling policy
SHOW WAREHOUSES LIKE 'ANALYST_MC_WH';

-- Change to ECONOMY
ALTER WAREHOUSE ANALYST_MC_WH SET SCALING_POLICY = 'ECONOMY';
ALTER WAREHOUSE ANALYST_MC_WH SET MAX_CLUSTER_COUNT = 3;
```

## Quiz prep

- What is the difference between STANDARD and ECONOMY
  scaling policy? (STANDARD spins up clusters faster and
  scales back slower; ECONOMY is more conservative)
- Which edition is required for multi-cluster warehouses?
  (Enterprise+)
- What is the alternative to multi-cluster for high-
  concurrency workloads? (One warehouse per team/workload,
  each single-cluster)

## Key takeaways

- Multi-cluster warehouses handle **concurrent** queries by
  spinning up additional clusters.
- `STANDARD` scaling policy = responsive; `ECONOMY` =
  cost-optimized.
- Set `MAX_CLUSTER_COUNT` to prevent runaway bills.
- Many production setups prefer **multiple single-cluster
  warehouses** over one multi-cluster for cost attribution.

## What's next

Next up is **L15 — Exploring tables & databases**, the first
lecture in section 3. We shift from compute to storage: how
tables, databases, and schemas fit together.
