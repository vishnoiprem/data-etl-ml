# 5.4 — Airflow, Cloud Composer, and Cloud Workflows

> **Section 5 · Processing & Orchestration · Lecture 5.4 · 8:00**

## 🎯 What you will learn

- What an orchestrator does, and why it is not the same thing as a pipeline
- The DAG model, tasks versus workflows, and what a DAG actually buys you
- The logical date, data intervals, and the half-open `[start, end)` convention
- Scheduling, retries, idempotency, and the properties that make retries safe
- XCom, sensors, deferrable operators, and executors
- The 3 a.m. question: the test every orchestrator design must pass
- Cloud Composer: environments, Composer 2 versus Composer 3, creating an environment, writing a DAG, and the UI
- Cloud Workflows: the serverless, event-driven alternative
- The honest verdict: Composer versus Workflows versus cron

---

## 🧠 Concept

### Orchestration is not processing

The most common confusion in data platforms is between a **pipeline** and an **orchestrator**.

A **pipeline** does the work: read this file, transform these rows, write that table. It has a data contract, a schema, and a runtime.

An **orchestrator** decides *when* the work runs and *in what order*. It knows that extraction must precede transformation, that transformation must precede load, that last night's load must succeed before this night's incremental job starts. It retries failures, reports status, and alerts humans.

Confusing them leads to two classic failures:

- **A scheduler that processes.** A cron job that contains the entire transformation logic. Nobody can see what runs when, retries are ad hoc, and a change requires editing a shell script on a server.
- **A processor that schedules.** A "pipeline" that decides on its own what to run next based on what it observed. It works until the ordering is wrong, and then it is a distributed system with no diagram.

The right separation: the orchestrator knows the **shape** of the work; the pipeline knows the **content** of the work.

### The DAG model

Airflow models a workflow as a **directed acyclic graph** of tasks. A cycle is forbidden because a cycle has no correct execution order.

The DAG buys you three things:

1. **Explicit dependencies.** Not "task B runs after A because A happens to finish first", but "B depends on A". This is testable and visible.
2. **Parallelism where it is safe.** Two independent extraction tasks run at the same time because the graph says they are independent.
3. **Failure containment.** When a task fails, the orchestrator can mark its downstream dependents as skipped and leave the unrelated branches running.

The cost is real. A DAG must be **acyclic**, which means "retry A, then A decides B should also run" is not expressible. And a very large DAG becomes hard for a human to read — Airflow's own advice is to keep the graph shallow and use sub-DAGs or dynamic task mapping rather than hundreds of nodes in one file.

### Tasks versus workflows

- A **task** is one unit of work: one operator instance, one node in the DAG. `PythonOperator`, `BashOperator`, `BigQueryOperator`, `GCSToBigQueryOperator`.
- A **workflow** (Airflow 2 terminology; a DAG in Airflow 1) is the collection of tasks and their dependencies. In Airflow 2, a workflow can contain multiple DAGs.

The distinction matters for ownership and versioning. A **DAG file** is a Python module in a DAGs folder. Airflow parses it on a schedule to discover what exists. That means the file is executed as Python at parse time, not only when the task runs — a mistake in module-level code can break the scheduler for every DAG in the folder.

This is why DAG files must have two personalities:

- **Parse time** — should be fast and side-effect free. No database calls, no `requests.get`, no reading a large file. The scheduler parses every file every 30 seconds; expensive module-level work makes the whole scheduler slow.
- **Task runtime** — do the expensive work inside the operator's `execute` method.

The standard pattern is a module-level constant for configuration and a function for anything that touches the network:

```python
BUCKET = "gs://my-bucket"

def fetch_config():
    import requests
    return requests.get("https://config.internal/schema.json").json()

# Good: network call happens inside the task, not at parse time.
```

### The logical date and data intervals

This is the part of Airflow that beginners get wrong and that experienced engineers get bitten by.

Every DAG run has a **logical date** (`execution_date` in Airflow 1, `logical_date` in Airflow 2). It is the timestamp the run *represents*, not the wall-clock time the run started. A run with logical date `2026-01-15T00:00:00` means "the run for the data interval that ended at 2026-01-15".

**Data interval.** The interval of data a run is responsible for. By default it is the interval between the previous logical date and the current one. For a daily DAG, the run with logical date `2026-01-15` covers `[2026-01-14T00:00:00, 2026-01-15T00:00:00)` — the half-open convention.

The half-open convention is not pedantry. It guarantees that adjacent intervals tile the timeline exactly: no gap, no overlap.

```text
run for 2026-01-14:  [2026-01-13, 2026-01-14)
run for 2026-01-15:  [2026-01-14, 2026-01-15)
run for 2026-01-16:  [2026-01-15, 2026-01-16)
                   ^ shared boundary belongs only to the later run
```

