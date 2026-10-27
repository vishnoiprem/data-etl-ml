# BigQuery for Big Data Engineers — Master BigQuery Internals

A complete, hands-on deep-knowledge guide to **Google Cloud BigQuery** for data engineers and analysts.
Every topic is taught from first principles — architecture, internals, pricing, optimization — and then
exercised for real through the **Web Console**, the **`bq` CLI**, and the **Python Client Library**.

> **Duration:** 20 sections · 105 lectures · ~8h 47m
> **Audience:** Data engineers, analytics engineers, data analysts, and anyone who has to design,
> build, or cost out a BigQuery-based warehouse.

---

## What You Will Learn

- **Full in & out of Google Cloud BigQuery** with hands-on examples from scratch.
- An overview of **Google Cloud Platform** and the set of services it provides.
- **Core concepts** — architecture, projects, datasets, tables, views, materialized views, scheduled
  queries, limitations and quotas.
- **Advanced topics** — query execution plans, efficient schema design, optimization techniques,
  partitioning, clustering.
- **Real pipelines** built with Dataflow, Pub/Sub, BigQuery, Cloud Storage, Apache Beam, Looker Studio,
  and Cloud Composer/Airflow.
- **Three ways to drive BigQuery** — Web Console, Command Line (`bq`), and the Python Client Library.
- **Best practices** for performance and cost savings at every layer of BigQuery.
- **Pricing models** for storage, querying, API requests, DML, and the free operations that keep a
  project cheap.

---

## Course Structure

### Module 1 — Introduction to Google Cloud Platform
| # | Chapter | Covers |
|---|---------|--------|
| 1.1 | [GCP vs AWS vs Azure](chapters/01-gcp-vs-aws-vs-azure.md) | Why choose GCP, service parity, ecosystem fit |
| 1.2 | [Compute Services in GCP](chapters/02-gcp-compute-services.md) | Compute Engine, GKE, Cloud Run, Functions, App Engine |
| 1.3 | [Storage Services in GCP](chapters/03-gcp-storage-services.md) | Cloud Storage classes, Filestore, Persistent Disk |
| 1.4 | [Big Data Services in GCP](chapters/04-gcp-bigdata-services.md) | BigQuery, Dataflow, Dataproc, Pub/Sub, Composer |
| 1.5 | [AI & ML Services in GCP](chapters/05-gcp-ai-ml-services.md) | Vertex AI, AutoML, Vision, Speech, Gemini |
| 1.6 | [Big Data Ecosystem in GCP](chapters/06-gcp-bigdata-ecosystem.md) | How the pieces fit into an end-to-end platform |

### Module 2 — BigQuery Fundamentals
| # | Chapter | Covers |
|---|---------|--------|
| 2.1 | [Conventional Data Warehouse Problems](chapters/07-conventional-warehouse-problems.md) | HDFS, Hive, Spark — cost, latency, ops burden |
| 2.2 | [What is BigQuery](chapters/08-what-is-bigquery.md) | Serverless warehouse, no cluster, no DBA |
| 2.3 | [Out-of-the-Box Features](chapters/09-bigquery-ootb-features.md) | Zero ops, scaling, federation, governance |
| 2.4 | [Architecture of BigQuery](chapters/10-bigquery-architecture.md) | Storage layer, compute layer, Colossus, Dremel |
| 2.5 | [Setup: Project & Billing](chapters/11-setup-gcp-account-project.md) | Account, project, billing, budget alerts |
| 2.6 | [BigQuery UI Tour](chapters/12-bigquery-ui-tour.md) | Console layout, query editor, execution details |
| 2.7 | [Datasets & Regions](chapters/13-datasets-and-regions.md) | Create datasets, region vs multi-region |
| 2.8 | [Create a Table](chapters/14-create-a-table.md) | DDL, UI table creation, table types |

### Module 3 — Querying & Schema Design
| # | Chapter | Covers |
|---|---------|--------|
| 3.1 | [Query Settings & Caching](chapters/15-query-settings-and-caching.md) | Maximum bytes billed, caching, use legacy SQL |
| 3.2 | [Wildcard Tables](chapters/16-wildcard-tables.md) | `_` and `*` suffixes, limitations |
| 3.3 | [Schedule, Save & Share Queries](chapters/17-scheduled-queries.md) | Scheduled queries, saved queries, sharing |
| 3.4 | [Schema Auto-Detection](chapters/18-schema-auto-detection.md) | Detection, schema updates, load-time behavior |
| 3.5 | [Efficient Schema Design](chapters/19-efficient-schema-design.md) | Types, costs, denormalization, naming |
| 3.6 | [Nested & Repeated Columns](chapters/20-nested-and-repeated-columns.md) | RECORD, ARRAY, UNNEST, STRUCT |
| 3.7 | [Copy Datasets & Transfer Service](chapters/21-copy-datasets-transfer-service.md) | Cross-region copies, scheduled transfers |
| 3.8 | [Modifying Table Schema](chapters/22-modifying-table-schema.md) | ALTER TABLE ADD/ALTER/DROP COLUMN |
| 3.9 | [Restore Deleted Data](chapters/23-restore-deleted-data.md) | Time travel, table snapshots, undelete |

