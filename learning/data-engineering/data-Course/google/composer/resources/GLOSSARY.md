# Glossary — Apache Airflow & Google Cloud Composer

Every term in the course, defined once, in one place.

---

## A

**Airflow** — The open-source workflow orchestrator for data pipelines. It
*coordinates* work; it does not usually perform the computation itself.

**Airflow UI** — The web interface for viewing DAGs, triggering runs, reading logs
and managing configuration. In Composer it is the Composer UI.

**Airflow 2** — The current major version line. Airflow 3 exists and changes
several core APIs; Composer 2.x environments run Airflow 2.x.

---

## B

**Backfill** — Re-running a DAG for past dates. The dangerous operation: a DAG that
is not idempotent will double-count every historical day you backfill.

**BashOperator** — An operator that runs a shell command on a worker.

**BigQuery** — Google's serverless columnar warehouse. Airflow's most common sink.

**BranchOperator** — An operator whose return value names the downstream task_ids
that should run. Every other downstream task is marked *skipped*.

---

## C

**Catchup** — Whether the scheduler creates runs for missed intervals since
`start_date`. Dangerous for a DAG that loads data, because it can replay months of
history on first deploy.

**CeleryExecutor** — The executor used by Composer 2. A distributed worker pool
pulling tasks from a broker (Redis or RabbitMQ).

**Composer 2** — The current Google-managed Airflow offering. GKE-based, Celery
executor, Airflow 2.x versions.

**Composer 3** — The newer Composer offering. GKE-based, KubernetesExecutor, Airflow
2.10+.

**Connection** — A named, stored credential in Airflow: a host, a login, a password,
and an `extra` JSON blob. The correct home for secrets.

**Cron** — A schedule expressed as a crontab line. Airflow's cron is evaluated in
UTC.

---

## D

**DAG** — Directed Acyclic Graph. A set of tasks with dependencies that contain no
cycles. Airflow's unit of orchestration.

**DAG file** — The Python file defining a DAG. Composer parses every `.py` file in
the DAG bucket.

**DAG processor** — The Airflow process that reads DAG files, parses them, and
writes the resulting structure into the metadata database.

**DAG run** — One execution of a DAG, identified by `dag_id` + `run_id`, and
labelled with a **logical date**.

**Dataset** (formerly "data-aware scheduling") — Airflow 2.4+'s mechanism for
scheduling a DAG on the *arrival* of data rather than on a clock. A DAG waits for
its datasets to be updated.

**Dynamic task mapping** — Airflow 2.3+'s `.expand()` / `.expand_kwargs()`, which
creates N task instances from one task definition at run time.

**Executor** — The component that runs tasks. The scheduler decides *what* to run;
the executor decides *where*.

---

## E

**Execution date** — The deprecated name for **logical date**. Airflow 2.2+
introduced `logical_date` and deprecated `execution_date`; the old name still
appears in a lot of code.

**Execution timeout** — The maximum duration a task may run. On exceeding it, the
task is killed and marked failed.

---

## F

**Fairness** — The scheduler's property of distributing slots fairly across DAGs,
so one busy DAG cannot starve another.

**Fan-out / fan-in** — A pattern where one task produces N downstream tasks, which
then converge on a join task.

---

## G

**GKE** — Google Kubernetes Engine. Composer's environments run on GKE.

**GCS** — Google Cloud Storage. Composer's DAG bucket, and the usual place for
intermediate data that is too large for XCom.

---

## H

**Half-open interval** — The convention that an interval is `[start, end)` — it
includes `start` and excludes `end`. Airflow's data intervals are half-open, and
your SQL filters must match.

---

## I

**Idempotent** — A task that can run twice with the same result and no side
effects. The property that makes a DAG safely re-runnable.

**Image version** — The Composer version string, e.g.
`composer-2.9.7-airflow-2.9.3`. It pins the Airflow version and the Composer
wrapper. **Airflow's DAG import API is not stable across minor versions** — a DAG
that parses on one version may fail on another.

---

## J

**Job** — A rough synonym for a DAG run, used loosely in the UI.

---

## K

**KubernetesExecutor** — An executor that runs each task in its own pod. Used by
Composer 3 and by self-managed Kubernetes deployments. Isolation is excellent;
pod startup cost (~30–60 s) is the trade-off.

**Key-value pair** — In XCom, a named value within a task's namespace.

---

## L

**LocalExecutor** — Runs tasks as subprocesses on the scheduler host. Parallel, but
the host is the bottleneck.

**Logical date** — The label of a DAG run, representing the *start of the data
interval* it processes. For a daily DAG scheduled at midnight, the run labelled
`2026-01-15` processes the data for `2026-01-15` — which usually arrives the next
morning.

---

## M

**Max active runs** — How many runs of one DAG may execute at once. `1` is the
sensible default for a daily load.

**Metadata database** — Airflow's central database (SQLite locally, Postgres or
MySQL in production; Cloud SQL in Composer). It holds DAG definitions, run and task
state, connections, variables, and **XCom values**.