In Airflow 2, the helpers are `{{ data_interval_start }}` and `{{ data_interval_end }}`. The older `{{ ds }}` gives the logical date as `YYYY-MM-DD`, and `{{ ds_nodash }}` gives `YYYYMMDD`.

**The practical consequence: never derive a partition from "now".** If your task computes `date.today()` or `datetime.now()`, then a backfill for March produces data labelled "today", and a retry at 2 a.m. produces data in a different partition than the original run. Derive the partition from `data_interval_start` (or `logical_date`) and every run — original, retry, or backfill — writes to the same place.

The course project enforces exactly this: `partition_for_date(logical_date)` takes a logical date string and returns a partition decorator such as `20260115`.

### Scheduling

Airflow has three schedule concepts:

- **Catchup.** By default a new DAG with `start_date` in the past backfills every interval since `start_date`. For a DAG that takes two hours per run, a year of history means thousands of queued runs and a large bill.
- **Max active runs.** How many runs of the same DAG may run at once. Setting it to 1 serialises runs and prevents overlapping writes.
- **Schedule interval.** A cron expression, a timedelta, or a timetable object.

The modern recommendation is `catchup=False` with an explicit backfill command. A new deployment should not silently execute a year of history.

For a daily warehouse job at 02:00, the schedule is typically `0 2 * * *`. But the *logical date* of that run is the previous day, so the DAG must use `data_interval_start` to find the partition.

### Retries and idempotency

Retries are the orchestrator's promise that transient failures will not require a human. But a retry is only safe if the task is **idempotent**: running it twice leaves the same state as running it once.

This is not optional. Retries are triggered by timeouts, worker crashes, and network failures — precisely the conditions where a task may have partially completed. If the task loaded 90 percent of a partition and then lost its connection, the retry must not duplicate the 90 percent.

The four properties that make a task safely retryable:

1. **Deterministic target.** The destination is derived from the logical date, not from the clock.
2. **Replace, not append.** Write to a staging location and swap, or use `MERGE`/`DELETE`+`INSERT` scoped to the partition, rather than blind appends.
3. **Deterministic identity.** Each row has a key derived from the data (`dedup_key(event_id, partition)` in the course project), so a duplicate load is detectable.
4. **Idempotent sink.** BigQuery's `MERGE` on a unique key, or a `WRITE_TRUNCATE` to a date partition, both satisfy this.

If you cannot make the task idempotent, disable retries and instead build a dead-letter or reconciliation path. That is a legitimate choice — but make it consciously.

### XCom

**XCom** is Airflow's mechanism for passing small values between tasks. A task returns a value; it is stored in the metadata database and made available to downstream tasks.

```python
from airflow.decorators import task

@task
def extract():
    return {"rows": 1234, "partition": "20260115"}

@task
def load(meta):
    print(f"loading {meta['rows']} rows for {meta['partition']}")
```

Rules that keep XCom from becoming a performance problem:

- **XCom is for metadata, not data.** Row counts, partition names, a schema version, a run identifier. Never a DataFrame, a list of a million records, or a file's contents.
- **Large values go to object storage.** Write to Cloud Storage, return the URI.
- **XCom lives in the metadata database.** Every task's return value is a row there. Backfills create backfills.
- **XCom has a size limit.** The default is around 48 KB per value; exceed it and you get a database error that is famously hard to interpret.

### Sensors

A **sensor** is an operator that waits for a condition rather than doing work:

- `GCSObjectExistenceSensor` — wait for a file to appear.
- `BigQueryTableExistenceSensor` — wait for a table.
- `PubSubMessageSensor` — wait for a message on a topic.

A sensor occupies a worker slot while it waits, which is why Airflow added **deferrable operators**.

### Deferrable operators

A **deferrable operator** releases its worker slot while it waits and resumes when the condition is met. It requires a trigger and a triggerer process.

The consequence is architectural: **deferrable operators only work on Airflow 2.2 or later, and they require the `airflow.triggerer` component**. In Cloud Composer this is enabled in the environment configuration (`enableTriggerer`).

Use deferrable operators for waits that are long or unpredictable — waiting for a Dataflow job that runs for an hour, or waiting for a file that arrives when it arrives. Do not use them for waits of a few seconds.

### Executors

The **executor** decides where tasks run:

| Executor | Behaviour | Use for |
|---|---|---|
| `LocalExecutor` | Runs tasks as subprocesses on the worker | The default; most production workloads |
| `SequentialExecutor` | One task at a time | Debugging only |
| `KubernetesExecutor` | Each task is a Kubernetes pod | Isolation, heterogeneous dependencies, high concurrency |
| `CeleryExecutor` | Distributed queue of workers | You manage the queue yourself |

