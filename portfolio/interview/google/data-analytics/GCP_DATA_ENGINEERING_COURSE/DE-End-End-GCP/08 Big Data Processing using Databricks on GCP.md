# Big Data Processing using Databricks on GCP

## Signing up for Databricks on GCP
Let us see how we can sign up for Databricks Subscription on GCP.
* Login to GCP Console.
* Search for Databricks in global search bar and complete the sign up process.

## Creating Databricks Workspace on GCP

As we have signed up for Databricks Subscription for GCP, it is time for us to create Databricks Workspace. Follow the steps as demonstrated in the lecture to create the Databricks Workspace.

Here are some references to review and also request to change the quota limits.
* Review Quotas by going to this [page](https://docs.gcp.databricks.com/administration-guide/account-settings-gcp/quotas.html).
* [Page](https://console.cloud.google.com/iam-admin/quotas) to review and change the quota limits.

## Overview of Databricks on GCP
Let us get an overview of Databricks on Google Cloud Platform.
* Databricks is available on all leading cloud platforms.
  * AWS
  * Azure
  * **Google Cloud Platform (GCP)**
* Databricks is cloud agnostic Spark based Big Data Processing Platform.
* Here are the features of Databricks on GCP.
  * Seamless Integration with GCS for Data Lake Storage.
  * Purpose Built Clusters for different workloads.
  * Pay-as-you-go
  * Scalability including Auto Scalability
  * Easy Integrations with other Google Services such as Big Query, Looker, etc
  * Big Query is used for Data Warehousing while Looker is used for Business Intelligence (Visualizations such as Reports and Dashboards).


## Overview of Databricks CLI

As part of this lecture we will understand what is Databricks CLI and also how to configure Databricks CLI.

## Limitations of Managing DBFS using Databricks CLI
Let us understand the limitations of managing DBFS on GCP using Databricks CLI.
* `databricks fs` can be used to manage DBFS Files and Folders on AWS and Azure.
* On GCP, the feature is currently not available.

Because `databricks fs` is unavailable on GCP, DBFS files are managed with
`gsutil` instead — which is what the next section does. On GCP, the GCS
bucket *is* the durable store; DBFS is the workspace-local mount point on
top of it.

## Creating a Databricks Cluster on GCP

A workspace without a cluster cannot run anything. Let us create one.

Go to **Compute → Clusters → Create cluster**.

| Setting | Value | Why |
|---|---|---|
| Cluster name | `retail-etl` | Matches the workload, not the person |
| Cluster type | `Single Node` | The daily product revenue pipeline is small. Single node has no shuffle latency and is much cheaper |
| Databricks Runtime | A recent DBR, e.g. `15.4.x-scala2.12` | Pin the runtime. An unpinned DBR means a notebook that worked yesterday can break today |
| Node type | `i3.xlarge` | 4 vCPU / 32 GB. Enough for the retail data set with headroom |
| Number of workers | `2` | Scales out from here if the data grows |
| Spark version | Bundled with DBR | Do not override unless you need a specific feature |
| Advanced → Init scripts | None | Keep the runtime clean; add init scripts only when a JAR is genuinely required |
| Advanced → Photon | Off | Photon accelerates SQL. This pipeline is too small to notice, and it adds a licensing question |
| Cluster policies | None attached | A policy is how you enforce node types and runtime versions across the workspace |

Then set the GCP resources for the cluster:

| Setting | Value | Why |
|---|---|---|
| GCP service account | A dedicated SA, e.g. `retail-etl-sa` | Not the default compute SA. The default has broad project access; a workload-specific SA does not |
| Availability zone / region | Same region as the GCS bucket and BigQuery | Cross-region reads are slow and billed |
| Network | The VPC where the bucket lives | Databricks needs to reach GCS and BigQuery privately |

The service account needs, at minimum:

```shell
# Read the lake and write the results
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:retail-etl-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# Write the output location
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:retail-etl-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectCreator"

# Read and write the BigQuery tables
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:retail-etl-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
```

> **Why a dedicated service account rather than the default compute SA?** The
> default compute SA carries project-wide permissions that the default
> compute SA has to have in order to function. A workload-specific SA
> carries only what that workload needs. When the pipeline is the thing
> under attack — a compromised notebook, a leaked credential — the blast
> radius is the pipeline's permissions, not the project's.

### Verifying the cluster

Attach to the cluster and confirm Spark is actually running:

```python
# In a Databricks notebook attached to the cluster
spark.conf.get("spark.version")

spark.sql("SELECT current_database(), current_user()").show()
```

If `spark.version` returns a DBR version and the session query returns a
row, the cluster is live and the service account is working.

### Cluster lifecycle for a daily pipeline

An always-on cluster costs money for every hour it runs, including the 23
hours a day this pipeline is idle. Two options:

- **All-purpose cluster** — always running. Simple, but you pay for idle
  time.
- **Job cluster** — created when a Job task runs, terminated when it
  finishes. The right choice for a scheduled pipeline, and this is what the
  Workflows section uses below.

For a daily batch, use **job clusters**. For interactive exploration during
development, keep one all-purpose cluster and terminate it when you are
done.

## Unity Catalog and Storage on GCP

Two governance questions come up with any Databricks-on-GCP project: *what
is the catalog*, and *where does the data physically live*.

### Where the data lives

| | Dataproc on GCP | Databricks on GCP |
|---|---|---|
| Default storage | GCS directly | DBFS (workspace-local, backed by a GCS bucket) |
| Access pattern | `gs://bucket/path` | `dbfs:/path`, or a mounted GCS path |
| Direct GCS access | Native | Supported via Unity Catalog external locations or direct `gs://` paths |
| Lifecycle | Governed by GCS bucket policies | Governed by Unity Catalog permissions |

The practical difference: on Dataproc, GCS *is* the filesystem and GCS IAM
applies directly. On Databricks, DBFS is the default and Unity Catalog
governs access — but GCS remains the durable store underneath, and you can
mount GCS paths directly when you want GCS-native semantics.

### Unity Catalog

Unity Catalog is Databricks' metastore — the catalog, schema, and table
management layer, with lineage and column-level lineage attached.

On GCP, Unity Catalog requires a metastore backed by a GCS bucket in the
same region as the workspace. The setup is:

```shell
# The metastore root must be a GCS bucket you own
gsutil mb -l us-central1 gs://YOUR_PROJECT_ID-metastore

# Create the metastore, pointing at that bucket
databricks metastores create \
  --name retail_metastore \
  --storage-root gs://YOUR_PROJECT_ID-metastore \
  --region us-central1
```

Then assign it to the workspace:

```shell
databricks workspace metastore assign \
  --workspace-id YOUR_WORKSPACE_ID \
  --metastore-id YOUR_METASTORE_ID \
  --default-catalog-name retail_catalog
```

What Unity Catalog buys over plain GCS IAM:

- **One namespace** (`catalog.schema.table`) instead of bucket paths and
  Hive databases.
- **Column-level lineage** — you can see which downstream tables depend on
  a column, which is what you need when a source schema changes.
- **Grant-once governance** — permissions live in the catalog, so revoking
  access is a catalog operation, not a sweep over every bucket.

> **Scope note for this course.** The pipeline in
> `notebooks/10 ELT Data Pipelines using Databricks on GCP/` uses DBFS
> paths (`dbfs:/public/retail_db`) and Hive-style temporary views, which
> is the pre-Unity-Catalog style. That keeps the exercise focused on the
> Spark and orchestration mechanics. Unity Catalog is shown here because
> you will be asked about it in an interview, and because it is the correct
> choice for a production workspace.

## Copy Data Sets to DBFS using gsutil Commands

Let us copy retail data set to DBFS using gsutil commands. We will be using `dbfs:/public` as base folder for the datasets.
* Create DBFS Folder using Databricks Notebook by name `public`
* Copy the retail_db data sets to relevant GCS bucket (using GCS Web UI or gsutil)
* Validate using `%fs` command on Databricks Notebook.

Here are the gsutil CLI commands that can be used for above mentioned tasks for the reference.

```shell
gsutil ls gs://databricks-2976459147516244/2976459147516244
gsutil cp -r data/retail_db gs://databricks-2976459147516244/2976459147516244/public/retail_db
gsutil ls -r gs://databricks-2976459147516244/public/retail_db
```

Here are the Databricks Notebook Commands used for your reference.

```shell
%fs mkdirs dbfs:/public
%fs ls dbfs:/public
%fs ls dbfs:/public/retail_db/orders
```

Here are the Spark SQL Commands used to process the data.

```sql
CREATE TEMPORARY VIEW orders (
    order_id INT,
    order_date STRING,
    order_customer_id INT,
    order_status STRING
) USING CSV
OPTIONS (
    path='dbfs:/public/retail_db/orders/'
)

SELECT order_status, count(*) AS order_count 
FROM orders
GROUP BY 1
ORDER BY 2 DESC
```

Here is the Pyspark code used to process the data.

```python
schema = 'order_id INT, order_date STRING, order_customer_id INT, order_status STRING'

orders = spark. \
    read. \
    csv('/public/retail_db/orders', schema=schema)

orders. \
    groupBy('order_status'). \
    count(). \
    show()
```

## Spark SQL Example using Databricks

Let us go ahead and compute daily product revenue using Spark SQL. We can compute daily product revenue using `orders` and `order_items` data sets.

Here are the steps involved to compute daily product revenue using Spark SQL.
* Create Temporary View by name `orders` pointing to `dbfs:/public/retail_db/orders`.
* Create Temporary View by name `order_items` pointing to `dbfs:/public/retail_db/order_items`.
* Develop Query to compute Daily Product Revenue.
* Make sure output is written back to `dbfs:/public/retail_db/daily_product_revenue` using parquet file format.
* Validate whether the output is saved in DBFS as per the expectations or not.
* The queries will be provided as part of Databricks Notebook.

## Pyspark Example using Databricks

Let us go ahead and compute daily product revenue using Pyspark Data Frame APIs. We can compute daily product revenue using `orders` and `order_items` data sets.

Here are the steps involved to compute daily product revenue using Pyspark Data Frame APIs.
* Create Data Frame by name `orders` pointing to `dbfs:/public/retail_db/orders`.
* Create Data Frame by name `order_items` pointing to `dbfs:/public/retail_db/order_items`.
* Develop Query to compute Daily Product Revenue.
* Make sure output is written back to `dbfs:/public/retail_db/daily_product_revenue` using parquet file format.
* As we will be using same location again and again, we need to make sure the data is written to target location using overwrite mode.
* Validate whether the output is saved in DBFS as per the expectations or not.
* The queries will be provided as part of Databricks Notebook.

## Overview of Databricks Workflows
Let us get an overview of Databricks Workflows.
* Data Pipelines are deployed using Workflows in Databricks.
* We create Jobs under Workflows. Each Job is group of tasks.
* Complex Spark Applications needs to be deployed using a Job under Workflows.
* Each Job can have multiple tasks with dependencies between them.
* If series of steps or tasks in the pipeline need to run using Databricks platform with out depending on external applications, then they can be orchestrated using a Job.
* We can pass parameters at each Task Level or Job Level.
* Each Task in the Job can be configured using different clusters based on the run time as well as cluster size requirements for the respective Task.

## Modularize Spark Applications as Multiple Tasks
Let us see how to modularize Spark Applications as Multiple Tasks.
* We will use folders under `retail_db`.

The logic will be divided into two SQL based Notebooks.
* File Format Converter - converts CSV to Parquet based on the argument passed.
* Compute Daily Product Revenue
* We will also create additional Notebook, to validate whether Notebooks are working as expected or not.

A dbc archive will be provided under the notebooks repository. One can just export into their platform and review the SQL Notebooks.

The archive contains five notebooks:

| Notebook | Language | Purpose |
|---|---|---|
| `01 Cleanup Database and Datasets` | SQL + Python | Drops the bronze database and removes the bronze and gold directories |
| `02 File Format Converter` | Python | Converts one dataset from CSV to Parquet. Parameterised by `src_base_dir`, `bronze_base_dir`, `ds` |
| `03 Create Spark SQL Tables` | SQL | Creates an external table over the bronze Parquet. Parameterised by `table_name`, `bronze_base_dir` |
| `04 Daily Product Revenue` | SQL | Aggregates order revenue into the gold layer. Parameterised by `gold_base_dir` |
| `Validate Notebook Runs` | SQL | Verifies the output landed correctly |

Note that `02 File Format Converter` is used **twice** — once for
`orders`, once for `order_items` — with different parameters. That reuse is
the reason the pipeline is modularised this way, and it is why the same
notebook appears as two separate tasks in the Job.

## Orchestration using Databricks Workflows
As the required Notebooks are ready, let us go ahead and create Databricks Workflow or Job with multiple tasks. We will create tasks using relevant Notebooks.
* Create a task by name `FileConverterOrders` to convert file format of orders data set.
* Create a task by name `FileConverterOrderItems` to convert file format of order_items data set.
* Create a task by name `ComputeDailyProductRevenue` to compute daily product revenue.
* Add the tasks to convert file format to the workflow without any dependencies.
* Add the task to compute daily product revenue to the workflow. Add both the file format converter tasks as dependencies to this one as dependencies.

### Passing Parameters to a Task

A Job passes parameters to a notebook task two ways, and they behave
differently. This distinction trips up most people.

**1. Job base parameters → widget values.**

The Job's `base_parameters` map into the notebook's `dbutils.widgets`
values. In `02 File Format Converter` the widgets are declared as:

```python
dbutils.widgets.text('src_base_dir', '', label='Enter Source Base Dir')
dbutils.widgets.text('bronze_base_dir', '', label='Enter Target Base Dir')
dbutils.widgets.text('ds', '', label='Enter Dataset Name')
```

and read back with `dbutils.widgets.get(...)`. The Job supplies
`src_base_dir`, `bronze_base_dir` and `ds` as base parameters, so the
notebook receives them without any code change.

**2. Task values → another task's output.**

This is the more powerful pattern. A task can publish a value at runtime,
and a downstream task can read it. The API is **`dbutils.jobs.taskValues`**.

In `01 Cleanup Database and Datasets`, the final cell removes the previous
run's output:

```python
%python
dbutils.fs.rm(dbutils.widgets.get('bronze_base_dir'), recurse=True)
```

That is a notebook cleaning up after itself. The better pattern is to let
the cleanup task *report* what it removed, and let the downstream task
consume it:

```python
# In the cleanup notebook — publish the location that was cleared
cleared_path = dbutils.widgets.get('bronze_base_dir')
dbutils.fs.rm(cleared_path, recurse=True)
dbutils.jobs.taskValues.set(key="cleared_bronze_path", value=cleared_path)
```

```python
# In the downstream notebook — consume the upstream task's value
cleared_path = dbutils.jobs.taskValues.get(
    taskKey="cleanup",
    key="cleared_bronze_path",
    debugValue="dbfs:/public/retail_db_bronze",
)
```

The signatures are:

```python
dbutils.jobs.taskValues.set(key=..., value=...)
dbutils.jobs.taskValues.get(taskKey=..., key=..., default=..., debugValue=...)
```

Both are **Python-only** — they do not work in a SQL or Scala notebook.
`get` requires the upstream task's name, which is why `taskKey="cleanup"`
must match the `task_key` in the Job definition. `default` is used when the
key cannot be found; `debugValue` is what the code sees when you run the
notebook interactively, outside a Job.

Values can also be referenced from the Job definition itself, without
Python, using dynamic value references:

```text
{{tasks.cleanup.values.cleared_bronze_path}}
```

**When each one matters**

| | Base parameters | Task values |
|---|---|---|
| Set by | The Job definition | An upstream task at runtime |
| Value known at | Job start | Only after the upstream task runs |
| Set with | The Job's `base_parameters` | `dbutils.jobs.taskValues.set(...)` |
| Read in notebook with | `dbutils.widgets.get(...)` | `dbutils.jobs.taskValues.get(...)` |
| Language | Any | Python only |
| Use when | The value is known upfront — a date, a bucket name | The value is only knowable after computing — a max id, a discovered partition, a schema version |

> **The practical rule:** if the value is in the Job definition, it is a
> base parameter. If it is computed during the run, it is a task value.
> Mixing them up produces a notebook that works when run manually and
> fails when run as a Job — because the manual run left the widget set
> interactively, and the Job run did not.
>
> **On `dbutils.notebook.task.reparameterize`:** you may see this name in
> older blog posts and tutorials. It is not a Databricks API. The real
> one is `dbutils.jobs.taskValues`. If an interview answer cites the
> former, it will be wrong.

### The Job definition as code

The GUI in the section above is how you create a Job by hand. But a Job
built only in the UI is not reviewable, not diffable, and not reproducible —
there is no artifact to commit. The Jobs API accepts the same definition as
JSON, and that JSON can live in version control.

The export for this pipeline is at
`apps/databricks_jobs/daily_product_revenue_job.json`.

Create or update the Job from it:

```shell
databricks jobs create --json-file apps/databricks_jobs/daily_product_revenue_job.json
```

To update an existing Job by id:

```shell
databricks jobs update --job-id 123456789012345 \
  --json-file apps/databricks_jobs/daily_product_revenue_job.json
```

The task graph it encodes:

```text
              ┌──────────────────────────────┐
              │ cleanup                      │
              │ 01 Cleanup Database and Data  │
              └───────┬──────────────┬───────┘
                      │              │
            ┌─────────▼──────┐  ┌────▼─────────────────┐
            │ convert_orders │  │ convert_order_items   │
            │ 02 File Format │  │ 02 File Format        │
            │    Converter   │  │    Converter          │
            └─────────┬──────┘  └────┬─────────────────┘
                      │              │
                      └──────┬───────┘
                             │
                 ┌───────────▼──────────────┐
                 │ create_spark_sql_tables  │
                 │ 03 Create Spark SQL      │
                 └───────────┬──────────────┘
                             │
                 ┌───────────▼──────────────┐
                 │ daily_product_revenue    │
                 │ 04 Daily Product Revenue │
                 └───────────┬──────────────┘
                             │
                 ┌───────────▼──────────────┐
                 │ validate                 │
                 │ Validate Notebook Runs   │
                 └──────────────────────────┘
```

Note `concurrency: 1` and `max_concurrent_runs: 1`. Two concurrent runs of
this pipeline would have the cleanup task deleting the bronze directory out
from under the convert tasks. That is the single most common way a
Databricks Job corrupts its own output, and it is why the concurrency
setting is not optional.

## Run and Validate Databricks Workflows
Let us understand different options to run jobs or workflows and also let us see how to run the job or workflow using **Run now**.

Here are the different options to run jobs or workflows.
* Run now
* Run now with parameters
* Using Schedule (supports cron syntax as well)

Let us run the job or workflow and review the details at job or workflow level.

From the CLI, trigger a run and watch it:

```shell
# Trigger the job
databricks jobs run-now --job-id 123456789012345

# Check the run state
databricks jobs runs list --job-id 123456789012345 --limit 5

# Get the run's output and state
databricks runs get --run-id 987654321098765
```

## Troubleshoot Spark Jobs using Spark UI on Databricks
As the Databricks job or workflow is run, let us review the Spark jobs associated with Databricks job tasks using Spark UI.
* Go to the latest run of Databricks job or workflow.
* For each task we can review the details of the respective Notebook.
* We can go to Spark UI and check the respective Spark Job logs as well.
* If the jobs fail, we need to make review driver logs as well as Spark Job level logs.

## Integration of GCS with Databricks on GCP