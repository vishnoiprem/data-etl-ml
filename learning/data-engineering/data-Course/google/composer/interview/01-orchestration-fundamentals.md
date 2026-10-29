# Module 1 — Orchestration Fundamentals & Model

> **14 questions · Module 1 · Why orchestration exists, the DAG model, Airflow vs Spark/Beam, architecture, scheduler, executors, the 3am question**

---

## Why orchestration exists

### 1. Your team's data platform has six cron jobs and a dashboard that is wrong by 11%. What did orchestration actually fix, and what did it not?

**Orchestration fixed the coordination failure, not the transformation.** The failure was never "the script crashed" — it was that *the pipeline crashed and half the system kept going*. Three downstream scripts started anyway, produced partial results, and nobody noticed until the morning dashboard showed a number that was off by eleven percent.

The mechanism is that Airflow makes the dependency graph **first-class and inspectable**. Before Airflow, the dependency "the fraud score needs cleaned orders *and* the customer segment table" lived in three separate `crontab` files and in someone's head. After Airflow it is an edge in a graph: `validate_orders >> score_fraud`, and `customer_segments` also feeds `score_fraud`. The failure semantics follow from the graph. If `validate_orders` fails, `score_fraud` never runs — it is marked `upstream_failed`, not `failed`, and the DAG run ends. The half-run is impossible by construction.

What it did **not** fix is that Airflow does not transform data. Airflow is the **control plane**; the pipeline is the **data plane**. If the eleven percent came from a wrong currency conversion rate inside the transformation, Airflow would not have helped at all. The bug in this story was a *logic* bug, and orchestration cannot see logic bugs.

The diagnostic that separates the two: if the dashboard number is wrong but every task is green, orchestration did its job and your transformation is wrong. If a task is red and downstream tasks are grey, orchestration is telling you the truth and the pipeline is correctly stopped.

**Numbers:** the course's pipeline is 5,000 raw order lines in `sample_data/orders.csv` (5,001 lines including the header), of which **1,245** pass validation and **0** are rejected. Aggregated by region: AMER 318 / 113592.19 EUR, APAC 285 / 108194.92, EMEA 322 / 118423.22, LATAM 320 / 110646.18. These are the numbers every chapter in the course asserts against, and they are the numbers you should have memorised for this course.

### 2. What is the difference between a pipeline and an orchestrator, and what goes wrong if you write a transformation inside a DAG file?

**A pipeline transforms data; an orchestrator decides when and in what order.** Airflow is the orchestrator. It does not transform anything itself — it runs your transformations, in the right order, on the right date, and it knows what happened.

Writing a transformation inside a DAG file breaks three things at once:

1. **Testability.** Importing a DAG file requires Airflow installed (~500 MB of dependencies), a metadata database, and credentials. A validation rule living inside a `PythonOperator` callable cannot be unit-tested in CI without the full Airflow stack.
2. **Parse-time execution.** The DAG processor imports your file on every parse cycle (Composer re-parses every 1–3 minutes). Any top-level code — a `print()`, an API call, a database connection — runs on the scheduler every cycle.
3. **Reusability.** The same logic called from a task, from a sensor, or from a test must exist in three places unless it lives in one importable module.

The course's architecture is exactly the fix, and it is the shape you want in a real code base:

```text
project/core/pipeline_logic.py   ← the pipeline (pure, testable, no Airflow import)
project/dags/03_etl_bigquery.py  ← the orchestration (imports Airflow, declares edges)
```

`pipeline_logic.py` imports only `csv`, `io`, `json`, `math`, `os`, `re`, `datetime`, `typing` — no `airflow`. `pytest` runs it in well under a second. And the orchestration is thin enough to read in five seconds and understand the shape of the workflow.

**The failure story:** a team had a 200-line `validate_and_load()` function inside a `PythonOperator` callable. When the source schema changed, three validation rules needed updating. The function was also called from a `BashOperator` via `python -c` in two other DAGs, which had their own *copies*. The three copies diverged. The nightly DAG accepted 1,245 rows; the finance DAG accepted 1,311 — a 66-row divergence between two copies of "the same" rule. The fix was to extract the rules into `core/validation.py`, which both DAGs import.

