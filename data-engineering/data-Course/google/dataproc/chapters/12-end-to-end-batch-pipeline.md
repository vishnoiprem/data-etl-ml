# 3.3 — End-to-End Batch Pipeline: GCS → Dataproc → BigQuery

> **Section 3 · Capstone · Lecture 3.3 · 1:17:19**

## 🎯 What you will learn

- The full architecture of a production batch pipeline: raw GCS landing zone → bronze → silver → gold (BigQuery) → dashboard
- The three-layer **medallion architecture** and the engineering reasons it exists: re-runnability, schema evolution, debuggability, isolation of raw from clean
- Two orchestrators — **Dataproc Workflows** (YAML, one auto-provisioned cluster) and **Cloud Composer** (Airflow DAGs) — and when each is the right tool
- How to write a real, runnable `job_pipeline.py` with staged functions, a `--run-date` argument, structured logging, per-stage timing, and guaranteed `spark.stop()`
- **Idempotency**: partition overwrite by run date, `partitionOverwriteMode=DYNAMIC`, write-then-swap, and why a rerun of the same date must produce the same result
- **Data quality gates** that physically prevent a bad load from reaching BigQuery, plus error handling, task retries, and resumability
- Cost optimization and observability: preemptible workers, shuffle partition tuning, `maxBytesBilled`, Cloud Logging filters, and custom Cloud Monitoring metrics

---

## 🧠 Concept

This is the capstone. Everything in the first two sections has been preparation. Here we
assemble the pieces into one thing that a data team would actually put in production and
run at 3 AM without a human watching it.

The single most important design decision in a batch pipeline is not the framework, not the
cluster size, not even the transformation logic. It is: **what happens when the job runs
twice?**

Everything else follows from that.

### The full flow

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│  LANDING ZONE (GCS)                                                               │
│                                                                                    │
│   gs://your-bucket/landing/orders/dt=2026-10-28/orders_2026-10-28.json            │
│   gs://your-bucket/landing/customers/dt=2026-10-27/customers_2026-10-27.csv      │
│   gs://your-bucket/landing/payments/dt=2026-10-28/payments_2026-10-28.json       │
│                                                                                    │
│   • Write-once, never mutated                                                     │
│   • Filenames carry the ingestion timestamp                                       │
│   • Producer-owned — the pipeline never writes here                                │
└───────────────────────────────┬────────────────────────────────────────────────────┘
                                │
                                │  gcloud dataproc workflow submit
                                │  (auto-creates a temporary cluster)
                                ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│  DATAPROC CLUSTER  (image 2.2-debian12, Spark 3.5)                                 │
│                                                                                    │
│   ┌──────────────────────────────────────────────────────────────────────────┐   │
│   │  job_pipeline.py                                                         │   │
│   │                                                                          │   │
│   │   extract()                    ── reads landing zone                     │   │
│   │        │                                                              │   │
│   │        ▼                                                              │   │
│   │   transform_bronze_to_silver() ── cleans, dedupes, conforms schema       │   │
│   │        │                                                              │   │
│   │        ▼                                                              │   │
│   │   run_quality_checks()          ── GATES. Failure ⇒ abort.              │   │
│   │        │  (pass)                                                     │   │
│   │        ▼                                                              │   │
│   │   load_silver_to_bigquery()     ── writes to gold tables                │   │
│   └──────────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌────────────────┐  ┌────────────────────┐  ┌──────────────────────────┐
│ BRONZE (GCS)   │  │  SILVER (GCS)      │  │  GOLD (BigQuery)         │
│ Parquet        │  │  Parquet           │  │  Partitioned tables      │
│ as-landed      │  │  cleaned/deduped   │  │  curated for analysts    │
│ dt=2026-10-28  │  │  dt=2026-10-28     │  │  orders_gold             │
└────────────────┘  └────────────────────┘  └────────────┬─────────────┘
                                                          │
                                                          ▼
                                              ┌──────────────────────────┐
                                              │  Looker / Looker Studio │
                                              │  dashboards, explorations│
                                              └──────────────────────────┘
```

### The medallion architecture

The **medallion** (or multi-layer) architecture comes from the Lakehouse / Delta Lake
convention, and Google Cloud has converged on it too — BigLake, Dataproc, and Looker all
assume the same shape. Three layers, each with a distinct job-to-be-done:

```
  BRONZE                SILVER                GOLD
  ───────               ──────                ────
  Raw, as-landed        Cleaned, typed,      Business-ready,
  append-only,          deduplicated,        aggregated, joined,
  schema-on-read        conformed schema      modelled for analysts

  "What arrived"        "What it means"       "What it says"

  Parquet on GCS        Parquet on GCS        BigQuery tables
```

| Layer | Format | Written by | Mutated? | Consumer |
|-------|--------|-----------|----------|----------|
| Bronze | Parquet, raw payload preserved | Extraction stage | Never | Bronze→silver transform |
| Silver | Parquet, typed + deduped + conformed | Transform stage | Overwritten per run date | Gold load, analysts |
| Gold | BigQuery tables | Load stage | Append / partition replace | Looker, BI, ML |

**Why three layers instead of one?**

**1. Re-runnability.** A one-layer pipeline ("raw → BigQuery") means if your transform has
a bug, you must re-read the raw source and redo everything. With a bronze layer, the
expensive, immutable, source-faithful copy is already materialized. A re-run of the
silver stage reads bronze and costs minutes, not hours. Bronze is your **checkpoint** and
your **replay buffer**.

**2. Schema evolution.** Source systems change. A JSON feed gains a field, a CSV gains a
column, a type widens from `int` to `bigint`. In the bronze layer that is fine — the raw
record is stored verbatim, so a change in producer schema is not a change in *your* schema.
Silver pins a stable, explicit schema; when the source evolves, you widen silver
deliberately, in one place, with a test, rather than discovering that your BigQuery table
now has a nullable column where analytics assumed non-null.

**3. Debuggability.** When a dashboard shows a wrong number, you can bisect: is the data
wrong in bronze (bad source)? Wrong in silver (bad transform)? Wrong in gold (bad load)?
One layer gives you a single point of failure and no way to isolate it. Three layers give
you three testable assertions. This is also why the bronze layer should keep the raw
payload — a `_raw` JSON string column, alongside parsed fields — so you can always recover
the original even if your parser had a bug.

**4. Isolation of raw from clean.** Analysts and downstream consumers should never read
bronze. Raw data has nulls in required fields, negative quantities, duplicate order IDs,
and mixed date formats. Mixing it with clean data is how you get a dashboard that is
sometimes wrong in a way nobody can reproduce. The layer boundary is an **access control
boundary** as much as a processing boundary.

💡 **A layer boundary is a contract.** Each layer should have a defined schema, a
documented owner, and a guarantee ("silver has exactly one row per `order_id` per
`order_date`"). If a layer's contract cannot be written down in a sentence, it is not a
layer — it is a staging area.

---

## The orchestrator layer

You have the pipeline logic. Now you need something to *run it on a schedule*, provision the
cluster, wire the jobs together, and retry when things break. Google Cloud gives you two
main options and they are not competitors — they solve different problems.

| | **Dataproc Workflows** | **Cloud Composer (Airflow)** |
|---|---|---|
| Model | A YAML template describing an ordered list of jobs | A Python DAG: tasks, dependencies, schedules, retries |
| Cluster | One temporary cluster for the whole workflow | You choose: temporary cluster, or submit to an existing one |
| Cross-job dependencies | Implicit — jobs run in listed order | Explicit — `task1 >> task2`, branches, `TriggerDagRunOperator` |
| Scheduling | Cloud Scheduler invoking a workflow submit API call | Native `schedule` / `schedule_interval` on the DAG |
| Conditional logic | None | Full Python — branching, sensors, dynamic task mapping |
| Fan-out / fan-in | Loop in the YAML | `expand()` / dynamic task mapping, XCom |
| Cross-workflow (multi-DAG) | No | Yes — `TriggerDagRunOperator`, datasets, `CrossDagDep` |
| UI | GCP console / API | Full Airflow UI: DAG graph, task logs, SLA, backfill |
| Best for | 2–10 linear ETL steps, one domain | Multi-team, multi-domain, many DAGs, anything with logic |
| Setup cost | Minutes | An Airflow environment (or Composer 2/3 managed) |

### When to use which

**Use Dataproc Workflows** when the pipeline is a **straight line**: ingest → transform →
load → publish, all in the same domain, all reading and writing the same tables. It is
declarative, the YAML is a readable description of your pipeline that lives next to the
code, and the temporary cluster is created and destroyed as one unit. This is most
pipelines, and it is what this course builds.

**Use Cloud Composer** when you need **anything the YAML cannot express**: multiple teams
sharing one scheduling system, a DAG that fans out over 200 customer partitions, a step
that waits on a BigQuery `INSERT COMPLETE` job, a data quality gate that pages a
Slack channel, backfill of 90 days, or a DAG that must trigger a *different* team's DAG
when its own data is ready.

💡 **The migration path is clean and worth knowing.** A Dataproc Workflow maps almost
1:1 onto a Composer DAG — each `jobs:` entry becomes a `DataprocSubmitJobOperator`
task, and the workflow's "one temporary cluster" becomes a
`DataprocCreateClusterOperator` → tasks → `DataprocDeleteClusterOperator` sandwich, or a
`DataprocWorkflowTemplateOperator` that invokes the workflow YAML from inside Airflow.
You can start with a workflow and lift it into Composer when the complexity demands it,
without rewriting the Spark code at all.

⚠️ **Do not put two orchestrators in charge of the same DAG.** If Composer schedules a
Composer DAG *and* Cloud Scheduler fires the underlying Dataproc workflow, you will
happily load the same run date twice. Pick one owner per pipeline. This chapter covers
both; pick one.

### Dataproc Workflows: the real YAML format

The workflow template is a YAML file with a top-level `jobs:` list. Each entry has a
`jobName`, `labels`, and a job-type-specific block. For PySpark, the block is `spark`
(and for Java/Scala it is `spark` with `mainClass` + `mainJarFileUri`; for a plain
`spark-sql` job it is `sparkSql`; for Hive it is `hive`).

```yaml
# DataprocWorkflow.yaml
jobs:
  - jobName: "extract-orders"
    labels:
      pipeline: "daily-orders"
      stage: "extract"
    spark:
      args:
        - "gs://your-bucket/jobs/job_pipeline.py"
        - "--run-date"
        - "${run_date}"
      pythonFileUris:
        - "gs://your-bucket/jobs/lib/quality.py"
      properties:
        spark.sql.shuffle.partitions: "200"
        spark.sql.sources.partitionOverwriteMode: "DYNAMIC"
        spark.executor.instances: "8"
        spark.executor.memory: "4g"

  # A JVM/Scala job in the same workflow. Same `spark:` block; the presence
  # of mainJarFileUri + mainClass is what distinguishes it from PySpark.
  - jobName: "build-lookup-index"
    labels:
      pipeline: "daily-orders"
      stage: "index"
    spark:
      args:
        - "gs://your-bucket/jobs/build_index.py"
        - "${run_date}"
      mainJarFileUri: "gs://your-bucket/jars/example.jar"
      mainClass: "com.example.BuildIndex"
      properties:
        spark.executor.instances: "4"

  - jobName: "publish-gold"
    labels:
      pipeline: "daily-orders"
      stage: "publish"
    spark:
      args:
        - "gs://your-bucket/jobs/job_pipeline.py"
        - "--run-date"
        - "2026-10-28"
        - "--only"
        - "load"
      pythonFileUris:
        - "gs://your-bucket/jobs/lib/quality.py"
      properties:
        spark.executor.instances: "4"
