# FAQ — Google Cloud Composer & Apache Airflow

The questions students actually ask, with the answers that are actually true.

---

## Getting started

### Do I need to install Airflow to do this course?

**No.** That is the entire point. The business logic lives in `project/core/` and
imports nothing from Airflow, so the tests run in 0.35 seconds and the notebooks
execute cell-by-cell on a bare Python install.

You *can* install Airflow in a separate virtualenv if you want to parse the DAG
files locally — the test suite gains 10 extra tests that do exactly that. But pin
the version to your Composer's version, and never install it into the course venv.

### Why is the logic in a separate module instead of inside the DAG file?

Because **logic inside a DAG file is logic you cannot test**. Importing a DAG file
requires Airflow, which means every unit test of that logic needs a scheduler, a
metadata database, and a slow install. That is why so many Airflow codebases have
untested business rules.

The split is also how you cross-validate: the local runner and a pure reference
implementation compute the same thing, and a test asserts they agree.

### What if my environment's Airflow version differs from the course's?

The course targets **Airflow 2.x** and **Composer 2**. The APIs used — `schedule`,
`logical_date`, `template_fields`, `BranchOperator`, `trigger_rule` — are stable
across Airflow 2.x. The things that *do* break across versions are the Airflow
management API and, in Airflow 3, `execution_date`, `schedule_interval` and
`DummyOperator`.

The version that matters most is the one you deploy to. Airflow's own docs are
explicit that Airflow is not a library with a stable API.

---

## Scheduling and dates

### What is the difference between `ds`, `ts` and `logical_date`?

They are the same instant, rendered differently.

| Template | Value for the 2026-01-15 run |
|---|---|
| `{{ ds }}` | `2026-01-15` |
| `{{ ts }}` | `2026-01-15T00:00:00+00:00` |
| `{{ logical_date }}` | `2026-01-15T00:00:00+00:00` |
| `{{ data_interval_start }}` | `2026-01-15T00:00:00+00:00` |
| `{{ data_interval_end }}` | `2026-01-16T00:00:00+00:00` |

`logical_date` is the label of the **run**. For a daily DAG, the run labelled
`2026-01-15` processes the data for `2026-01-15`.

### My DAG runs at midnight but the data for today is not there yet. What do I do?

That is the normal daily problem. Three options, in order of preference:

1. **Schedule the DAG for the next day.** A DAG scheduled at 02:00 with
   `schedule="@daily"` has the logical date of the *previous* day, so it processes
   yesterday's data — which is complete. This is the standard answer.
2. **Use a sensor** to wait for the file.
3. **Use a Dataset** (Airflow 2.4+) to schedule on the arrival of the data.

### Why is my interval end-exclusive?

Because it prevents double-counting. With `[2026-01-15, 2026-01-16)`, the row at
exactly `2026-01-16T00:00:00` belongs to the next day and only the next day. If
intervals were inclusive at both ends, that row would be loaded twice.

This is the single most common bug in a daily Airflow pipeline, and it stays
invisible until the monthly totals are wrong.

### Should I use `schedule_interval` or `schedule`?

`schedule`. `schedule_interval` was deprecated in Airflow 2.4 in favour of
`schedule`, which handles the `None` case (manual-trigger-only DAGs) properly.

### Should I enable `catchup`?

For a DAG that **loads data**: no. Turn it on and a DAG with a `start_date` six
months ago will try to replay six months of history the first time it is deployed
— loading the same partitions repeatedly, or failing on data that no longer
exists.

For a DAG that **processes a bounded backlog** — a one-time migration — use a
separate DAG with an explicit `start_date` and `catchup=True`, and delete it when
it is done.

### What is `max_active_runs` for?

How many runs of the same DAG may execute at once. The default `1` is right for a
daily load: if yesterday's run is still going, today's should wait rather than
compete for the same destination partition.

### Why does my DAG run twice?

Almost always `catchup=True` with a `start_date` in the past, or a DAG that was
deployed with `catchup` on and the scheduler creating historical runs. Check
`airflow dags list` for runs with older logical dates.

---

## Templating and configuration

### `jinja2.exceptions.UndefinedError` — what is happening?

A Variable, param or connection field in your template does not exist. Airflow
renders templates **before** the task runs, so this fails at the start of the task
rather than halfway through.

The fix is usually `{{ var.value.name | default('fallback') }}`. That is not a
workaround — a fallback is the right design for anything that might be missing in
a given environment, and it makes the DAG parse and run everywhere.

### Variable, param or Connection — which one?