In Cloud Composer, the default is `LocalExecutor` on the worker nodes, which means a task runs in a subprocess on a worker rather than in the scheduler process. The KubernetesExecutor is also available if you want per-task isolation.

The executors are also where the **resource model** comes from. `LocalExecutor` tasks share the worker's CPU and memory. If a task needs 16 GB, the worker must have it; there is no per-task memory limit as in Kubernetes. This is why Composer environments come in sizes and why a memory-hungry task can cause the whole worker to be evicted.

### The 3 a.m. question

Every orchestration design should survive one scenario: it is 3 a.m., the alert fired, and you are trying to work out what happened.

The design questions are:

1. **Can I see the whole state?** The Airflow UI shows the DAG graph with each task coloured by state, the run history, the task logs, and the XCom values. Cloud Workflows shows the execution history with per-step results. A cron script shows you a log file.
2. **Can I answer "what ran, what did it touch, and what will it do next"?** Airflow's answer includes the logical date, the data interval, and the task instance state. Without a logical date, a retry has no defined target.
3. **Can I safely rerun the failed part without rerunning everything?** Airflow's `clear` command resets a task instance and its downstream so it can be re-run. Workflows has no equivalent of a partial re-run; you re-execute the workflow.
4. **Does the failure message tell me what to do?** A generic "Task exited with return code 1" tells me nothing. A task that fails because the BigQuery table does not exist, naming the table, is actionable.

This is the test. A pipeline that works and cannot be diagnosed at 3 a.m. is not finished.

### Cloud Composer: Composer 2 versus Composer 3

**Cloud Composer** is managed Apache Airflow on GCP. It is Airflow with Google-managed infrastructure: the scheduler, the web server, the workers, the database, and the DAG distribution mechanism.

The major version distinction:

| Aspect | Composer 2 | Composer 3 |
|---|---|---|
| Airflow version | Airflow 2.x | Airflow 2.x with newer features, plus APIs that were previously Cloud Composer-specific |
| DAG distribution | Git sync, or upload | Git sync, or upload |
| Airflow API | Airflow's own REST API, externally reachable | Airflow APIs are **private**, only accessible from inside the environment |
| Managed services | Airflow itself managed | Airflow plus integrated GCP service connectivity, Private Service Connect |
| Image version pinning | `composer-2.x.x-airflow-2.x.y` | `composer-3.x.x-airflow-2.x.y` |

**The important operational difference:** in Composer 3, the Airflow REST API is not exposed outside the environment by default. If your platform depends on calling Airflow's API from Cloud Run or from a laptop, Composer 3 requires a deliberate networking design — a VPC peering with Private Service Connect, or an internal load balancer.

My default recommendation: **Composer 3** for new environments, because it has the newer Airflow features and better integration with private networking. Choose Composer 2 if you have a hard requirement to reach the Airflow API from outside the environment.

### Creating an environment

```bash
gcloud composer environments create analytics-pipelines \
  --project=my-project \
  --location=us-central1 \
  --environment-size=ENVIRONMENT_SIZE_SMALL \
  --image-version=composer-3.0.0-airflow-2.9.3 \
  --python-version=3.11 \
  --airflow-config-overrides \
    core-dags_folder=/home/google/cloud_composer/dags \
    core-logs_folder=/home/google/cloud_composer/logs \
    core-max_active_tasks_per_dag=16 \
    core-parallelism=32 \
    scheduler-catchup_by_default=False \
    scheduler-max_dagruns_to_create_per_loop=20 \
    webserver-dag_default_view=graph \
    core-max_active_runs_per_dag=1
```

The key configuration choices:

- **`--environment-size`** — `ENVIRONMENT_SIZE_SMALL` (1 worker), `MEDIUM` (3), `LARGE` (6), `XLARGE` (9). Each additional worker adds cost and is needed only for parallelism. The Airflow *database* and *scheduler* are included in the environment cost, so a small environment is the right starting point.
- **`--image-version`** — pin it. An unpinned environment can be upgraded by Google, and an Airflow minor upgrade can break a deprecated operator import.
- **`core-parallelism`** — the maximum number of tasks the scheduler will run at once. It must not exceed what the workers can execute.
- **`scheduler-catchup_by_default=False`** — the modern default. Do not backfill a year of history because you enabled a DAG.
- **`core-max_active_runs_per_dag=1`** — prevents overlapping runs of the same DAG, which protects against two runs writing the same partition.

### Writing a DAG