```

Note the shape carefully: the `spark:` block takes `args`, `pythonFileUris`,
`properties`, and (for JVM jobs) `mainJarFileUri` + `mainClass`. There is **no**
`pysparkSubmit` key — the workflow template API uses the same `spark` block for PySpark
and JVM jobs, and distinguishes them by whether you supply `mainJarFileUri`/`mainClass`
(JVM) or not (PySpark). Getting this wrong yields a workflow that submits successfully and then fails
with a confusing `mainClass not found` or `mainJarFileUri is required`.

Submitting it:

```bash
gcloud dataproc workflow submit \
  --region=us-central1 \
  --workflows.gcs_uri=gs://your-bucket/workflows/DataprocWorkflow.yaml \
  --name=orders-daily-2026-10-28 \
  --parameters=run_date=2026-10-28 \
  --labels=pipeline=daily-orders,run_date=2026-10-28
```

```
   gcloud dataproc workflow submit
        │
        ├──► reads the YAML from GCS
        ├──► creates a WorkflowTemplate + Workflow operation
        ├──► creates a TEMPORARY cluster (2.2-debian12 by default)
        ├──► job1 → job2 → ... in listed order
        │      each job waits for the previous to reach a terminal state
        ├──► deletes the cluster when the last job finishes
        └──► writes operation status + per-job logs to Cloud Logging
```

**Workflow parameter substitution.** The template is stored in GCS, so it cannot contain
a run date that changes daily. Dataproc solves this with `parameters` in the submit
command and `${PARAMETER}` placeholders in the YAML:

```bash
gcloud dataproc workflow submit \
  --region=us-central1 \
  --workflows.gcs_uri=gs://your-bucket/workflows/DataprocWorkflow.yaml \
  --name=orders-daily-2026-10-28 \
  --parameters=run_date=2026-10-28 \
  --parameters=landing_uri=gs://your-bucket/landing
```

```yaml
# Inside the YAML, reference the parameter:
jobs:
  - jobName: "extract-orders"
    labels: {pipeline: "daily-orders"}
    spark:
      args:
        - "gs://your-bucket/jobs/job_pipeline.py"
        - "--run-date"
        - "${run_date}"
        - "--landing-uri"
        - "${landing_uri}"
```

💡 **A workflow is a cluster-per-run.** The cluster lives for the duration of the
workflow and is deleted at the end (or by the deletion schedule). This means the cluster
configuration — machine types, Spark properties, initialization actions — is fixed for
all jobs in the workflow, and it must be specified in the **submit** command (via
`--clusters` flags) or left at the service default. For a production pipeline you will
usually define the cluster spec once in a shell script and pass it to every workflow
submit.

⚠️ **Workflow parameter names must be lowercase alphanumeric with hyphens** — the
placeholder syntax is `${param-name}`. CamelCase or underscores in the *name* are
rejected. (The *value* can be anything, including a `gs://` URI.)

### Cloud Composer: the Airflow DAG

Cloud Composer runs Apache Airflow. Composer 2 is the current environment type; Composer
3 is available and adds managed Apache Beam support. Airflow 2.x DAG syntax is standard.

The modern operator for submitting a job to Dataproc is
**`DataprocSubmitJobOperator`** from `airflow.providers.google.cloud.operators.dataproc`.
(There is also a `DataprocSubmitJobOperator` in the older `airflow.contrib` path — do not
use that.)

```python
# dags/daily_orders_pipeline.py
import datetime as dt

from airflow import DAG
from airflow.providers.google.cloud.operators.dataproc import (
    DataprocCreateClusterOperator,
    DataprocDeleteClusterOperator,
    DataprocSubmitJobOperator,
)

PROJECT_ID = "your-project-id"
REGION = "us-central1"
JOB_BUCKET = "gs://your-bucket/jobs"


def ds_nodash(ds):
    """Airflow logical date (2026-10-28) → compact form for a cluster name."""
    return ds.replace("-", "")


with DAG(
    dag_id="daily_orders_pipeline",
    description="GCS → Dataproc → BigQuery daily orders pipeline",
    schedule="0 2 * * *",          # Airflow 2.4+
    # schedule_interval="0 2 * * *",  # Airflow 2.0–2.3 (renamed in 2.4)
    start_date=dt.datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["dataproc", "etl", "bigquery", "course"],
    default_args={
        "retries": 2,
        "retry_delay": dt.timedelta(minutes=5),
        "retry_exponential_backoff": True,
    },
) as dag:

    # ── 1. Create a temporary cluster for this run ──────────────────────────
    create_cluster = DataprocCreateClusterOperator(
        task_id="create_cluster",
        project_id=PROJECT_ID,
        region=REGION,
        cluster_name="orders-{{ ds_nodash }}",
        image_version="2.2-debian12",
        config={
            "masterConfig": {"machineType": "n2-standard-4", "numInstances": 1},
            "workerConfig": {
                "machineType": "n2-standard-4",
                "numInstances": 2,
                "secondaryWorkerConfig": {
                    "numInstances": 4,
                    "type": "SPOT",           # preemptible workers
                },
            },
            "configBucket": "your-bucket",
            "labels": {"pipeline": "daily_orders"},
        },
    )

    # ── 2. Run the pipeline (extract → transform → quality → load) ─────────
    run_pipeline = DataprocSubmitJobOperator(
        task_id="run_pipeline",
        project_id=PROJECT_ID,
        region=REGION,
        job_config={
            "spark": {
                "args": [
                    f"{JOB_BUCKET}/job_pipeline.py",
                    "--run-date",
                    "{{ ds }}",
                    "--landing-uri",
                    "gs://your-bucket/landing",
                ],
                "pythonFileUris": [f"{JOB_BUCKET}/lib/quality.py"],
                "properties": {
                    "spark.sql.shuffle.partitions": "200",
                    "spark.sql.sources.partitionOverwriteMode": "DYNAMIC",
                },
            }
        },
        labels={"pipeline": "daily_orders", "run_date": "{{ ds }}"},
    )

    # ── 3. Tear the cluster down, whatever happened ─────────────────────────
    delete_cluster = DataprocDeleteClusterOperator(
        task_id="delete_cluster",
        project_id=PROJECT_ID,
        region=REGION,
        cluster_name="orders-{{ ds_nodash }}",
        trigger_rule="all_done",   # ← deletes even if run_pipeline failed
    )

    create_cluster >> run_pipeline >> delete_cluster
```

`"{{ ds }}"` is the Airflow **logical date** template — a `YYYY-MM-DD` string, resolved by
Airflow at task-instance time. The `job_config` field on `DataprocSubmitJobOperator` is
templated, so Jinja inside it is rendered per run. That is how a single DAG body handles
every run date without any code change.

⚠️ **Airflow's `schedule_interval` vs `schedule`.** In Airflow 2.0–2.3 the parameter is
`schedule_interval`; in Airflow 2.4+ it was renamed to `schedule` and `schedule_interval`
is deprecated (still accepted, but emits a deprecation warning). For new code targeting
Composer 2, use `schedule`. For code that must run on 2.0–2.3, use `schedule_interval`.
They are mutually exclusive — passing both raises an error.

💡 **`trigger_rule="all_done"` on the delete task is essential.** With the default
`all_success`, a failed pipeline leaves the cluster running and billing you until someone
notices. `all_done` means the cluster is torn down regardless of the upstream outcome.
(A safer variant is `trigger_rule="all_done"` plus a `DataprocDeleteClusterOperator` with
a `timeout` so a hung delete does not block the DAG forever.)

💡 **To submit to an *existing* cluster instead of managing one, drop the create and
delete tasks and set `region` plus a `cluster_name` on the submit operator.** For a
"submit to a persistent cluster" model, use `DataprocSubmitJobOperator` with the
`gcp_conn_id` and an explicit `cluster_name` — but note this couples the DAG to a
long-lived cluster, which is a cost and an operational decision, not a default.

💡 **`max_active_runs=1` is a correctness setting, not a politeness setting.** If two
runs of the same DAG overlap, they may process the same run date concurrently and race on
the same output partitions. `max_active_runs=1` serialises runs within a DAG. If two
*different* DAGs can touch the same tables, you need a shared lock or a partition-ownership
convention instead.

---

## Idempotency: the central engineering concern

**Definition.** An operation is *idempotent* if running it N times produces the same
result as running it once. A batch pipeline must be idempotent with respect to a run
date, because:

- the scheduler will fire it again if it missed a heartbeat
- you will re-run it manually after a bug fix
- a workflow job will be retried by the orchestrator after a transient failure
- an operator will re-run "just the failed part" — and you want that to be safe

**The requirement:** re-running `--run-date=2026-10-28` must leave the pipeline in exactly
the state it would have been in after the first successful run. Not "approximately". Not
"twice the rows". Exactly.

### The failure mode: append-on-rerun

```
  Run 1:  write orders/dt=2026-10-28  → 1,000,000 rows
  Run 2:  write orders/dt=2026-10-28  → 1,000,000 rows appended → 2,000,000 rows
          ↓
  BigQuery load appends again        → 3,000,000 rows
          ↓
  Dashboard revenue is 3× reality. Nobody notices for two weeks.
```

This is the single most common batch pipeline bug in the world. It is invisible in
testing (where you run once) and catastrophic in production.

### The mechanism: partition overwrite

The fix is to make the output **partitioned by run date** and to write each partition
with *replace* semantics rather than *append* semantics.

```
  gs://your-bucket/silver/orders/dt=2026-10-28/   ← one directory = one run date
```

Then:

```python
(
    silver_df.write
    .mode("overwrite")                          # replace the partition, not append
    .option("partitionOverwriteMode", "DYNAMIC") # only touch partitions present in the DF
    .partitionBy("dt")
    .parquet(SILVER_URI)
)
```

**`spark.sql.sources.partitionOverwriteMode=DYNAMIC` is the key setting.** Its two
values:

| Mode | Behavior | When to use |
|------|----------|-------------|
| `STATIC` (default) | Overwrites the **entire output directory**, wiping all partitions including ones not in the DataFrame | You always write a complete dataset |
| `DYNAMIC` | Overwrites **only the partitions present in the DataFrame**; other partitions are left alone | ✅ You write a subset (one run date) and must not delete other dates |

