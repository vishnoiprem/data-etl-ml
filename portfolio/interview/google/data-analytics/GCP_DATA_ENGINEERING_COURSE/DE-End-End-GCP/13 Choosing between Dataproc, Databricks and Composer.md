# Choosing between Dataproc, Databricks and Composer

> **Why this chapter exists.** The course deliberately builds the same
> daily-product-revenue pipeline twice — once on Dataproc
> ([07](07 Big Data Processing using Google Dataproc.md),
> [notebooks/08](notebooks/08 ELT Data Pipelines using Dataproc on GCP/))
> and once on Databricks
> ([08](08 Big Data Processing using Databricks on GCP.md),
> [notebooks/10](notebooks/10 ELT Data Pipelines using Databricks on GCP/)) —
> and then orchestrates it a third way in Airflow
> ([12](12 Data Pipeline Orchestration using Google Cloud Composer.md)).
>
> Building the same thing three ways is not redundancy. It is how you find
> out which parts of a pipeline are Spark problems and which are
> orchestration problems.
>
> This chapter is the argument. Everything before it is evidence.

---

## The one-sentence answer

> **Dataproc and Databricks solve the same problem — running Spark — and
> differ in who owns the operational burden. Composer and Databricks Jobs
> solve the same problem — sequencing work — and differ in where the
> metadata lives. Choose based on which of those two axes your organisation
> is actually short on.**

Everything below is the detail behind that sentence.

---

## The two axes

Most "Databricks vs Dataproc" arguments go wrong by treating it as a single
question with one answer. It is actually two questions, and they have
different answers.

### Axis 1 — where does the Spark runtime come from?

| | **Dataproc** | **Databricks on GCP** |
|---|---|---|
| What you get | A managed Spark/Hadoop cluster — VMs, provisioning, networking | A managed Spark platform — cluster, notebooks, jobs, UI, governance |
| Who owns the OS, the JVM, the Spark distribution | Google | Databricks |
| Who owns the notebook IDE, job scheduler, experiment tracking | Nobody (you build it) | Databricks |
| Who owns Spark version upgrades and CVEs | You, via the image version | Databricks |
| Storage | GCS native (HDFS is emulated, and discouraged) | Unity Catalog on GCS, or DBFS |
| Openness | Pure Apache Spark — bring any JAR, any library | Databricks Runtime — a curated, patched Spark build |
| You can bring your own Spark runtime | No — you pick an image version | No — you pick a DBR version |

**The honest framing:** Dataproc gives you *more* control and *less*
platform. Databricks gives you *less* control and *more* platform. Neither is
better. They are different products for different team shapes.

### Axis 2 — where does the pipeline metadata live?

This is the axis most discussions miss, and it is usually the deciding one.

| | **Composer (Airflow)** | **Databricks Workflows** | **Dataproc Workflows** |
|---|---|---|---|
| Unit of orchestration | A DAG of tasks | A Job of tasks | A Workflow Template of jobs |
| State lives in | Airflow's metadata database, managed by Composer | Databricks' control plane | Dataproc's control plane |
| Can it orchestrate non-GCP things | **Yes** — anything with an API | Mostly Databricks-native; some external | Mostly Dataproc-native |
| Retry/backfill semantics | Mature — catchup, backfill, `max_active_runs` | Good, improving | Basic |
| Dynamic DAG generation | Yes — write Python at parse time | No | No |
| Observability | Airflow UI, task logs, SLA alerts | Databricks UI, run history | Dataproc UI, job history |
| Cost model | Airflow runs always-on → you pay for idle scheduler | Included in workspace | No extra cost, but needs a cluster |

---

## The actual decision

### Pick Dataproc when

- **Your team already runs Spark in production on something else** (EMR,
  Databricks, self-managed) and wants to keep one Spark codebase.
- **You need a specific JAR** that Databricks Runtime does not ship.
- **Your workloads are batch, with a clear start and stop.** Dataproc's
  ephemeral clusters and `--max-idle-duration` are excellent for this.
- **Data gravity is entirely on GCP** — everything already lives in GCS and
  BigQuery, and adding a second vendor's control plane has no offsetting
  benefit.
- **You want to avoid a second billing relationship** and a second
  enterprise contract.

### Pick Databricks on GCP when

- **Your team does not want to run Spark.** Dataproc hands you a cluster;
  Databricks hands you a working platform with notebooks, jobs, and a UI
  that non-engineers can read.
- **The pipeline is productised** — many pipelines, many owners, and people
  outside the data team need to inspect and rerun them.
- **You want the medallion architecture** — Delta Lake, Unity Catalog,
  time travel, and `MERGE` semantics without hand-rolling them.
