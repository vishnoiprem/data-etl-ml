# Google Cloud Data Engineering — Master the Platform

A complete, hands-on guide to designing and operating data platforms on
**Google Cloud** — from first principles to the service-by-service
decisions that decide whether a platform is cheap or ruinous.

Every topic is taught from the mechanism up — *why* the platform behaves
the way it does — and then exercised for real through a **working
project** that runs with **no GCP account, no credentials and no bill**.

> **Duration:** 8 modules · 34 chapters · ~33,000 lines
> **Audience:** Data engineers, analytics engineers, and architects who
> design, build, operate or cost out data platforms on GCP.

---

## What You Will Learn

- **The platform's shape** — regions, zones, the resource hierarchy, and
  why *where* a resource lives changes its price, its latency and its
  legal status.
- **IAM as a blast-radius decision** — identities, roles, permissions,
  service accounts, conditional bindings, and the question that matters:
  *if this credential leaks, what can it touch?*
- **Every storage and database service, and the one to pick** — Cloud
  Storage, block and file storage, Cloud SQL, Spanner, Bigtable,
  Datastore, Firestore, Memorystore, with a decision matrix that ends
  the debate.
- **BigQuery in depth** — Dremel, slots, reservations, partitioning,
  clustering, schema design, and a 30-technique optimisation playbook
  with real numbers.
- **Streaming done properly** — Kafka's log-structured model, Pub/Sub's
  delivery semantics and ordering keys, Datastream's CDC, and when
  at-least-once is enough.
- **Processing and orchestration, separated** — Hadoop's honest verdict,
  Spark and Dataproc, the Beam model and Dataflow, Airflow and Composer,
  serverless Workflows, and Dataform's transformation layer.
- **Governance as an engineering discipline** — DLP inspection and
  de-identification, data residency, CMEK, and the shared-responsibility
  split for a regulated workload.
- **ML on the platform** — where the data engineer's job actually sits,
  from labelling pipelines to training/serving skew.
- **128 interview questions** with answers written the way a senior
  engineer answers them.

---

## Course Structure

### Module 1 — Cloud Fundamentals & the GCP Platform

| # | Chapter | Covers |
|---|---------|--------|
| 1.1 | [Introduction to Cloud Computing](chapters/01-introduction-to-cloud-computing.md) | Cloud concepts, serverful vs serverless, vertical vs horizontal scaling, GCP vs Azure vs AWS, free tier |
| 1.2 | [Regions, Zones & the Resource Hierarchy](chapters/02-regions-zones-and-resource-hierarchy.md) | Regions and zones, org → folder → project → resource, project ID vs name, Cloud Shell |
| 1.3 | [Identity & Access Management](chapters/03-identity-and-access-management.md) | Identities, roles, permissions, service accounts, conditional bindings, blast radius |
| 1.4 | [Organization Policies, Networking & Compute](chapters/04-org-policies-networking-and-compute.md) | Org policy vs IAM, VPC, firewall rules, Compute Engine, App Engine, GKE, Cloud Run, functions, containers |
| 1.5 | [Proposing a Data Processing Strategy](chapters/05-proposing-a-data-processing-strategy.md) | Data types, batch vs streaming, pipelines, ETL vs ELT, the client-facing decision framework |

### Module 2 — Storage & Databases

| # | Chapter | Covers |
|---|---------|--------|
| 2.1 | [Cloud Storage](chapters/06-cloud-storage.md) | Classes, lifecycle, versioning, UBLA, signed URLs, retention, encryption, pricing |
| 2.2 | [Block & File Storage](chapters/07-block-and-file-storage.md) | Persistent Disk, local SSD, Filestore, which storage to use when |
| 2.3 | [Cloud SQL](chapters/08-cloud-sql.md) | Instances, connecting, whitelisting, failover, import/export, the Auth Proxy |
| 2.4 | [Cloud Spanner](chapters/09-cloud-spanner.md) | Horizontal scaling, the precise CAP claim, TrueTime, schema design |
| 2.5 | [NoSQL: Bigtable, Datastore, Firestore, Memorystore](chapters/10-nosql-bigtable-datastore-firestore-memorystore.md) | Wide-column, document, cache; row-key design; Redis vs Memcached |
| 2.6 | [Selecting a Database](chapters/11-selecting-a-database.md) | OLTP vs OLAP, RPO/RTO, availability vs durability, the full decision matrix |

### Module 3 — Analytics & Warehousing