| | Use for | Example |
|---|---|---|
| `params` | Values that differ per **run** | A backfill date range, a `force_full_load` flag |
| `Variable` | Values that differ per **environment** | Bucket names, project IDs, thresholds |
| `Connection` | **Credentials** | A database password, an API key |

### Is it safe to put a password in a Variable?

**No.** Variables are visible in the UI to anyone with Variable read access, and
are stored **unencrypted** in the metadata database. Airflow encrypts the
`password` field of a Connection with Fernet; it does not encrypt a Variable's
value.

### Can a Variable hold a JSON document?

Yes — `{{ var.value.my_json | fromjson }}`, or in Python:
`Variable("my_json").json()`. Useful for a small config blob.

### How do I template a path with the run's date?

```bash
gs://{{ var.value.source_bucket }}/{{ ds }}/orders.csv
```

For a BigQuery partition decorator, use `{{ ds_nodash }}` → `20260115`.

---

## XCom

### What is the size limit on an XCom value?

Around **48 KB** is the practical soft limit for a value pushed through the
metadata database. It is not enforced as a hard error — the insert simply fails,
or the row is truncated depending on the column type, and you get a database error
rather than a clear message.

### Can I pass a DataFrame between tasks?

**Do not.** Put it in Cloud Storage or BigQuery and pass the *reference* — the
path, the table name, the partition — through XCom. XCom is a database table
shared with the scheduler; writing megabytes into it slows down every DAG in the
environment.

### Why isn't my XCom there?

Three common reasons:

1. **You pulled without `task_ids`.** `ti.xcom_pull()` with no arguments looks in
   the *current task's* namespace, which is almost never what you want.
2. **The task did not run.** A skipped task pushes nothing.
3. **You are in a different DAG run.** XCom is scoped to `(dag_id, task_id,
   run_id, key)`. A value from yesterday's run is not visible today.

---

## Branching

### My downstream task is skipped and I do not know why.

Three causes, in order of likelihood:

1. **A branch chose a different path.** Look at which task ran.
2. **A trigger rule.** `all_success` (the default) skips a task when a dependency
   was *skipped*, not just when it failed.
3. **The dependency failed** — that state is `upstream_failed`, not `skipped`.

### Why does my task after a branch never run?

Because it depends on **both** branches, and one was skipped. Under the default
`all_success`, a skipped dependency means the task is skipped.

```python
join = EmptyOperator(task_id="load_complete", trigger_rule="none_failed")
```

This is the join-point pattern, and it is the most common branching bug.

### `BranchOperator` vs `ShortCircuitOperator`?

`BranchOperator` names the tasks that should run; everything else downstream is
skipped. `ShortCircuitOperator` skips **all** downstream tasks when it returns
False — useful for a simple "is there anything to do?" guard.

### Does a branch skip tasks that do not depend on it?

No. Only downstream tasks.

---

## Reliability

### My DAG retried and double-counted the revenue. Why?

The write was not idempotent. `WRITE_APPEND` into BigQuery appends a second copy
of every row on retry. The fix is `WRITE_TRUNCATE` against the partition, or a
merge keyed on a deterministic row identity.

### What is the difference between `sla`, `execution_timeout` and `retries`?

| | Meaning |
|---|---|
| `sla` | When the task should have **finished**, measured from the data interval end |
| `execution_timeout` | How long the task may **run** |
| `retries` | How many times to **re-attempt** after a failure |

An SLA miss does **not** fail the task — it fires `sla_miss_callback`. An
`execution_timeout` kills the task and marks it failed.

### What does "late" mean in the Composer UI?

The run's task exceeded its SLA. The task itself may have succeeded. Late and
failed are different things, and conflating them sends you down the wrong path.

### How do I make a DAG safe to backfill?

Make it idempotent, then:

1. Use a dedicated backfill DAG with an explicit `start_date` — do not flip
   `catchup` on a live DAG.
2. Write with `WRITE_TRUNCATE` per partition, or merge on a deterministic key.
3. Set `max_active_runs=1` so two backfill dates cannot write the same partition.
4. Use `depends_on_past=False` — a backfilled date should not wait for a date
   that was never run.

---

## Testing

### How do I test a DAG without a scheduler?

Assert on the **structure**: that the DAG exists, has the expected task count, and
that the dependencies are right. That catches the mistakes that actually happen —
a renamed task, a missing dependency, a duplicate label.

```python
from airflow.models import DagBag

dag = DagBag(dag_folder="project/dags").get_dag("etl_orders_to_bigquery")
assert dag is not None
assert len(dag.tasks) == 5
assert dag.get_task("load_to_bigquery").upstream_task_ids == {"validate_and_stage"}
```