### 3. Why is "directed acyclic" a feature rather than a limitation, and what do you do when you need a loop?

**Acyclic means the graph always has a topological order, so it is always schedulable.** A cycle would mean "A waits for B, B waits for A" — there is no well-defined first task, so no execution order exists. Airflow rejects cycles at parse time and your DAG simply does not appear in the UI.

The subtle payoff of acyclicity is that **a DAG can be analysed as a whole**. You can ask "what are the upstream dependencies of `analytics.orders_enriched`?", "which tasks are on the critical path?", "if `validate_orders` fails, what else is affected?". With cycles, none of those questions has a well-defined answer.

The cost is that looping must be expressed as **repetition, not as a graph edge**. "Process each of the 500 customer files" is 500 runs of the same DAG, or one DAG with **dynamic task mapping** (`.expand()`, Airflow 2.3+). It is *not* a task that points at itself. That is a deliberate design decision and it is the right one: it turns "loop until done" into a set of independently retriable, independently observable, independently idempotent units.

The course's `local_runner.py` implements the same guarantee in miniature — `DAG._validate()` runs a DFS colouring and raises:

```text
ValueError: cycle detected in DAG 'demo_failure': a -> b -> a
```

**The failure story:** a team expressed "retry each failing region until it succeeds" by having a task re-trigger its own DAG via `TriggerDagRunOperator`. On the third iteration the DAG produced 300 rows instead of 1,245, because each re-trigger appended. The graph had no cycle — the cycle was in the *state* across runs, which the DAG model cannot see. The fix was dynamic task mapping with one mapped task instance per region, each idempotent.

### 4. What is the difference between a task and a workflow, and why does the distinction decide who owns retry logic?

**A task is one node with its own state and its own retry policy. A workflow is the whole DAG, run once per logical date.** Airflow has two nested state machines:

```text
DAG run  (one per logical date)
  ├── Task instance: read_orders        → success
  ├── Task instance: transform_orders   → success
  ├── Task instance: aggregate          → success
  └── Task instance: write_summary      → failed
        └── retries: 1 of 2 remaining
```

The DAG run's state is *derived* from its task instances' states. The scheduler asks a different question at each level:

- **At the task level:** "Are all my dependencies successful, and has the executor given me a worker?" → run me.
- **At the DAG level:** "Have all my task instances reached a terminal state?" → the DAG run is done.

The distinction decides who owns retry logic because **retries are a task-level property**. `default_args={"retries": 2, "retry_delay": timedelta(minutes=5)}` applies to every task in the DAG, and any individual task can override it — the course's `load_to_bigquery` task uses `retries=3, retry_delay=timedelta(minutes=10)` while the DAG default is 2/5min.

That granularity matters because different tasks have different failure semantics. A `BigQueryInsertJobOperator` hitting a transient 503 should retry 3 times. A task that sends a Slack notification should probably *not* retry at all, because the first attempt probably succeeded and the error was in the response read. Retrying a non-idempotent task is how you get two Slack messages.

**The failure story:** a team set `retries=5` globally in `default_args` "because BigQuery is flaky". The `send_daily_digest` task then retried 5 times on a malformed email address, and each retry fired a partial-digest email. The pipeline sent 6 emails a day for 11 days. The fix was per-task retry policy, and the rule became: `retries > 0` only on tasks that are demonstrably idempotent.

### 5. "Did today's data land?" — walk me through exactly why a log line saying "02:04 job finished OK" does not answer this.

**Because the log line records wall-clock completion, not which data the run was responsible for.** Answering the 3am question needs three facts:

1. Did the pipeline **run**? (Was it scheduled? Did the scheduler see it?)
2. Did it **succeed**? (Did every task succeed, or did some fail and get retried?)
3. Did it produce **the right data**? (Did it load *yesterday's* partition, or *today's*?)