```python
from __future__ import annotations

import datetime as dt

from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.google.cloud.sensors.bigquery import BigQueryTableExistenceSensor
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator

PROJECT_ID = "my-project"
DATASET = "analytics"
TABLE = "events"
BUCKET = "gs://my-bucket"

with DAG(
    dag_id="daily_events_load",
    description="Load raw events into the partitioned events table",
    start_date=dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc),
    schedule="0 2 * * *",
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 3,
        "retry_delay": dt.timedelta(minutes=5),
        "retry_exponential_backoff": True,
        "max_retry_delay": dt.timedelta(hours=1),
    },
    tags=["events", "bigquery"],
) as dag:
    load = GCSToBigQueryOperator(
        task_id="load_events",
        bucket=BUCKET,
        source_objects=["events/*.csv"],
        destination_project_dataset_table=f"{PROJECT_ID}.{DATASET}.{TABLE}",
        write_disposition="WRITE_APPEND",
        create_disposition="CREATE_IF_NEEDED",
        schema_fields=[
            {"name": "event_id", "type": "STRING", "mode": "REQUIRED"},
            {"name": "user_id", "type": "STRING", "mode": "REQUIRED"},
            {"name": "event_ts", "type": "TIMESTAMP", "mode": "REQUIRED"},
            {"name": "region", "type": "STRING", "mode": "REQUIRED"},
            {"name": "amount_eur", "type": "NUMERIC", "mode": "NULLABLE"},
        ],
    )

    verify = BigQueryTableExistenceOperator(
        task_id="verify_table",
        project_id=PROJECT_ID,
        dataset_id=DATASET,
        table_id=TABLE,
        deferrable=True,
        poke_interval=30,
    )

    load >> verify
```

Note the deliberate choices:

- `start_date` is timezone-aware. A naive datetime is interpreted as UTC by default, but being explicit avoids the class of bug where a DST change shifts your schedule.
- `max_active_runs=1` prevents overlapping runs.
- `catchup=False`.
- The retry policy uses exponential backoff, so a transient outage does not produce five immediate retries.
- `verify` is **deferrable**, so it does not hold a worker slot while waiting.
- `write_disposition="WRITE_APPEND"` is safe here only because the source objects are immutable and uniquely named. If the same file can be re-delivered, use `WRITE_TRUNCATE` on a date partition or a `MERGE`.

### The Composer UI

The Composer UI has four tabs that matter:

- **DAGs** — the list, with the last run's state and the schedule.
- **Graph** — the task graph for a selected run, coloured by state. This is the first thing to open during an incident.
- **Calendar** — a heatmap of run history by day, which makes gaps and mass failures obvious at a glance.
- **Browse / Admin** — connections, pools, variables, and XComs.

The `Admin > Pools` view is the one people forget. A pool caps concurrency for a group of tasks. If your DAG submits Dataflow jobs and each one occupies a slot for hours, put those tasks in a pool with a low `slots` value so they cannot starve the DAG's other tasks. This is the orchestrator's resource-control mechanism and it is the Airflow equivalent of a YARN queue.

### Cloud Workflows

**Cloud Workflows** is a serverless, event-driven orchestration service. You define a workflow in YAML as a sequence of steps, each of which calls an API — a Dataflow job, a BigQuery query, a Cloud Run service, a Cloud Function.

```yaml
main:
  params: [bucket, project, dataset]
  steps:
    - start:
        call: dataflow.jobs.launch
        args:
          projectId: ${project}
          region: us-central1
          gcsPath: ${bucket}/jobs/events.py
          parameters: {}
        result: launched

    - wait:
        call: dataflow.jobs.get
        args:
          projectId: ${project}
          region: us-central1
          jobId: ${launched.id}
        result: job
        loop:
          condition: ${result.state != "JOB_STATE_DONE"}
          backoff:
            initial: 5
            max: 60
          do:
            - wait:
                call: dataflow.jobs.get
                args:
                  projectId: ${project}
                  region: us-central1
                  jobId: ${launched.id}
                result: result

    - check:
        call: dataflow.jobs.get
        args:
          projectId: ${project}
          region: us-central1
          jobId: ${launched.id}
        result: final

    - fail_if:
        condition: ${final.state != "JOB_STATE_DONE" || final.error != null}
        raise: ${final.error}
```

The differences from Airflow are structural:

| Aspect | Airflow / Composer | Cloud Workflows |
|---|---|---|
| Unit | Task with retries, XComs, sensors | Step in a workflow |
| Trigger | Cron, or external API call | Eventarc event, HTTP call, schedule via Cloud Scheduler, or a queue |
| Retry | Declarative per task, with backoff | Declarative per step |
| State | Metadata database, XComs | Step results stored by the service |
| Dynamic branching | Python code at runtime | Limited; conditional steps exist, but no arbitrary runtime logic |
| Cost | Continuous environment cost | Per operation, scales to zero |
| Long waits | Sensors, deferrable operators | `call: sleep` or a poll loop with backoff |
| Partial re-run | `airflow tasks clear` | Not supported; re-execute the workflow |

