---
l_id: L17
title: What is a data warehouse?
duration: "5:00"
prereqs: ["L16"]
downloads: []
---

# L17 — What Is a Data Warehouse?

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 3 — Snowflake Architecture
> **Duration:** ~5:00

## Prereqs

L16 — Loading data in Snowflake (intro). This is a short
context lecture.

## Key terms

- **OLTP** — Online Transaction Processing. Row-oriented,
  fast single-row writes, low latency. Examples: Postgres,
  MySQL, DynamoDB.
- **OLAP** — Online Analytical Processing. Column-oriented,
  fast aggregations over many rows, high throughput. Examples:
  Snowflake, BigQuery, Redshift.
- **Data warehouse** — a database optimized for OLAP workloads
  — analytical queries over large historical data.
- **Data lake** — raw files (often Parquet/JSON) in object
  storage, schema-on-read. Examples: S3 + Athena, ADLS + Synapse.
- **Data lakehouse** — a hybrid that combines warehouse
  performance with lake flexibility. Snowflake is positioned
  as a data lakehouse.

## Lecture

A quick context lecture for readers new to data warehousing.
Skip ahead if you already know the difference between OLTP and
OLAP.

### OLTP vs OLAP

The two dominant database paradigms serve very different
purposes:

| Aspect | OLTP | OLAP |
|---|---|---|
| Use case | Application backend | Reporting, analytics |
| Workload | Many small reads/writes | Few large scans |
| Latency | Sub-millisecond | Seconds to minutes |
| Data volume | GBs | TBs to PBs |
| Schema | Normalized (3NF) | Denormalized (star/snowflake) |
| Storage | Row-oriented | Column-oriented |
| Examples | Postgres, MySQL | Snowflake, BigQuery, Redshift |

Snowflake is a **columnar OLAP** system. It's optimized for
"scan a billion rows and aggregate them" rather than "find
this one user by ID". Don't use it for transactional
backends.

### Why "data warehouse" specifically

The data warehouse pattern, formalized by Inmon and Kimball in
the 1990s, is the standard architecture for enterprise
analytics:

- **Source systems** — OLTP databases, SaaS APIs, event
  streams, files.
- **Staging area** — raw landing zone; often schema-on-read.
- **Data warehouse** — cleaned, conformed, modeled for
  reporting. Star schema with fact and dimension tables.
- **Data marts** — subsets of the warehouse tailored to a
  team (sales, finance, marketing).
- **BI / analytics** — dashboards, reports, ad-hoc SQL.

Snowflake sits squarely in the **data warehouse** layer (and,
with semi-structured support, in the data lakehouse layer).

### Why Snowflake is different from "classic" warehouses

Traditional data warehouses (Teradata, Netezza, Vertica,
Exadata) had two big problems:

1. **Compute and storage were co-located.** Adding storage
   meant adding compute (and vice versa), whether you needed
   it or not.
2. **Concurrency was a problem.** When many analysts ran
   reports at the same time, they all competed for the same
   fixed cluster.

Snowflake's separation of compute and storage (and per-query
clusters) solves both. You scale compute and storage
independently, and many concurrent users don't contend because
each can spin up a new warehouse.

### A short history

- **1980s** — first data warehouses (Teradata, Red Brick)
- **1990s** — Inmon and Kimball formalize dimensional modeling
- **2000s** — columnar MPP warehouses (Vertica, Netezza,
  ParAccel)
- **2010s** — cloud-native warehouses (Redshift 2012, BigQuery
  2011/GA 2016, Snowflake 2014/GA 2015)
- **2020s** — lakehouse convergence (Snowflake, Databricks,
  BigQuery Omni)

## Hands-on

No lab. This is a context lecture.

## Quiz prep

- What is the difference between OLTP and OLAP? (OLTP =
  transactional, low latency; OLAP = analytical, high
  throughput)
- What are the three layers of a classic data warehouse
  architecture? (Staging, warehouse, data marts)
- What problem does Snowflake's separation of compute and
  storage solve? (Independent scaling + better concurrency)

## What's next

Next up is **L18 — Cloud computing**, where we cover the
basics of cloud computing as they apply to Snowflake's
deployment model.
