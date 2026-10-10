# Section 7 — Performance Optimization

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Lectures:** L50–L58
> **Duration:** ~62 min

This section is the "make Snowflake fast" toolkit. We swap
JSON for **Parquet** (columnar binary, 5–10× faster on big
data), then go deep on the three performance levers:
**dedicated warehouses** (one per workload), **scale up vs
scale out**, and the **three caches** that make a repeated
query almost free.

By the end of this section you should be able to size a
warehouse per workload, choose between scale up and scale out,
read the Query Profile to spot a missed cache, and design SQL
that maximises the result cache hit ratio.

| L# | Title | Min |
|---|---|---|
| L50 | Querying PARQUET data | 7:00 |
| L51 | Loading PARQUET data | 8:00 |
| L52 | Performance Considerations in Snowflake | 7:00 |
| L53 | Create dedicated virtual warehouse | 6:00 |
| L54 | Implement dedicated virtual warehouse | 7:00 |
| L55 | Scaling up | 7:00 |
| L56 | Scaling out | 7:00 |
| L57 | Caching — Theory | 6:00 |
| L58 | Maximize Caching | 7:00 |

## Key concepts you'll need later

- **Parquet** — columnar binary. Reads only the columns a query
  references; 5–10× faster than JSON.
- **Three performance levers** — warehouse size, scale up vs
  out, caching.
- **Dedicated warehouses** — `loading_wh`, `transform_wh`,
  `bi_wh`, `admin_wh`. One per workload.
- **Three caches** — result (24 h, exact match), local disk
  (~24 h, file-level), query history (micro-partition
  pruning, always on).
- **Scale up vs out** — bigger clusters vs more clusters.

## What comes next

Section 8 is **Loading from AWS** — clustering (theory +
practice), the AWS free trial, creating an S3 bucket, the IAM
policy that grants Snowflake access, and the **storage
integration object** that ties it all together.