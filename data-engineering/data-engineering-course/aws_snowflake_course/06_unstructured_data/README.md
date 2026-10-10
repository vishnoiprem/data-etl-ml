# Section 6 — Loading Unstructured Data

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Lectures:** L41–L49
> **Duration:** ~65 min

This section teaches the **two-step JSON pipeline** every real
Snowflake warehouse eventually settles on: land the file as a
single `VARIANT` column in `raw_orders`, then `LATERAL FLATTEN`
it into typed `curated_*` tables. We cover `:` and `:.`
navigation, multi-segment paths into nested objects, `[N]`
array indexing, and the `LATERAL FLATTEN` table function.

By the end of this section you should be able to ingest any
JSON-shaped file, parse objects three levels deep, explode
arrays into facts, and materialise an analytics-ready curated
table from a `raw_orders` `VARIANT` source.

| L# | Title | Min |
|---|---|---|
| L41 | High-level steps | 5:00 |
| L42 | Understanding our data | 6:00 |
| L43 | Creating stage & raw table | 7:00 |
| L44 | Load raw JSON | 7:00 |
| L45 | Parsing JSON (`:` and `:.`) | 8:00 |
| L46 | Handling nested data | 8:00 |
| L47 | Parsing & handling array | 8:00 |
| L48 | Flatten hierarchical data (`LATERAL FLATTEN`) | 9:00 |
| L49 | Insert final data | 7:00 |

## Key concepts you'll need later

- **`VARIANT`** — Snowflake's universal semi-structured type.
- **`raw` vs `curated` tables** — `raw` is the safety net
  (`VARIANT` + filename); `curated` is what BI reads.
- **`:` and `::`** — path navigation and type cast.
- **`LATERAL FLATTEN`** — turns an array into rows; the
  foundational operation for JSON fact pipelines.
- **Watermark pattern** — `WHERE loaded_at > MAX(loaded_at)` for
  incremental inserts.

## What comes next

Section 7 is **Performance optimization** — we swap JSON for
**Parquet** (columnar binary, 5–10× faster on big data),
introduce dedicated virtual warehouses, walk through **scale up
vs scale out**, and explain the three caches Snowflake uses to
make the same query faster the second time you run it.