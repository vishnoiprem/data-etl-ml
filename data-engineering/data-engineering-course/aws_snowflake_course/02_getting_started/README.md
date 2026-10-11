# Section 2 — Getting Started

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Lectures:** L05–L14
> **Duration:** ~72 min

This is the first hands-on section. We sign up for the **30-day
free trial** with $400 of credits, tour the **Snowsight UI**
(worksheets, dashboards, role selector, query history), and set
up our first **virtual warehouses** through both the UI and SQL.
We cover the **three-layer architecture** (storage, compute,
cloud services) and the **scaling policy** options for multi-
cluster warehouses.

By the end of this section you should have a working Snowflake
account, three starter warehouses (`LOADING_WH`, `TRANSFORM_WH`,
`ANALYST_WH`), and a clear mental model of how compute and
storage are independently scaled and billed.

| L# | Title | Min |
|---|---|---|
| L05 | Sign up for free trial | 6:00 |
| L06 | Getting to know the interface | 8:00 |
| L07 | Understanding Workspaces & Querying Data | 7:00 |
| L08 | Snowflake architecture | 10:00 |
| L09 | Architecture (deeper) | 9:00 |
| L10 | Setting up warehouse | 8:00 |
| L11 | Setting up warehouse using SQL | 7:00 |
| L12 | Setting up warehouse (recap) | 4:00 |
| L13 | Manage warehouses | 8:00 |
| L14 | Scaling policy | 7:00 |

## Key concepts you'll need later

- **Three-layer architecture** — storage (micro-partitions in
  S3/ADLS/GCS), compute (virtual warehouses), cloud services
  (always-on metadata + query planner).
- **Partition pruning** — micro-partition min/max metadata lets
  the optimizer skip irrelevant data.
- **Auto-suspend** — the most important cost lever. Default
  60s; production usually 60–300s.
- **Multi-cluster warehouses** — Enterprise+ only. `STANDARD`
  vs `ECONOMY` scaling policy.
- **Right-sizing** — start Small, profile, scale up or out.

## What comes next

Section 3 is **Snowflake Architecture** (deeper) — we go from
the conceptual three-layer model into the **editions**, the
**pricing model**, **storage cost details**, and **resource
monitors** (the credit cap system). By L23 you'll be able to
estimate the monthly bill for a Snowflake workload and set
budget guards.
