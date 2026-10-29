# Google Dataproc with PySpark — Beginner to Pro

A complete, hands-on deep-knowledge guide to **Google Cloud Dataproc** for data engineers.
Every topic is taught from first principles — Big Data foundations, Spark architecture, cluster
economics — and then exercised for real through the **`gcloud` CLI**, **interactive notebooks**,
and **production-style PySpark jobs** running on Dataproc.

> **Duration:** 4 sections · 12 chapters · ~8h 30m
> **Audience:** Data engineers, analytics engineers, and anyone who has to build, run, or cost out
> a distributed batch pipeline on Google Cloud.

---

## What You Will Learn

- **Why Big Data exists** — the four Vs, what Hadoop solved, what Spark changed, and where
  Dataproc fits into the picture.
- **Full in & out of Dataproc** — create, size, autoscale, secure, monitor, and delete clusters
  without touching a Hadoop distro.
- **PySpark from scratch** — RDDs, DataFrames, the Catalyst optimizer, and exactly when each
  abstraction is the right tool.
- **Multi-source extraction** — GCS, BigQuery, JDBC, Pub/Sub, and Kafka into one DataFrame.
- **Multi-sink writing** — Parquet, BigQuery, JDBC, Pub/Sub, and Kafka, with idempotency and
  atomicity handled properly.
- **Deep transformation coverage** — joins, windows, aggregations, nested data, skew handling, and
  data quality gates.
- **Two complete case studies** — retail sales analytics and healthcare claims processing, each
  with a full runnable production job.
- **An end-to-end pipeline** — bronze/silver/gold medallion architecture, orchestration, quality
  gates, observability, and a troubleshooting playbook.

---

## Course Structure

### Module 1 — Foundations & Dataproc
| # | Chapter | Covers |
|---|---------|--------|
| 1.1 | [Big Data Challenges: Hadoop → Spark → Dataproc](chapters/01-bigdata-challenges-and-landscape.md) | Four Vs, MapReduce limits, Spark's in-memory model, Dataproc's value |
| 1.2 | [Dataproc Cluster Creation & Management](chapters/02-dataproc-cluster-creation-and-management.md) | `gcloud dataproc clusters create`, machine types, autoscaling, IAM, VPC, cost control |
| 1.3 | [Submitting Jobs to Dataproc](chapters/03-submitting-jobs-to-dataproc.md) | `gcloud dataproc jobs submit pyspark`, Jupyter, SSH, job states, logging, metadata server |

### Module 2 — PySpark Core
| # | Chapter | Covers |
|---|---------|--------|
| 2.1 | [PySpark Fundamentals & Spark Architecture](chapters/04-pyspark-fundamentals-and-spark-architecture.md) | Driver/executor model, DAG scheduling, lazy evaluation, read/write, caching |
| 2.2 | [RDDs vs DataFrames: Choosing the Right Abstraction](chapters/05-rdds-vs-dataframes-and-when-to-use-each.md) | Lineage, checkpointing, Catalyst, `explain(True)`, `pandas_udf`, when RDDs still win |
| 2.3 | [Extracting Data from Multiple Sources](chapters/06-extracting-data-from-multiple-sources.md) | GCS, BigQuery, JDBC, Pub/Sub, Kafka; error modes; `_corrupt_record` quarantine |
| 2.4 | [Writing DataFrames to Multiple Sinks](chapters/07-writing-dataframe-to-multiple-sinks.md) | BigQuery (direct vs indirect), partitioned Parquet, JDBC batching, fan-out |
| 2.5 | [PySpark Transformations — Part 1](chapters/08-pyspark-transformations-part-1.md) | Column API, casting, nulls, strings, all 7 join types, `groupBy`, window functions |
| 2.6 | [PySpark Transformations — Part 2](chapters/09-pyspark-transformations-part-2.md) | Advanced windows, skew, `repartition` vs `coalesce`, nested data, quality patterns |