Point 3 is the one that bites. Airflow's **logical date** is not the wall-clock time the task ran. A daily DAG scheduled at `02:00` runs after midnight but processes the interval `[2026-01-15, 2026-01-16)`. Its logical date is `2026-01-15`. A cron log says "02:00 job started, finished OK" and never records which interval was processed — so it cannot answer point 3 at all.

The mechanism that closes the gap: **Airflow records the logical date on the run, the task instances, every log line, every XCom, and every rendered template.** The logical date is the primary key of "which run am I talking about". Because the data interval is a half-open `[start, end)` range derived from the logical date, the run's identity *is* its data scope.

```python
from pipeline_logic import logical_date_window

logical_date_window("2026-01-15")
# ('2026-01-15', '2026-01-16')   ← [start, end)
```

That is why the 3am answer is a **single lookup** rather than a forensic investigation across seven machines.

**The failure story:** a nightly job ran at 02:00 with `retries=3`. On 14 March the upstream export was two hours late, so the run found an empty file, "succeeded" with 0 rows, and loaded an empty partition. Every log line said OK. The dashboard said "OK" too, because the dashboard's health check was "did the DAG go green". The data was silently missing for 3 days until a finance reconciliation caught it. The fix was two-fold: an explicit **row-count assertion** in the load task (`assert rows_loaded > 0`, or compare against an expected count pushed by an upstream sensor), and an SLA measured from the interval end.

---

## Airflow vs Spark vs Beam

### 6. A teammate says "rewrite our Spark job as an Airflow DAG so Airflow can do the joins faster". What do you say?

**Airflow cannot do the joins at all — it has no data processing model.** Airflow is an orchestrator; Spark is a compute engine. Putting your join inside a `PythonOperator` does not make it faster, it makes it *impossible to parallelise*.

The five concrete things that break when you use Airflow as a processing engine:

1. **No parallelism.** One task runs on one worker, in one process. A `PythonOperator` has exactly one.
2. **No autoscaling.** The worker size is fixed by the Composer environment. A job needing 64 GB either OOMs on a 16 GB worker or wastes a 64 GB worker every day.
3. **Retries are catastrophic.** A task fails at minute 35 of a 40-minute job, the retry starts from minute 0. With `retries=2` that is 120 minutes of compute for one result.
4. **No checkpointing.** A crash at minute 39 loses 39 minutes of work.
5. **The worker slot is held for 40 minutes.** One such task consumes a concurrency slot for the whole run.

The correct architecture puts Airflow *above* the engine:

```text
┌──────────────────────────────────────────────┐
│  Airflow / Composer                          │  ← WHEN, IN WHAT ORDER
│  ┌────────┐  ┌──────────┐  ┌────────┐        │
│  │ extract│→ │transform │→ │  load  │        │  ← WHAT
│  └────────┘  └──────────┘  └────────┘        │
│      │            │            │             │
│      └────────────┴────────────┘             │
│                  │                          │
│            ┌─────▼──────┐                   │
│            │ Spark job  │                   │  ← HOW (the engine)
│            └────────────┘                   │
└──────────────────────────────────────────────┘
```

**The one-line test:** *if the task takes more than a few minutes, or holds more than a few hundred megabytes, it belongs in a processing engine.*

**The failure story:** a team moved a 2-billion-row join into a `PythonOperator` on Composer. The task OOMed at 8 GB, retried twice, and failed after 90 minutes. The traceback was `MemoryError` inside the callable. The fix was a BigQuery query, which finished the same work in 4 minutes for $3 instead of 3 hours of a worker.

### 7. Airflow, Spark, and Beam — where exactly is the boundary, and when do you need more than one of them?

**The boundary is orchestration vs data processing.** Airflow decides *what should run, when, and in what order*. Beam and Spark transform data. Spark also has a DAG scheduler, but it is *within* a Spark job, not across jobs and pipelines — which is precisely the distinction people miss.