**Min interval** — The minimum gap between scheduled runs of one DAG.

---

## N

**Next execution date** — When the scheduler will next create a run.

---

## O

**Operator** — The type of a task. An operator determines *how* the work is done:
`PythonOperator`, `BashOperator`, `BigQueryExecuteQueryOperator`, and so on.

**Orchestrator** — A system that coordinates work across systems. Airflow is one.
Spark and Beam are *processing* engines that an orchestrator can trigger.

---

## P

**Params** — Per-run configuration passed when triggering a DAG. Distinct from
Variables, which are per-environment.

**Pod** — A Kubernetes container group. The KubernetesExecutor creates one per task.

**Pool** — A named limit on how many concurrent tasks (or slots of weight) can run.
Used to protect a scarce resource such as a database connection.

**Pull** — Retrieving an XCom value. `ti.xcom_pull(task_ids=..., key=...)`.

**Push** — Storing an XCom value. `ti.xcom_push(key=..., value=...)`.

---

## Q

**Queue** — Where tasks wait to be picked up by a worker.

---

## R

**Reschedule mode** — A sensor mode that releases its worker slot while waiting and
is re-evaluated later. Use it for waits longer than a minute.

**Retries** — How many times a failed task is re-attempted, with `retry_delay`
between attempts.

**Run ID** — The unique identifier of a DAG run.

---

## S

**Schedule** — When a DAG run is created. `@daily`, `@hourly`, a cron expression, a
`timedelta`, or (2.4+) a Dataset schedule.

**Schedule interval** — Deprecated alias for **schedule**.

**Sensor** — An operator that waits for a condition — a file to appear, a table to
be populated, another DAG to finish — and then succeeds.

**SLA** — A Service Level Agreement: a commitment that a task or DAG will complete
by a certain time. In Airflow, measured against the **data interval end**, not the
wall-clock start.

**SLA miss** — The event of not meeting that commitment. Fires
`sla_miss_callback`.

**SLO** — Service Level Objective: the target you aim for. An SLA is the
contractual consequence of missing an SLO.

**Start date** — The earliest date a DAG may run.

**SubDAG** — A DAG inside a DAG. Deprecated and discouraged in Airflow 2 — model
the structure with ordinary dependencies instead.

**Sync** — A sensor that holds its worker slot while waiting. The opposite of
reschedule mode.

---

## T

**Task** — A node in a DAG: a unit of work with dependencies.

**Task instance** — One execution of one task in one DAG run.

**TaskFlow API** — Airflow 2.0+'s decorator-based API (`@task`, `@dag`), where a
Python function becomes a task and return values become XComs implicitly.

**Trigger rule** — The condition under which a task runs, given its dependencies'
states. `all_success` (default), `none_failed`, `all_done`,
`none_failed_min_one_success`, `always`.

**Triggerer** — The Airflow process that manages **deferrable operators**, letting
a task release its worker slot while waiting on an external event.

---

## U

**Unit test** — A test of pure logic, with no scheduler, no database and no network.

---

## V

**Variable** — An environment-level key/value pair in Airflow, readable in a DAG via
`{{ var.value.name }}`. **Not** a place to store secrets — it is visible in the UI
and stored unencrypted.

**Virtualenv** — An isolated Python environment.

---

## W

**Webhook** — An HTTP endpoint Airflow exposes for external systems to trigger a
DAG. (In Airflow 2.8+, the DAG-level REST API is the preferred mechanism.)

**Worker** — The process that executes tasks. Each task runs in a worker slot for
the duration of the task.

---

## X

**XCom** — Airflow's cross-communication store: values passed between tasks.
**Stored in the metadata database**, scoped to `(dag_id, task_id, run_id, key)`.
Intended for *small control data* — a count, a partition name, a decision — not
bulk payloads. The practical soft limit is around **48 KB**.

**XComArg** — The TaskFlow-era reference to a task's output, usable directly as a
function argument.

**XCom backend** — Where XCom values are stored. The metadata database by default;
custom backends (including object storage) are possible.

---

## Y, Z

**YAML** — The format of `airflow dags` and DAG serialization in Airflow 2.

---

## Composer-specific

**Composer environment** — A managed Airflow deployment. Includes a GKE cluster, a
Cloud SQL metadata database, a GCS DAG bucket, a web server, and a worker pool.

**DAG bucket** — The GCS bucket holding the DAG files. Composer syncs from it
continuously.

**Environment size** — `SMALL` (1–2 workers), `MEDIUM` (3–6), `LARGE` (7–15) in
Composer 2. Determines capacity and cost.

**Composer 2** — Celery-executor Composer. **Composer 3** — KubernetesExecutor
Composer.

**Airflow CLI inside the environment** — `gcloud composer environments run` or a
shell into the environment give you `airflow` commands: `airflow dags list`,
`airflow dags trigger`, `airflow dags backfill`, `airflow tasks states-for-dag-run`.