### Module 3 — Case Studies
| # | Chapter | Covers |
|---|---------|--------|
| 3.1 | [Case Study 1: Retail Sales Analytics Pipeline](chapters/10-case-study-1-retail-sales-analytics.md) | POS transactions, dimension conformance, dedup, reconciliation, BigQuery marts |
| 3.2 | [Case Study 2: Healthcare Claims Processing](chapters/11-case-study-2-healthcare-claims-processing.md) | Nested JSON, `from_json`, `explode`, ICD validation, quarantine, z-score outliers |
| 3.3 | [End-to-End Batch Pipeline](chapters/12-end-to-end-batch-pipeline.md) | Medallion layers, Workflows, Composer, idempotency, quality gates, troubleshooting |

### Module 4 — Assignments & Practice
| # | Chapter | Covers |
|---|---------|--------|
| 4.1 | [Assignments & Capstone Projects](chapters/13-assignments-and-capstone-projects.md) | Four graded projects, rubric, stretch goals, self-assessment |

---

## Hands-On Notebooks

Every notebook runs **top-to-bottom offline** — sample data is generated in-cell, so you can work
through the whole course without spending a cent. Cells that touch GCS or BigQuery are clearly
marked and left commented until you are ready to authenticate.

| # | Notebook | What you build |
|---|----------|----------------|
| 01 | [Setup & Cluster Basics](notebooks/01-setup-and-cluster-basics.ipynb) | `SparkSession`, config knobs, first DataFrame, reading the Spark UI |
| 02 | [RDD Fundamentals](notebooks/02-rdd-fundamentals.ipynb) | Parallelized collections, transformations vs actions, `reduceByKey`, lineage |
| 03 | [DataFrames & Schema](notebooks/03-dataframes-and-schema.ipynb) | Explicit schemas, casting, null handling, `try_cast` for bad data |
| 04 | [Transformations & Joins](notebooks/04-transformations-and-joins.ipynb) | Joins, broadcasts, windows, `dropDuplicates`, `explain(True)` |
| 05 | [Reading from GCS & BigQuery](notebooks/05-reading-from-gcs-and-bigquery.ipynb) | Multi-source reads, glob patterns, incremental BigQuery, error modes |
| 06 | [Writing to Multiple Sinks](notebooks/06-writing-to-multiple-sinks.ipynb) | BigQuery writes, partitioned Parquet, JDBC batching, fan-out |
| 07 | [Case Study: Retail](notebooks/07-case-study-retail.ipynb) | Full retail ETL with dedup, joins, quality gates |
| 08 | [Case Study: Healthcare](notebooks/08-case-study-healthcare.ipynb) | Nested JSON, validation, quarantine, anomaly detection |
| 09 | [Performance Tuning](notebooks/09-performance-tuning.ipynb) | `explain` reading, shuffle tuning, skew, `pandas_udf` benchmark, AQE |
| 10 | [End-to-End Pipeline](notebooks/10-end-to-end-pipeline.ipynb) | Bronze→silver→gold, idempotency proof, quality gate that fails loudly |

---

## SQL Scripts

Every SQL example in the chapters is also available as a standalone, runnable BigQuery Standard SQL
script in [`sql/`](sql/).

| Script | Contents |
|--------|----------|
| [`sql/01_bigquery_setup.sql`](sql/01_bigquery_setup.sql) | Medallion schemas (bronze/silver/gold/mart/quarantine), labels, expiration |
| [`sql/02_dimensions.sql`](sql/02_dimensions.sql) | SCD Type 2 dimension DDL with surrogate keys and integrity checks |
| [`sql/03_fact_tables.sql`](sql/03_fact_tables.sql) | Partitioned, clustered fact tables and quarantine tables |
| [`sql/04_marts_and_aggregates.sql`](sql/04_marts_and_aggregates.sql) | Aggregate marts with CTAS refresh and `QUALIFY` ranking |
| [`sql/05_data_quality_checks.sql`](sql/05_data_quality_checks.sql) | 12 validation queries — null rates, orphans, duplicates, reconciliation |
| [`sql/06_case_study_retail.sql`](sql/06_case_study_retail.sql) | Full retail model layer with SCD2 merges |
| [`sql/07_case_study_healthcare.sql`](sql/07_case_study_healthcare.sql) | Healthcare model layer with ICD validation and z-score mart |
| [`sql/08_pipeline_orchestration.sql`](sql/08_pipeline_orchestration.sql) | Idempotent multi-statement script with `DECLARE` and `RAISE EXCEPTION` |

