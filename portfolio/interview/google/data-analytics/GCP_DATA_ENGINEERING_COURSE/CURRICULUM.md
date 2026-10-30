# gcp-de — Curriculum Design

The umbrella **Google Cloud Data Engineer** course. It covers the platform
layer and the certification scope end to end, and links out to the sibling
service courses rather than duplicating their depth.

## Design principle

The sibling courses are **deep dives** into one service each:

- `../BigQuery` — 57 chapters, the warehouse
- `../Dataflow` — 52 chapters, the batch/streaming engine
- `../composer` — 16 chapters, the orchestrator
- `../dataproc` — 13 chapters, the Spark platform
- `../dataform` — 7 chapters, the transformation layer

`gcp-de` is the **platform layer** — the context needed to pick between
services, secure them, cost them, and wire them together. Where the
certification outline deep-dives a service the siblings already own, this
course gives the *decision framework* and the link.

## Source outlines

This course is built from two course outlines, merged:

1. **The 39-section platform outline** — cloud fundamentals, compute,
   storage, databases, analytics, streaming, processing, governance, ML.
2. **The Google Cloud Data Engineer certification outline** — the
   hands-on lab track: IAM labs, container and serverless deploys, GCS
   security labs, database labs, Pub/Sub delivery types, Dataflow and
   Dataproc job submission, Data Fusion, Composer, DLP inspection and
   de-identification, AutoML, BigQuery ML, Dataform workspaces,
   Datastream CDC, and BigQuery query optimization.

## Modules and chapters

### Module 1 — Cloud Fundamentals & the GCP Platform (5 chapters)

| # | Chapter | Covers |
|---|---------|--------|
| 1.1 | [Introduction to Cloud Computing](chapters/01-introduction-to-cloud-computing.md) | Cloud concepts, serverful vs serverless, vertical vs horizontal scaling, GCP vs AWS vs Azure, free tier |
| 1.2 | [Regions, Zones & the Resource Hierarchy](chapters/02-regions-zones-and-resource-hierarchy.md) | Regions and zones, the resource hierarchy, Cloud Shell, project ID vs name |
| 1.3 | [Identity & Access Management](chapters/03-identity-and-access-management.md) | Identity, roles, permissions, assigning roles, service accounts, the three identity types |
| 1.4 | [Org Policies, Networking & Compute](chapters/04-org-policies-networking-and-compute.md) | Organization policy, VPC, firewall rules, Compute Engine, App Engine, GKE, Cloud Run, Cloud Run functions, containers |
| 1.5 | [Proposing a Data Processing Strategy](chapters/05-proposing-a-data-processing-strategy.md) | Types of data, batch vs streaming, ETL vs ELT, choosing a strategy for a client |

### Module 2 — Storage & Databases (6 chapters)

| # | Chapter | Covers |
|---|---------|--------|
| 2.1 | [Cloud Storage](chapters/06-cloud-storage.md) | Classes, location, lifecycle, versioning, encryption, uniform bucket-level access, signed URLs, retention, pricing |
| 2.2 | [Block & File Storage](chapters/07-block-and-file-storage.md) | Persistent Disk, local SSD, Filestore, and which storage to use when |
| 2.3 | [Cloud SQL](chapters/08-cloud-sql.md) | Instances, connecting, whitelisting, failover, import/export, console explore |
| 2.4 | [Cloud Spanner](chapters/09-cloud-spanner.md) | Horizontal scale, CAP theorem, global consistency, which RDBMS to use when |
| 2.5 | [NoSQL: Bigtable, Datastore, Firestore, Memorystore](chapters/10-nosql-bigtable-datastore-firestore-memorystore.md) | Wide-column, document, cache; Redis vs Memcached |
| 2.6 | [Selecting a Database](chapters/11-selecting-a-database.md) | OLTP vs OLAP, RPO/RTO, availability vs durability, the decision matrix |

### Module 3 — Analytics & Warehousing (4 chapters)

| # | Chapter | Covers |
|---|---------|--------|
| 3.1 | [Data Warehousing Concepts](chapters/12-data-warehousing-concepts.md) | Warehouse architecture, columnar storage, ACID |
| 3.2 | [BigQuery — Platform Overview](chapters/13-bigquery-platform-overview.md) | BigQuery concepts, architecture, hierarchy; deep dive links to `../BigQuery` |
| 3.3 | [BigQuery Query Optimization](chapters/14-bigquery-query-optimization.md) | 30 optimization techniques: partitions, clustering, dry runs, select *, denormalisation |
| 3.4 | [BigLake, Dataplex & Data Catalog](chapters/15-biglake-dataplex-and-data-catalog.md) | BigLake, Dataplex, Data Catalog, tag templates |