- **You are running ML on the same platform** — the feature store, model
  serving, and experiment tracking are the reason many teams choose
  Databricks over a bare Spark platform.
- **Your analysts need a self-serve path** to run and rerun pipelines
  without a deploy.

### Pick Composer when

- **You orchestrate across GCP services.** This is Composer's actual job —
  BigQuery, Dataproc, Dataflow, Cloud Functions, GCS, Cloud Run. A DAG
  with fifteen task types in five services is Composer.
- **Your pipelines need Python logic** between steps — dynamic task
  generation, custom branching, per-run configuration.
- **You need backfill.** Airflow's `airflow dags backfill` with logical
  dates is a real operational capability.
- **You already run Airflow.** Moving from MWAA or Composer 2 to Composer 3
  is a platform upgrade, not a rewrite.

### Pick Databricks Workflows when

- **Every task is a Databricks task.** If the whole pipeline runs on
  Databricks — notebook, SQL, Python script, or `dbt` — there is no
  reason to route the orchestration through Airflow.
- **You want one platform, one permission model, one audit trail.**
- **Your pipeline is driven by data, not by time** — Delta Live Tables and
  Lakeflow pipelines are declarative and trigger off new data arriving.

---

## The case study: one pipeline, three implementations

This is the actual pipeline the course builds. It runs daily and computes
daily product revenue.

```text
raw (GCS)  →  convert CSV to Parquet  →  compute daily revenue  →  BigQuery
```

### Implementation A — Dataproc + Dataproc Workflows

**Artifacts in this repo:**
- `notebooks/08 ELT Data Pipelines using Dataproc on GCP/Managing Dataproc Workflows using gcloud.ipynb` — the workflow template build
- `notebooks/08 …/Run and Validate ELT Data Pipeline using Dataproc.ipynb`
- `scripts/daily_product_revenue/cleanup.sql`, `file_format_converter.sql`,
  `compute_daily_product_revenue.sql`
- `apps/airflow_dags/daily_product_revenue_jobs.py` — the same steps as
  Airflow tasks
- `apps/airflow_dags/daily_product_revenue_wf.py` — Airflow triggering the
  Dataproc workflow template

The shape: a **Workflow Template** (`wf-daily-product-revenue-bq`) holds
the job dependency graph. Spark SQL jobs run against a Dataproc cluster.
The template is a versioned, reviewable YAML — a real artifact you can diff
in a pull request.

**Strength:** the template is the source of truth for the job graph, and
Airflow can trigger the *whole template* with one operator
(`DataprocInstantiateWorkflowTemplateOperator`). You get workflow-level
dependency resolution without hand-chaining tasks.

**Weakness:** the graph lives in Dataproc, so it cannot orchestrate a
BigQuery job or a Cloud Function in the same run. If the pipeline grows a
non-Spark step, you need a second orchestrator.

### Implementation B — Databricks on GCP + Databricks Workflows

**Artifacts in this repo:**
- `notebooks/10 ELT Data Pipelines using Databricks on GCP/ELT Data Pipeline for Daily Product Revenue.dbc`
- `notebooks/10 …/06 Copy Data Sets to DBFS using gsutil Commands.ipynb`

The shape: modularise the Spark application into separate notebooks — a
**File Format Converter** for `orders` and `order_items`, a **Compute Daily
Product Revenue** notebook, and a validator. Each becomes a task in a
Databricks Job, with the two converters as dependencies of the revenue task.
Parameters are passed at task level or job level.

**Strength:** a notebook is the unit of work, so it is also the unit of
review, the unit of testing, and the unit of rerun. When a downstream task
fails, you can rerun just that notebook interactively with the same
parameters and see the Spark UI immediately.

**Weakness:** the Job definition is built through the Databricks UI, and
without an exported JSON definition there is no version-controlled record of
the task graph. That is a real gap, and it is the gap this course should
close.

### Implementation C — Composer (Airflow) orchestrating either

**Artifacts in this repo:**
- `12 Data Pipeline Orchestration using Google Cloud Composer.md`
- `apps/airflow_dags/` — five DAGs

The shape: `daily_product_revenue_jobs.py` submits each step as a
`DataprocSubmitSparkSqlJobOperator` or `DataprocSubmitPySparkJobOperator`,
with Airflow managing the dependencies. `daily_product_revenue_vars_wf.py`
takes the different route — it instantiates the Dataproc Workflow Template
as a single task.

**Strength:** Airflow owns the *timeline*. Logical dates, catchup,
backfill, `max_active_runs`, SLA alerts, and a task-level retry policy all
come free. And because Airflow can call any API, adding a BigQuery
materialisation step or a dbt invocation later is trivial.