| Dimension | Airflow | Beam (Dataflow) | Spark (Dataproc) |
|---|---|---|---|
| Unit of work | task | PTransform / stage | DataFrame / RDD |
| Best at | dependencies, retries, scheduling, SLAs | unified batch+stream, portability | large-scale structured data, iterative SQL |
| Failure recovery | per-task retry, per-DAG state | per-stage retry, checkpointing | per-stage retry, lineage recompute |
| Cost shape | per-environment, mostly fixed | per-worker-hour | per-node-hour |

You need more than one when you have **both** a dependency *and* heavy processing. The canonical architecture:

```text
dag_ingest ──▶ dag_transform ──▶ dag_publish
    │              │
    ▼              ▼
  Beam stream   Beam batch  (or Spark on Dataproc)
    │              │
    └──────┬──────┘
           ▼
    BigQuery / GCS
```

Airflow contributes: when to run, retry on transient failure, the SLA, the cross-DAG dependency, and the ability to pause a streaming job around maintenance. Beam contributes: the transformation at scale, sub-minute streaming latency, autoscaling that responds to volume.

**When Airflow is not needed at all:** if your pipeline is one big job with no dependencies, no retry policy, and no backfill requirement, a cron job is fine. That is a real and valid architecture. The moment you have a dependency, a retry policy, a backfill requirement, or someone asking "why did Tuesday fail?", you need Airflow.

**The failure story:** a team used Beam on Dataflow *and* Airflow for the same job — Beam's own scheduler inside an Airflow task that submitted a Dataflow job. Two schedulers, one pipeline. When a job ran twice, nobody could say which scheduler was responsible. The fix was to make the Dataflow job a pure function of its inputs (fixed input path, fixed output path, no internal state depending on a previous run) and let Airflow own scheduling and retries.

### 8. You have one DAG with 12 tasks that depends on nothing and nothing depends on it. Do you still need Airflow?

**You probably do not — and saying so is a strong answer.** A single 12-task pipeline with no cross-pipeline dependencies, no SLA to track, and no backfill requirement can be a cron job or a shell script. Adding a Composer environment for it means paying a fixed monthly cost and a whole operational surface (IAM, version upgrades, scheduler monitoring) for coordination you do not need.

The test is **"does this need dependency management?"** If it does not, Airflow is overkill. But 12 tasks almost certainly *does* have dependencies — the point is that "12 tasks" is not the criterion; "12 tasks with 11 edges" is.

The realistic version of this question: a DAG that reads a GCS file, runs one BigQuery query, and writes one output. That is a **BigQuery scheduled query**, not a DAG. BigQuery's own scheduler does the same job, writes to a destination table, and sends a failure email — with BigQuery's SLA, no environment to size, and no IAM to manage.

Use Airflow when any of these is true:

| Condition | Why Airflow |
|---|---|
| The job depends on another DAG | The entire point of Airflow |
| The job needs retries with backoff and alerting | Scheduled queries have no retry policy |
| There is an SLA to track and report | Airflow's SLA mechanism and callbacks |
| The pipeline has more than a handful of steps | A chain of scheduled queries has no dependency model |
| You need XCom / dynamic fan-out | Scheduled queries cannot do that |
| The job must trigger other systems | Retry and observability are worse |

**The failure story:** a team ran 40 small BigQuery scheduled queries and also had a Composer environment for two DAGs that genuinely needed dependencies. The environment cost $700/month and 11 of the 40 queries could have been scheduled queries. After moving them, the environment shrank from 6 workers to 2 and the bill dropped to $280/month. The lesson: *one Composer environment for everything is usually right — but only if everything genuinely belongs in it.*

---

## Architecture and the scheduler

### 9. Walk me through the Airflow scheduler loop, step by step. Where do the surprising behaviours live?

**Seven steps, and the surprises live in steps 2, 3 and 4.**