### Module 4 — Streaming & Ingestion (4 chapters)

| # | Chapter | Covers |
|---|---------|--------|
| 4.1 | [Apache Kafka & the Streaming Model](chapters/16-kafka-and-the-streaming-model.md) | Kafka architecture, partitions, consumer groups, use cases |
| 4.2 | [Pub/Sub](chapters/17-pubsub.md) | Architecture, topics, subscriptions, push vs pull, delivery types, ordering keys, schemas, Pub/Sub Lite |
| 4.3 | [Datastream & CDC](chapters/18-datastream-and-cdc.md) | Change data capture from Cloud SQL and Oracle, to BigQuery and Pub/Sub |
| 4.4 | [Transfer Services & Migration](chapters/19-transfer-services-and-migration.md) | Storage Transfer Service, BigQuery DTS, Transfer Appliance, Database Migration Service |

### Module 5 — Processing & Orchestration (5 chapters)

| # | Chapter | Covers |
|---|---------|--------|
| 5.1 | [Hadoop & the Big Data Ecosystem](chapters/20-hadoop-and-big-data-ecosystem.md) | HDFS, YARN, MapReduce, the ecosystem, and why it lost to Spark |
| 5.2 | [Apache Spark & Cloud Dataproc](chapters/21-apache-spark-and-dataproc.md) | Spark, clusters, jobs, PySpark, notebooks, workflow templates, ephemeral clusters |
| 5.3 | [Apache Beam & Cloud Dataflow](chapters/22-apache-beam-and-dataflow.md) | Beam model, runners, Dataflow jobs and templates; deep dive links to `../Dataflow` |
| 5.4 | [Airflow, Composer & Workflows](chapters/23-airflow-composer-and-workflows.md) | DAGs, Composer environments, first DAG, serverless Workflows; links to `../composer` |
| 5.5 | [Dataform & the Transformation Layer](chapters/24-dataform-and-the-transformation-layer.md) | Repositories, workspaces, SQLX, refs, incremental models, tests |

### Module 6 — Integration & No-Code (2 chapters)

| # | Chapter | Covers |
|---|---------|--------|
| 6.1 | [Cloud Data Fusion](chapters/25-cloud-data-fusion.md) | Instances, pipelines, connectors, running on Dataproc |
| 6.2 | [Cloud Dataprep](chapters/26-cloud-dataprep.md) | Workspaces, flows, agents, recipes |

### Module 7 — Governance, Security & BI (3 chapters)

| # | Chapter | Covers |
|---|---------|--------|
| 7.1 | [Sensitive Data Protection & DLP](chapters/27-sensitive-data-protection.md) | InfoTypes, inspect and de-identify templates, custom info types, the DLP API |
| 7.2 | [Compliance, Residency & Encryption](chapters/28-compliance-residency-and-encryption.md) | Data residency, legal compliance, encryption at rest and in transit, CMEK |
| 7.3 | [Looker Studio & BI](chapters/29-looker-studio-and-bi.md) | Reports, data sources, dashboards, connectors |

### Module 8 — ML on GCP & Capstone (5 chapters)

| # | Chapter | Covers |
|---|---------|--------|
| 8.1 | [Machine Learning Foundations on GCP](chapters/30-machine-learning-foundations.md) | Types of ML, the workflow, EDA, feature engineering |
| 8.2 | [Prebuilt & AutoML Models](chapters/31-prebuilt-and-automl-models.md) | Vision, Natural Language, Speech-to-Text, AutoML text classification and image |
| 8.3 | [Custom Training & Vertex AI](chapters/32-custom-training-and-vertex-ai.md) | Scikit-learn to Vertex AI, endpoints, prediction |
| 8.4 | [BigQuery ML](chapters/33-bigquery-ml.md) | CREATE MODEL, evaluation, prediction in SQL |
| 8.5 | [End-to-End Capstone](chapters/34-end-to-end-capstone.md) | The full platform, wired together, end to end |

## Deliverables

- `chapters/` — 34 chapters across 8 modules
- `project/` — a runnable local pipeline simulating the platform
- `notebooks/` — hands-on notebooks
- `resources/` — SETUP, CHEATSHEET, GLOSSARY, FAQ, linter, sample data
- `interview/` — certification-style question bank
