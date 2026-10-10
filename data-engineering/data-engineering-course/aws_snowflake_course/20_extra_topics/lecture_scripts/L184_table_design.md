---
l_id: L184
title: Table design
duration: "5:00"
prereqs: ["L183"]
---

# L184 — Table design

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 7. Best Practices & Bonus
> **Duration:** 5:00

## Prereqs

L183 — Warehouse Usage.

## Key terms

- **Clustering key** — a column (or columns) Snowflake
  uses to physically co-locate data.
- **Clustering depth** — a measure of how well the data
  is clustered; lower is better.
- **Naming convention** — `snake_case` for tables,
  `UPPER_SNAKE` for warehouses, etc.

## Lecture

Welcome back. Today's lecture is the table design
playbook. By the end, you should be able to design a
table for performance, cost, and maintainability.

### The right type for the right use

| Use | Type | Why |
|---|---|---|
| Production data | Permanent | Fail Safe, full retention |
| Staging | Transient | No Fail Safe, cheaper |
| Session scratch | Temporary | Auto-drops |
| Dev / test | Transient | Cheap |

L113–L115 covered this in detail. The rule of thumb: if
in doubt, choose **transient** and promote to permanent
later.

### Clustering

```sql
ALTER TABLE orders CLUSTER BY (order_date, customer_id);
```

Clustering is Snowflake's equivalent of an index. It
co-locates data with the same `order_date` and
`customer_id` so that range queries and equality joins
on those columns can prune micro-partitions.

A few rules:

- Cluster on the **filter / join** columns, not the
  `PRIMARY KEY`.
- Cluster on **1–3 columns**; more is slower to maintain.
- Don't cluster on **high-cardinality unique IDs** —
  they don't benefit from clustering.
- Monitor the **clustering depth** with
  `SYSTEM$CLUSTERING_DEPTH`. If it climbs above ~10,
  re-cluster.

### The clustering trade-off

| | No clustering | Clustered |
|---|---|---|
| Query performance | Slower on filters | Faster on filter columns |
| Maintenance | None | Re-clustering cost on writes |
| Storage | Normal | Slightly more (overlapping partitions) |

For tables < 1 TB, clustering rarely helps — Snowflake
scans the whole table fast enough. For tables > 1 TB
with hot filter columns, clustering is a clear win.

### Naming conventions

- Tables: `snake_case` plural, e.g. `customers`,
  `orders`, `line_items`.
- Columns: `snake_case`, no abbreviations unless
  universal (`id`, `url`).
- Warehouses: `UPPER_SNAKE_CASE`, prefixed by purpose
  (`ETL_WH`, `BI_WH`).
- Schemas: `lower_snake_case` plural or by purpose
  (`raw`, `staging`, `marts`).
- Roles: `lower_snake_case` (`analyst`, `data_engineer`).

Pick a convention, write it down, enforce it in code
review.

### Schema design

A standard layout:

```text
database
├── raw        (loaded data, never modified)
├── staging    (in-flight transformations)
├── marts      (final, conformed)
└── meta       (audit, lineage, control tables)
```

Every team I've seen converges on this. The boundaries
are sharp: `raw` is read-only except by the load
process; `marts` is read-only except by the publication
process.

### Constraints

Snowflake does not enforce `PRIMARY KEY` or `FOREIGN
KEY` constraints. You can declare them for documentation,
but Snowflake does not check them. The validations happen
in your ETL code or via streams.

```sql
CREATE TABLE orders (
  order_id     NUMBER,
  customer_id  NUMBER,
  amount       NUMBER(10,2),
  PRIMARY KEY (order_id)              -- documentation only
);
```

## Hands-on

```sql
-- Inspect clustering on a table
SELECT SYSTEM$CLUSTERING_DEPTH('orders');

-- Inspect retention
SHOW TABLES LIKE 'orders';

-- Inspect a sample table's structure
DESC TABLE orders;
```

## Key takeaways

- Right table type for the right use; default to
  transient.
- Cluster on filter / join columns for tables > 1 TB.
- Naming conventions: snake_case for tables, UPPER_SNAKE
  for warehouses.
- Schema layout: `raw` / `staging` / `marts` / `meta`.

## What's next

L185 — Monitoring. The deeper dive on observability.