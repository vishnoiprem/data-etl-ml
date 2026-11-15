# Data Engineering on GCP

## Getting Started with Data Engineering on GCP
* Pre-requisite Skills for the course
* Overview of Google Cloud Platform
* Signing up for GCP
* Setup Google Cloud SDK
* Overview of Analytics Services on GCP

## Setting up Data Lake using GCS
* Setup GCS Bucket
* Overview of GCS Web UI
* Overview of gsutil
* Overview of Data Sets
* Manage Files in GCS using gsutil commands
* Copy Retail Data Set to GCS using gsutil commands
* Manage Files in GCS using Python
* Overview of processing data in GCS using Pandas

## Getting Started with GCP Secrets Manager
* Overview of Secrets Manager
* Create Secret using UI
* Managing Secrets using Google Cloud CLI
* Reading Secret Details using Python
* Use Cases of Secrets


## Setup Postgres Database using Cloud SQL
* Overview of Cloud SQL
* Setup Postgres Database Server using Cloud SQL
* Configure Network to Connect to Database
* Install PostgreSQL Database Server
* Configure psql CLI
* Connect to Postgres Database using pgAdmin
* Create Database for Retail using Postgres
* Setup Tables and Load Data using Postgres

## Data Warehouse using Google Big Query
* Getting Started with Google Big Query
* Overview of Running Queries using Public Data Sets
* Setup Database for Retail in Google Big Query
* Setup Tables and Load Data using Google Big Query
* Compute Daily Product Revenue using Google Big Query
* Create Dimensions and Facts using Google Big Query
* Cumulative Aggregations and Ranking using Google Big Query

## Data Processing using Google Functions
* Overview of Google Cloud Functions
* Validate GCS Bucket
* Create Google Cloud Function for Cloud Storage
* Update Requirements for the Project
* Review File Converter Logic
* Deploy File Converter Logic

## Big Data Processing using Google Dataproc
* Overview of GCP Dataproc
* Setup Single Node Hadoop and Spark Cluster using Dataproc
* Setup Remote Development Environment using VS Code
* Review Data Sets
* Run Spark SQL Commands or Scripts using Dataproc
* Run Pyspark Applications using Dataproc
* Review Spark Jobs on Dataproc using Spark UI

## Big Data Processing using Databricks on GCP
* Overview of Databricks on GCP
* Overview of DBFS
* Mount GCS Buckets on DBFS
* Run Spark SQL Commands or Scripts using Databricks Workflows
* Run Pyspark Applications using Databricks
* Review Spark Jobs on Dataproc using Spark UI

## Orchestration using Cloud Composer
* Overview of Google Cloud Composer
* Create Cloud Composer Environment
* Development Process of Airflow DAGs for Cloud Composer
* Install required dependencies for development
* Develop Airflow DAG for Spark SQL Jobs on Dataproc
* Develop Airflow DAG for Dataproc Workflow Template
* Deploy DAGs to Cloud Composer and Monitor

## Choosing between Dataproc, Databricks and Composer
* The two axes: runtime ownership and pipeline-metadata ownership
* Dataproc vs Databricks: control vs platform
* Composer vs Databricks Workflows vs Dataproc Workflows
* The same pipeline, three implementations
* A decision procedure, and the stack I would actually ship

---

## Chapter index

| File | Module |
|---|---|
| [01 Getting Started with Data Engineering on GCP](01 Getting Started with Data Engineering on GCP.md) | Getting Started |
| [02 Setting up Data Lake using GCS](02 Setting up Data Lake using GCS.md) | Data Lake |
| [03 Setup Local Environment using VS Code](03 Setup Local Environment using VS Code.md) | Local environment (Windows and Mac) |
| [04 Setup Postgres Database using GCP Cloud SQL](04 Setup Postgres Database using GCP Cloud SQL.md) | Cloud SQL and Secrets |
| [05 Data Warehouse using Google Big Query](05 Data Warehouse using Google Big Query.md) | BigQuery |
| [06 Data Processing using Google Cloud Functions](06 Data Processing using Google Cloud Functions.md) | Cloud Functions |
| [07 Big Data Processing using Google Dataproc](07 Big Data Processing using Google Dataproc.md) | Dataproc |
| [08 Big Data Processing using Databricks on GCP](08 Big Data Processing using Databricks on GCP.md) | Databricks on GCP |
| [09 Integration of Dataproc and Google BigQuery](09 Integration of Dataproc and Google BigQuery.md) | Spark and BigQuery |
| [12 Data Pipeline Orchestration using Google Cloud Composer](12 Data Pipeline Orchestration using Google Cloud Composer.md) | Composer |
| [13 Choosing between Dataproc, Databricks and Composer](13 Choosing between Dataproc, Databricks and Composer.md) | The comparison |

Modules 10 (ELT with Dataproc) and 11 (ELT with Databricks) have no `.md`
file — their material is in `notebooks/08 ELT Data Pipelines using Dataproc
on GCP/`, `notebooks/10 ELT Data Pipelines using Databricks on GCP/`,
`scripts/daily_product_revenue/`, and
`apps/databricks_jobs/daily_product_revenue_job.json`.

See also [README.md](README.md) for the setup instructions and
[CURRICULUM_COVERAGE.md](CURRICULUM_COVERAGE.md) for the item-by-item gap
analysis.