| # | Chapter | Covers |
|---|---------|--------|
| 3.1 | [Data Warehousing Concepts](chapters/12-data-warehousing-concepts.md) | Kimball modelling, fact grain, star vs snowflake, columnar storage, ACID |
| 3.2 | [BigQuery — Platform Overview](chapters/13-bigquery-platform-overview.md) | Dremel, Colossus, slots, reservations, editions, when BigQuery is wrong |
| 3.3 | [BigQuery Query Optimization](chapters/14-bigquery-query-optimization.md) | Partitioning, clustering, schema design, denormalisation, dry runs, the checklist |
| 3.4 | [BigLake, Dataplex & Data Catalog](chapters/15-biglake-dataplex-and-data-catalog.md) | Managed lakehouse tables, universal catalogue, lineage, tag templates |

### Module 4 — Streaming & Ingestion

| # | Chapter | Covers |
|---|---------|--------|
| 4.1 | [Kafka & the Streaming Model](chapters/16-kafka-and-the-streaming-model.md) | Log-structured storage, partitions, consumer groups, offset semantics, ordering |
| 4.2 | [Pub/Sub](chapters/17-pubsub.md) | Topics, subscriptions, push/pull/exactly-once, ordering keys, schemas, DLQ, Lite |
| 4.3 | [Datastream & CDC](chapters/18-datastream-and-cdc.md) | The log-position problem, change streams, snapshot consistency, the idle-stream trap |
| 4.4 | [Transfer Services & Migration](chapters/19-transfer-services-and-migration.md) | Storage Transfer, BigQuery DTS, Transfer Appliance, Database Migration Service |

### Module 5 — Processing & Orchestration

| # | Chapter | Covers |
|---|---------|--------|
| 5.1 | [Hadoop & the Big Data Ecosystem](chapters/20-hadoop-and-big-data-ecosystem.md) | HDFS, YARN, MapReduce, the ecosystem, and where Hadoop still wins |
| 5.2 | [Apache Spark & Cloud Dataproc](chapters/21-apache-spark-and-dataproc.md) | DataFrames, Catalyst, the shuffle, cluster types, workflow templates, the Spot trick |
| 5.3 | [Apache Beam & Cloud Dataflow](chapters/22-apache-beam-and-dataflow.md) | The Beam model, runner portability, the job graph, templates, streaming |
| 5.4 | [Airflow, Composer & Workflows](chapters/23-airflow-composer-and-workflows.md) | DAGs, logical dates, data intervals, retries, XCom, sensors, serverless Workflows |
| 5.5 | [Dataform & the Transformation Layer](chapters/24-dataform-and-the-transformation-layer.md) | Repositories, SQLX, refs, model types, incremental strategies, data quality tests |

### Module 6 — Integration & No-Code

| # | Chapter | Covers |
|---|---------|--------|
| 6.1 | [Cloud Data Fusion](chapters/25-cloud-data-fusion.md) | Instances, the pipeline canvas, connectors, running on Dataproc, versioning |
| 6.2 | [Cloud Dataprep](chapters/26-cloud-dataprep.md) | Workspaces, flows, recipes, agents, the per-user-hour pricing trap |

### Module 7 — Governance, Security & BI

| # | Chapter | Covers |
|---|---------|--------|
| 7.1 | [Sensitive Data Protection](chapters/27-sensitive-data-protection.md) | InfoTypes, inspect and de-identify templates, findings, the de-identification methods |
| 7.2 | [Compliance, Residency & Encryption](chapters/28-compliance-residency-and-encryption.md) | Residency, HIPAA/PCI/SOC 2/FedRAMP, CMEK, transit encryption, shared responsibility |
| 7.3 | [Looker Studio & BI](chapters/29-looker-studio-and-bi.md) | Reports, connectors, calculated fields, the freshness-vs-cost tension |

### Module 8 — ML on GCP & Capstone

| # | Chapter | Covers |
|---|---------|--------|
| 8.1 | [Machine Learning Foundations](chapters/30-machine-learning-foundations.md) | Supervised/unsupervised, the workflow, metrics, overfitting, where the platform breaks |
| 8.2 | [Prebuilt & AutoML Models](chapters/31-prebuilt-and-automl-models.md) | Vision, Natural Language, Speech-to-Text, AutoML Vision/NL/Tables |
| 8.3 | [Custom Training & Vertex AI](chapters/32-custom-training-and-vertex-ai.md) | Datasets, notebooks, training jobs, the Model Registry, endpoints, MLOps |
| 8.4 | [BigQuery ML](chapters/33-bigquery-ml.md) | `CREATE MODEL`, the model types, `ML.EVALUATE`, `ML.PREDICT`, the no-movement advantage |
| 8.5 | [End-to-End Capstone](chapters/34-end-to-end-capstone.md) | The whole platform wired together, with its cost model and runbook |