1. **Heartbeat.** Update the scheduler's own heartbeat in the metadata DB. If this stops, other schedulers take over.
2. **DAG-run creation.** For every DAG whose `next_dagrun_create_after <= now`, and whose `max_active_runs` allows, `INSERT` a `dag_run` row.
3. **Task-instance creation.** For every `dag_run` with no task instances yet, `INSERT` `task_instance` rows for each task, computing dependencies from the DAG.
4. **Task evaluation.** For each task instance, compute whether dependencies are met and whether the `trigger_rule` permits it to run.
5. **Queueing.** Set `queued_by_scheduler` on runnable TIs; the executor picks them up.
6. **SLA check.** Compare running tasks against their SLA deadline; fire `sla_miss_callback`.
7. **Cleanup.** Mark finished TIs, update DAG run states, expire old XComs and logs, commit, sleep, loop.

Two properties explain almost every surprising Airflow behaviour:

**It is polling, not event-driven.** The scheduler wakes on a timer (typically every few seconds) and *re-evaluates* the world. It does not receive a webhook when a task finishes; it notices. That is why a task shows `running` for a few seconds after it actually finished, and why a DAG's state lags its last task's state.

**The scheduler does not execute tasks.** It decides *what* should run and marks it queued. The executor and workers do the running. This is why you can have many workers and one (or a few, HA) scheduler: the scheduler's work is cheap metadata manipulation; the workers' work is arbitrary user code.

**The failure story:** a team deployed a DAG whose module-level code opened a BigQuery client and ran a `SELECT 1` on every import. Composer re-parses every 1–3 minutes, so the DAG processor was issuing a query every 90 seconds, forever, and each query took 400 ms of the scheduler's parse window. With 40 DAGs in the environment the scheduler fell behind, and DAG runs started being created 8–12 minutes late. The symptom was "our DAGs run late but nothing is failed" — which looks exactly like a scheduler problem, and it was.

### 10. What are the five components of an Airflow deployment, and which one is on the critical path of every run?

**DAG processor, scheduler, metadata database, executor, workers** — plus the web server. Composer runs all of them for you.

| Component | What it actually does | Symptom when it is broken |
|---|---|---|
| **DAG processor** | scans `dags/`, imports each `.py`, writes `dag`/`task` rows, computes `next_dagrun` | DAGs vanish from the UI; `import_error` rows appear |
| **Scheduler** | the loop: create runs → create TIs → evaluate → queue → SLA → cleanup | *Nothing new runs.* Existing runs continue |
| **Metadata DB** (Cloud SQL) | Postgres: `dag`, `task`, `dag_run`, `task_instance`, `xcom`, `job`, `log`, `variable`, `connection` | Everything is slow; scheduler lag; UI timeouts |
| **Executor** | the queue that turns "runnable task" into an executable command | Tasks queue forever and never start |
| **Workers** | run `airflow tasks run <dag_id> <task_id> <logical_date>`, render templates, call `execute()`, push XComs | Tasks start and hang, or error out |

The one on the critical path of **every** run is the **metadata database**, because it is the single source of truth — the DAG run's state, the task instance's state, the XCom values, the log lines. The scheduler is critical for *creating* runs but not for *finishing* them: an already-running task continues even if the scheduler restarts, and Composer's SLA guarantees a scheduler.

**The failure story:** a Composer environment's Cloud SQL instance hit its connection limit. The symptom was not an obvious database error — it was that **all** DAGs in the environment stalled at the same moment, tasks sat `queued` and never became `running`, and the UI's task logs were empty rather than erroring. Because the environment is shared, one team's runaway query that opened 400 connections took down scheduling for 14 other DAGs. The fix was a per-DAG `pool` to cap concurrency, and raising the Cloud SQL max connections.

### 11. You said "the executor is a queue, not a worker." Explain what that means and which executor Composer actually runs.

**The executor is the transport mechanism between the scheduler and the workers** — "here is a command, give it to a worker, tell me when it is done". The executor name tells you *what kind of queue* is in the middle.