### Module 4 — Performance: Partitioning & Clustering
| # | Chapter | Covers |
|---|---------|--------|
| 4.1 | [How BigQuery Builds an Execution Plan](chapters/24-execution-plans.md) | Stage graph, slots, bytes scanned |
| 4.2 | [Reading the Execution Plan in the UI](chapters/25-execution-plan-ui.md) | Query plan, timeline, details pane |
| 4.3 | [Partitioning: Concepts](chapters/26-partitioning-concepts.md) | Why partition, pruning, limitations |
| 4.4 | [Ingestion-Time Partitioned Tables](chapters/27-partitioning-ingestion-time.md) | `_PARTITIONTIME`, `__PARTITIONS_SUMMARY__` |
| 4.5 | [Date & Integer Partitioned Tables](chapters/28-partitioning-date-integer.md) | Date bucketing, range partitioning |
| 4.6 | [ALTER, COPY & DML on Partitioned Tables](chapters/29-partitioning-dml-and-alter.md) | Partition filters, decorator syntax |
| 4.7 | [Best Practices for Partitioning](chapters/30-partitioning-best-practices.md) | Common mistakes, partitioning strategy |
| 4.8 | [Clustering](chapters/31-clustering.md) | Clustering columns, benefits, limits |
| 4.9 | [Partitioning vs Clustering vs Both](chapters/32-partition-vs-cluster.md) | Decision framework, cost/benefit |

### Module 5 — External Data, Views & Materialized Views
| # | Chapter | Covers |
|---|---------|--------|
| 5.1 | [Cloud Storage Buckets](chapters/33-cloud-storage-buckets.md) | Classes, lifecycle, URI conventions |
| 5.2 | [Permanent External Tables](chapters/34-external-tables.md) | Hive partitioning, file formats, limits |
| 5.3 | [Views](chapters/35-views.md) | Logical views, row-level security, limits |
| 5.4 | [Materialized Views](chapters/36-materialized-views.md) | MV semantics, refresh, query tuning, limits |

### Module 6 — The `bq` Command Line
| # | Chapter | Covers |
|---|---------|--------|
| 6.1 | [Cloud SDK Setup](chapters/37-cloud-sdk-setup.md) | Install, auth, ADC, project config |
| 6.2 | [bq Basic Commands](chapters/38-bq-basic-commands.md) | `ls`, `show`, `rm`, `mk`, `cp` |
| 6.3 | [bq Querying Commands](chapters/39-bq-query-commands.md) | Dry runs, jobs, output formats |
| 6.4 | [Dataset & Table Commands](chapters/40-bq-dataset-table-commands.md) | DDL via CLI, all table types |
| 6.5 | [Loading Data & Exclusive Ops](chapters/41-bq-load-and-exclusive-ops.md) | `load`, `extract`, `copy`, `insert` |

### Module 7 — Python Client Library
| # | Chapter | Covers |
|---|---------|--------|
| 7.1 | [Setup & Authentication](chapters/42-python-setup.md) | `google-cloud-bigquery`, ADC, `bigquery.Client` |
| 7.2 | [Create a Dataset](chapters/43-python-create-dataset.md) | Dataset API, labels, location |
| 7.3 | [Create a Table](chapters/44-python-create-table.md) | Schema objects, partitioning, clustering |
| 7.4 | [Query Tables](chapters/45-python-query-tables.md) | `client.query`, jobs, `to_dataframe` |

### Module 8 — Case Study: End-to-End Pipeline
| # | Chapter | Covers |
|---|---------|--------|
| 8.1 | [Case Study Requirements](chapters/46-case-study-requirements.md) | Business problem, requirements, SLA |
| 8.2 | [Apache Beam Pipeline](chapters/47-apache-beam-pipeline.md) | Beam SDK, transforms, BigQuery IO |
| 8.3 | [Airflow DAG on Composer](chapters/48-airflow-composer-dag.md) | DAG design, schedule, dependencies |

### Module 9 — Real-Time: Pub/Sub & Streaming
| # | Chapter | Covers |
|---|---------|--------|
| 9.1 | [Pub/Sub Architecture](chapters/49-pubsub-architecture.md) | Topics, subscriptions, push/pull, ordering |
| 9.2 | [Beam Streaming Pipeline](chapters/50-beam-streaming-pipeline.md) | Streaming sources, windows, triggers |

### Module 10 — Pricing, Optimization & File Formats
| # | Chapter | Covers |
|---|---------|--------|
| 10.1 | [BigQuery Pricing Models](chapters/51-pricing-models.md) | Storage, query, API, DML, free ops |
| 10.2 | [Cost Optimization Techniques](chapters/52-cost-optimization.md) | Reduce scan, reduce CPU, anti-patterns |
| 10.3 | [File Formats](chapters/53-file-formats.md) | CSV, JSON, Avro, RC, ORC, Parquet |
| 10.4 | [Apache Beam Fundamentals](chapters/54-apache-beam-fundamentals.md) | Batch vs streaming, runners, model |