Workflows is genuinely serverless: you pay per operation, there is no environment to keep alive, and it starts from nothing. It is triggered by an event — a Pub/Sub message, a Cloud Storage object, a Cloud Run request, or a Cloud Scheduler schedule.

**Where Workflows wins:**

- The orchestration is a short, linear sequence of API calls with no complex branching.
- The orchestration should start from an event, not from a clock.
- You want zero idle cost and no environment to patch.
- The steps are service API calls — "launch this Dataflow job and wait for it", "run this BigQuery query", "call this endpoint".

**Where Workflows loses:**

- Complex conditional logic, dynamic task generation, or per-record branching.
- Rich fan-out with per-item parallelism — Airflow's dynamic task mapping has no equivalent.
- A large DAG with many independent tasks — Workflows calls are serial unless you use `parallel` steps, and each call has latency.
- Backfill semantics. There is no logical date, no data interval, no catchup.

### The honest verdict: Composer versus Workflows versus cron

**Use a cron job when** there is one command, it runs less often than hourly, it has no dependencies, and failure handling can be "the next run will fix it". A Cloud Scheduler job triggering a Cloud Run job or a Cloud Run Job is a legitimate, cheap, low-complexity answer. Do not build an orchestrator for a three-step pipeline.

**Use Composer when** you have multiple tasks with dependencies, retries, backfills, schedules, monitoring, and multiple owners. The learning cost is real — Airflow has a large API, a large operational surface, and a specific set of footguns — but if you have ten pipelines with cross-dependencies, Composer is dramatically cheaper than the alternative: a pile of cron jobs and shell scripts that only one person understands.

**Use Workflows when** the orchestration is event-driven rather than clock-driven, the steps are API calls, the sequence is short, and you want no environment to operate. The classic example: "when a Pub/Sub message arrives, start a Dataflow streaming job that processes it and write the result". The classic anti-example: "a daily DAG with forty interdependent tasks and a backfill".

**The decision rule I would give a team:**