| Executor | The queue is… | A task runs… | Startup cost | Idle cost |
|---|---|---|---|---|
| `SequentialExecutor` | one in-process slot | in the scheduler process | ~0 | n/a |
| `LocalExecutor` | a `multiprocessing` pool | in a subprocess | ~ms (fork) | low |
| `CeleryExecutor` | a message broker (Redis/RabbitMQ) | in a Celery worker process | ~seconds | **billed continuously** |
| `KubernetesExecutor` | the Kubernetes API server | in a brand-new Pod | **30–60 s** | zero |

`SequentialExecutor` was removed in Airflow 2.0 — it existed so the DAG-authoring API had *something* to fall back on, and was never for production.

On **Composer 2**, the default is **`CeleryExecutor`**: Composer runs a pool of long-lived Celery workers pulling from a managed broker, and you size that pool. A **Composer 3** environment is GKE-based and can use the **KubernetesExecutor** (one Pod per task). The critical operational difference: **Composer's default CeleryExecutor has no pod-startup tax** — a task starts in seconds. The KubernetesExecutor's 30–60 s per task is worth paying only when you need per-task resource shapes or per-task images.

Two Composer-specific behaviours worth internalising:

- **The scheduler is a singleton.** One scheduler process decides what runs. A brief scheduler restart does not fail your DAGs — already-running tasks continue.
- **Worker sizing is per-environment, not per-DAG.** Every DAG shares the pool. A DAG with 50 concurrent sensors can starve a DAG with 3 tasks.

**The failure story:** a team ran 12 sensors in `mode="poke"` with `timeout=3600`, on an environment with 4 workers. Each sensor held a worker for up to an hour doing nothing. The other DAGs in the environment queued for 55 minutes. The symptom in the UI was "tasks are queued but not running" with no errors anywhere — the classic executor starvation signature. The fix was `mode="reschedule"`, which releases the worker slot between pokes.

### 12. Your DAG file raises an ImportError at module scope. What does the user see, and what does the scheduler see?

**The user sees no DAG at all, and the scheduler records an `import_error` row.** This is the single most confusing Composer behaviour for new users, because the symptom is *absence*.

The mechanism is that the **DAG processor imports your file as a module**. If the import raises, the file never registers a `DAG` object, so there is no `dag` row to show. In Airflow 2.x the traceback is recorded in the `import_error` table and surfaced in the UI under **Browse → DAGs → <filename>**. In Composer, the DAG file's own detail view shows the parse error.

Three common causes:

1. **The file failed to import.** Look for the traceback in the DAG file's detail view.
2. **Duplicate `dag_id`.** Two files declaring the same `dag_id` raise `airflow.exceptions.DagFileExists: The DAG file ... already exists`. In Airflow 2.x this is an import error and **neither** DAG registers — worse than a duplicate that merely overwrites, because you get no DAG at all.
3. **The core module is not importable.** `ImportError: cannot import name 'transform_orders' from 'pipeline_logic'` — in Composer the `dags/` folder and the core module must be siblings in the same uploaded package, or the core must be installed into the environment:

```python
import sys
sys.path.append("/opt/airflow/dags/your_package")
```

**The failure story:** a team deployed a DAG that imported `from pipeline_logic import transform_orders` but uploaded only the single `.py` file, not the package. The DAG simply did not appear. They spent 40 minutes checking IAM, the GCS bucket path, and the parse interval before noticing the absence of an `import_error` notice in a notification they were not subscribed to. The fix was uploading the whole `dags/` tree and adding a CI check that runs `DagBag` and fails on `bag.import_errors`.

### 13. Why is the metadata database the "single source of truth", and what does that imply for XCom?

**Because every piece of state Airflow has lives in Postgres: the DAG graph, the run states, the task instance states, the XCom values, the Variables, the Connections, the log lines.** Nothing important lives in the scheduler's memory — the scheduler is a polling loop that reads and writes that database.

The implication that surprises people: **XCom values are rows in the `xcom` table**, not an in-memory dict.

```text
┌──────────────────────────────────────────────┐
│                  xcom table                   │
├──────────────────────────────────────────────┤
│ dag_id | task_id  | run_id | key  | value    │
├──────────────────────────────────────────────┤
│ etl    | aggregate| run_1  | return_value | … │
│ etl    | aggregate| run_1  | summary      | … │
│ etl    | transform| run_1  | accepted     | … │
│ etl    | transform| run_1  | rejected     | … │
└──────────────────────────────────────────────┘
```