---

## Hands-On Notebooks

All notebooks use the **Python Client Library** (`google-cloud-bigquery`) and run against a real
BigQuery project. They are designed to be executed top-to-bottom.

| # | Notebook | What you build |
|---|----------|----------------|
| 01 | [Setup & Authentication](notebooks/01-setup-and-authentication.ipynb) | Authenticate, resolve project, run first query |
| 02 | [Datasets & Tables](notebooks/02-datasets-and-tables.ipynb) | Create dataset, table, load sample data |
| 03 | [Querying & Query Settings](notebooks/03-querying-and-settings.ipynb) | Query execution, dry runs, bytes billed |
| 04 | [Schema Design & Nested Data](notebooks/04-schema-and-nested-data.ipynb) | Schema objects, JSON, UNNEST |
| 05 | [Partitioning](notebooks/05-partitioning.ipynb) | Ingestion-time, date, integer partitioning |
| 06 | [Clustering](notebooks/06-clustering.ipynb) | Clustered tables, pruning behavior |
| 07 | [Views & Materialized Views](notebooks/07-views-and-materialized-views.ipynb) | Logical views, row-level security, MVs |
| 08 | [Cost Analysis](notebooks/08-cost-analysis.ipynb) | Dry runs, bytes processed, estimation |
| 09 | [External Tables & File Formats](notebooks/09-external-tables-and-file-formats.ipynb) | Cloud Storage external tables, Parquet |
| 10 | [Pipeline Patterns](notebooks/10-pipeline-patterns.ipynb) | Load → transform → publish patterns |

---

## SQL Scripts

Every SQL example in the chapters is also available as a standalone, runnable script in [`sql/`](sql/).

| Script | Contents |
|--------|----------|
| [`sql/01_setup_and_datasets.sql`](sql/01_setup_and_datasets.sql) | Project setup, dataset creation, labels, TTL |
| [`sql/02_tables_and_schemas.sql`](sql/02_tables_and_schemas.sql) | CREATE TABLE for every table type |
| [`sql/03_queries_and_settings.sql`](sql/03_queries_and_settings.sql) | Query settings, caching, wildcard tables |
| [`sql/04_schema_modification.sql`](sql/04_schema_modification.sql) | ALTER TABLE, nested schemas, autodetect |
| [`sql/05_partitioning.sql`](sql/05_partitioning.sql) | All partitioning flavours + DML |
| [`sql/06_clustering.sql`](sql/06_clustering.sql) | Clustered tables, pruning demos |
| [`sql/07_external_tables.sql`](sql/07_external_tables.sql) | External table DDL over Cloud Storage |
| [`sql/08_views_and_materialized_views.sql`](sql/08_views_and_materialized_views.sql) | Views, row-level security, MVs |
| [`sql/09_pricing_and_optimization.sql`](sql/09_pricing_and_optimization.sql) | Estimation, anti-patterns, rewrite examples |
| [`sql/10_case_study.sql`](sql/10_case_study.sql) | Full case-study model layer |

---

## Resources

| Resource | Description |
|----------|-------------|
| [`resources/SETUP.md`](resources/SETUP.md) | Full environment setup — account, project, billing, budget, service accounts |
| [`resources/CHEATSHEET.md`](resources/CHEATSHEET.md) | SQL, `bq`, and Python one-page reference |
| [`resources/GLOSSARY.md`](resources/GLOSSARY.md) | BigQuery terminology explained |
| [`resources/FAQ.md`](resources/FAQ.md) | Frequently asked questions and troubleshooting |
| [`resources/sample_data.py`](resources/sample_data.py) | Generates the sample dataset (CSV / NDJSON / Parquet) for all exercises |
| [`resources/bq_client.py`](resources/bq_client.py) | Shared BigQuery helper module used by every notebook |
| [`resources/requirements.txt`](resources/requirements.txt) | Python dependencies for the notebooks |
| [`resources/requirements-beam.txt`](resources/requirements-beam.txt) | Apache Beam extras for the pipeline chapters |

---

## Getting Started

```bash
# 1. Read the setup guide
less resources/SETUP.md

# 2. Create a virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r resources/requirements.txt

# 3. Authenticate
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID

# 4. Run the first notebook
jupyter lab notebooks/01-setup-and-authentication.ipynb
```

---

## Course Conventions

Throughout the chapters:

- **`sql`** code blocks are BigQuery Standard SQL and run in the Web Console or via `bq query`.
- **`python`** blocks use the `google-cloud-bigquery` v3 client.
- **`bash`** blocks use the `bq` CLI or `gcloud` for setup.
- ⚠️ blocks mark actions that **cost money** or **delete data**.
- 💡 blocks mark production tips that go beyond the basics.
- Every chapter ends with **Key Takeaways** and **Practice Exercises**.

---

## Related Courses

Sibling GCP courses in this repository: `Dataflow`, `Pub/Sub`, `Composer`, `Dataproc`, `Dataform`,
`Dataplex`, `Looker`.

---

*Built for data engineers who need to know not just how to run a query, but why it costs what it
costs and how to make it ten times faster.*