1. One task, no dependencies → Cloud Scheduler plus Cloud Run Job.
2. Event-triggered, short, API-call sequence → Cloud Workflows.
3. Anything with a daily schedule, multiple dependent tasks, backfills, or many operators → Cloud Composer.
4. Anything requiring arbitrary Python branching at runtime → Cloud Composer (Airflow's Python operators are exactly for that), and accept the operational cost.

One warning that applies to all three: **the orchestrator does not make your tasks idempotent**. An orchestrator that retries a non-idempotent task is a duplication machine. Fix the tasks.

---

## 🛠️ Hands-On

### Exercise 1: build the data interval from the logical date

This is the single most important habit in Airflow. The course project provides `partition_for_date` for exactly this.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import partition_for_date

logical_dates = [
    "2026-01-14T00:00:00+00:00",
    "2026-01-15T00:00:00+00:00",
    "2026-01-16T00:00:00+00:00",
]

for logical_date in logical_dates:
    print(logical_date, "->", partition_for_date(logical_date))
```

Output:

```text
2026-01-14T00:00:00+00:00 -> 20260114
2026-01-15T00:00:00+00:00 -> 20260115
2026-01-16T00:00:00+00:00 -> 20260116
```

Compare with `datetime.now()`: the logical date is stable across the original run, every retry, and every backfill. The partition is therefore the same in all three cases.

### Exercise 2: prove the half-open interval tiles without gaps or overlaps

```python
import sys
sys.path.insert(0, "project/core")

from datetime import datetime, timedelta, timezone

from pipeline_logic import partition_for_date

start = datetime(2026, 1, 14, tzinfo=timezone.utc)
current = start

for index in range(3):
    logical_date = current
    nxt = current + timedelta(days=1)
    print(f"run {index}: [{current.isoformat()}, {nxt.isoformat()}) "
          f"partition={partition_for_date(logical_date.isoformat())}")
    current = nxt

print()
print("boundary belongs to exactly one interval:",
      partition_for_date("2026-01-15T00:00:00+00:00"))
```

Output:

```text
run 0: [2026-01-14T00:00:00+00:00, 2026-01-15T00:00:00+00:00) partition=20260114
run 1: [2026-01-15T00:00:00+00:00, 2026-01-16T00:00:00+00:00) partition=20260115
run 2: [2026-01-16T00:00:00+00:00, 2026-01-17T00:00:00+00:00) partition=20260116

boundary belongs to exactly one interval: 20260115
```

Each partition covers exactly one day, and no event is counted twice at a boundary.

### Exercise 3: write an idempotent load and prove replay safety

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import (
    ingest_events,
    partition_for_date,
    filter_rows_for_partition,
    deduplicate,
    dedup_key,
)

with open("sample_data/events.csv", encoding="utf-8") as handle:
    accepted, _ = ingest_events(handle.read().splitlines())

logical_date = "2026-01-15"
partition = partition_for_date(logical_date)
rows = filter_rows_for_partition(accepted, partition)

print("logical date:   ", logical_date)
print("partition:      ", partition)
print("rows selected:  ", len(rows))

# The original run.
first = deduplicate(rows, partition=partition)
print("after first run:", len(first))

# The retry: the same rows arrive again.
retry = deduplicate(rows + rows[:200], partition=partition)
print("after retry:    ", len(retry))

print("same rows:", first == retry)
print("sample key:", dedup_key(first[0]["event_id"], partition))
```

Output:

```text
logical date:    2026-01-15
partition:       20260115
rows selected:   4800
after first run: 4800
after retry:     4800
same rows: True
sample key: 20260115:e00000000
```

The retry produced exactly the same rows because the identity is derived from the partition and the business key, not from arrival time. This is what makes a Composer task safely retryable.

### Exercise 4: model a task DAG and find the parallel branches

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, aggregate_events

with open("sample_data/events.csv", encoding="utf-8") as handle:
    accepted, rejected = ingest_events(handle.read().splitlines())

# A plausible daily DAG:
#
#   extract ──┬──> validate ──> aggregate ──> publish
#              └──> reference ──┘
#
# The two branches are independent, so they can run concurrently.
# Everything after validate is a single chain.

tasks = {
    "extract": [],
    "reference": [],
    "validate": ["extract"],
    "aggregate": ["validate", "reference"],
    "publish": ["aggregate"],
}

for task, dependencies in tasks.items():
    print(f"{task:10s} depends on: {dependencies if dependencies else '(none)'}")

indegree = {task: len(deps) for task, deps in tasks.items()}
print()
print("tasks that can start immediately:",
      [task for task, count in indegree.items() if count == 0])
print("tasks on the critical chain: aggregate -> publish")
```

Output:

```text
extract    depends on: (none)
reference  depends on: (none)
validate   depends on: ['extract']
aggregate  depends on: ['validate', 'reference']
publish    depends on: ['aggregate']

tasks that can start immediately: ['extract', 'reference']
tasks on the critical chain: aggregate -> publish
```

The critical path is `extract → validate → aggregate → publish`. Optimising `reference` will not make the pipeline faster. This is the first thing to compute when a DAG feels slow.

### Exercise 5: the 3 a.m. diagnostic for the course pipeline

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import (
    ingest_events,
    reject_counts,
    render_summary_csv,
    aggregate_events,
)

with open("sample_data/events.csv", encoding="utf-8") as handle:
    accepted, rejected = ingest_events(handle.read().splitlines())

print("WHAT RAN")
print(f"  logical date: 2026-01-15")
print(f"  partition:    20260115")
print(f"  accepted:     {len(accepted)}")
print(f"  rejected:     {len(rejected)}")
print()
print("WHAT IT TOUCHED")
print(render_summary_csv(aggregate_events(accepted)))
print("WHAT TO DO NEXT")
if rejected:
    for reason, count in sorted(reject_counts(rejected).items()):
        print(f"  investigate {reason}: {count}")
else:
    print("  no action; the run is clean and safe to publish")
```

The output is the answer to the 3 a.m. question without needing the scheduler's UI. That is what good observability means: the state of the world is derivable from the data plus the logical date.

### Exercise 6: cost an orchestrator

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import estimate, monthly_runway

# A one-node Composer environment, always on.
composer = estimate("composer", environment_nodes=1, monthly=True)
print(composer)
print()

# The same environment for a month of runtime.
print(monthly_runway("composer", environment_nodes=1))
```

The Composer environment bills whether or not a DAG is running. An environment that runs one DAG once a day is over-provisioned; if you genuinely only need one or two daily DAGs, Cloud Scheduler plus Cloud Run Jobs is cheaper. If you have a dozen DAGs with cross-dependencies, the environment is a bargain.

---

## 🛠️ Common Errors and Fixes

### 1. `DagNotFound` or `DagCodeException`

```text
airflow.exceptions.DagNotFound: Dag: 'daily_events_load' not found
```

**Cause.** The DAG file is not in the DAGs folder, the environment has not picked it up yet (parsing happens every 30 seconds), the file has a syntax error, or the DAG failed to import because of a module-level exception.

**Fix.** Check the import errors first — Airflow shows them in the UI under **Browse > DAG Import Errors**, and in the Cloud Logging console under the `airflow-task-log` and scheduler logs. Then verify the file is in `core-dags_folder` and that `dag_id` is unique. A common cause of an invisible DAG is that an import at module level requires a package that is not installed in the environment. Test the import locally:

```bash
python3 -c "import my_dag_file"
```

If it fails locally, it will fail in Composer.

### 2. `Task failed with UnmappableError: [Errno 2] No such file or directory`

```text
airflow.exceptions.UnmappableError: [Errno 2] No such file or directory:
'/tmp/airflow_task_tmp_random_string'
```

**Cause.** The worker cannot write to its temporary directory. This happens when the worker's disk is full — a common result of a task writing a large file to `/tmp` — or when the environment has been resized in a way that left a stale mount.

**Fix.** Free disk on the worker, and stop writing unbounded data to local disk. Write to Cloud Storage and pass the URI in the XCom. Check the environment's disk usage in Cloud Monitoring, and reduce the environment size if the DAG is not designed for parallel local disk use.

### 3. `apache-airflow.exceptions.AirflowTaskTimeout`

```text
airflow.exceptions.AirflowTaskTimeout: Task timed out after 0:05:00
```

**Cause.** The task exceeded its `execution_timeout`. This is Airflow's protection against a task that hangs forever — it is not a bug in Airflow, it is a bug in the task.

**Fix.** Identify what is hanging. A common pattern is a `BashOperator` running a command that waits for input or polls an external service without a timeout. Raise `execution_timeout` if the task legitimately needs longer, but first fix the underlying wait — usually by replacing a poll loop with a deferrable operator or a sensor.

### 4. `dag_id ... already exists` or two DAGs with the same id

```text
airflow.exceptions.DuplicateDagId: The DAG with id 'daily_events_load' already exists
```

**Cause.** Two files in the DAGs folder define the same `dag_id` — often a copy left behind during development, or a DAG file imported by another module.

**Fix.** Give every DAG a unique id, derived from its file path if in doubt. Delete the stale file. This error appears at import time and causes *both* DAGs to fail to load, so a duplicate id can silently disable an entire pipeline.

### 5. `BackfillJob is not running` or a backfill that processes the wrong partition

```text
BackfillJob failed: Cannot read property 'data_interval_start' of undefined
```

or, more dangerously, a backfill that completes successfully with wrong data:

```text
# The DAG ran for 2026-01-01 but wrote the partition for today's date.
```

**Cause.** The task derived its target from `datetime.now()` or `{{ ds }}` instead of `{{ data_interval_start }}`. `ds` is the *logical date*, which is close but not identical to the interval start for non-midnight schedules. `now()` is simply wrong.

**Fix.** Use `{{ data_interval_start }}` (and `{{ data_interval_end }}`) for the interval, and `{{ logical_date }}` for the run identity. In a `BashOperator`, render them explicitly:

```python
bash_command=f"""
  python jobs/load.py \
    --start-date {{{{ data_interval_start }}}} \
    --end-date {{{{ data_interval_end }}}} \
    --partition {{{{ ds_nodash }}}}
"""
```

Then verify by running the DAG for a historical date and confirming the partition matches the logical date.

### 6. Composer environment creation fails or times out

```text
ERROR: (gcloud.composer.environments.create) Operation timed out after 10m.
The environment may still be being created; check its state with
gcloud composer environments describe.
```

**Cause.** The environment is still provisioning. Composer creates the database, scheduler, web server, and workers, which takes several minutes, and the `gcloud` command's default timeout can expire first.

**Fix.** Do not retry the create immediately — a second create may conflict with the first. Describe the environment until it reaches `RUNNING`:

```bash
gcloud composer environments describe analytics-pipelines \
  --location=us-central1 \
  --format="value(state)"
```

If it reaches `FAILED`, the error message in `gcloud composer environments describe` names the cause — most often a quota on the worker machine type or an invalid image version.

---

## 💡 Production Notes

- **Pin the Composer image version.** Do not use a floating tag. Airflow minor upgrades change operator signatures and can break an import overnight.
- **Use pools to cap concurrency.** A pool with `slots=2` for long-running Dataflow launch tasks stops them from starving everything else in the environment.
- **Keep `catchup=False` and backfill explicitly.** An accidental catchup on a DAG with a year of start date is a very large surprise bill.
- **Set `max_active_runs=1` for DAGs that write partitions.** It is the cheapest protection against two runs writing the same partition concurrently.
- **Make every task idempotent before enabling retries.** Derive the target from the logical date; use `MERGE` or partition-scoped `WRITE_TRUNCATE`; key rows on data-derived identifiers.
- **Keep XCom payloads small.** Counts, URIs, partition names, and run identifiers. Anything larger goes to Cloud Storage.
- **Use deferrable operators for long waits** and enable the triggerer in the environment. A sensor that waits six hours while holding a worker slot is a capacity bug.
- **Grant the Composer service account the narrowest roles.** It needs to create and update the resources your DAGs manage — not `roles/editor`.
- **Keep DAG files side-effect free at module level.** The scheduler parses every file every 30 seconds; a network call at import time is a scheduler outage.
- **Do not put a shell script in `BashOperator` and call it orchestration.** If the script has branching, retries, or dependencies, express it as tasks.

---

## 🔑 Key Takeaways

- An orchestrator decides when work runs and in what order; a pipeline decides what the work does. Mixing the two produces systems nobody can operate.
- Airflow's DAG model gives explicit dependencies, safe parallelism, and failure containment. Its cost is that DAG files execute at parse time and cycles are impossible.
- The logical date is the timestamp a run represents, and the data interval is the half-open `[start, end)` slice of data it owns. Deriving a partition from the clock breaks retries and backfills; deriving it from `data_interval_start` fixes both.
- Retries are only safe when tasks are idempotent. Deterministic target, replace-not-append, deterministic row identity, idempotent sink.
- XCom carries metadata, not data. Sensors wait; deferrable operators wait without occupying a worker slot. Executors decide where tasks run.
- The 3 a.m. question is the design test: can you see the whole state, identify what ran and what it touched, re-run only the failed part, and act on a meaningful error?
- Composer 3 is the right default for new environments; Composer 2 remains relevant when you must reach the Airflow REST API from outside the environment.
- Cloud Workflows is serverless and event-driven with per-operation pricing; it is excellent for short API-call sequences and poor for complex branching, rich fan-out, and backfills.
- The decision rule: one task → Cloud Scheduler plus Cloud Run Job; event-driven API sequence → Workflows; anything with schedules, dependencies, backfills, or many operators → Composer.

---

## 📚 Practice Exercises

1. **Write the DAG.** Implement a Composer DAG for the course pipeline with four tasks: `extract`, `validate`, `aggregate`, and `publish`. Set `catchup=False`, `max_active_runs=1`, an exponential-backoff retry policy, and derive the partition from `{{ data_interval_start }}`. Explain what each setting prevents.
2. **Prove interval correctness.** Using `partition_for_date`, show that three consecutive daily logical dates produce three distinct, adjacent partitions and that the boundary timestamp belongs to exactly one of them. Explain what breaks if the interval were closed on both ends.
3. **Demonstrate retry safety.** Load `sample_data/events.csv` twice into the same partition using `filter_rows_for_partition` and `deduplicate`, then compare against a variant keyed by an arrival timestamp. Explain the duplicate-row failure the timestamp key causes.
4. **Design the backfill.** Write the command sequence to backfill the DAG for `2026-01-01` to `2026-01-07`, one logical date at a time. Then explain why `airflow dags backfill` with a range can be dangerous for a DAG with non-idempotent tasks, and how you would verify the resulting partitions.
5. **Find the critical path.** Extend the DAG model from Exercise 4 to eight tasks with three parallel branches. Compute the longest dependency chain and identify which branch is worth optimising. Explain how you would answer the same question in the Composer UI.
6. **Add a pool.** Design an Airflow pool configuration for a DAG that launches Dataflow jobs which occupy slots for hours, alongside fast BigQuery tasks. Give the pool names, slot counts, and which tasks go in each. Explain the failure mode you are preventing.
7. **Compare the three orchestrators.** For each of these scenarios, choose Composer, Workflows, or Cloud Scheduler plus Cloud Run Job and justify it: (a) a nightly five-task DAG with backfill, (b) a Pub/Sub-triggered workflow that starts a Dataflow job and waits for it, (c) a daily `gsutil` sync of one bucket to another.
8. **Cost the orchestrator.** Using `cost_model.estimate("composer", environment_nodes=1, monthly=True)` and `monthly_runway`, price a one-node environment over a month. Then argue, with the same numbers, when a single daily DAG justifies Composer and when it does not.

---

## 📖 Further Reading

- [Cloud Composer Documentation](https://cloud.google.com/composer/docs)
- [Cloud Composer: Environment Versioning](https://cloud.google.com/composer/docs/composer-2/environment-versioning)
- [Cloud Composer: Airflow Version Upgrades](https://cloud.google.com/composer/docs/composer-2/airflow-version-upgrades)
- [Apache Airflow: Core Concepts](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html)
- [Apache Airflow: Data Interval](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dag-run.html)
- [Cloud Workflows Documentation](https://cloud.google.com/workflows/docs)
- [Cloud Scheduler Documentation](https://cloud.google.com/scheduler/docs)