---

## Resources

| Resource | Description |
|----------|-------------|
| [`resources/SETUP.md`](resources/SETUP.md) | Full environment setup — account, project, billing, IAM, service accounts, buckets |
| [`resources/CHEATSHEET.md`](resources/CHEATSHEET.md) | `gcloud`, PySpark API, Spark configs, connector options — one page per topic |
| [`resources/GLOSSARY.md`](resources/GLOSSARY.md) | 100+ Spark/Dataproc/Big Data terms defined |
| [`resources/FAQ.md`](resources/FAQ.md) | 40+ student questions across cost, PySpark, performance, troubleshooting |
| [`resources/spark_helpers.py`](resources/spark_helpers.py) | Reusable `SparkSession` factory, quality assertions, sink wrappers |
| [`resources/sample_data.py`](resources/sample_data.py) | Deterministic synthetic retail + healthcare data (with deliberately dirty rows) |
| [`resources/requirements.txt`](resources/requirements.txt) | Python dependencies for the notebooks |

---

## Getting Started

```bash
# 1. Read the setup guide
less resources/SETUP.md

# 2. Create a virtual environment and install dependencies
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/data-engineering/data-Course/google/dataproc
python3 -m venv .venv
source .venv/bin/activate
pip install -r resources/requirements.txt

# 3. Run the first notebook — no cloud account needed
jupyter lab notebooks/01-setup-and-cluster-basics.ipynb
```

When you're ready to move to a real cluster:

```bash
# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Create an ephemeral cluster with a deletion schedule
gcloud dataproc clusters create dataproc-course \
  --region=europe-west1 \
  --image-version=2.2-debian12 \
  --master-machine-type=n1-standard-4 \
  --worker-machine-type=n1-standard-4 \
  --num-workers=2 \
  --optional-components=JUPYTER \
  --enable-component-gateway \
  --delete-max-idle=30m

# Submit a job
gcloud dataproc jobs submit pyspark \
  --cluster=dataproc-course \
  --region=europe-west1 \
  -- main.py --input-path=gs://YOUR_BUCKET/raw --output-project=YOUR_PROJECT_ID

# Clean up — always
gcloud dataproc clusters delete dataproc-course --region=europe-west1 --quiet
```

---

## Course Conventions

Throughout the chapters:

- **`bash`** blocks use the `gcloud` CLI or `bq` for setup and operation.
- **`python`** blocks are PySpark 3.5 targeting the Dataproc `2.2-debian12` image.
- **`sql`** blocks are BigQuery Standard SQL.
- ⚠️ blocks mark actions that **cost money** or **delete data**.
- 💡 blocks mark production tips that go beyond the basics.
- Every chapter ends with **Key Takeaways** and **Practice Exercises**.

### Which cluster commands to use

The current CLI surface is `gcloud dataproc jobs submit pyspark`. The older
`gcloud dataproc clusters submit` form still appears in older tutorials and blog posts — this
course uses the current form throughout, and flags the legacy one where it comes up.

### Image version

Every command in this course pins `--image-version=2.2-debian12` (Spark 3.5.3, Python 3.11).
**Never rely on the default image version** — it changes, and your job's behavior can change
with it.

---

## Related Courses

Sibling GCP courses in this repository: `BigQuery`, `Dataflow`, `Pub/Sub`, `Composer`, `Dataform`,
`Dataplex`, `Looker`.

---

*Built for data engineers who need to know not just how to submit a Spark job, but why it costs
what it costs, how to make it ten times faster, and how to make it safe to run twice.*