⚠️ **With `STATIC` and `mode("overwrite")`, a single-day run deletes every other day's
silver data.** This is a spectacularly destructive bug and it *looks* like it works
perfectly in a demo with one date. Always use `DYNAMIC` for a date-partitioned,
incrementally-written dataset. The exception is the very first run against an empty
directory, where either works.

⚠️ **DYNAMIC requires `mode("overwrite")`.** In `mode("append")`, the
`partitionOverwriteMode` setting is ignored entirely — Spark appends. The two settings
only compose when the mode is `overwrite`.

You can also set it cluster-wide:

```bash
gcloud dataproc jobs submit pyspark job_pipeline.py \
  --cluster=course-dev --region=us-central1 \
  --properties="spark.sql.sources.partitionOverwriteMode=DYNAMIC"
```

### Delete-then-write vs overwrite

There are two ways to guarantee "re-running produces the same result". They trade
correctness against atomicity.

**Option A — delete then write:**

```python
# Delete the target partition first, then write
spark.sql(f"ALTER TABLE delta.`{path}` DROP PARTITION (dt = '{run_date}')")  # Delta
# or for plain GCS + Spark SQL external table:
spark.sql(f"ALTER TABLE spark_catalog.default.orders_silver DROP PARTITION (dt='{run_date}')")

df.write.mode("overwrite").partitionBy("dt").parquet(path)
```

- ✅ Simple, obviously correct, easy to reason about.
- ❌ **Not atomic.** Between the delete and the write, the partition does not exist. Any
  concurrent reader sees a hole. And if the job crashes *after* the delete, you have
  **destroyed good data and written nothing** — the pipeline is now in a worse state than
  before it started.

**Option B — write to a staging path, then swap:**

```python
staging = f"{SILVER_URI}/_staging/{run_id}"
final   = f"{SILVER_URI}/dt={run_date}"

df.write.mode("overwrite").partitionBy("dt").parquet(staging)
# ... only after a successful write:
# copy/rename staging into place
```

- ✅ The old partition stays readable until the very last instant.
- ✅ A crash mid-write leaves the staging directory behind, not a hole in production data.
- ❌ A GCS "rename" is a **copy + delete** under the hood (there is no true atomic move in
  object storage), so it is not free. For large partitions this doubles I/O.
- ❌ Needs cleanup logic for abandoned staging directories.

💡 **The pragmatic answer for GCS + Parquet: use `mode("overwrite")` with
`partitionOverwriteMode=DYNAMIC`.** Spark's Parquet writer, when overwriting a static
partition, writes to a temporary directory and commits by *renaming the leaf directory* —
so on GCS the effect is close to atomic for that one partition. The gap is small (the
duration of the final rename/copy), and the operational simplicity is worth a lot.

Where you truly need atomicity at the *table* level — multi-partition commits, merge,
time travel — that is what **Delta Lake** or **Apache Iceberg** on Dataproc is for.
Delta's `MERGE` and transactional table semantics give you a real `DROP PARTITION` +
`INSERT` in one atomic operation, and it works on GCS with `delta-io` JARs.

⚠️ **Plain Parquet on GCS has no transactions.** There is no way to atomically update
two partitions. If your gold layer needs multi-table consistency, that is a signal to
introduce Delta/Iceberg, or to make the BigQuery load itself the atomic unit (which it
effectively is — see below).

### The BigQuery side of idempotency

BigQuery has its own three write modes, and getting this wrong is the second most common
idempotency bug.

| Mode | Behavior on rerun | Idempotent? |
|------|-------------------|-------------|
| `WRITE_APPEND` | Adds rows again | ❌ No — duplicates |
| `WRITE_TRUNCATE` | Wipes the table, writes all rows | ✅ Yes, but loses other partitions |
| `WRITE_EMPTY` | Writes only the rows in the partition being loaded | ✅ Yes — for a partitioned table |

The correct pattern: make the BigQuery table **partitioned by the same run-date column**,
and use `WRITE_EMPTY` (or `partition_date` matching) so a rerun replaces just that
partition.

In the BigQuery Storage Write API (which the Spark connector uses), the equivalent is
setting the **partition decorator** on the write stream. With the Spark BigQuery
connector, the cleanest way to get this is:

```python
# Write silver → BigQuery, replacing only the target partition
(
    silver_df.write
    .format("bigquery")
    .option("writeMethod", "direct")            # Storage Write API, no temp bucket
    .option("temporaryGcsBucket", TMP_BUCKET)    # required for 'indirect' method
    .option("partitionField", "dt")             # the BQ partition column
    .option("partitionExpirationTime", "2592000s")
    .option("mode", "overwrite")
    .option("createDisposition", "CREATE_IF_NEEDED")
    .option("writeDisposition", "WRITE_TRUNCATE")
    .save(BIGQUERY_TABLE)
)
```

With `writeDisposition=WRITE_TRUNCATE` on a **partitioned** table, BigQuery replaces the
partition identified by the rows' partition values — the same semantics as
`WRITE_EMPTY` for the affected partition. So a rerun of `--run-date=2026-10-28` replaces
the `dt=2026-10-28` partition and leaves every other date intact.

⚠️ **`WRITE_TRUNCATE` on an unpartitioned table wipes the entire table.** If your gold
table is not partitioned by run date, a rerun destroys all other dates' data. Partition
the table (`PARTITION BY dt`) — or use a different destination per date.

💡 **BigQuery's `maxBytesBilled` on a write is your cost circuit breaker.** It prevents
a runaway job from loading an unexpected 10 TB into a table. But note: when
`maxBytesBilled` is exceeded, the load **fails** — it does not truncate the table first,
so you do not lose the existing partition. Set it deliberately above your expected
partition size.

⚠️ **Do not use `mode("append")` into BigQuery from Spark without a partition-aware
destination.** Even with a partitioned table, the Spark connector's append mode appends
into the partition implied by each row's partition value — so a rerun duplicates within
the partition rather than replacing it. You want `WRITE_TRUNCATE` (replace) or
`WRITE_EMPTY`.

### A note on the `run_id`

A `run_id` is a unique identifier for one *execution* of the pipeline, distinct from the
`run_date` which identifies the *data*. A rerun of the same run date is a **new
`run_id`** targeting the **same `run_date`**.

```
  run_date=2026-10-28  run_id=8f3a2c1d-20261028T020000Z   (first attempt, failed at silver)
  run_date=2026-10-28  run_id=b91e7f44-20261028T041500Z   (retry, succeeded)
  run_date=2026-10-28  run_id=c02d5a10-20261028T061200Z   (manual re-run, idempotent)
```

The `run_id` goes into logs, metrics, staging paths, and a manifest object. The
`run_date` goes into partition paths. Keeping them separate is what lets you rerun
without polluting the deterministic output.

---

## 🛠️ Hands-On: The Complete Pipeline

### Step 0 — Variables and layout

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export BUCKET="your-bucket"
export RUN_DATE="2026-10-28"
export TMP_BUCKET="your-bucket-tmp"
```

```
gs://your-bucket/
├── landing/                     # producer-owned, never mutated
│   ├── orders/dt=2026-10-28/orders_2026-10-28.json
│   ├── customers/dt=2026-10-27/customers_2026-10-27.csv
│   └── payments/dt=2026-10-28/payments_2026-10-28.json
├── bronze/orders/dt=2026-10-28/part-*.parquet
├── silver/orders/dt=2026-10-28/part-*.parquet
├── jobs/
│   ├── job_pipeline.py
│   └── lib/quality.py
└── workflows/DataprocWorkflow.yaml
```

### Step 1 — The pipeline script

```python
# job_pipeline.py
"""
End-to-end daily pipeline: GCS landing zone → bronze → silver → BigQuery gold.

Run date semantics:
  --run-date YYYY-MM-DD   The logical date of the data being processed.
                          Re-running the same run-date is idempotent.

Stage order:
  extract()                    landing  → bronze
  transform_bronze_to_silver() bronze   → silver
  run_quality_checks()        gates    → pass/fail
  load_silver_to_bigquery()   silver   → BigQuery gold
"""

import argparse
import datetime as dt
import logging
import sys
import time
import uuid

from pyspark.sql import SparkSession, Window, functions as F, types as T

# ─────────────────────────────────────────────────────────────────────────────
# Logging: structured, single-line, greppable. Every record carries run_id,
# run_date, and the current stage, so Cloud Logging can filter on them.
# ─────────────────────────────────────────────────────────────────────────────
LOG_FORMAT = (
    "%(asctime)s %(levelname)-8s [%(name)s] "
    "run_id=%(run_id)s run_date=%(run_date)s stage=%(stage)s :: %(message)s"
)

# Mutable context for the current execution, shared by all loggers.
CTX = {"run_id": "-", "run_date": "-", "stage": "init"}


class ContextLogger(logging.LoggerAdapter):
    """
    Adapter that injects the run context into every log record.

    LoggerAdapter.process() merges self.extra into the record's `extra`
    dict; overriding it lets us pull the *current* values from CTX on
    every call, so a stage change is reflected in subsequent lines.
    """

    def process(self, msg, kwargs):
        extra = dict(self.extra or {})
        extra.update(CTX)
        extra.update(kwargs.get("extra") or {})
        kwargs["extra"] = extra
        return msg, kwargs