**Weakness:** the Python framework adds a failure mode the data platform
does not have — the DAG can fail because of Airflow, not because of the
data. It is another always-on service to operate, and another place where
permissions live.

---

## The comparison, side by side

| Dimension | Dataproc + Composer | Dataproc + Dataproc Workflows | Databricks + Workflows |
|---|---|---|---|
| Unit of work | Airflow task | Workflow template job | Databricks task (notebook/SQL) |
| Dependency graph lives in | Airflow metadata DB | Dataproc | Databricks control plane |
| Source-controlled? | **Yes** — the DAG is Python in git | **Yes** — the template is YAML in git | **Only if exported** — otherwise UI-only |
| Backfill | **Yes** — `airflow dags backfill` | Basic | Good |
| Cross-service orchestration | **Yes** — anything with an API | No — Dataproc only | Mostly Databricks-native |
| Non-engineer can rerun | No | No | **Yes** |
| Idle cost | Composer environment + cluster | Cluster only | Workspace + cluster |
| Governance | GCP IAM | GCP IAM | **Unity Catalog** |
| Open-source Spark | **Yes** | **Yes** | No — Databricks Runtime |

---

## How I would decide in practice

If someone asked me to pick a stack for a new GCP data platform today, here
is the reasoning I would walk through.

**Step 1 — is there more than one engine in the picture?**

If the pipeline mixes Spark with BigQuery-only steps, dbt models, and
Cloud Run functions, orchestrate in **Composer**. Airflow's generality is
the reason it wins: the DAG coordinates *the whole pipeline*, not just the
Spark part. The `daily_product_revenue_jobs.py` DAG in this repo is exactly
this shape, and extending it with a `BigQueryInsertJobOperator` task is a
five-line change.

**Step 2 — is the team running Spark, or running a platform?**

If the team is comfortable with Spark and already has Spark code, **Dataproc**
is the answer — it is the same Apache Spark, on the same GCS, with GCP IAM
doing the authorisation. If the team is building a data platform rather than
running jobs, Databricks removes a lot of work: the notebook IDE, the job UI,
Delta's `MERGE`, Unity Catalog's lineage, and the ML tooling.

**Step 3 — does the org want one vendor or one cloud?**

There is a real cost to Databricks-on-GCP that is rarely quantified: it is a
second enterprise relationship on top of Google Cloud, with its own
contract, its own commit structure, and its own quota negotiation. For
some organisations that is a governance win — one vendor owns the support
escalation. For others it is a procurement problem that outweighs the
engineering benefit.

**Step 4 — what does the failure mode cost?**

Composer adds a scheduler that can fail independently of the data. Dataproc
Workflows cannot orchestrate outside GCP, so a growing pipeline eventually
needs Airflow anyway. Databricks Workflows keep everything in one control
plane, which is simplest — until you need a step that is not a Databricks
task.

---

## The version I would actually ship

For a GCP-native retail analytics platform, with a data team that knows
Spark, and a reporting layer in BigQuery:

```text
  Dataproc (ephemeral, per-run)          ← Spark jobs
        ↑
  Composer (Airflow)                    ← the timeline
        ↓
  BigQuery (partitioned + clustered)     ← the warehouse
```

- **Composer orchestrates**, because the pipeline will grow non-Spark steps
  and Airflow handles them natively.
- **Dataproc executes Spark**, because ephemeral clusters cost nothing when
  idle and the team already knows Spark.
- **BigQuery is the warehouse**, because the serving layer is queries, not
  Spark jobs.

And I would use **Databricks** instead of Dataproc when one of these becomes
true:

- Non-engineers need to rerun pipelines themselves.
- The platform needs medallion/Delta semantics rather than plain Parquet.
- ML work is landing on the same platform and MLflow is wanted.
- The team wants to stop maintaining Spark infrastructure.

That is the argument — and it is the argument this course was built to
support.

---

## Where the next chapter would go

Three gaps in this course are worth closing, and this chapter is where they
would be closed:

1. **A Databricks cluster creation walkthrough.** The Databricks chapter
   never shows creating a cluster or node types, which makes "Big Data
   Processing using Databricks" thin on evidence.
2. **An exported Databricks job definition.** The Workflows chapter is
   GUI-only; a Jobs API 2.2 JSON export would make the task graph
   reviewable in a pull request, the way the Airflow DAG already is.
3. **`dbutils.jobs.taskValues`.** The chapter claims task-level
   and job-level parameters are supported but never shows the code. (Note:
   `dbutils.notebook.task.reparameterize` is *not* a real API — it appears
   in old tutorials. The real one is `dbutils.jobs.taskValues`.)