### How do I test the logic?

Put it in a module that does not import Airflow, and test it as ordinary Python.
That is the entire argument for the split, and it is why this course's tests run
in 0.35 seconds.

### Should I test that a task succeeds?

Only if it is cheap and deterministic. Testing "the BigQuery load worked" in CI
means a BigQuery project, a table and a cleanup step — and it will be flaky. Test
the *shape* of what you pass to BigQuery instead, and test the load in the
environment.

---

## Composer and GCP

### How much does a Composer environment cost?

The environment bills **continuously**, whether or not a DAG runs. The bill is
dominated by the web server, the Cloud SQL metadata database and the worker pool.

- **Small** is enough to learn in and costs the least.
- **Medium** suits a team with a dozen daily DAGs.
- **Large** is for many concurrent DAGs or heavy tasks.

Create a budget alert as a backstop, and **delete the environment when you are
done**. The "forgot to delete it for a month" story is the most common way people
get a surprise bill from a course.

### What happens to my data when I delete the environment?

Your **DAG bucket is yours** — it survives. A Composer-managed Cloud SQL instance
may also survive, depending on the Composer version; check the Cloud SQL console.
Everything else — the GKE cluster, the workers, the Airflow metadata — goes.

### How long does a DAG take to appear after I upload it?

**1–2 minutes.** Composer watches the bucket continuously and re-parses on change.
If it does not appear, check the DAG import errors in the UI — a syntax error in
one DAG does not block others, but it is silent.

### Why is my DAG showing an import error?

The most common causes:

- A syntax error.
- A missing dependency — the environment's Python does not have your package.
- An Airflow version mismatch: `schedule_interval` on a newer version, or a
  provider not installed in the image.
- Two files defining the same `dag_id`.

The UI shows the traceback. Read it — it is the same traceback you would get
locally.

### Can I use a custom Python package in a DAG?

Yes, by installing it into the environment's Python. In Composer, build a custom
image or use the environment update with a startup script. The simpler path for
most cases is to avoid the dependency.

### Composer 2 or Composer 3?

**Composer 2** for a learning environment — cheaper, simpler, Celery executor.
**Composer 3** when you need Kubernetes-style isolation or bursty concurrency, and
you are comfortable with pod startup cost (~30–60 s per task).

### How do I run an ad-hoc query from the environment?

```bash
gcloud composer environments run ENV --location=REGION --dag DAG_ID
```

Or open a shell into the environment and use `airflow dags trigger`.

### What is the `gcloud` command to list DAGs?

```bash
gcloud composer environments run ENV --location=REGION \
  --exec "airflow dags list"
```

---

## Airflow vs the alternatives

### Should I use Airflow to run Spark jobs?

Sometimes, and it is fine — but be honest about what you are doing. Airflow is
submitting a job and waiting for it; Spark is doing the work. If the Spark job
takes 40 minutes and Airflow's SLA is 30 minutes, you have built a pipeline that
is late every day.

### Airflow or Airflow on Composer?

Same DAGs, different operations. Composer removes the installation and the
metadata-database administration, and costs money for that. Self-managing Airflow
on Kubernetes gives you more control and more responsibility.

### When is Airflow the wrong tool?

- The work is a single SQL query on a schedule → **BigQuery scheduled queries**.
- The work is a stream → **Dataflow**, with Airflow only for the batch side.
- The coordination is between two services over HTTP → a **queue**, not Airflow.

---

## Miscellaneous

### What is a SubDAG, and should I use one?

A DAG inside a DAG, from Airflow 1. In Airflow 2 it is **deprecated**. Model the
structure with ordinary task dependencies and `trigger_rule` instead — SubDAGs
have their own scheduling quirks and are much harder to read.

### Can two DAGs depend on each other?

Yes, but pick one direction. `TriggerDagRunOperator` fires another DAG;
`ExternalTaskSensor` waits for one. Avoid a cycle — Airflow will deadlock or
fail the runs.

### Why does my task run twice when I clear it?

Because "clearing" a task re-runs it, and it may run on a different worker with a
different environment. If it is not idempotent, that is a data-correctness bug
waiting to happen.

### What is the 48 KB again?

The practical limit on an XCom value. Store bulk data in Cloud Storage or
BigQuery and pass the reference through XCom.

### Where do I look first when a DAG fails?

In order:

1. **The task's log**, not the DAG's. The failing task's log has the traceback.
2. **The upstream task's log**, if the failure is `upstream_failed`.
3. **The task's XCom**, if the task succeeded but produced the wrong value.
4. **The scheduler log**, only for "the DAG never ran" problems.