def get_logger(name: str) -> ContextLogger:
    """Return a context-aware logger writing to stdout."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return ContextLogger(logger, {})


def set_stage(stage: str) -> None:
    """Advance the run context to a new stage (affects subsequent log lines)."""
    CTX["stage"] = stage
    get_logger("pipeline").info("── stage %s ──", stage)


def elapsed(t0: float) -> float:
    return round(time.time() - t0, 2)


# ─────────────────────────────────────────────────────────────────────────────
# Spark session
# ─────────────────────────────────────────────────────────────────────────────
def build_spark(app_name: str) -> SparkSession:
    spark = (
        SparkSession.builder
        .appName(app_name)
        # DYNAMIC is required so a single-date write replaces only that date.
        .config("spark.sql.sources.partitionOverwriteMode", "DYNAMIC")
        # AQE: coalesces shuffle partitions and handles skew automatically.
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .config("spark.sql.adaptive.skewJoin.enabled", "true")
        # Retry failed tasks; default is 4, raised for transient GCS blips.
        .config("spark.task.maxFailures", "6")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark


# ─────────────────────────────────────────────────────────────────────────────
# Quality gates
# ─────────────────────────────────────────────────────────────────────────────
class QualityGateError(RuntimeError):
    """Raised when a data quality gate fails. Aborts the pipeline."""


def run_quality_checks(spark, silver_df, run_date, config) -> dict:
    """
    Gate the silver dataset before it is allowed into BigQuery.

    Each gate returns (name, passed, detail). Any failure raises
    QualityGateError, which main() turns into a non-zero exit — so the
    BigQuery load never runs.

    Gates:
      1. Row-count drop       silver rows vs bronze rows
      2. Null rate             per critical column
      3. Schema conformance   required columns and types
      4. Reconciliation total sum(amount) silver vs bronze
    """
    log = get_logger("quality")
    results = []

    bronze_df = spark.read.parquet(config["bronze_uri"] + f"dt={run_date}")
    bronze_count = bronze_df.count()
    silver_count = silver_df.count()
    log.info("row counts: bronze=%d silver=%d", bronze_count, silver_count)

    # ── Gate 1: row-count drop threshold ──────────────────────────────────
    max_drop_pct = config["max_row_drop_pct"]
    drop_pct = 0.0 if bronze_count == 0 else (
        (bronze_count - silver_count) / bronze_count
    ) * 100.0
    passed = drop_pct <= max_drop_pct
    results.append(("row_count_drop", passed, f"{drop_pct:.3f}% (max {max_drop_pct}%)"))
    log.info("gate=row_count_drop passed=%s detail=%s", passed, f"{drop_pct:.3f}%")

    # ── Gate 2: null rate on critical columns ──────────────────────────────
    nulls = silver_df.select(
        *[
            F.sum(F.when(F.col(c).isNull(), 1).otherwise(0)).alias(c)
            for c in config["critical_columns"]
        ]
    ).first().asDict()
    for col, null_count in nulls.items():
        rate = (null_count / silver_count * 100.0) if silver_count else 0.0
        passed = rate <= config["max_null_pct"]
        results.append((f"null_rate[{col}]", passed, f"{rate:.3f}%"))
        log.info("gate=null_rate[%s] passed=%s detail=%.3f%%", col, passed, rate)

    # ── Gate 3: schema conformance ─────────────────────────────────────────
    actual = {f.name: f.dataType.simpleString() for f in silver_df.schema.fields}
    for col, expected_type in config["expected_schema"].items():
        actual_type = actual.get(col)
        passed = actual_type == expected_type
        results.append(
            (f"schema[{col}]", passed, f"expected {expected_type}, got {actual_type}")
        )
        log.info(
            "gate=schema[%s] passed=%s expected=%s actual=%s",
            col, passed, expected_type, actual_type,
        )

    # ── Gate 4: reconciliation of a business total ─────────────────────────
    amount_col = config["reconcile_column"]
    bronze_total = (
        bronze_df.agg(F.sum(F.col(amount_col).cast("double")).alias("t"))
        .first()["t"] or 0.0
    )
    silver_total = (
        silver_df.agg(F.sum(F.col(amount_col).cast("double")).alias("t"))
        .first()["t"] or 0.0
    )
    diff = abs(bronze_total - silver_total)
    tolerance = config["reconcile_abs_tolerance"]
    passed = diff <= tolerance
    results.append(
        ("reconciliation_total", passed, f"bronze={bronze_total} silver={silver_total} diff={diff}")
    )
    log.info(
        "gate=reconciliation_total passed=%s bronze=%.2f silver=%.2f diff=%.4f",
        passed, bronze_total, silver_total, diff,
    )

    failed = [r for r in results if not r[1]]
    summary = {"results": results, "failed": failed}
    write_gate_report(spark, run_date, summary, config)
    if failed:
        raise QualityGateError(
            "quality gates failed: " + ", ".join(f"{n} ({d})" for n, _, d in failed)
        )
    log.info("all %d quality gates passed", len(results))
    return summary


def write_gate_report(spark, run_date, summary, config):
    """Persist the gate report to GCS so it is auditable after the run."""
    rows = [
        {
            "run_date": run_date,
            "run_id": CTX["run_id"],
            "gate": name,
            "passed": passed,
            "detail": detail,
        }
        for name, passed, detail in summary["results"]
    ]
    df = spark.createDataFrame(rows)
    path = f"{config['reports_uri']}quality/{run_date}"
    (df.write.mode("overwrite").option("partitionOverwriteMode", "DYNAMIC").parquet(path))
    log = get_logger("quality")
    log.info("wrote gate report to %s", path)


# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: extract (landing → bronze)
# ─────────────────────────────────────────────────────────────────────────────
def extract(spark, run_date, config) -> str:
    """
    Read the raw landing zone for this run date and land it as bronze Parquet.

    Bronze is:
      - verbatim (raw payload preserved in a _raw column)
      - typed only where the type is unambiguous
      - append-only in spirit, but written with overwrite semantics so a
        rerun of the same date is idempotent
    """
    set_stage("extract")
    log = get_logger("extract")
    t0 = time.time()

    landing = config["landing_uri"] + f"orders/dt={run_date}"
    bronze_path = f"{config['bronze_uri']}orders/dt={run_date}"

    log.info("reading landing zone %s", landing)

    # Read JSON with a permissive schema: let Spark infer, then stabilize.
    raw_df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .option("mode", "PERMISSIVE")
        .option("columnNameOfCorruptRecord", "_corrupt")
        .json(landing)
    )

    if raw_df.isEmpty():
        raise ValueError(f"no landing data found at {landing}")

    # Preserve the raw payload so bronze is never a lossy representation.
    bronze_df = raw_df.withColumn("_raw", F.to_json(F.struct(*raw_df.columns)))
    bronze_df = bronze_df.withColumn("_ingested_at", F.current_timestamp())
    bronze_df = bronze_df.withColumn("dt", F.lit(run_date))

    row_count = bronze_df.count()
    log.info("bronze rows=%d", row_count)

    # Idempotent write: overwrite this run-date's partition only.
    (bronze_df.write
     .mode("overwrite")
     .option("partitionOverwriteMode", "DYNAMIC")
     .partitionBy("dt")
     .parquet(bronze_path))

    log.info("wrote bronze → %s in %ss", bronze_path, elapsed(t0))
    return bronze_path


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: transform (bronze → silver)
# ─────────────────────────────────────────────────────────────────────────────
def transform_bronze_to_silver(spark, run_date, config) -> str:
    """
    Clean and conform bronze into silver.

    Operations:
      - strict schema cast to a declared target schema
      - null / invalid-value handling
      - deduplication on a business key (keep latest)
      - derived columns and a stable column order
    """
    set_stage("transform")
    log = get_logger("transform")
    t0 = time.time()

    bronze_path = f"{config['bronze_uri']}orders/dt={run_date}"
    silver_path = f"{config['silver_uri']}orders/dt={run_date}"

    bronze_df = spark.read.parquet(bronze_path)
    in_count = bronze_df.count()
    log.info("bronze rows in=%d", in_count)

    # ── 1. Cast to the declared silver schema ──────────────────────────────
    target_schema = T.StructType([
        T.StructField("order_id", T.StringType(), True),
        T.StructField("customer_id", T.StringType(), True),
        T.StructField("order_ts", T.TimestampType(), True),
        T.StructField("order_date", T.DateType(), True),
        T.StructField("status", T.StringType(), True),
        T.StructField("currency", T.StringType(), True),
        T.StructField("amount", T.DoubleType(), True),
        T.StructField("tax", T.DoubleType(), True),
        T.StructField("quantity", T.IntegerType(), True),
    ])

    # Keep only columns that exist, then cast. Missing columns become null.
    available = {f.name for f in bronze_df.schema.fields}
    select_cols = [
        F.col(c).cast(target_schema[c].dataType).alias(c)
        for c in target_schema.fieldNames()
        if c in available
    ]
    for c in target_schema.fieldNames():
        if c not in available:
            select_cols.append(F.lit(None).cast(target_schema[c].dataType).alias(c))


    silver_df = bronze_df.select(*select_cols)

    # ── 2. Data cleaning rules ─────────────────────────────────────────────
    silver_df = (
        silver_df
        .withColumn("order_id", F.trim(F.upper(F.col("order_id"))))
        .withColumn("status", F.lower(F.trim(F.col("status"))))
        .withColumn("currency", F.upper(F.trim(F.col("currency"))))
        .withColumn("order_ts", F.to_timestamp("order_ts"))
        .withColumn("order_date", F.to_date("order_date"))
        .withColumn("amount", F.round(F.col("amount"), 2))
        .withColumn("tax", F.round(F.col("tax"), 2))
        .withColumn("quantity", F.col("quantity").cast("int"))
        # Invalid values → null rather than a silently wrong default.
        .withColumn("amount", F.when(F.col("amount") < 0, F.lit(None)).otherwise(F.col("amount")))
        .withColumn("status", F.when(
            F.col("status").isin("new", "paid", "shipped", "cancelled", "refunded"),
            F.col("status"),
        ).otherwise(F.lit("unknown")))
    )

    # ── 3. Deduplicate on the business key, keep the latest ───────────────
    # order_id is the business key; order_ts is the tiebreaker.
    before_dedup = silver_df.count()
    silver_df = (
        silver_df.withColumn("_rn", F.row_number().over(
            Window.partitionBy("order_id").orderBy(F.col("order_ts").desc_nulls_last())
        ))
        .filter(F.col("_rn") == 1)
        .drop("_rn")
    )
    after_dedup = silver_df.count()
    log.info("dedup: %d → %d rows (dropped %d duplicates)",
             before_dedup, after_dedup, before_dedup - after_dedup)

    # ── 4. Derive and partition ────────────────────────────────────────────
    silver_df = (
        silver_df
        .withColumn("total_amount", F.round(F.col("amount") + F.coalesce(F.col("tax"), F.lit(0.0)), 2))
        .withColumn("dt", F.lit(run_date))
        .select(
            "order_id", "customer_id", "order_ts", "order_date", "status",
            "currency", "amount", "tax", "quantity", "total_amount", "dt",
        )
    )

    out_count = silver_df.count()
    log.info("silver rows out=%d", out_count)

    (silver_df.write
     .mode("overwrite")
     .option("partitionOverwriteMode", "DYNAMIC")
     .partitionBy("dt")
     .parquet(silver_path))

    log.info("wrote silver → %s in %ss", silver_path, elapsed(t0))
    return silver_path


# ─────────────────────────────────────────────────────────────────────────────
# Stage 3: load (silver → BigQuery)
# ─────────────────────────────────────────────────────────────────────────────
def load_silver_to_bigquery(spark, run_date, config) -> None:
    """
    Load the silver partition into the BigQuery gold table.

    Idempotency: the gold table is partitioned by dt, and we use
    WRITE_TRUNCATE, so a rerun replaces only this run date's partition.
    """
    set_stage("load")
    log = get_logger("load")
    t0 = time.time()

    silver_path = f"{config['silver_uri']}orders/dt={run_date}"
    table = config["bigquery_table"]           # e.g. "your-project.analytics.orders_gold"

    silver_df = spark.read.parquet(silver_path)
    row_count = silver_df.count()
    log.info("loading %d rows → %s", row_count, table)

    (
        silver_df.write
        .format("bigquery")
        .option("writeMethod", "direct")
        .option("temporaryGcsBucket", config["tmp_bucket"])
        .option("partitionField", "dt")
        .option("partitionExpirationTime", "2592000s")   # 30 days
        .option("createDisposition", "CREATE_IF_NEEDED")
        .option("writeDisposition", "WRITE_TRUNCATE")    # replace the partition
        .option("maxBytesBilled", str(config["max_bytes_billed"]))
        .save(table)
    )

    log.info("loaded %d rows in %ss", row_count, elapsed(t0))


# ─────────────────────────────────────────────────────────────────────────────
# Orchestration
# ─────────────────────────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(description="Daily batch pipeline")
    parser.add_argument("--run-date", required=True, help="YYYY-MM-DD logical date")
    parser.add_argument("--landing-uri", default="gs://your-bucket/landing")
    parser.add_argument("--bronze-uri", default="gs://your-bucket/bronze")
    parser.add_argument("--silver-uri", default="gs://your-bucket/silver")
    parser.add_argument("--reports-uri", default="gs://your-bucket/reports")
    parser.add_argument("--bigquery-table", default="your-project.analytics.orders_gold")
    parser.add_argument("--tmp-bucket", default="your-bucket-tmp")
    parser.add_argument("--only", choices=["all", "extract", "transform", "load"],
                        default="all", help="Run a single stage (for recovery)")
    parser.add_argument("--max-row-drop-pct", type=float, default=2.0)
    parser.add_argument("--max-null-pct", type=float, default=0.5)
    parser.add_argument("--reconcile-abs-tolerance", type=float, default=1.0)
    parser.add_argument("--max-bytes-billed", type=int, default=5 * 1024 ** 3)
    args = parser.parse_args()

    # Validate the run date early — a typo must not silently create a partition.
    try:
        dt.date.fromisoformat(args.run_date)
    except ValueError:
        print(f"ERROR: --run-date must be YYYY-MM-DD, got '{args.run_date}'")
        return 2

    run_id = f"{uuid.uuid4().hex[:8]}-{dt.datetime.utcnow():%Y%m%dT%H%M%SZ}"
    CTX.update(run_id=run_id, run_date=args.run_date, stage="init")
    log = get_logger("pipeline")

    config = {
        "landing_uri": args.landing_uri,
        "bronze_uri": args.bronze_uri,
        "silver_uri": args.silver_uri,
        "reports_uri": args.reports_uri,
        "bigquery_table": args.bigquery_table,
        "tmp_bucket": args.tmp_bucket,
        "max_row_drop_pct": args.max_row_drop_pct,
        "max_null_pct": args.max_null_pct,
        "max_bytes_billed": args.max_bytes_billed,
        "reconcile_column": "amount",
        "critical_columns": ["order_id", "customer_id", "order_ts", "amount"],
        "expected_schema": {
            "order_id": "string",
            "customer_id": "string",
            "order_ts": "timestamp",
            "order_date": "date",
            "status": "string",
            "currency": "string",
            "amount": "double",
            "tax": "double",
            "quantity": "int",
        },
    }

    log.info("=" * 70)
    log.info("PIPELINE START run_id=%s run_date=%s only=%s",
             run_id, args.run_date, args.only)
    log.info("=" * 70)

    spark = None
    t_start = time.time()
    try:
        spark = build_spark(f"daily-pipeline-{args.run_date}")

        if args.only in ("all", "extract"):
            extract(spark, args.run_date, config)
        if args.only in ("all", "transform"):
            transform_bronze_to_silver(spark, args.run_date, config)
        if args.only == "all":
            # Quality gates run BEFORE the load. A failure here aborts the run
            # and the BigQuery table is never touched.
            silver_df = spark.read.parquet(
                f"{args.silver_uri}orders/dt={args.run_date}"
            )
            run_quality_checks(spark, silver_df, args.run_date, config)
        if args.only in ("all", "load"):
            load_silver_to_bigquery(spark, args.run_date, config)

        log.info("PIPELINE SUCCESS run_id=%s total=%ss", run_id, elapsed(t_start))
        return 0

    except QualityGateError as exc:
        log.error("PIPELINE FAILED — QUALITY GATE: %s", exc)
        log.error("BigQuery load was NOT executed. Silver partition retained for triage.")
        return 3
    except Exception as exc:  # noqa: BLE001
        log.exception("PIPELINE FAILED run_id=%s: %s", run_id, exc)
        return 1
    finally:
        if spark is not None:
            spark.stop()
            log.info("spark.stop() called")


if __name__ == "__main__":
    sys.exit(main())
```

Note the `finally` block: `spark.stop()` runs on success, on a quality-gate failure, and
on an unhandled exception. Without it, a failed driver leaves executors registered with
the YARN ResourceManager and the cluster's resources pinned until the job times out.

💡 **Exit codes are a contract for the orchestrator.** `0` = success, `1` = unexpected
error, `2` = bad arguments, `3` = quality gate failure. Composer and your monitoring can
branch on the specific code — a `3` means "the data is bad, page a human", a `1` means
"the code is broken, roll back".

### Step 2 — The workflow YAML

```yaml
# workflows/DataprocWorkflow.yaml
jobs:
  - jobName: "extract-orders"
    labels:
      pipeline: "daily-orders"
      stage: "extract"
    spark:
      args:
        - "gs://your-bucket/jobs/job_pipeline.py"
        - "--run-date"
        - "${run_date}"
        - "--only"
        - "extract"
      pythonFileUris:
        - "gs://your-bucket/jobs/lib/quality.py"
      properties:
        spark.sql.shuffle.partitions: "200"
        spark.sql.sources.partitionOverwriteMode: "DYNAMIC"
        spark.sql.adaptive.enabled: "true"
        spark.executor.instances: "8"
        spark.executor.memory: "4g"
        spark.task.maxFailures: "6"

  - jobName: "transform-silver"
    labels:
      pipeline: "daily-orders"
      stage: "transform"
    spark:
      args:
        - "gs://your-bucket/jobs/job_pipeline.py"
        - "--run-date"
        - "${run_date}"
        - "--only"
        - "transform"
      pythonFileUris:
        - "gs://your-bucket/jobs/lib/quality.py"
      properties:
        spark.sql.shuffle.partitions: "200"
        spark.sql.sources.partitionOverwriteMode: "DYNAMIC"
        spark.executor.instances: "16"
        spark.executor.memory: "8g"

  - jobName: "load-gold"
    labels:
      pipeline: "daily-orders"
      stage: "load"
    spark:
      args:
        - "gs://your-bucket/jobs/job_pipeline.py"
        - "--run-date"
        - "${run_date}"
        - "--only"
        - "load"
      pythonFileUris:
        - "gs://your-bucket/jobs/lib/quality.py"
      properties:
        spark.executor.instances: "4"
        spark.executor.memory: "4g"
```

⚠️ **Note the `pythonFileUris`.** Every job that imports a shared helper module must
list it. A job that imports `quality.py` without `pythonFileUris` fails at import time
with `ModuleNotFoundError` — and because the quality module is only *used* by the
`all` path, a job submitted with `--only load` might not even need it. Listing it
everywhere is simpler than being surprised.

### Step 3 — Upload the artifacts

```bash
gsutil -m cp job_pipeline.py gs://$BUCKET/jobs/
gsutil -m cp lib/quality.py gs://$BUCKET/jobs/lib/
gsutil -m cp workflows/DataprocWorkflow.yaml gs://$BUCKET/workflows/
```

### Step 4 — Run the whole thing as a workflow

```bash
gcloud dataproc workflow submit \
  --region=$REGION \
  --workflows.gcs_uri=gs://$BUCKET/workflows/DataprocWorkflow.yaml \
  --name=orders-daily-$RUN_DATE \
  --parameters=run_date=$RUN_DATE \
  --labels=pipeline=daily-orders,run_date=$RUN_DATE \
  --clusters="$REGION:cluster-config/orders-cluster:dataproc-2.2-debian12"
```

`--clusters` points at a **cluster config file** stored in GCS, which is how you control
the ephemeral cluster's shape (machine types, workers, Spot, Spark properties) for a
workflow. Create it:

```yaml
# workflows/orders-cluster.yaml
config:
  masterConfig:
    machineType: "n2-standard-4"
    numInstances: 1
  workerConfig:
    machineType: "n2-standard-4"
    numInstances: 2
    secondaryWorkerConfig:
      numInstances: 4
      type: "SPOT"
  softwareConfig:
    imageVersion: "2.2-debian12"
    properties:
      "spark:spark.sql.sources.partitionOverwriteMode": "DYNAMIC"
      "spark:spark.sql.adaptive.enabled": "true"
  labels:
    pipeline: "daily-orders"
  gceClusterConfig:
    configBucket: "your-bucket"
```

⚠️ **Cluster config file keys use the `spark:` prefix; per-job `--properties` do not.**
`softwareConfig.properties` in a cluster config takes `"spark:key": "value"`. Job-level
`--properties` in gcloud takes `key=value` with **no** prefix. Mixing them up silently
does nothing.

### Step 5 — Watch it

```bash
# List workflow operations
gcloud dataproc workflows list --region=$REGION --limit=5

# Describe one
gcloud dataproc workflows describe WORKFLOW_ID --region=$REGION \
  --format="table(name,status.state,createTime)"

# The individual jobs in the workflow
gcloud dataproc workflows describe WORKFLOW_ID --region=$REGION \
  --format="value(graph.nodes)" | head -40

# Find the auto-created cluster and watch it appear
gcloud dataproc clusters list --region=$REGION --limit=5 \
  --format="table(clusterName,status.state,config.workerConfig.secondaryWorkerConfig.type)"
```

### Step 6 — Run a single job directly (for development and recovery)

```bash
# Interactive dev: a persistent cluster you keep around
gcloud dataproc clusters create course-dev \
  --region=$REGION \
  --image-version=2.2-debian12 \
  --master-machine-type=n2-standard-4 \
  --worker-machine-type=n2-standard-4 \
  --num-workers=2 \
  --num-secondary-workers=2 \
  --secondary-worker-type=spot \
  --delete-max-idle=1h

# Submit the pipeline as a single job
gcloud dataproc jobs submit pyspark gs://$BUCKET/jobs/job_pipeline.py \
  --cluster=course-dev \
  --region=$REGION \
  --py-files=gs://$BUCKET/jobs/lib/quality.py \
  --properties-file=spark.properties \
  --labels=pipeline=daily-orders,run_date=$RUN_DATE \
  -- --run-date=$RUN_DATE \
     --landing-uri=gs://$BUCKET/landing \
     --bronze-uri=gs://$BUCKET/bronze \
     --silver-uri=gs://$BUCKET/silver \
     --bigquery-table=$PROJECT_ID.analytics.orders_gold
```

`spark.properties`:

```text
spark.executor.instances=4
spark.executor.cores=2
spark.executor.memory=4g
spark.sql.shuffle.partitions=200
spark.sql.adaptive.enabled=true
spark.sql.sources.partitionOverwriteMode=DYNAMIC
spark.task.maxFailures=6
spark.serializer=org.apache.spark.serializer.KryoSerializer
```

⚠️ **`gcloud dataproc clusters submit` is obsolete.** Use
`gcloud dataproc jobs submit pyspark`. The older form still appears in most tutorials
and AI-generated code; it was superseded years ago.

### Step 7 — Verify idempotency (this is the important test)

```bash
# Run 1
gcloud dataproc jobs submit pyspark gs://$BUCKET/jobs/job_pipeline.py \
  --cluster=course-dev --region=$REGION \
  -- --run-date=$RUN_DATE --only=load

# Count rows in the gold partition
bq query --use_legacy_sql=false --format=table \
  "SELECT COUNT(*) AS rows FROM \`$PROJECT_ID.analytics.orders_gold\`
   WHERE dt='$RUN_DATE'"

# Run 2 — SAME run date, SAME data
gcloud dataproc jobs submit pyspark gs://$BUCKET/jobs/job_pipeline.py \
  --cluster=course-dev --region=$REGION \
  -- --run-date=$RUN_DATE --only=load

# Count again — the number must be IDENTICAL
bq query --use_legacy_sql=false --format=table \
  "SELECT COUNT(*) AS rows FROM \`$PROJECT_ID.analytics.orders_gold\`
   WHERE dt='$RUN_DATE'"
```

```
  Run 1: rows = 1000000
  Run 2: rows = 1000000     ← ✅ idempotent
```

If run 2 shows 2000000, your write disposition is `WRITE_APPEND` or your Spark write
mode is `append`. Fix that before going any further.

### Step 8 — Verify the results in BigQuery

```bash
# Row count per partition — should show each date exactly once
bq query --use_legacy_sql=false --format=table \
  "SELECT dt, COUNT(*) AS rows, COUNT(DISTINCT order_id) AS distinct_orders
   FROM \`$PROJECT_ID.analytics.orders_gold\`
   GROUP BY dt ORDER BY dt DESC LIMIT 14"

# The business metric the dashboard shows
bq query --use_legacy_sql=false --format=table \
  "SELECT dt, SUM(total_amount) AS revenue, COUNT(*) AS orders
   FROM \`$PROJECT_ID.analytics.orders_gold\`
   WHERE dt >= '2026-10-15'
   GROUP BY dt ORDER BY dt"

# Confirm no duplicate business keys survived
bq query --use_legacy_sql=false --format=table \
  "SELECT order_id, COUNT(*) c
   FROM \`$PROJECT_ID.analytics.orders_gold\`
   WHERE dt='$RUN_DATE'
   GROUP BY order_id HAVING c > 1 LIMIT 20"

# Inspect the table schema and partitioning
bq show --schema --format=prettyjson "$PROJECT_ID:analytics.orders_gold"

# Table metadata: partitioning, row count, size
bq show --format=prettyjson "$PROJECT_ID:analytics.orders_gold" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d.get('tableReference'),indent=2)); print(d.get('numRows'), d.get('numBytes'))"
```

### Step 9 — Schedule it

**Option A — Cloud Scheduler → Dataproc workflow (no Airflow).**

```bash
gcloud scheduler jobs create http daily-orders-workflow \
  --location=us-central1 \
  --schedule="0 2 * * *" \
  --time-zone="America/Los_Angeles" \
  --uri="https://workflows.googleapis.com/v1/projects/$PROJECT_ID/locations/$REGION/workflows:submit" \
  --http-method=POST \
  --headers="Content-Type=application/json" \
  --body='{
    "templateUri": "gs://BUCKET/workflows/DataprocWorkflow.yaml",
    "operation": {"operationTimeout": "6h"},
    "labels": {"pipeline": "daily-orders"},
    "parameters": {"run_date": "RUN_DATE_PLACEHOLDER"}
  }'
```

⚠️ **The `run_date` in a Cloud Scheduler body must be computed at request time**, not at
creation time. `--body` is a literal string, so `$(date ...)` inside single quotes is
evaluated by the shell *when you create the job* — it becomes a fixed date and the
schedule reprocesses that same date forever. The reliable fix is to let the pipeline
default to "yesterday" when `--run-date` is omitted, or to use Composer, where `{{ ds }}`
is resolved per run by Airflow.

**Option B — Cloud Scheduler → Composer DAG (recommended for anything non-trivial).**

```bash
# Trigger the DAG with a specific logical date (this is also your backfill tool)
gcloud composer environments run daily_orders_pipeline \
  --region=$REGION \
  --run-date="$RUN_DATE"

# The DAG's own `schedule="0 2 * * *"` handles the recurring trigger.
# Cloud Scheduler is only needed for a cron cadence Airflow can't express.
```

💡 **Composer gives you `{{ ds }}` for free** — the logical date is resolved per run and
is always the intended data date, with no shell-quoting hazards. This is the main
practical reason to prefer Composer over a raw Cloud Scheduler → workflow call.

### Step 10 — Emit metrics to Cloud Monitoring

The standard way to get Spark job metrics into Cloud Monitoring is the **Spark
executor metrics** agent that Dataproc installs — executor memory, GC time, shuffle
bytes, and task counts are exported automatically as `spark.executor.*` metrics against
the `cloud_dataproc_cluster` monitored resource. **This is the first thing to enable**,
because it is free.

For *business* metrics (row counts, bytes written, stage duration), emit them yourself.
The `google-cloud-monitoring` client library writes a custom metric to the Cloud
Monitoring API:

```python
# lib/monitoring.py
"""Emit custom pipeline metrics to Cloud Monitoring."""
import time

from google.api.metric_pb2 import Metric
from google.cloud import monitoring_v3
from google.protobuf.timestamp_pb2 import Timestamp


def write_pipeline_metrics(project_id, cluster_name, run_date, metrics):
    """
    Write one GAUGE time series per metric to the Cloud Monitoring API.

    metrics: {"rows_in": 1000, "rows_out": 980, "bytes_written": 12345}
    Produces:
      custom.googleapis.com/pipeline/rows_in
      custom.googleapis.com/pipeline/rows_out
      custom.googleapis.com/pipeline/bytes_written

    The monitored resource type is "cloud_dataproc_cluster"; Dataproc
    clusters surface there with a global location label.
    """
    client = monitoring_v3.MetricServiceClient()

    for name, value in metrics.items():
        series = monitoring_v3.TimeSeries()
        series.metric.type = f"custom.googleapis.com/pipeline/{name}"
        series.metric.kind = Metric.GAUGE
        series.metric.value_type = Metric.ValueType.INT64
        # Bounded cardinality: run_date, never run_id.
        series.metric.labels["run_date"] = run_date
        series.resource.type = "cloud_dataproc_cluster"
        series.resource.labels["project_id"] = project_id
        series.resource.labels["location"] = "global"
        series.resource.labels["cluster_name"] = cluster_name
        series.points[0].value.int64_value = int(value)
        series.points[0].interval.end_time = Timestamp(seconds=int(time.time()))

        client.create_time_series(
            name=client.project_path(project_id),
            time_series=[series],
        )
```

The service account running the job needs `roles/monitoring.metricWriter` on the project,
and the Dataproc worker's default scopes must include `cloud-platform`:

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:YOUR_SA@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/monitoring.metricWriter"
```

💡 **Alternatively, and often better: write metrics to BigQuery.** A
`pipeline_runs` table with `(run_id, run_date, stage, rows_in, rows_out, bytes_written,
duration_seconds, status)` is trivially queryable, versioned with the data, and joins
with everything else. Use Cloud Monitoring for *operational* signals (alerts, SLOs) and
BigQuery for *analytical* signals. Most mature teams use both.

⚠️ **Do not put a `run_id` label on a metric you intend to graph over time.** Every
distinct `run_id` creates a new time series, and Cloud Monitoring has a limit on the
number of active time series per metric — a high-cardinality label will eventually hit
the quota and start dropping data. Label with `run_date` (bounded cardinality) and put
`run_id` only in logs.

---

## Error handling, retries, and resumability

### Spark's task-level retry

When an executor dies — a Spot VM reclaimed, a transient GCS error — Spark does not fail
the job immediately. It **relaunches the task** on another executor, up to
`spark.task.maxFailures` attempts (default **4**). Only when that limit is exhausted does
the stage fail.

```text
spark.task.maxFailures=6
```

Raising it is the right call for pipelines reading from GCS, because the two most common
transient failures (a preempted worker, a 503 from GCS) resolve themselves on retry.

💡 **Spot VMs and task retries are a matched pair.** A Spot cluster with
`spark.task.maxFailures=6` will survive the occasional reclaim with no user-visible
error, and the job finishes at a fraction of the on-demand cost. This is the single
biggest cost win in the whole course.

⚠️ **But a preemption storm can still kill the job.** If the cluster has 4 Spot workers
and the reclaim rate is high, the same stage can exhaust 6 attempts. Mitigate with:
more workers (so failed tasks can be rescheduled), a
`secondaryWorkerConfig` with a `maxPreemptibleAttempts`, or falling back to on-demand for
the final (small) stages. Also set
`dataproc:cluster.shutdown.script` and use `--delete-max-idle` so a half-dead cluster
does not linger.

⚠️ **Task retry does not retry the *driver*.** If the driver itself dies (OOM on the
master, a Python exception in `main()`), the whole job fails. The orchestrator's retry
(Dataproc Workflow / Composer `retries`) is what covers that. You need both layers.

### The atomicity of a Spark write to GCS

A Spark write to GCS is **not** atomic by default. Spark writes each partition to a
temporary file, then renames it into place. On local HDFS that rename is atomic. On GCS,
the Hadoop FileSystem implementation performs the "rename" as a **copy + delete** — not
atomic.

That means: a job that dies halfway through writing 200 partition files leaves a
**partially written output directory**. If the next run uses `mode("append")` — or if
anything reads that directory — you get a corrupt dataset that looks fine.

Two mitigations:

**1. Write to a staging path, then promote.**

```python
staging = f"{config['silver_uri']}_staging/{run_id}"
final   = f"{config['silver_uri']}orders/dt={run_date}"

# 1. Write to a path unique to this run. If the job dies, the staging
#    directory is orphaned but the production partition is untouched.
silver_df.write.mode("overwrite").partitionBy("dt").parquet(staging)

# 2. Only now, promote staging → final.
#    Use gsutil/Storage API to copy then delete, or write via a Spark job
#    that reads staging and writes final with overwrite semantics.
```

**2. Use the "failed" marker + a cleanup step.** Many production pipelines write a
`_SUCCESS`-style marker file and have the loader refuse to read a partition that lacks
one. The BigQuery connector's `writeMethod=direct` and Dataproc's own atomic-move
helpers cover most of this.

💡 **In practice, `mode("overwrite")` with `partitionOverwriteMode=DYNAMIC` on a
single-partition-per-run-date layout is safe enough for the vast majority of pipelines.**
Spark overwrites the *static partition directory*, and because the whole partition is
rewritten by the same job, a partial write is at worst replaced by the next run of the
same date. The genuinely dangerous case is `mode("append")` into a shared directory,
which has no protection at all. **Never append to a date-partitioned path.**

### Making the workflow resumable

"Resumable" means: after a failure, you can pick up from the failed stage without
re-running the successful ones — and doing so is safe.

The `--only` flag in `job_pipeline.py` is the mechanism:

```bash
# The workflow's first job (extract) failed. Re-run just that stage.
gcloud dataproc jobs submit pyspark gs://$BUCKET/jobs/job_pipeline.py \
  --cluster=course-dev --region=$REGION \
  -- --run-date=$RUN_DATE --only=extract

# Then resume from the next stage
gcloud dataproc jobs submit pyspark gs://$BUCKET/jobs/job_pipeline.py \
  --cluster=course-dev --region=$REGION \
  -- --run-date=$RUN_DATE --only=transform
```

For this to be safe, every stage must be idempotent — which is exactly the design
constraint from earlier in this chapter. The `--only` flag is a convenience; idempotency
is the actual guarantee. **A resumable pipeline is an idempotent pipeline with extra
commands.**

💡 **Make stage completion observable.** Write a small `_stage_complete` marker (or a
row in the `pipeline_runs` table) after each stage succeeds, keyed by
`(run_date, stage)`. A recovery tool can then look up which stages completed and pick up
from the first missing one. This turns "resume" from a guess into a lookup.

---

## Cost optimization

| Lever | Flag / setting | Effect | Trade-off |
|-------|---------------|--------|-----------|
| Ephemeral cluster | Dataproc Workflow / Composer create+delete | Pay only for run duration | ~90s cluster startup per run |
| Preemptible workers | `--secondary-worker-type=spot` | ~60-70% cheaper per vCPU | Needs `spark.task.maxFailures` > 1 |
| On-demand primary workers | `--num-workers=2` | Guaranteed capacity for the job | Full price on 2 nodes |
| Shuffle partitions | `spark.sql.shuffle.partitions` | Fewer, larger tasks → less overhead | Too few = OOM; too many = slow |
| AQE | `spark.sql.adaptive.enabled=true` | Auto-coalesces shuffle partitions | Needs Spark 3+ |
| BigQuery bytes cap | `maxBytesBilled` | Hard cap on the load cost | Load fails if exceeded |
| Partition expiration | `partitionExpirationTime` | Old gold partitions auto-deleted | Historical data disappears |
| Storage classes | `gsutil set-storage-class` | Cold data → Archive | Retrieval delay |
| Job label pruning | `--labels` | Metrics/logs filterable | No cost effect, big ops effect |

### `spark.sql.shuffle.partitions` — the most under-tuned setting

The default is **200**. That is a terrible default for almost every workload.

```
  Your dataset has 50 MB and 1 partition
  → 200 shuffle tasks, 199 of which do nothing
  → 200 task-scheduling overhead, 200 small files

  Your dataset has 50 TB and 1,000,000 natural partitions
  → 200 shuffle tasks, each processing 250 GB
  → task OOM, or 250 GB spills to disk
```

The rule of thumb: **shuffle partitions ≈ 2–3× the total executor cores**, and let AQE
fix the rest.

```
  10 workers × 4 cores = 40 cores
  → spark.sql.shuffle.partitions = 100 (2.5×)
  → spark.sql.adaptive.enabled = true   (AQE coalesces to the right size)
```

With AQE on, you can set the shuffle partitions somewhat high and let Spark coalesce
small partitions automatically at runtime. AQE's `coalescePartitions` merges the
under-sized partitions the join produced, and `skewJoin` splits the ones that are too
big. **Enable AQE and stop micro-tuning.**

💡 **Also watch the number of output files.** `spark.sql.shuffle.partitions` determines
the number of *files* written per partition. 200 files × 1,000 partitions × 1.2 GB = a
240,000-file directory that BigQuery will choke on reading. Use `repartition` or
`coalesce` deliberately:

```python
# Target ~128 MB per output file
silver_df.repartition(
    F.col("dt"),                        # keep the date partition
    (F.size(F.to_json(F.struct(*silver_df.columns))) / (128 * 1024 * 1024)).cast("int")
).write.mode("overwrite").option("partitionOverwriteMode", "DYNAMIC").parquet(path)
```

⚠️ **`maxBytesBilled` is a hard failure, not a throttle.** When the limit is hit, the
BigQuery load errors out. Set it at roughly 1.5–2× your expected partition size so a
normal run never trips it, and a pathological run fails loudly instead of quietly
spending your budget.

---

## Observability

### What to log

Every pipeline run should answer, without a human digging: *what ran, on what data, and
what came out?* Log this, per stage:

| Field | Example | Why |
|-------|---------|-----|
| `run_id` | `8f3a2c1d-20261028T020000Z` | Correlates logs, metrics, and GCS paths |
| `run_date` | `2026-10-28` | The data being processed |
| `stage` | `transform` | Where in the pipeline |
| `rows_in` / `rows_out` | `1000000 → 980000` | The single most important metric |
| `bytes_written` | `1458398720` | Storage and cost impact |
| `duration_seconds` | `412.3` | Performance regression detection |
| `input_path` / `output_path` | `gs://...` | Reproducibility |
| `status` | `SUCCESS` / `FAILED` | Dashboarding |
| `error` | exception repr | Triage |

The `job_pipeline.py` in this chapter logs rows in/out and per-stage timing. Add bytes
written with a simple helper:

```python
def gcs_bytes(path: str) -> int:
    """Total bytes across all files under a GCS path."""
    from pyspark.sql import functions as F
    return (
        spark.read.format("binaryFile")
        .option("recursiveFileLookup", "true")
        .load(path)
        .select(F.sum(F.length("content")).alias("b"))
        .first()["b"] or 0
    )
```

### Cloud Logging filters

Driver stdout lands in Cloud Logging with the resource type
`cloud_dataproc_cluster`. Because our log lines are structured with a stable prefix,
you can filter on them:

```bash
# All pipeline lines for one run date
gcloud logging read \
  "resource.type=cloud_dataproc_cluster
   AND textPayload:\"run_date=2026-10-28\"
   AND textPayload:\"run_id=8f3a2c1d\"" \
  --project=$PROJECT_ID --limit=100 \
  --format="table(timestamp,severity,textPayload)"

# Only errors
gcloud logging read \
  "resource.type=cloud_dataproc_cluster
   AND severity>=ERROR" \
  --project=$PROJECT_ID --limit=50

# Only the stage timing lines
gcloud logging read \
  "resource.type=cloud_dataproc_cluster
   AND textPayload:\"wrote silver\"" \
  --project=$PROJECT_ID --limit=20

# Exclude the Spark progress-bar noise
gcloud logging read \
  "resource.type=cloud_dataproc_cluster
   AND NOT textPayload:\"INFO SparkContext\"
   AND NOT textPayload:\"INFO ShuffleReader\"" \
  --project=$PROJECT_ID --limit=50
```

💡 **Put your own labels on the Dataproc job and the cluster** and filter on those
instead of parsing message text. `gcloud dataproc jobs submit --labels=pipeline=daily-orders,run_date=2026-10-28`
propagates to the job resource, and `resource.labels.pipeline="daily-orders"` is a
first-class filter — much more robust than grepping for a substring.

⚠️ **Dataproc driver logs are capped.** Very chatty drivers can hit the Cloud Logging
per-log-entry size limit (256 KB) and get truncated, and a job that emits tens of
thousands of lines becomes painful to query. Emit one line per stage, not one line per
row.

### Building a run-history table

The most useful observability artifact is a table of past runs:

```sql
CREATE TABLE IF NOT EXISTS `your-project.analytics.pipeline_runs` (
  run_id        STRING,
  run_date      DATE,
  pipeline      STRING,
  stage         STRING,
  status        STRING,       -- SUCCESS | FAILED | SKIPPED
  rows_in       INT64,
  rows_out      INT64,
  bytes_written INT64,
  duration_secs FLOAT64,
  error_message STRING,
  ts            TIMESTAMP
)
PARTITION BY DATE(ts);
```

Write a row per stage at the end of that stage, in a `finally`-style block so failures
are recorded too. Then:

```sql
-- Runs per day, success rate
SELECT DATE(ts) AS day,
       COUNT(DISTINCT run_id) AS runs,
       COUNTIF(status = 'SUCCESS') AS ok,
       ROUND(100.0 * COUNTIF(status='SUCCESS') / COUNT(run_id), 1) AS success_pct
FROM `your-project.analytics.pipeline_runs`
WHERE ts > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY day ORDER BY day DESC;

-- Which stage is the bottleneck?
SELECT stage,
       AVG(duration_secs) AS avg_s,
       MAX(duration_secs) AS max_s,
       COUNTIF(status='FAILED') AS failures
FROM `your-project.analytics.pipeline_runs`
WHERE ts > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY stage ORDER BY avg_s DESC;
```

---

## Troubleshooting playbook

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| **`java.lang.OutOfMemoryError` in executor** | Insufficient executor memory, or a single huge partition (skew) | Raise `spark.executor.memory`; add `spark.sql.shuffle.partitions` tuning; enable AQE; check for skew on the join key; repartition the skewed key with a salt |
| **`OutOfMemoryError` in driver** | `collect()`/`toPandas()` on a big result, or too many small tasks | Never collect a large DataFrame; use `limit()`; raise `spark.driver.memory` via `--properties=spark.driver.memory=8g`; reduce `spark.sql.shuffle.partitions` |
| **One task takes 10× longer than the rest** | **Data skew** — one key dominates a shuffle partition | Enable `spark.sql.adaptive.skewJoin.enabled=true`; add a salt column (random 1..N) to the hot key and re-join; broadcast the small side with `F.broadcast()` |
| **`quota exceeded` / `RESOURCE_EXHAUSTED` at cluster create** | Region capacity or a project quota on vCPUs | Request a quota increase; use a different region; reduce `--num-workers`; add `--num-secondary-workers` with Spot; retry with backoff |
| **Cluster creation fails: `ZONE_RESOURCE_POOL_EXHAUSTED`** | No capacity in the chosen zone | Use Auto Zone (`--zone=""`); use `--auto-zone-exclude-zones`; try another region |
| **Job sits `PENDING` for hours** | Scheduler contention, or the cluster is still being created | Check `gcloud dataproc jobs describe` → `status.substate`; check `status.details`; verify the cluster reached `RUNNING`; check for a `dataproc:dataproc.scheduler.max-concurrent-jobs` limit; cancel with `gcloud dataproc jobs kill` |
| **Duplicate rows on rerun** | Write mode is `append`, or BigQuery disposition is `WRITE_APPEND` | Use `mode("overwrite")` + `partitionOverwriteMode=DYNAMIC`; use BigQuery `writeDisposition=WRITE_TRUNCATE` on a **partitioned** table |
| **All other dates' data disappeared** | `partitionOverwriteMode=STATIC` with `mode("overwrite")` — wiped the whole directory | Set `spark.sql.sources.partitionOverwriteMode=DYNAMIC`; restore from a GCS version or re-run those dates |
| **`FileAlreadyExistsException` on write** | Writing to a path that already exists in `mode("error")` | Use `mode("overwrite")`; or delete the target first |
| **`AnalysisException: Path does not exist`** | Missing `dt=` partition directory, or a run-date typo | `gsutil ls gs://bucket/silver/orders/` to list actual partitions; validate `--run-date` format early |
| **`ModuleNotFoundError` for a helper module** | Helper `.py` not on the Python path | Add `--py-files=gs://.../lib/quality.py` or list `pythonFileUris` in the workflow YAML |
| **`AnalysisException: Table or view not found` for BigQuery** | Table doesn't exist and `createDisposition` is `CREATE_NEVER` | Use `createDisposition=CREATE_IF_NEEDED`, or pre-create the partitioned table |
| **BigQuery load fails with "too many errors"** | Malformed rows rejected by the schema | Write a `_errors` table and use `writeMethod=indirect`; or cast/clean in silver |
| **`maxBytesBilled` exceeded** | The partition is much larger than expected | Raise the cap deliberately; or partition the load more finely; or check for a join blow-up upstream |
| **Job is slow after adding workers** | Shuffle partitions too low for the new parallelism, or data skew | Raise `spark.sql.shuffle.partitions`; enable AQE; check the Spark UI's stage timeline |
| **Task killed, `ExecutorLostFailure`** | Spot worker preempted, or executor OOM-killed | Raise `spark.task.maxFailures`; use more Spot workers; raise `spark.executor.memory` |
| **Costs are higher than expected** | Cluster left running; BigQuery scanning a lot; GCS Class A ops from many small files | Set `--delete-max-idle` / use ephemeral clusters; partition-prune the BigQuery query; coalesce output files to reduce GCS ops |
| **Workflow submitted but no jobs ran** | YAML is not at the `workflows.gcs_uri` path, or the `jobs:` key is misspelled | `gsutil cat gs://bucket/workflows/DataprocWorkflow.yaml`; validate the YAML locally with `python3 -c "import yaml,sys; yaml.safe_load(open('f.yaml'))"`; check the workflow operation's `details` |
| **Workflow job fails with `mainClass not found`** | A `mainJarFileUri`/`mainClass` was supplied for a PySpark job | Remove `mainJarFileUri` and `mainClass` for PySpark jobs — the `spark:` block with only `args` and `pythonFileUris` is correct |
| **Composer DAG task "stuck" in `running`** | The operator is waiting on a job that errored, or a Worker slot is exhausted | Check the Airflow task log; check the Dataproc job state; increase Composer `max_num_workers`; use `poke_interval`/`timeout` on the operator |
| **Composer DAG is not running at all** | `schedule`/`schedule_interval` not matching Airflow 2.4+ expectations, or the DAG has never been parsed | Check the DAG import errors in the Airflow UI; verify `start_date` and `catchup`; run the DAG manually with a logical date |

---

## 🔑 Key Takeaways

- The capstone architecture is **GCS landing → bronze Parquet → silver Parquet → BigQuery gold → Looker**, and the layer boundaries are contracts, not just directories.
- The **medallion architecture** exists for four engineering reasons: re-runnability (bronze is your replay buffer), schema evolution (raw is stored verbatim; silver pins a stable schema), debuggability (bisect which layer broke), and isolation of raw from clean (an access-control boundary).
- **Dataproc Workflows** are a declarative YAML of an ordered job list on one auto-provisioned cluster. **Cloud Composer** adds branching, fan-out, cross-DAG triggers, backfills, and a real UI. Use workflows for straight-line ETL; use Composer when you need logic.
- The workflow YAML uses a top-level `jobs:` list with `jobName`, `labels`, and a **`spark:`** block containing `args`, `pythonFileUris`, `properties`, and (for JVM jobs) `mainJarFileUri`. There is **no `pysparkSubmit` key**. Submit with `gcloud dataproc workflow submit --region=... --workflows.gcs_uri=gs://... --name=...`.
- The modern Composer operator is **`DataprocSubmitJobOperator`** from `airflow.providers.google.cloud.operators.dataproc`. Use `schedule_interval` on Airflow 2.0–2.3 and `schedule` on 2.4+. Always set `catchup=False` and `max_active_runs=1`, and `trigger_rule="all_done"` on the cluster-delete task.
- **Idempotency is the central requirement.** Re-running the same run date must produce the identical result. `mode("overwrite")` + `partitionOverwriteMode=DYNAMIC` replaces only the target partition; `STATIC` destroys every other date.
- On the BigQuery side, the gold table must be **partitioned by `dt`** and loaded with `writeDisposition=WRITE_TRUNCATE` so a rerun replaces that partition instead of appending into it. `WRITE_TRUNCATE` on an *unpartitioned* table wipes the whole table.
- `spark.task.maxFailures` (default 4) is Spark's task-level retry. It is the mechanism that makes Spot/preemptible workers viable — raise it to 6 for GCS-backed pipelines. The **driver** is not covered by it; the orchestrator's retry covers that.
- Quality gates must run **before** the load. Row-count drop threshold, null-rate threshold, schema conformance, and reconciliation total. A failed gate raises, the `finally` block stops Spark, and BigQuery is never touched. Keep `run_id` (one execution) and `run_date` (one logical date) separate.
- Cost levers that actually matter: **ephemeral cluster per run**, **Spot secondary workers**, `spark.sql.shuffle.partitions` tuned to ~2–3× total cores with **AQE enabled**, and `maxBytesBilled` as a hard circuit breaker on the load. Remember `gcloud dataproc jobs submit pyspark` is the current command — `gcloud dataproc clusters submit` is obsolete.

---

## 📚 Practice Exercises

1. **Prove idempotency, then break it.** Run the full pipeline for `2026-10-28` twice and
   confirm the BigQuery row count and `SUM(total_amount)` are identical after both runs.
   Then change `writeDisposition` to `WRITE_APPEND` in `load_silver_to_bigquery()`,
   re-run once, and observe the doubling. Restore the code. Then remove
   `partitionOverwriteMode=DYNAMIC` (leaving it at `STATIC`), re-run for `2026-10-28`,
   and check whether the `dt=2026-10-27` partition still exists in GCS and in BigQuery.
   Write a one-paragraph explanation of exactly which mechanism saved you from data loss
   in each of the three cases, and what a Dataproc Workflow would have done in each case.

2. **Implement a staging-path write with promotion.** Rewrite
   `transform_bronze_to_silver()` to write to
   `gs://$BUCKET/silver/_staging/{run_id}/` and promote to the final partition only
   after the write completes. Use `google-cloud-storage` (or `gsutil` via
   `subprocess`) to copy-then-delete. Then simulate a crash: kill the job mid-write with
   `gcloud dataproc jobs kill` and verify that the production partition is still
   readable and correct, and that only an orphaned staging directory remains. Write the
   cleanup logic for orphaned staging directories older than 24 hours.

3. **Add a fourth quality gate and wire it to a failure.** Implement a
   "referential integrity" gate: every `customer_id` in silver orders must exist in the
   silver customers table for the same run date. Report the percentage of orphan rows.
   Make the gate fail when the orphan rate exceeds 1%. Then deliberately corrupt the
   customers dataset so the gate fails, and verify from the Cloud Logging output that:
   (a) the job exited with code 3, (b) the BigQuery load was never executed (check the
   gold table's row count for that date is unchanged), and (c) the gate report was still
   written to `gs://$BUCKET/reports/quality/`. This is the most important exercise in
   the chapter — it is the difference between a pipeline that fails safely and one that
   fails silently.

4. **Port the workflow to Cloud Composer, then do a cost audit.** Create a Composer DAG
   that reproduces the `DataprocWorkflow.yaml` behaviour: create a temporary cluster
   (`n2-standard-4` master, 2 on-demand workers, 4 Spot secondary workers, image
   `2.2-debian12`), submit the pipeline job, and delete the cluster. Use `{{ ds }}` for
   the run date, `schedule="0 2 * * *"`, `catchup=False`, `max_active_runs=1`, and
   `trigger_rule="all_done"` on the delete task. Then run `gcloud composer environments
   run daily_orders_pipeline --region=REGION --run-date=2026-10-28` to backfill a
   specific date. Finally, explain in writing why you would or would not keep *both* the
   Dataproc Workflow and the Composer DAG in this repository, and what would break if you
   scheduled both.

   Then run the pipeline on a 10-worker on-demand cluster and record the wall-clock time
   and the Dataproc cost. Repeat on a 2-worker on-demand + 8-Spot cluster with
   `spark.task.maxFailures=8` and `spark.sql.shuffle.partitions=100`. Compare cost per
   run, run time, and task failures; use the Spark UI stage timeline to show where the
   extra parallelism went; and identify the single change that would cut the bill most.

---

## 📖 Further Reading

- Dataproc Workflows overview — https://cloud.google.com/dataproc/docs/concepts/workflows
- Dataproc Workflows API (WorkflowTemplate / Workflow operations) — https://cloud.google.com/dataproc/docs/reference/rest/v1/projects.regions.workflowtemplates
- `gcloud dataproc workflow submit` reference — https://cloud.google.com/sdk/gcloud/reference/dataproc/workflows/submit
- Submitting jobs (console, gcloud, REST) — https://cloud.google.com/dataproc/docs/guides/submit-job
- `gcloud dataproc jobs submit pyspark` reference — https://cloud.google.com/sdk/gcloud/reference/dataproc/jobs/submit/pyspark
- Cloud Composer overview — https://cloud.google.com/composer/docs/composer-2/overview
- Composer 2 operators reference — https://cloud.google.com/python/docs/airflow/providers/google/cloud/operators/dataproc
- `DataprocSubmitJobOperator` API docs — https://cloud.google.com/python/docs/airflow/providers/google/cloud/operators/dataproc#dataprocsubmitjoboperator
- Airflow DAG scheduling (`schedule` vs `schedule_interval`) — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html
- BigQuery Storage Write API overview — https://cloud.google.com/bigquery/docs/write-api
- BigQuery write dispositions — https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language#insert_statement
- BigQuery partition pruning and `maxBytesBilled` — https://cloud.google.com/bigquery/docs/partitioned-tables
- Spark partition discovery / `partitionOverwriteMode` — https://spark.apache.org/docs/latest/sql-data-sources-load-save-functions.html
- Spark configuration reference (incl. `spark.task.maxFailures`) — https://spark.apache.org/docs/latest/configuration.html
- Spark tuning guide (AQE, partition sizing) — https://spark.apache.org/docs/latest/sql-performance-tuning.html
- Cloud Monitoring custom metrics — https://cloud.google.com/monitoring/custom-metrics/creating-metrics
- `google-cloud-monitoring` Python client — https://cloud.google.com/python/docs/reference/monitoring/latest/index
- Cloud Logging query language — https://cloud.google.com/logging/docs/view/logging-query-language
- Cloud Scheduler API — https://cloud.google.com/scheduler/docs/reference/rest
- Delta Lake on Dataproc (transactional table semantics) — https://cloud.google.com/dataproc/docs/concepts/delta-lake
- Apache Iceberg on Dataproc — https://cloud.google.com/dataproc/docs/concepts/iceberg
- Dataproc pricing — https://cloud.google.com/dataproc/pricing
- Dataproc Spot (preemptible) workers — https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/spot
- Dataproc autoscaling — https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/autoscaling