Everything follows from that one fact. It is **durable** (a value survives the task, the worker, the pod, the run). It is **scoped** to `(dag_id, task_id, run_id, key)`. It is **namespaced by task** — `aggregate`'s `summary` is invisible to `write_summary` unless the pull names the task. And it is **slow at scale** — writing megabytes into it slows down *every* DAG in the environment, because it is the same database the scheduler uses.

The course's `local_runner.py` models this exactly, and its `XCom` docstring says so:

```python
run.xcom.push(task.task_id, "return_value", result)   # ← the automatic push
```

**The failure story:** a task pushed a list of 500 order dicts through XCom — roughly 100–200 KB of pickled JSON. The scheduler's write latency on the shared Cloud SQL instance doubled for *all* DAGs in the environment, and the whole team's DAGs started missing their scheduled start times. The offending DAG had one task; its own runtime was 4 seconds. The fix was to write the rows to GCS and push the URI (~40 bytes) instead.

### 14. What does Cloud Composer actually change about Airflow, and what does it not change?

**It changes the operations, not the semantics.** A DAG that works in OSS Airflow 2.x works in Composer 2.x unchanged.

**What Composer gives you:**

- A pre-configured Airflow environment: web server, scheduler, workers, Cloud SQL Postgres, and a **GCS bucket holding your DAG files**.
- Autoscaling worker pools that scale with the number of queued tasks.
- **IAM-based access control** instead of Airflow's own RBAC in Composer 2.x (Composer 3 adds the built-in RBAC).
- **Environment Versioning** — you can pin Airflow 2.9.3 while you test 2.10 on a copy of the environment.
- Google Cloud-native integrations: BigQuery, GCS, Dataproc, Dataflow, GKE, Cloud Run.
- **The Airflow UI *is* the Composer UI** — there is no separate console.

**What Composer does not change:**

- Airflow's data model, semantics, or APIs.
- The fact that your DAG file is Python and is imported by the scheduler (so top-level side effects still hurt).
- The metadata database being the source of truth.
- The executor being Celery by default in Composer 2.x.
- The fact that the DAG file is **the deployable artefact**. `project/dags/*.py` are real Airflow 2.x DAGs; the local runner is a teaching aid that runs the *same core functions* with a miniature scheduler.

Two consequences for this course specifically: you do not need a local Airflow install (Composer is the runtime), and everything in `project/core/` is pure Python precisely so you can learn, test and verify without one.

**The failure story:** a team assumed "managed" meant "nothing to operate". The Composer environment's Cloud SQL instance was left on its default size, and with 60 DAGs writing XCom the instance saturated its CPU. The scheduler fell behind by 20 minutes and the team spent two days debugging "Composer being slow" before finding that the managed database was simply undersized for their write volume. The fix was a larger Cloud SQL instance and moving bulk XCom to GCS. Managed means Google runs the control plane; it does not mean the database sizes itself.

---

## Next module

→ [Module 2 — DAGs, Scheduling & Templates](02-dags-scheduling-and-templates.md)

---

## Related chapters

| Module section | Chapter |
|---|---|
| Why orchestration exists (1–5) | [01-what-is-orchestration-and-why-airflow](../chapters/01-what-is-orchestration-and-why-airflow.md) |
| Airflow vs Spark vs Beam (6–8) | [15-airflow-vs-beam-vs-spark](../chapters/15-airflow-vs-beam-vs-spark.md) |
| Architecture and the scheduler (9–14) | [02-airflow-architecture-and-concepts](../chapters/02-airflow-architecture-and-concepts.md) |
| Executor choice | [10-executors-and-workers](../chapters/10-executors-and-workers.md) |
| KubernetesExecutor and Composer | [16-airflow-on-kubernetes](../chapters/16-airflow-on-kubernetes.md) |