---

## The Project

A working pipeline that runs **locally with no GCP account, no
credentials, and no bill**. It is a faithful simulation of the platform:
the resource hierarchy, the IAM policy engine, the cost model and the
service catalogue are all modelled in pure Python.

```
project/
├── local_runner.py          # the console the labs run against
├── core/
│   ├── service_catalog.py   # 34 services, 12 regions, 8 categories
│   ├── iam_policy.py        # 23 roles, inheritance, conditions, explicit deny
│   ├── cost_model.py        # the pricing model for every service
│   ├── pipeline_logic.py    # the pure business logic
│   └── platform_sim.py      # the project, the resources, the runtime
└── tests/                   # 102 tests (no cloud SDK required)
    ├── test_iam_and_cost.py
    ├── test_pipeline_logic.py
    └── test_audit_checks.py  # the linter's own checks, under test

notebooks/                   # exploratory work, executed by the linter
├── 01-explore-the-event-stream.ipynb
├── 02-validate-and-route-to-the-dead-letter-path.ipynb
└── 03-price-the-architectures.ipynb
```

The design decision that makes it work: **the core modules import
nothing from Google Cloud**. That is why `pytest` runs in under half a
second with no SDK installed — and why every number printed in the
chapters is a number the course actually produced.

```bash
python resources/sample_data.py --output-dir ./sample_data

python project/local_runner.py --run
# ingest: 4800 accepted, 0 rejected
# aggregate: 4 regions, 4800 events
# publish: 4800 messages to events-normalised
# load: partition 20260115, 4800 rows
#
# region,event_count,revenue_eur
# AMER,1238,464848.02
# APAC,1159,421049.85
# EMEA,1176,432544.17
# LATAM,1227,445554.36
#
# Dead-letter path
#   malformed rows rejected: 12
#     bad_amount               1
#     bad_timestamp            1
#     missing_event_id         1
#     missing_user_id          1
#     negative_amount          1
#     unknown_channel          1
#     unknown_currency         1
#     unknown_event_type       1
#     unknown_region           2
#     wrong_field_count        2
```

The reject counts are the point of the dead-letter path: **every reason
code appears at least once**, so the failure taxonomy is testable rather
than a hope. And because the dedup key is derived from the data
(`20260115:e00000001`) rather than from arrival time, a retry produces
the *same* rows — which is what makes a pipeline safe to re-run.

See [`project/README.md`](project/README.md) for the full walkthrough.

---

## Resources

| Resource | Purpose |
|----------|---------|
| [`resources/SETUP.md`](resources/SETUP.md) | The 5-minute local path, the optional GCP path, troubleshooting |
| [`resources/CHEATSHEET.md`](resources/CHEATSHEET.md) | `gcloud` reference, service-selection tables, IAM roles, cost formulas |
| [`resources/GLOSSARY.md`](resources/GLOSSARY.md) | Every term the course uses, defined |
| [`resources/FAQ.md`](resources/FAQ.md) | The questions students actually ask |
| [`resources/sample_data.py`](resources/sample_data.py) | Deterministic sample data, with `--hot-key-rate` |
| [`resources/audit_course.py`](resources/audit_course.py) | The course linter — see below |
| [`resources/build_notebooks.py`](resources/build_notebooks.py) | Regenerates the notebooks; `--check` detects drift |
| [`resources/execute_notebooks.py`](resources/execute_notebooks.py) | Runs every notebook end-to-end |

---

## Notebooks

Three exploratory notebooks sit alongside the chapters, for the work
that is *investigation* rather than *construction* — the part where you
look at data before you decide what to build.

| Notebook | What it answers |
|----------|-----------------|
| [`01-explore-the-event-stream.ipynb`](notebooks/01-explore-the-event-stream.ipynb) | What actually arrives in the raw stream, and what is the cardinality of each field? |
| [`02-validate-and-route-to-the-dead-letter-path.ipynb`](notebooks/02-validate-and-route-to-the-dead-letter-path.ipynb) | What is the complete failure taxonomy, and why is a reason code better than a boolean? |
| [`03-price-the-architectures.ipynb`](notebooks/03-price-the-architectures.ipynb) | What does each architecture actually cost, and why does the ranking depend on the inputs? |

