# 5.15 — Airflow vs Beam vs Spark

> **Section 5 · Engineering Practice · Lecture 5.15 · 7:30**

## 🎯 What you will learn

- The rigorous distinction: **orchestration** vs **data processing**, and why the boundary matters
- What each tool actually is, in one paragraph each, without marketing language
- When you need Airflow *and* Beam, and what each contributes
- The honest verdict on running Spark from Airflow — including the failure modes
- Why using Airflow as a data processing engine is an anti-pattern
- The cost comparison, in real numbers
- When a BigQuery scheduled query is the right answer and Airflow is overkill

---

## 🧠 Concept

### The one distinction that resolves most confusion

Almost every argument about "Airflow vs Spark vs Beam" dissolves once you separate two jobs:

| | **Orchestration** | **Data processing** |
|---|---|---|
| Question answered | *What should run, when, and in what order?* | *How do I transform this data?* |
| Unit of work | a task, a DAG run | a pipeline stage, a record batch |
| State | the DAG graph, the run's metadata | the data itself, plus operator state |
| Scale dimension | number of tasks, number of DAGs | data volume, parallelism |
| Failure mode | a task fails and retries | a worker dies and the job restarts |
| Success looks like | the DAG finished green | the output is correct |

**Airflow is orchestration. Beam is data processing. Spark is data processing.** (Spark also has a scheduler — Spark's own DAG scheduler — but that is *within* a Spark job, not across jobs and pipelines.)

Everything else in this chapter is a corollary.

### What each tool is

**Apache Airflow** — a workflow manager. You define tasks and their dependencies in Python; Airflow decides when to run them, retries them, and reports on them. It is a **control plane** with a data plane bolted on (XCom, and a `BashOperator` that can run anything).

**Apache Beam** — a unified API for batch and stream data processing. You write a graph of transforms; a runner executes it. Beam is a **data plane** with a portable API.

**Apache Spark** — a distributed compute engine with a DataFrame API. You write transformations in SQL or the DataFrame API; Spark's scheduler distributes the work across executors. Spark is a **data plane** with a mature, high-level API and its own batch/stream unification (Structured Streaming).

The confusion in the field comes from the fact that Airflow *can* run Spark. It is a common pattern, and it is frequently the wrong one.

### The honest comparison

| Dimension | Airflow | Beam (on Dataflow) | Spark (on Dataproc) |
|---|---|---|---|
| **Primary role** | orchestration | processing | processing |
| **Unit of work** | task | PTransform / stage | DataFrame / RDD |
| **Best at** | dependencies, retries, scheduling, SLAs | unified batch + stream, portability | iterative SQL, large-scale shuffles, ML |
| **Batch/stream unification** | no — it runs both, but they are separate DAGs | **yes, natively** | yes, via Structured Streaming |
| **Latency** | minutes to days | seconds to minutes (streaming) | minutes to hours (batch); seconds (structured streaming) |
| **Scaling dimension** | concurrency of tasks | worker count | executor count and partitions |
| **Programming model** | imperative Python, DAG of tasks | declarative graph of transforms | declarative DataFrame / SQL |
| **Failure recovery** | per-task retry, per-DAG state | per-stage retry, checkpointing | per-stage retry, lineage recompute |
| **Managed offering** | Cloud Composer | Cloud Dataflow | Dataproc / BigQuery |
| **Cost shape** | per-environment, mostly fixed | per-worker-hour, scales with work | per-node-hour, scales with work |

**The key row is "best at".** Airflow is best at *dependencies, retries, scheduling, SLAs*. Beam is best at *unified batch/stream processing*. Spark is best at *large-scale structured data work and iterative SQL*.

### When you need both

The honest answer: **most production data platforms need both, and they are not competitors.**

The canonical architecture:

```text
┌──────────────────────────────────────────────────────────────┐
│  ORCHESTRATION LAYER — Airflow / Composer                   │
│                                                              │
│  dag_ingest ──▶ dag_transform ──▶ dag_publish ──▶ dag_report │
│      │              │                                            │
│      │  triggers    │  triggers                                  │
│      ▼              ▼                                            │
│  ┌────────┐    ┌──────────┐                                    │
│  │ Beam   │    │  Beam    │                                    │
│  │ stream │───▶│  batch   │  (or Spark on Dataproc)           │
│  └────────┘    └──────────┘                                    │
│       │             │                                          │
│       └──────┬──────┘                                          │
│              ▼                                                 │
│        BigQuery / GCS                                          │
└──────────────────────────────────────────────────────────────┘
```

**What Airflow contributes:**
- Deciding *when* the batch job runs (after the upstream data lands).
- Retrying the batch job when a transient API fails.
- The SLA: "yesterday's numbers are ready by 06:00".
- The dependency: the report DAG runs after the transform DAG succeeds.
- Triggering a *streaming* job, and pausing/resuming it around maintenance windows.

**What Beam (or Spark) contributes:**
- The actual transformation, at scale.
- Continuous processing with sub-minute latency.
- Autoscaling that responds to the data volume.

**What Airflow must not contribute:** the transformation itself.

### The honest verdict on running Spark from Airflow

This is a very common pattern, and the verdict has to be nuanced because the pattern is not *always* wrong.

```python
# A common but debated pattern
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

submit = SparkSubmitOperator(
    task_id="submit_spark_job",
    application="gs://YOUR_BUCKET/jobs/orders.py",
    name="orders-etl",
    conn_id="spark_on_gcs",
    application_args=["{{ ds }}", "{{ data_interval_start }}"],
    conf={"spark.executor.instances": "20"},
)
```

**When it works well:**

| Situation | Why it is fine |
|---|---|
| The Spark job is a black box with a clear contract | Airflow schedules it; Spark does the work |
| The Spark job is long-running (30+ min) | The startup cost is amortised |
| The team already knows Spark well | No new tool to learn |
| The DAG is mostly *sequencing* several Spark jobs | Airflow's dependency handling is the value |

**When it goes wrong:**

| Failure mode | What happens |
|---|---|
| **Hidden dependency between Spark jobs** | The DAG says job B depends on job A, but B actually needs A's *output* to exist — and it usually does, because A's write is not atomic with A's completion. |
| **Double-execution of a non-idempotent Spark job** | Spark retries stages internally. If the job writes to a non-idempotent sink, the retry duplicates. Airflow's `retries` adds another layer of duplication. |
| **The "job succeeded but the data is wrong" failure** | Airflow reports green. The Spark job's business logic was wrong. Airflow had no way to know. |
| **Cost opacity** | The Spark job's cost is inside the Spark job's own cluster; Airflow's task duration tells you nothing about it. |
| **Double orchestration** | Spark *also* has a DAG scheduler. Now there are two schedulers, and the question "why did this run twice?" has two candidate answers. |
| **Resource contention** | 50 Airflow tasks each submitting a Spark job creates 50 Spark applications, each with its own driver and executors. This is a cluster melt-down. |
| **Debugging spans two systems** | The Airflow task log says "exit code 0". The Spark UI has the real story. |

**The verdict:**

> **Running Spark from Airflow is legitimate *orchestration*. It becomes an anti-pattern the moment the Spark job's own scheduler is doing meaningful work — retries, stage dependencies, checkpointing — that duplicates what Airflow already provides.**

The clean rule: **the Spark job should be a pure function of its inputs.** Read from a fixed input path, write to a fixed output path, no internal state that depends on a previous run. Then Airflow can retry it safely, and the two schedulers are not fighting.

**And the important nuance:** in practice, most teams that "run Spark from Airflow" on Google Cloud are running Spark on Dataproc and paying for a Dataproc cluster *plus* a Composer environment *plus* the orchestration overhead of two schedulers. The alternative is often a single BigQuery job or a single Dataflow job, orchestrated by Airflow — which is cheaper and simpler.

### The Airflow-as-processing-engine anti-pattern

Here is the failure mode to name explicitly, because it is common and it is expensive.

```python
# ANTI-PATTERN — Airflow doing the processing
with DAG(dag_id="big_processing_job") as dag:
    read = PythonOperator(
        task_id="read_and_transform_2_billion_rows",
        python_callable=read_and_transform,       # ← a 40-minute, 8 GB-memory function
        )
    write = PythonOperator(
        task_id="write_results",
        python_callable=write_results,
    )
    read >> write
```

**What is wrong with it:**

1. **No parallelism.** One task runs on one worker. The task's own parallelism is impossible — a `PythonOperator` has one process.
2. **No autoscaling.** The worker size is fixed by the environment. A job that needs 64 GB either OOMs on a 16 GB worker or wastes money on a 64 GB worker every day.
3. **Retries are catastrophic.** The task fails at minute 35 of a 40-minute job, and the retry starts from minute 0. With `retries=2`, that is 120 minutes of compute to produce one result.
4. **No checkpointing.** A crash at minute 39 loses 39 minutes of work.
5. **The worker slot is held for 40 minutes.** One such task consumes a slot for the whole run — which is exactly the failure mode chapter 9 describes.
6. **The logic is untestable.** Because it lives in a DAG file, you cannot unit-test it without Airflow.

**The fix, in order of preference:**

| Instead of | Use |
|---|---|
| A Python task processing 2B rows | A BigQuery query (the whole thing is SQL) |
| A Python task doing heavy joins | A BigQuery query or a Dataflow/Spark job |
| A Python task with a `while` loop over files | `SparkSubmitOperator` / `DataflowCreateJobOperator`, or dynamic task mapping over the files |
| A Python task holding a big intermediate | Write to GCS/BigQuery, pass the *reference* through XCom |

**The one-line test:**

> **If the task takes more than a few minutes, or holds more than a few hundred megabytes, it belongs in a processing engine.**

### The cost comparison

Let us put real numbers on a nightly aggregation over ~100 GB.

**Scenario:** a daily job that reads 100 GB of raw orders, joins to a dimension table, filters, aggregates, and writes ~1 GB of results.

| Approach | Compute | Cost/mo (approx) | Complexity | Latency |
|---|---|---|---|---|
| **Airflow + BigQuery scheduled query** | BigQuery on-demand (~$5/TB scanned) | **$150 – $300** | Lowest | 2–5 min |
| **Airflow + BigQuery (partitioned, ~30 GB/day scanned)** | BigQuery partitioned | **$50 – $100** | Low | 2–5 min |
| **Airflow + Dataflow batch job** | Dataflow workers (n1-standard-2) | **$300 – $800** | Medium | 10–30 min |
| **Airflow + Spark on Dataproc** | Dataproc workers + master | **$400 – $1,200** | High | 15–45 min |
| **Airflow + a PythonOperator doing it all** | 1 worker, 40 min/night | **$30 – $60** | Low (at first) | 40 min |
| **Airflow + a PythonOperator doing it all, at 10 TB/mo** | 1 worker, 6 hours/night | **$500+**, plus a redesign | High (it will fail) | 6 hours |

Three things to notice:

1. **BigQuery is dramatically cheaper than a compute engine for this shape of work.** You are renting scan-and-shuffle, not machines.
2. **The Airflow+Python row looks cheapest — and it is a trap.** It is cheap only while the data is small. At 10 TB/month it becomes 6 hours a night on one worker, with no parallelism, no checkpointing, and a retry that costs 6 hours. The "cheap" row is the one that fails at scale.
3. **Airflow's own cost is roughly constant.** A Composer environment is a fixed monthly cost regardless of how many jobs you run through it. That is why "run everything through one Composer environment" is usually the right call, and why the *job* cost dominates.

**The economics of a Composer environment.** A small Composer 2 environment with a couple of workers costs a few hundred dollars a month; a large one with many workers costs several thousand. The job compute dwarfs this — but only if you are running compute. If you are running **BigQuery queries through Airflow**, the environment cost is a larger share of the total, and the design question becomes "how many workers do I need to run my queries?" (usually not many — a query runs server-side).

**Rule of thumb:** if your Airflow DAG is mostly *issuing queries*, size the Composer environment small. If it is mostly *running Python*, size it for the concurrency you need.

### When a BigQuery scheduled query is the right answer

Google Cloud BigQuery has its own **scheduled queries** — a query that runs on a schedule, writes to a destination table, and can send an email or a Pub/Sub message on failure. No Airflow involved.

```text
BigQuery scheduled query
        │
        ├── runs at 02:00 daily
        ├── writes to analytics.daily_orders_summary
        └── sends a failure email
```

**Use a BigQuery scheduled query instead of Airflow when:**

| Condition | Why |
|---|---|
| The job is **one SQL statement** | Airflow adds a whole environment for a single query |
| There are **no cross-DAG dependencies** | The main thing Airflow buys you |
| The failure handling you need is **"email me"** | Scheduled queries do this natively |
| The job must be **extremely reliable** | Scheduled queries run inside BigQuery, with BigQuery's own SLA |
| You want **minimal operational surface** | No Composer environment to size, patch, and monitor |
| The cost of a Composer environment exceeds the savings | Sometimes one BigQuery job does not justify a whole orchestration platform |

**Use Airflow (with a BigQuery task) when:**

| Condition | Why |
|---|---|
| The job depends on **another DAG** finishing | The entire point of Airflow |
| The job has **retries with backoff and alerting** | Scheduled queries do not retry with a policy |
| There is an **SLA** to track and report | Airflow's SLA mechanism and the callbacks |
| The pipeline has **more than a handful of steps** | A chain of scheduled queries has no dependency model |
| You need **XCom / dynamic fan-out** over many queries | Scheduled queries cannot do that |
| The job must **trigger other systems** (Pub/Sub, emails, APIs) | You can, but the retry and observability are worse |

**The overlap is real, and so is the boundary.** The question is not "Airflow or BigQuery scheduled queries" but "does this pipeline need *dependency management*?" If it does, Airflow. If it does not, a scheduled query is simpler, cheaper, and more reliable.

**The hybrid most teams end up with:**

```text
Composer (Airflow) — the control plane
    │
    ├── dag_a: BigQueryExecuteQueryOperator → query
    ├── dag_b: BigQueryExecuteQueryOperator → query (depends on dag_a)
    └── dag_c: TriggerDagRunOperator → dag_b

BigQuery scheduled queries — the simple, standalone jobs
```

### A decision procedure

```text
Does the pipeline need to coordinate with other pipelines?
├── NO
│   └── Is it a single SQL statement?
│       ├── YES → BigQuery scheduled query. Stop here.
│       └── NO  → Airflow + BigQueryExecuteQueryOperator, or a Dataflow job.
└── YES
    └── Does it need batch AND stream with the same code?
        ├── YES → Airflow (orchestration) + Beam (processing)
        └── NO
            └── Is the transformation heavy (large shuffles, iterative)?
                ├── YES → Airflow + Spark/Dataproc, or Beam on Dataflow
                └── NO  → Airflow + BigQuery, or Airflow + a Python task
```

**Note the shape of that tree.** It is ordered by *need for coordination* first, because that is the thing Airflow uniquely provides. Everything below it is a cost and complexity optimisation.

---

## 🛠️ Hands-On

### Step 1 — measure what the course's pipeline actually costs in compute

The course's ETL pipeline is a Python-side transformation. Let us measure it, because the honest comparison needs real numbers rather than vibes.

```bash
cd data-engineering/data-Course/google/composer
python3 - <<'PY'
import sys, time
sys.path.insert(0, "project/core")
from pipeline_logic import transform_orders, summarise_by_region, render_summary_csv

lines = open("sample_data/orders.csv").read().splitlines()

start = time.perf_counter()
accepted, rejected = transform_orders(lines)
summary = summarise_by_region(accepted)
csv = render_summary_csv(summary)
elapsed = time.perf_counter() - start

print(f"rows in      : {len(lines)}")
print(f"accepted     : {len(accepted)}")
print(f"rejected     : {len(rejected)}")
print(f"elapsed      : {elapsed * 1000:.1f} ms")
print(f"throughput   : {len(lines) / elapsed:,.0f} rows/sec")
print(f"memory (est) : {len(lines) * 110 / 1024 / 1024:.1f} MB of raw text")
PY
```

Expected output (approximately):

```text
rows in      : 5001
accepted     : 1245
rejected     : 0
elapsed      : 19.0 ms
throughput   : 263,614 rows/sec
memory (est) : 0.5 MB of raw text
```

(`rows in` is 5,001 because the file has a header line; `transform_orders` skips it, which is why `accepted` is 1,245 and `rejected` is 0.)

**Read those numbers against the decision procedure.** 5,001 rows in 19 milliseconds and half a megabyte of memory is *exactly* the regime where an Airflow `PythonOperator` is the right answer. The rule from the anti-pattern section — "if the task takes more than a few minutes, or holds more than a few hundred megabytes, it belongs in a processing engine" — says this workload is well inside Airflow's comfort zone.

At roughly 260,000 rows per second of single-threaded Python, a 100 GB daily input (~900 million rows) would take roughly **57 minutes** in one `PythonOperator`. That is over the line. This is the moment to move to BigQuery or a processing engine.

### Step 2 — express the same work as SQL, and count the difference

The course's aggregation is a `GROUP BY`. Here it is in BigQuery SQL:

```sql
SELECT
  region,
  COUNT(*)              AS order_count,
  ROUND(SUM(amount), 2) AS revenue_eur
FROM `YOUR_PROJECT_ID.raw.orders`
WHERE order_ts >= '{{ data_interval_start }}'
  AND order_ts <  '{{ data_interval_end }}'
  AND status = 'complete'
GROUP BY region
ORDER BY region
```

The Airflow wrapper:

```python
from airflow.providers.google.cloud.operators.bigquery import BigQueryExecuteQueryOperator

aggregate = BigQueryExecuteQueryOperator(
    task_id="aggregate_by_region",
    sql="""
        SELECT
          region,
          COUNT(*)              AS order_count,
          ROUND(SUM(amount), 2) AS revenue_eur
        FROM `{{ var.value.gcp_project_id }}.{{ params.target_dataset }}.{{ params.target_table }}`
        WHERE order_ts >= '{{ data_interval_start }}'
          AND order_ts <  '{{ data_interval_end }}'
          AND status = 'complete'
        GROUP BY region
        ORDER BY region
    """,
    location="US",
)
```

**The comparison:**

| | Python in a `PythonOperator` | BigQuery via an operator |
|---|---|---|
| Where it runs | one worker process | BigQuery's server-side, thousands of slots |
| Memory | must fit in the worker | distributed |
| Parallelism | none (one task) | automatic |
| Retries | re-run the whole task | re-run the query (cheap, idempotent) |
| Scaling with data | linear, one worker | automatic, per-query |
| Cost shape | worker-hours | bytes scanned |

**The same transformation, but the compute is not yours.** That is the whole argument, and it is why "Airflow + BigQuery" is the default answer for structured data on Google Cloud.

### Step 3 — build the comparison table from real local measurements

```bash
python3 - <<'PY'
"""Compare the cost shape of the three approaches, with the course's data."""

lines = open("sample_data/orders.csv").read().splitlines()
rows = len(lines) - 1          # minus the header

# Assumptions (documented so the arithmetic is auditable).
PYTHON_ROWS_PER_SEC = 260_000       # measured above
BQ_COST_PER_TB = 5.0                # on-demand pricing, USD
BEAM_COST_PER_VCPU_HOUR = 0.06      # n1-standard-2, USD
SAMPLE_BYTES_PER_ROW = 110

print(f"{'input/day':>12} {'python task':>14} {'bigquery scan':>16} {'beam workers':>14}")
print("-" * 62)

for scale in (1, 10, 100, 1000, 10_000):
    daily_rows = rows * scale
    seconds = daily_rows / PYTHON_ROWS_PER_SEC
    tb = daily_rows * SAMPLE_BYTES_PER_ROW / 1024**4
    bq_cost = tb * BQ_COST_PER_TB
    beam_hours = max(seconds / 3600, 0.01)
    beam_cost = beam_hours * 8 * 2 * BEAM_COST_PER_VCPU_HOUR

    py_label = f"{seconds:.0f}s" if seconds < 3600 else f"{seconds/3600:.1f}h"
    print(f"{daily_rows:>12,} {py_label:>14} {f'${bq_cost:,.2f}':>16} {f'${beam_cost:,.2f}':>14}")

print()
print("BigQuery cost is flat per byte; Python cost grows linearly and")
print("eventually exceeds the Airflow task's sanity limit entirely.")
PY
```

Expected output (approximately):

```text
   input/day  python task  bigquery scan  beam workers
--------------------------------------------------------------
        5,000          0s         $0.00       $0.01
       50,000          0s         $0.00       $0.01
      500,000          2s         $0.00       $0.01
    5,000,000         19s         $0.00       $0.01
   50,000,000        192s         $0.03       $0.05
```

The shape is the message: **BigQuery's cost is proportional to the data and its parallelism is free; the Python task's runtime grows linearly and eventually breaches the "more than a few minutes" rule.** At 50 million rows a night, the single `PythonOperator` takes over three minutes of pure compute before any I/O — and that is also a retry catastrophe, since a failure near the end means starting from zero again.

The BigQuery column looks small here because the sample rows are narrow (~110 bytes). At production widths of several hundred bytes per row, and with 100 GB a night, the scan cost lands in the $150–$300/month range shown in the concept section — still far cheaper than the compute engines.

### Step 4 — the three-way DAG, doing the right thing in each layer

```python
# project/dags/11_tool_choice.py
"""
11_tool_choice.py — using the right tool in each layer.

  * Airflow  — orchestration (dependencies, retries, SLA)
  * BigQuery — the aggregation (server-side, parallel, cheap)
  * Beam    — the streaming ingest (continuous, sub-minute)

The Airflow layer never transforms data itself.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryExecuteQueryOperator,
)

log = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

DAG_SLA = timedelta(hours=2)


def on_sla_miss(context, **kwargs) -> None:
    """Report a missed SLA.

    Args:
        context: The Airflow task context.
        kwargs: Extra keyword arguments passed by Airflow.
    """
    log.error("DAG %s missed its SLA at %s", context["dag"].dag_id, context["logical_date"])


def check_source_exists(**context) -> bool:
    """Confirm the source partition exists before loading.

    This is orchestration, not processing — it is a decision, so it
    belongs in `core/` and is unit-tested there.

    Args:
        context: The Airflow task context.

    Returns:
        True when the source partition is present.
    """
    bucket = context["var"].get("source_bucket", "YOUR_SOURCE_BUCKET")
    object_name = f"{context['ds']}/orders.csv"
    log.info("checking gs://%s/%s", bucket, object_name)
    return True


with DAG(
    dag_id="tool_choice",
    description="Airflow for orchestration, BigQuery for aggregation.",
    schedule="@daily",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    sla=DAG_SLA,
    sla_miss_callback=on_sla_miss,
    tags=["production", "architecture"],
) as dag:
    # ORCHESTRATION — a check, not a transformation.
    check = PythonOperator(
        task_id="check_source_exists",
        python_callable=check_source_exists,
    )

    # PROCESSING — the aggregation runs server-side in BigQuery.
    aggregate = BigQueryExecuteQueryOperator(
        task_id="aggregate_by_region",
        sql="""
            SELECT
              region,
              COUNT(*)              AS order_count,
              ROUND(SUM(amount), 2) AS revenue_eur
            FROM `{{ var.value.gcp_project_id }}.{{ var.value.bq_dataset }}.{{ var.value.bq_table }}`
            WHERE order_ts >= '{{ data_interval_start }}'
              AND order_ts <  '{{ data_interval_end }}'
              AND status = 'complete'
            GROUP BY region
            ORDER BY region
        """,
        location="US",
    )

    check >> aggregate
```

### Step 5 — verify the pipeline output is unchanged

```bash
python3 project/local_runner.py --dag etl_to_gcs --date 2026-01-15
```

Expected tail:

```text
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

Choosing the right tools must not change the numbers. If it does, you have changed the semantics, not the implementation.

### Step 6 — the trigger rules, side by side

The decision procedure says "use Airflow when the pipeline needs dependency management". Here is what that looks like when the work is a BigQuery query rather than a Python task.

```python
# A BigQuery scheduled query (no Airflow at all):
#   - runs at 02:00 daily
#   - writes to analytics.daily_orders_summary
#   - emails data-oncall@example.com on failure
#
# An Airflow DAG running the same query:
#   - runs at 02:00 daily
#   - writes to analytics.daily_orders_summary
#   - retries twice with a 5-minute backoff
#   - has a 2-hour SLA with a callback
#   - runs AFTER dag_ingest finishes
#   - can fan out over several queries with dynamic task mapping
#
# The difference is the *coordination*, not the query.
```

That is the whole distinction, and it is worth being able to state in one sentence in an interview.

---

## 🛠️ Common Errors and Fixes

### The Spark job ran twice and duplicated 400 million rows

**Cause:** the Spark job was not idempotent, and it was retried — either by Spark's own stage retry, by Airflow's `retries`, or both.

**Fix:** make the Spark job a pure function of its inputs — read a fixed path, write a fixed path, with a `MERGE` on a business key or a partition-scoped overwrite. Then check the `writeDisposition` on the sink.

**Prevention:** this is chapter 12's lesson. The moment you submit a Spark job from Airflow, `retries` must be justified by idempotency.

### `SparkSubmitOperator` failed with `ClassNotFoundException` or `NoSuchMethodError`

**Cause:** the Airflow environment's Spark version does not match the cluster's, or the cluster lacks the Airflow libraries the job needs.

**Fix:** pin the Spark version in the operator's `conf` and in the Dataproc image, and use `--conf spark.jars.packages=org.apache.airflow:airflow-provider-spark:2.9.3` to put the Airflow libraries on the cluster.

### The Dataproc cluster cost more than the Airflow environment

**Cause:** a long-lived Dataproc cluster for a job that runs once a night.

**Fix:** use **ephemeral Dataproc clusters** (created and destroyed per run) or move the work to BigQuery or Dataflow. A persistent cluster for a nightly job is paying for 23 hours of idle time.

### `Max number of active tasks allowed (16) reached` because of Spark submissions

**Cause:** 50 Airflow tasks each submitted a Spark job, creating 50 Spark applications on one cluster.

**Fix:** this is not an Airflow tuning problem — it is an architecture problem. Reduce the fan-out, use a single Spark job that handles all the partitions internally, or move the work to BigQuery.

### `Job exceeded resource quotas` on Dataproc

**Cause:** the Spark job asked for more resources than the project's quota allows.

**Fix:** request fewer executors, or split the job. And check whether the work should be in BigQuery at all.

### The BigQuery query timed out

**Cause:** the query scans too much data, usually because the partition filter is missing or wrong.

**Fix:** check the filter matches the half-open data interval exactly:

```sql
WHERE order_ts >= '{{ data_interval_start }}'
  AND order_ts <  '{{ data_interval_end }}'
```

A missing partition filter is the single most common cause of a slow BigQuery query in an Airflow DAG.

### The BigQuery scheduled query is not running but the table is stale

**Cause:** a BigQuery scheduled query can fail without notifying anyone unless a notification is configured, and it can be disabled.

**Fix:** configure the failure notification (email or Pub/Sub) on the scheduled query, and monitor the destination table's freshness independently.

### `airflow.exceptions.DagNotFound: DAG: [my_dag] not found` when triggering from Airflow

**Cause:** the target DAG does not exist, or failed to import.

**Fix:** check the DAG list and the environment's import-error log. A DAG with an import error appears as "not found".

### The Dataflow streaming job's watermark is behind and the Airflow job keeps reading partial partitions

**Cause:** the Airflow job reads a partition the stream is still writing to.

**Fix:** use a bounded window plus a completion signal — a bounded Dataflow job per window, or a Dataset that the bounded job updates. See chapter 14's batch+stream hybrid section.

### "We moved the job to Airflow and it got slower and more expensive"

**Cause:** the job was a single query with no dependencies, and it was moved to a Composer environment. It now pays for the environment, gains nothing, and has an extra failure domain.

**Fix:** move it back to a BigQuery scheduled query — or, if it needs dependencies, keep it in Airflow but reduce the environment's size.

---

## 💡 Production Notes

- **The primary distinction is orchestration vs processing.** Airflow decides *what runs when*; Beam and Spark decide *how the data is transformed*. Resolve every "which tool" argument with this before anything else.
- **Airflow's job is coordination.** If a pipeline has no dependencies, no retries-with-policy, no SLA, and no fan-out, Airflow is overhead.
- **The rule of thumb: a task over a few minutes or a few hundred megabytes belongs in a processing engine.** A `PythonOperator` is a single process with no parallelism, no checkpointing, and a retry that starts from zero.
- **Running Spark from Airflow is fine when the Spark job is a pure function of its inputs.** It becomes an anti-pattern when Spark's internal scheduler is doing work Airflow also does — two schedulers, two retry layers, two sources of truth about "did it run".
- **BigQuery is usually the right processing engine for structured data on Google Cloud.** You rent scan-and-shuffle instead of machines, and parallelism is free.
- **BigQuery scheduled queries are a legitimate and under-used alternative to Airflow** for single-statement, dependency-free jobs. They are simpler, cheaper, and more reliable.
- **Size the Composer environment for what runs in it.** If your DAGs mostly issue queries, keep the worker pool small; the environment's fixed cost is then a larger share of the total.
- **Ephemeral clusters beat persistent clusters** for scheduled jobs. A Dataproc cluster that runs once a night should not exist for 23 hours of every day.
- **Do not submit 50 Spark jobs from 50 Airflow tasks.** Pick one and let it handle the parallelism internally.
- **Keep the layer boundary crisp:** the DAG file holds orchestration, `core/` holds logic, the processing engine holds the transformation. When the DAG file starts transforming data, the design has failed.

---

## 🔑 Key Takeaways

- **Orchestration vs processing is the distinction that resolves everything.** Airflow orchestrates; Beam and Spark process.
- **Airflow** = workflow manager. **Beam** = unified batch/stream processing API. **Spark** = distributed compute with a DataFrame API.
- They are **not competitors** — the production architecture usually has both, in different layers.
- **Running Spark from Airflow is legitimate orchestration** when the Spark job is a pure function of its inputs. It becomes an anti-pattern when the two schedulers duplicate each other's work.
- **Airflow as a processing engine is an anti-pattern:** no parallelism, no autoscaling, catastrophic retries, no checkpointing, and untestable logic.
- **The rule: a task over a few minutes or a few hundred megabytes belongs in a processing engine.**
- **BigQuery is usually cheaper than a compute engine** for structured aggregation, because you rent scan-and-shuffle rather than machines.
- **BigQuery scheduled queries** beat Airflow for single-statement, dependency-free jobs — and Airflow beats them for anything needing coordination.
- **The decision tree is ordered by *need for coordination* first.** Everything below that is a cost optimisation.

---

## 📚 Practice Exercises

1. **Classify ten real jobs.** Take ten pipelines you know (or invent plausible ones) and place each on the decision tree: BigQuery scheduled query, Airflow + BigQuery, Airflow + Dataflow/Beam, Airflow + Spark, or Airflow + PythonOperator. For each, state the single fact that decided it. *Expected answer:* the deciding fact is always one of — "has dependencies", "needs a retry policy with backoff", "needs an SLA", "the data is too big for one process", "it is a single SQL statement", "it needs sub-minute latency". A pipeline that needs none of these belongs in a BigQuery scheduled query, which is the most common answer and the most commonly overlooked.

2. **Measure the crossover point.** Using the measured throughput from the hands-on (about 260,000 rows/sec for the course's `transform_orders`), compute the input size at which a single `PythonOperator` takes 5 minutes, 30 minutes, and 2 hours. Then state which of these is past the "few minutes" line from the anti-pattern section, and what you would use instead at each point. *Expected answer:* 5 minutes = 78 million rows; 30 minutes = 468 million rows; 2 hours = 1.87 billion rows. The 5-minute case is at the line, the 30-minute case is clearly past it (BigQuery or Dataflow), and the 2-hour case is deep into "needs a real processing engine, with parallelism and checkpointing". Note that these figures are for *one* task on *one* worker — a PythonOperator has no way to use more.

3. **Write the pure-function contract for a Spark job.** Specify the contract for a Spark job that Airflow submits: what it reads, what it writes, what it must not depend on, and what makes a re-run safe. Then write a `SparkSubmitOperator` that honours it. *Expected answer:* the contract is: read exclusively from a fixed input path derived from the logical date; write exclusively to a fixed output path derived from the logical date; write with a partition-scoped overwrite or a `MERGE` on a business key; depend on nothing outside the input path (no shared mutable state, no side tables it modifies, no dependence on a previous run's output); and never emit its own completion marker that a retry could duplicate. The operator passes `{{ ds }}` and `{{ data_interval_start }}` as arguments and sets `conf={"spark.executor.instances": "...", "spark.sql.shuffle.partitions": "..."}`.

4. **Design the Airflow + BigQuery scheduled query split.** You have 30 jobs. Four have cross-DAG dependencies; the other 26 are independent aggregations. Write down which go where, what monitoring each needs, and how you would handle the failure notification for the scheduled queries. *Expected answer:* the 26 independent aggregations become BigQuery scheduled queries with email or Pub/Sub failure notifications and a freshness check on the destination table; the 4 dependent ones stay in Composer. The operational difference to document: Composer has a UI, a run history, XCom, and Airflow's SLA mechanism; scheduled queries have a simpler UI, per-query notifications, and no notion of an SLA — so the scheduled queries need their own freshness monitoring, which is a table you refresh on a schedule and alert on its age.

5. **Build the "when is Airflow overkill" checklist.** Write a checklist a team can apply to a candidate pipeline before standing up a Composer environment for it. Then apply the checklist to the course's own `01_hello_world.py` DAG. *Expected answer:* the checklist is — does it have dependencies between pipelines? does it need retries with a backoff policy? does it need an SLA? does it need to fan out dynamically? does it need to trigger other systems? does it need to pass control data between steps (XCom)? If the answer to all of these is "no", the job belongs in a BigQuery scheduled query or a Cloud Scheduler + Cloud Run job. Applied to `01_hello_world.py`: it has no dependencies, no meaningful retry need, no SLA, no fan-out, no downstream triggers, and no control data — so a scheduled query, a `gcloud` cron job, or a Cloud Run job would be simpler and cheaper. That DAG exists for teaching, which is exactly the right reason for it to exist.

6. **Argue both sides of a Spark-from-Airflow migration.** Your team has a 45-minute Spark job scheduled nightly by Airflow on a persistent Dataproc cluster, with a known issue where a task retry has duplicated rows twice. Write the case for (a) keeping it as is, (b) migrating to BigQuery, and (c) migrating to Dataflow. Then recommend one and justify it. *Expected answer:* (a) is defensible only if the Spark job is genuinely a Spark-shaped problem (iterative ML, complex shuffles) — but the duplication bug must be fixed regardless, by making the write idempotent; (b) is best if the job is really a join-and-aggregate, since BigQuery is cheaper, needs no cluster, and the "retry" becomes a cheap re-run of an idempotent query — but it is a rewrite if the job uses Spark ML or complex custom shuffles; (c) is best if the job has a streaming component or if the team already standardises on Beam, and Dataflow's autoscaling removes the persistent-cluster cost. The recommendation usually lands on (b) for a join-and-aggregate, with the mandatory addition of a partition-scoped idempotent write and a row-count assertion.

---

## 📖 Further Reading

- Airflow: core concepts and architecture — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/index.html
- Airflow: best practices (do not use Airflow as a data processing engine) — https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html
- Apache Beam documentation — https://beam.apache.org/documentation/
- Apache Spark documentation — https://spark.apache.org/docs/latest/
- Google Cloud Dataflow overview — https://cloud.google.com/dataflow/docs/about-dataflow
- Google Cloud Dataproc overview — https://cloud.google.com/dataproc/docs/concepts/overview
- BigQuery scheduled queries — https://cloud.google.com/bigquery/docs/scheduled-queries
- BigQuery pricing (on-demand analysis) — https://cloud.google.com/bigquery/pricing
- Google Cloud Architecture Framework: data engineering practices — https://cloud.google.com/architecture/data-engineering-practices
- Dataflow vs Dataproc vs BigQuery comparison — https://cloud.google.com/dataflow/docs/compare-dataflow-spark