They run against the same sample data as the rest of the course, need
no cloud SDK, and are **executed by the linter** — a notebook that
parses but does not run is a broken notebook, and parsing alone would
not have caught the missing brace that shipped in the first draft of
the exploration notebook.

```bash
jupyter lab notebooks/                  # explore interactively
python resources/execute_notebooks.py   # verify they all run
```

---

## Getting Started

```bash
cd portfolio/medium/google/data-analytics/GCP_DATA_ENGINEERING_COURSE

python3 -m venv .venv
source .venv/bin/activate

# Generate the deterministic dataset
python resources/sample_data.py --output-dir ./sample_data

# Run the pipeline — no GCP account required
python project/local_runner.py --run

# Run the tests
python3 -m pytest project/tests/ -q

# Lint the course
python resources/audit_course.py
```

---

## The Course Linter

The course ships with a static audit harness that catches the mistakes a
reader would otherwise only hit on a worker, hours into a job:

```bash
python resources/audit_course.py
```

It checks that:

- every relative link in every chapter resolves;
- every Python snippet in the chapters **parses**;
- every Python snippet in the chapters **executes**, in a fresh
  namespace, so a missing import is caught rather than silently
  rescued by an earlier block;
- every decorator and base class a snippet uses is either imported in
  that snippet, defined in it, or named in the surrounding prose;
- every chapter has all eight required sections, **in order**;
- every name a chapter imports from the course modules **actually
  exists** in those modules — this catches a renamed or misspelled
  function automatically;
- the published expected outputs match what the code really produces;
- every notebook is a valid `nbformat` document, imports only names that
  exist, and **executes end-to-end**;
- no leftover `TODO`/`FIXME` markers.

---

## Course Conventions

- **Chapters** are `NN-kebab-case.md`, numbered from 01, in eight
  sections: What you will learn, Concept, Hands-On, Common Errors and
  Fixes, Production Notes, Key Takeaways, Practice Exercises, Further
  Reading.
- **Pipeline diagrams and shell output** use ` ```text ` fences, so the
  linter does not try to parse a fragment as Python.
- **Placeholders** like `YOUR_PROJECT_ID` are expected in shell commands
  and must be replaced with your own values.
- **Every error message quoted in this course is real**, copied from the
  actual CLI or API.

---

## Interview Preparation

A bank of **128 questions** — 88 across six topic files plus a
top-40 — written the way a senior engineer answers them: a direct
answer, the mechanism, the trade-off, a production detail with numbers,
and often a failure story.

| File | Questions | Theme |
|------|-----------|-------|
| [`interview/01-platform-fundamentals.md`](interview/01-platform-fundamentals.md) | 14 | Cloud concepts, regions, hierarchy, IAM, compute |
| [`interview/02-storage-and-databases.md`](interview/02-storage-and-databases.md) | 14 | Storage, SQL, Spanner, NoSQL, database selection |
| [`interview/03-analytics-and-cost.md`](interview/03-analytics-and-cost.md) | 16 | BigQuery, optimisation, BigLake, governance, cost |
| [`interview/04-streaming-and-ingestion.md`](interview/04-streaming-and-ingestion.md) | 14 | Kafka, Pub/Sub, CDC, transfer services |
| [`interview/05-processing-and-orchestration.md`](interview/05-processing-and-orchestration.md) | 16 | Hadoop, Spark, Beam, Airflow, Dataform, no-code |
| [`interview/06-governance-security-and-ml.md`](interview/06-governance-security-and-ml.md) | 14 | DLP, residency, encryption, BI, ML |
| [`interview/top-40.md`](interview/top-40.md) | 40 | The highest-yield subset — read the night before |

See [`interview/README.md`](interview/README.md) for the 14-day study plan.

---

## Related Material

Within this course:

- [`interview/README.md`](interview/README.md) — the 14-day study plan
  for the 128-question bank.
- [`resources/CHEATSHEET.md`](resources/CHEATSHEET.md) — the `gcloud`
  reference, service-selection tables and cost formulas.
- [`resources/GLOSSARY.md`](resources/GLOSSARY.md) — every term the
  course uses, defined.
- [`CURRICULUM.md`](CURRICULUM.md) — the module-by-module design.

---

*Built to be run, not just read. Every command in this course has been
executed, and every error message has been reproduced.*
