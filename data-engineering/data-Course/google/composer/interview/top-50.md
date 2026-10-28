# Top 50 — Google Cloud Composer with Apache Airflow

> **50 questions · The highest-yield subset · Read this the night before**

These fifty questions were selected from the full bank by five criteria:
**high decision impact** (the answer changes what you build), **cross-layer**
(the answer connects the model to the runtime to the operations), **quantifiable**
(a number is attached), **contested** (reasonable senior engineers disagree),
and **common misconception** (the wrong answer is what a lot of people say).

Every answer here is **tighter** than in the module files: direct answer, the
one mechanism that explains it, the one number, and the failure you have seen.

> **How to use this file.** Read it once, end to end, the night before the
> interview. Do not write anything down. Notice which answers you could not
> produce. Then go back to the module files for the ones you missed.

---

## If you only remember five things

1. **The logical date is the data interval, not the run time.** A daily DAG's run for `2026-01-15` processes `[2026-01-15, 2026-01-16)`. Filter with `>= data_interval_start AND < data_interval_end`. The off-by-one here is the most common production bug in Airflow.
2. **XCom is a table in the metadata database, not a dict.** It is for control data — a count (`1245`), a partition (`20260115`), a GCS URI. Not for rows. A 200 KB XCom slows every DAG in the environment.
3. **A retry re-runs your code and undoes nothing.** So `retries > 0` requires idempotency. `WRITE_APPEND` + `retries=3` = the day's rows written 4 times. Exactly-once is not achievable; idempotency is.
4. **Airflow orchestrates; it does not process.** If a task takes more than a few minutes or holds more than a few hundred MB, it belongs in BigQuery, Dataflow, or Spark — with Airflow above it.
5. **Airflow's SLA is measured from the end of the data interval**, not from when the run started. `interval_end + sla` is the deadline.

---

## Architecture & the scheduler (8)

### 1. ⭐ What is the DAG model, and why is "acyclic" a feature?

**A DAG is nodes (tasks) plus edges (dependencies). Acyclic means there is always a topological order, so the graph is always schedulable.** A cycle would mean "A waits for B, B waits for A" — no well-defined first task, so no execution order exists. Airflow rejects cycles at parse time and the DAG simply does not appear in the UI.

The subtle payoff: **a DAG can be analysed as a whole.** You can ask "what are the upstream dependencies of this table?", "which tasks are on the critical path?", "if this task fails, what else is affected?". With cycles, none of those has a well-defined answer.

The cost: **looping must be repetition, not a graph edge.** "Process each of 500 customer files" is 500 runs, or one DAG with dynamic task mapping (`.expand()`, Airflow 2.3+). That turns "loop until done" into a set of independently retriable, independently observable units.

The course's runner enforces this in `DAG._validate()`:
```text
ValueError: cycle detected in DAG 'demo_failure': a -> b -> a
```

### 2. ⭐ Walk me through the scheduler loop.

**Seven steps, and the surprises live in 2, 3 and 4.** (1) Heartbeat. (2) Create `dag_run` rows for DAGs whose `next_dagrun_create_after <= now`, subject to `max_active_runs`. (3) Create `task_instance` rows for runs that have none. (4) Evaluate each task instance's dependencies and `trigger_rule`. (5) Queue runnable TIs for the executor. (6) Check SLAs, fire `sla_miss_callback`. (7) Clean up finished TIs, expire old XComs/logs, commit, sleep, loop.

Two properties explain most surprises: **it is polling, not event-driven** (the scheduler *notices* a task finished; it does not get a webhook), and **the scheduler does not execute tasks** (it decides what runs; workers do the running). That is why many workers + one scheduler works.

**Failure story:** a DAG's module-level code opened a BigQuery client and ran `SELECT 1` on every import. Composer re-parses every 1–3 minutes, so the parse window was permanently busy and DAG runs were created 8–12 minutes late. Symptom: "runs are late but nothing failed."

### 3. ⭐ The five components of an Airflow deployment, and which one is on the critical path of every run?

**DAG processor, scheduler, metadata database, executor, workers** — plus the web server.

| Component | Symptom when broken |
|---|---|
| DAG processor | DAGs vanish; `import_error` rows appear |
| Scheduler | *nothing new runs*; existing runs continue |
| Metadata DB | everything slow; scheduler lag; UI timeouts |
| Executor | tasks queue forever and never start |
| Workers | tasks start and hang, or error out |

The critical path of every run is the **metadata database** — it holds the DAG graph, run states, task instance states, XCom values, Variables, Connections, and logs. The scheduler is critical for *creating* runs but not for *finishing* them: a scheduler restart does not fail running tasks, and Composer's SLA guarantees a scheduler.

**Failure story:** a Composer environment's Cloud SQL hit its connection limit. The symptom was not a database error — **all** DAGs stalled simultaneously, tasks sat `queued` and never became `running`, and logs were empty rather than erroring. One team's runaway query had opened 400 connections.

### 4. The executor is "a queue, not a worker". Explain, and which executor does Composer run?

**The executor is the transport between the scheduler and the workers** — "here is a command, give it to a worker, tell me when it's done". The name tells you what kind of queue is in the middle.

| Executor | Queue | Startup | Idle cost |
|---|---|---|---|
| `SequentialExecutor` | in-process slot | ~0 | removed in Airflow 2.0 |
| `LocalExecutor` | multiprocessing pool | ~ms (fork) | low |
| `CeleryExecutor` | Redis/RabbitMQ broker | ~seconds | **billed continuously** |
| `KubernetesExecutor` | the K8s API | **30–60 s** | zero |

**Composer 2 defaults to `CeleryExecutor`** (managed long-lived workers, you size the pool). **Composer 3** is GKE-based and can use the `KubernetesExecutor` (one Pod per task). The operational difference: **Composer's default CeleryExecutor has no pod-startup tax** — a task starts in seconds. Choose the KubernetesExecutor only for per-task resource shapes or per-task images, and accept the ~45 s.

**Failure story:** 12 `mode="poke"` sensors with `timeout=3600` on a 4-worker environment held every worker for up to an hour. Everything else queued for 55 minutes with **no errors anywhere** — the executor-starvation signature. Fix: `mode="reschedule"`.

### 5. Why is the metadata database the "single source of truth", and what does that imply for XCom?

**Because every piece of state Airflow has lives in Postgres** — the DAG graph, run states, task instance states, XCom values, Variables, Connections, logs. The scheduler is a polling loop over that database; nothing important lives in its memory.

The implication: **XCom values are rows in the `xcom` table**, not an in-memory dict.

```text
dag_id | task_id   | run_id | key          | value
etl    | aggregate | run_1  | return_value | …
etl    | transform | run_1  | accepted     | …
```

So XCom is durable, scoped to `(dag_id, task_id, run_id, key)`, namespaced by task, and **slow at scale** — it is the same database the scheduler uses, so writing megabytes into it slows every DAG in the environment.

**Failure story:** a task pushed 500 order dicts (~100–200 KB pickled) into XCom. The shared Cloud SQL write latency doubled for *all* DAGs and the whole team started missing their scheduled start times. The offending DAG's own task ran in 4 seconds. Fix: write to GCS, push the URI (~40 bytes).

### 6. What is Composer, and what does it change about Airflow?

**It changes the operations, not the semantics.** A DAG that works in OSS Airflow 2.x works in Composer 2.x unchanged.

Composer gives you: a pre-configured environment (web server, scheduler, workers, Cloud SQL, and a **GCS bucket for your DAGs**), autoscaling workers, **IAM-based access control** (Composer 3 adds built-in RBAC), **Environment Versioning** (pin Airflow 2.9.3 while testing 2.10 on a copy), and GCP-native operators. **The Airflow UI *is* the Composer UI.**

It does not change: Airflow's data model or APIs; the fact that your DAG file is Python and is imported by the scheduler (so top-level side effects still hurt); the metadata DB as the source of truth; or the CeleryExecutor default in Composer 2.

**Failure story:** a team assumed "managed" meant "nothing to operate". Their Composer-managed Cloud SQL was left on its default size; with 60 DAGs writing XCom it saturated its CPU and the scheduler fell 20 minutes behind. Two days lost. Managed means Google runs the control plane — it does not size your database for you.

### 7. ⭐ Airflow vs Spark vs Beam — where is the boundary?

**Orchestration vs data processing.** Airflow decides *what should run, when, and in what order*. Beam and Spark transform data. Spark also has a DAG scheduler, but it is *within* a Spark job, not across pipelines — which is the distinction people miss.

| | Airflow | Beam (Dataflow) | Spark (Dataproc) |
|---|---|---|---|
| Unit of work | task | PTransform/stage | DataFrame/RDD |
| Best at | dependencies, retries, SLAs | unified batch+stream | large-scale structured data, iterative SQL |
| Cost shape | per-environment, mostly fixed | per-worker-hour | per-node-hour |

Most production platforms need **both**, not one. Airflow contributes when to run, retry on transient failure, the SLA, the cross-DAG dependency, and pausing a stream for maintenance. Beam/Spark contribute the transformation at scale.

**When Airflow is not needed:** one job, no dependencies, no retry policy, no backfill requirement — a cron job is fine, or a **BigQuery scheduled query** (no environment to size, no IAM to manage).

**Failure story:** a team ran Beam *and* Airflow for the same job — Beam's own scheduler inside an Airflow task that submitted a Dataflow job. Two schedulers, one pipeline. When a job ran twice, nobody could say which was responsible. Fix: make the Dataflow job a pure function of its inputs (fixed in path, fixed out path, no state depending on a previous run).

### 8. What is the "3am question", and why can't a log line answer it?

**"Did today's data land?"** needs three facts: did it run, did it succeed, and — the one that bites — **did it produce the *right* data?**

A log saying "02:04 job finished OK" records wall-clock completion, not data scope. A daily DAG's run for `2026-01-15` processes `[2026-01-15, 2026-01-16)`; the run happens at 02:00 but the logical date is `2026-01-15`. The log never recorded which interval was processed, so point 3 is unanswerable from it.

The mechanism that closes the gap: **Airflow records the logical date on the run, the task instances, every log line, every XCom, and every rendered template.** The logical date is the primary key of "which run am I talking about", so the answer is a single lookup rather than a forensic investigation across seven machines.

**Failure story:** an upstream export was 2 hours late; the nightly job found an empty file, "succeeded" with 0 rows, and loaded an empty partition. Every log line said OK — because the health check was "did the DAG go green". Data was silently missing for 3 days. Fix: an explicit row-count assertion, and an SLA measured from the interval end.

---

## DAGs, schedules & the data interval (8)

### 9. ⭐ ⭐ Logical date vs execution date vs data interval vs wall-clock start. Which goes in your SQL filter?

**Use `data_interval_start` and `data_interval_end`.** `execution_date` is the deprecated old name for `logical_date` and means the same thing.

| Name | For the 2026-01-15 daily run |
|---|---|
| Logical date | `2026-01-15T00:00:00+00:00` |
| Data interval | `[2026-01-15, 2026-01-16)` |
| Wall-clock start | `2026-01-16T00:05:00+00:00` |

The interval is **half-open**. The filter must match exactly:

```sql
WHERE order_ts >= '{{ data_interval_start }}'
  AND order_ts <  '{{ data_interval_end }}'
```

`<= '2026-01-15'` double-counts the midnight row; `BETWEEN` loads the boundary row into two days. This off-by-one is invisible until the monthly totals are wrong.

**Failure story:** a daily load used `BETWEEN '2026-01-15' AND '2026-01-16'`. The row at exactly `2026-01-16T00:00:00Z` loaded into both runs. Monthly revenue was **0.8% high** — one extra day out of 31, times the average midnight order. Nobody noticed for 2 months because 0.8% is within normal reporting variance.

### 10. ⭐ What is `catchup=True` and why is it dangerous?

**It tells the scheduler: "for every scheduled interval between `start_date` and now that has no run, create one."** Deploy a DAG with `start_date=datetime(2024, 1, 1)` and `catchup=True` and you get **~730 DAG runs** — each creating task instances, each able to consume BigQuery load quota, GCS write budget, or API rate limit.

The reason it is dangerous is not the volume, it is that **historical data often does not exist in the form the pipeline expects.** A pipeline written in 2026 may reference a column added in 2026. A partner API may retain only 90 days.

Correct default: `catchup=False` — which every DAG in this course sets. When you *do* want a backfill, use a **backfill job** (`airflow dags backfill`, Composer's **Run → Backfill**, or `gcloud composer environments run backfill`), not `catchup`.

**Failure story:** ~730 runs appeared within 4 minutes; ~200 started concurrently; the DAG read a partner API with a 20 req/s limit, so the live run could not get through and missed its SLA — because of history it did not need.

### 11. ⭐ `max_active_runs` — when must it be 1?

**Set it to 1 when the pipeline writes to a fixed destination** (one table, one prefix), reads a mutable source and needs a consistent snapshot, or is expensive enough to serialise. Set it higher when runs are independent — each writes its own date partition.

The failure mode of too high is **interleaved writes**: two runs for different logical dates appending to the same unpartitioned table. A `MERGE` keyed on `order_id` can have run N overwrite run N+1's row for the same order — which happens when a customer reorders the same product id on consecutive days.

`max_active_tasks` is the companion: it caps concurrent tasks across *all* runs. For cross-DAG control use a **pool**.

**Failure story:** `max_active_runs=16` (the default) on a pipeline appending to a single unpartitioned table. During a backfill, 16 runs wrote concurrently and the month-end `GROUP BY region` was **2.4× too high** — and the error varied by day, so it looked like a source data-quality bug rather than an orchestration bug.

### 12. What does `start_date` mean, and what are its two rules?

**It is the earliest logical date Airflow will consider** — not "when the DAG was created", not "when the first run happens".

1. **It must be timezone-aware.** `datetime(2026, 1, 1, tzinfo=timezone.utc)`. A naive datetime is read in the *server's* local timezone, which differs between your laptop and Composer.
2. **It is a floor, not a trigger.** Setting it to `2026-01-01` does not create 20 runs for January.

Lowering it retroactively creates history **only if `catchup=True`**. Every course DAG uses `2026-01-01` deliberately early.

**Failure story:** `start_date=datetime(2026, 1, 1)` with no `tzinfo`. Composer's local timezone differed from the developer's, so the partition decorator (`20260115`) did not match the source date directory (`20260114`). The load found 0 rows and "succeeded".

### 13. What schedule forms exist, and which is most misunderstood?

**Presets, cron, `timedelta`, Datasets, `None`.** The most misunderstood is cron: **it is evaluated in UTC** in Airflow 2.x. `"0 6 * * *"` fires at 06:00 **UTC**, not 06:00 local. Composer does not change this.

`@daily` is exactly `"0 0 * * *"`. `timedelta(hours=6)` fires every 6 hours from `start_date` — and the logical date is still the interval start.

**Version note:** `schedule_interval` → **`schedule`** in Airflow 2.4 (deprecated, removed in Airflow 3). On Airflow 2.0–2.3 `schedule` does not exist.

**Failure story:** `"0 6 * * *"` written by a developer in UTC+5:30 who assumed local time. The DAG fired at 00:30 UTC, before the previous day's upstream data was complete, and ran on empty data for 3 weeks.

### 14. ⭐ What are the trigger rules, and how do `skipped` and `failed` interact with them?

**Trigger rules decide whether a task runs at all, given the state of its upstream — and `skipped` is the state people forget.**

| Rule | Runs when |
|---|---|
| `all_success` (default) | every upstream succeeded |
| `none_failed` | no upstream **failed** (skipped is OK) |
| `none_failed_min_one_success` | no upstream failed **and** at least one succeeded |
| `none_skipped` | no upstream was skipped |
| `all_done` | all upstream finished, whatever the state |
| `always` | always |

Two things to internalise:

- **A failed dependency is not a trigger-rule question.** It produces `upstream_failed` regardless (except `all_done`/`always`). That is why `failed` and `upstream_failed` are distinct: the first ran and raised; the second never ran.
- **`none_failed` vs `none_failed_min_one_success`** differs when *every* upstream branch is skipped. The latter is usually what you want for a join.

**Failure story:** a cleanup task used `none_failed_min_one_success`, so on days when a branch chose a path that excluded the join, **both** branches were skipped and the cleanup was skipped too. Staging tables accumulated: 40 in 3 weeks, 400 in 6 months. Fix: `all_done` for cleanup.

### 15. ⭐ When a DAG is missing from the UI — what is the ordered triage?

**Check from cheapest to most likely, and read the evidence in the UI rather than re-reading the DAG file.**

1. **Is the file in the DAGs bucket?** Composer parses only the configured folder.
2. **Is there an import error?** See **Browse → DAGs → <filename>**. `airflow.exceptions.DagFileExists` means a duplicate `dag_id` — and in Airflow 2.x **neither** DAG registers.
3. **Has it re-parsed?** Composer re-parses every 1–3 minutes.
4. **Is it paused?**
5. **Is `schedule=None`?** Manual-trigger only. The course's `branching_and_xcom` DAG is exactly this.
6. **Is `max_active_runs` saturated?**

**Failure story:** a team spent 40 minutes on IAM, bucket permissions, and parse intervals for a DAG that did not appear. The cause was a duplicate `dag_id` — **zero** DAGs where they expected one. Fix: `grep -h 'dag_id=' project/dags/*.py | sort | uniq -c | sort -rn` in CI.

### 16. `schedule=None` vs `schedule="@daily"` vs a Dataset — and what does `catchup` do when a DAG has no schedule?

**`schedule=None` means never scheduled; manual trigger only.** The course's `branching_and_xcom` DAG is `schedule=None` because it is a demo you trigger by hand.

A **Dataset** schedule (Airflow 2.4+) is event-driven: the DAG runs when the producer updates the dataset, not on a clock. That is the right tool for "wait for the data", and it replaces a lot of sensors.

`catchup` only has meaning when there *is* a schedule — with `schedule=None` there are no intervals to catch up on, so `catchup` is inert.

**Failure story:** a "wait for the file" DAG used a sensor with `timeout=3600, poke_interval=300` instead of a Dataset. It held a worker slot for up to an hour every night, and the file arrived at 23:10 — 2 hours *after* the DAG's interval closed, so the data was written into the previous day's partition. Fix: a Dataset, and the producer publishes the dataset *after* the file is complete.

---

## XCom, branching & dynamic tasks (8)

### 17. ⭐ ⭐ What is XCom's storage model, and what follows from it?

**Every push is an `INSERT` into the `xcom` table; every pull is a `SELECT`.** Key: `(dag_id, task_id, run_id, key)`.

Five properties: **durable** (survives the worker and the run), **scoped** to a run, **namespaced by task**, **pickled** (serialise on push, deserialise on pull), and **slow at scale** — it is the same database the scheduler uses.

The rule: **XCom carries the pointer, not the payload.**

| Good XCom | Bad XCom |
|---|---|
| row count (`1245`) | the 1,245 rows |
| partition (`20260115`) | the whole dataset |
| table name | the table contents |
| GCS URI (~40 bytes) | the file |

The 48 KB figure is a **soft limit** — the `xcom.value` column is `BYTEA` (unbounded) in most Airflow 2.x configs. The reason to respect it is that the metadata DB is shared and latency-sensitive.

**Failure story:** a task pushed 1,245 order dicts (~100–200 KB). The shared Cloud SQL doubled write latency for *all* DAGs and the whole team missed their scheduled start times. Fix: write to GCS, push the URI.

### 18. ⭐ Why does Airflow push a task's return value automatically, and what breaks if you rely on it?

**Because TaskFlow's data-passing model is built on it.** Under the hood TaskFlow pushes the return value under `return_value` and pulls it by task id — one storage mechanism for both APIs.

What breaks:

- **It only works for a single value.** A tuple is pushed as one object; `xcom_pull(task_ids=["a","b"])` returns a *list* — easy to confuse.
- **`do_xcom_push=False` suppresses it** — and forgetting that on a big return is how you accidentally write 50 MB to the metadata DB.
- **The push happens even when nobody pulls it.** A task whose return value is ignored still paid the full write cost.
- **In TaskFlow, `multiple_outputs=True` changes the shape** — the dict's keys become separate XCom entries.

**Failure story:** a `PythonOperator` returned a list of 500 order dicts "just to be safe", expecting it to be ignored because the downstream read from BigQuery. It was pickled and inserted. The task took 4 seconds; the insert took 9 and slowed the shared scheduler for 20 minutes. Fix: `do_xcom_push=False`.

### 19. ⭐ `xcom_pull` returned `None`. What are the three causes and the right defensive pattern?

**Three causes, and the defensive pattern is to make the absence explicit rather than to assume it.**

1. **The upstream task was skipped or failed** — its XCom is absent. This is the classic branch bug.
2. **You forgot `task_ids`** — without it, the pull looks in the *current task's own* namespace.
3. **The key is wrong** — `key` defaults to `"return_value"`.

The common defensive pattern:

```python
accepted = ti.xcom_pull(task_ids="transform_orders", key="accepted") or []
```

But `or []` **hides a real bug**: a `None` meaning "upstream failed" becomes "no data", and the pipeline continues green with zero rows. The production form distinguishes them:

```python
accepted = ti.xcom_pull(task_ids="transform_orders", key="accepted")
if accepted is None:
    raise ValueError("transform_orders produced no XCom — skipped or failed")
```

**Failure story:** a join task downstream of a branch pulled `None`, treated it as empty, and published an empty summary. The DAG went green. The dashboard was empty for 5 hours — and the health check was "did the DAG go green", so the outage was invisible.

### 20. ⭐ `BranchOperator` returns a list of task ids. What is skipped, and what does the branch task itself do?

**The branch task succeeds. It does not skip itself. Its *downstream* tasks are the ones skipped.**

The classic bug: a task depending on **both** branches must use `trigger_rule="none_failed"` or `"all_done"`. With the default `all_success`, it is skipped too — because one dependency was skipped. The result is a DAG that looks correct and **quietly does nothing**.

```python
finalise = PythonOperator(
    task_id="finalise",
    dependencies=["full_load", "incremental_load"],
    trigger_rule="none_failed",
)
```

**Failure story:** a branch DAG's join used the default `all_success`. The branch chose `incremental_load` on 180 of 181 days. The join ran **exactly once, in 6 weeks**. The DAG was green every day; the dashboard was empty for 180 days and the daily email went out once. Caught by a stakeholder asking why the dashboard had no data for half a year.

### 21. `ShortCircuitOperator` vs `BranchOperator` — and what does `ignore_downstream_trigger_rules` do?

**`BranchOperator` chooses among paths. `ShortCircuitOperator` has one outcome: skip everything downstream, or nothing.** It returns a boolean — `True` means "succeed and continue normally"; `False` means "mark skipped and skip all downstream".

`ignore_downstream_trigger_rules=True` skips downstream **regardless of their own trigger rules**. Leave it `False` (the default) so a downstream `always` task (cleanup, notification) still runs.

**Failure story:** a team used `ShortCircuitOperator` with `ignore_downstream_trigger_rules=True` to disable a feature subtree behind a flag. The flag was off for 3 days — because the feature was broken — and the team's *error-notification* task was inside that subtree, so **the 3 days of errors were never reported**. Fix: put the notifier outside the subtree and leave `ignore_downstream_trigger_rules=False`.

### 22. ⭐ How does dynamic task mapping work, and when does it beat a loop?

**`.expand()` / `.expand_kwargs()` (Airflow 2.3+) fan a task out over a list known only at run time.** Airflow creates one task instance per item, each with its own `map_index`, each independently retriable and independently observable.

```python
load_region.expand_kwargs(load_tasks(summary, partition))
```

For the course's dataset that is **4 mapped instances** (AMER, APAC, EMEA, LATAM).

A `PythonOperator` with a `for` loop over 500 files has **one** task instance, one retry granularity, one log stream, and no parallelism. A mapped task has 500 instances, each retriable on its own, each visible in the UI, parallel up to `max_active_tasks`.

`.expand()` takes positional args (same-length lists); `.expand_kwargs()` takes a list of dicts.

**Failure story:** a task looped over 1,200 customer files uploading to GCS. It failed at file 900 on a transient 503; the retry restarted at file 1 (900 uploads redone), and the 40-minute task held one worker slot throughout. `.expand_kwargs` gave 1,200 task instances: the retry touched one file, the UI showed which customer failed, and `max_active_tasks=20` cut it to 6 minutes.

### 23. What are the three knobs on a sensor, and what does `soft_fail=True` actually do?

**`timeout`, `poke_interval`, and `mode` — plus `soft_fail`, which changes what a timeout means.**

| Knob | Meaning |
|---|---|
| `timeout` | total budget, computed from the task's **start time** — not the number of pokes |
| `poke_interval` | time between checks; must be < `timeout` |
| `soft_fail` | what happens when the timeout expires |

`soft_fail=True` (the default): the sensor task **succeeds** on timeout and downstream runs normally. `soft_fail=False`: it **fails** and downstream goes `upstream_failed`.

That is exactly right for "wait for yesterday's file; if it never arrives, carry on with what we have", and exactly wrong for "wait for the reconciliation before we close the books".

And the cost that decides sensor design: **a sensor occupies a concurrency slot for its entire lifetime.** 50 sensors waiting an hour consume 50 slots. In `reschedule` mode the worker *process* is released; the slot is not.

**Failure story:** a reconciliation DAG used `soft_fail=True` to wait for the month-end close. The close took 4+ hours, the sensor "succeeded", and the reconciliation ran against a half-closed ledger — a variance report with $4.2M unexplained. Fix: `soft_fail=False`.

### 24. What is `poke` vs `reschedule`, and why is the choice a capacity decision?

**`poke`** keeps the worker occupied and re-invokes the callable every `poke_interval` — fast response, but the slot is held the whole time. **`reschedule`** sets the TI back to `scheduled` with a start time of `now + poke_interval` and **releases the worker** — slower response (up to a scheduler cycle) but the worker is free.

| | `poke` | `reschedule` |
|---|---|---|
| Worker slot | held for the whole wait | held only during each check |
| Detection latency | ~`poke_interval` | `poke_interval` + scheduler delay |
| Best for | short waits (<2–3 min) | long waits |

**Rule: poke for minutes, reschedule for anything longer.** On Composer, reschedule is usually the default, because the worker pool is sized for your DAGs and a pile of poke-mode sensors is the fastest way to hit the concurrency ceiling.

**Failure story:** 12 poke-mode sensors on a 4-worker environment starved every other DAG for 55 minutes, with no errors anywhere in the UI.

---

## Reliability: retries, SLAs & idempotency (9)

### 25. ⭐ ⭐ Define idempotency for an Airflow task and give the test.

**Running it N times produces the same result as running it once.** That is what makes Airflow's retry, backfill, and re-run features safe.

The test: **if this task fails halfway and Airflow retries it in five minutes, what is in the target?** If the answer is "more than before", the task is not idempotent.

| Task | Idempotent? |
|---|---|
| `MERGE INTO ... USING ...` | yes (keyed upsert) |
| `WRITE_TRUNCATE` + partition decorator | yes |
| `WRITE_APPEND` | **no** |
| write to `gs://bucket/{{ ds }}/f.csv` | yes |
| write to `gs://bucket/{{ run_id }}/f.csv` | **no** |
| send an email / post a webhook | **no** |

**Failure story:** a daily ETL used `WRITE_APPEND` with `retries=3`. A BigQuery quota error hit at 92% through the load; the retry appended all 1,245 rows again. The table had **1.9× the correct rows**. Reconciliation by `order_id` worked; the missing piece was a single `writeDisposition`.

### 26. ⭐ ⭐ A retry re-executes your task. What does it *not* undo, and why is that the source of most corruption?

**A retry re-runs the task's code. It does not undo what the task already did.** Airflow does not checkpoint inside your callable; it restarts from the beginning. If your task wrote 800 of 1,000 rows and then failed, the retry writes all 1,000 — the 800 are now duplicated.

```text
attempt 1 ──fail──▶ wait 5 min ──▶ attempt 2 ──fail──▶ wait 5 min ──▶ attempt 3 ──fail──▶ failed
                                                                                         └── downstream: upstream_failed
```

Airflow's contract is **at-least-once**. Every mechanism that causes a double run: `retries`, worker pre-emption, pod eviction, scheduler restart, manual re-run, `airflow tasks clear`, and a backfill overlapping a live run.

**Exactly-once is not achievable** — the side effect (BigQuery) and the state record (the metadata DB) are two systems with no transaction spanning both. **Idempotency is the right goal.**

**Failure story:** a task with `retries=3` and `WRITE_APPEND` hit a quota error at 92%. Two weeks later the monthly revenue report was 14% high because the manual reconciliation for one week was missed on a second, similar failure. Root cause: one missing `writeDisposition`.

### 27. ⭐ What makes "effectively once" true in practice?

**Make the effect itself idempotent, keyed on data rather than on time.** Four mechanisms:

1. **Partition-scoped writes** — `WRITE_TRUNCATE` + a partition decorator from `{{ ds }}`.
2. **Keyed upserts** — `MERGE` on a business key: `dedup_key(order_id, partition)` = `f"{partition}:{order_id}"`.
3. **Deterministic paths** — `gs://bucket/{{ ds }}/f.csv`, never `{{ run_id }}`.
4. **Idempotent notifications** — a GCS marker checked before sending.

**Failure story:** a team added `CURRENT_TIMESTAMP()` "just for debugging". The dedup job keyed on `(order_id, load_ts)` — so a retry produced a *different* key and deduplication silently stopped working. The docstring says it exactly: *"The identity must be derived from the data, never from arrival time."*

### 28. ⭐ What is Airflow's SLA measured against, and what does that mean for a run that starts late?

**From the end of the data interval, not from the start of the run.** For logical date `2026-01-15`, the interval is `[2026-01-15, 2026-01-16)`, so the deadline is `2026-01-16 00:00 + sla`.

```text
sla = 2 hours   →   deadline = 2026-01-16T02:00:00+00:00
actual start  = 2026-01-16T01:30   actual finish = 2026-01-16T01:45
Did it miss the SLA?  NO.
```

A run that starts *late* can still meet its SLA, because the clock starts at the interval end.

**Failure story:** a team set `sla=timedelta(hours=1)` on a DAG that normally ran at 02:30, measuring from the run start. **Every run missed** — deadline computed as 01:00, run finished 02:45. A 100% miss rate with zero business impact. Fix: `sla=timedelta(hours=4)`.

### 29. ⭐ `sla`, `execution_timeout`, `retries`, `retry_delay`, `delay` — what does each bound?

**Five knobs, five different clocks, and mixing them up is the source of most Airflow scheduling confusion.**

| Knob | Bounds | On breach |
|---|---|---|
| `sla` | time from the **interval end** | SLA missed; callback fires; **the task keeps running** |
| `execution_timeout` | wall-clock of the callable | task **fails** with `AirflowTaskTimeout` |
| `retries` | attempts after a failure | — |
| `retry_delay` | wait between attempts | — |
| `delay` | how long before the task may start | task stays `scheduled` |

The interaction people miss: **`execution_timeout` applies per attempt, not per task.** `execution_timeout=30min` + `retries=2` = up to **90 minutes** of worker time plus retry delays.

**Failure story:** a task had a memory leak that made it hit 30 minutes at 95% of the job. Three attempts burned 90 minutes and produced nothing. The team had assumed the timeout was a total budget. Fix: set it to the real expected duration (12 min) so it acts as an alarm, and fix the leak.

### 30. `sla_miss_callback` — why is it not an alerting system?

**It is a hook, called at most once per task per run.** Three reasons it is not alerting: it fires once per task *and* once per DAG for the same incident; it is detected on the scheduler's polling loop so it can be minutes late; and it does not distinguish a backfill run from a live run.

Real alerting needs run type and business impact, so it belongs outside Airflow — the course's `sla_tracker.py` computes a **compliance rate over a window**, not a per-run boolean.

**Failure story:** a team wired `sla_miss_callback` straight to PagerDuty. A 30-day backfill created 30 runs, all finishing long after their deadlines, all firing the callback — **30 pages at 2am for a recovery that was working perfectly**. Fix: exclude `run_type='backfill'` from compliance (a backfill is a recovery, not a fresh miss), and alert from a scheduled job reading the metadata DB.

### 31. What is the difference between an SLA and an SLO, and what is the classic mistake?

**An SLA is a contractual commitment with consequences; an SLO is an internal objective you measure against.** The mistake is setting the SLA equal to the SLO at 100%, then discovering the effort is unbounded and the alert volume is useless.

The measurable version is a **compliance rate over a period** — what `SlaTracker.compliance()` computes. That makes "99.5%" observable rather than aspirational.

**Failure story:** an SLA of "100% of daily reports before 09:00" with alerting on every miss produced 2–3 pages a month, all caused by a genuine upstream dependency. Over 6 months the on-call rotation burned **~120 hours** on 17 misses, 15 of them upstream-caused with no available remedy. Fix: renegotiate to 99.5%, alert on the *rolling 30-day rate*, and page separately when the cause is internal.

### 32. What are the rules for a safe backfill, and what specifically makes one dangerous?

**A backfill re-runs the same logical dates, in a different order, at a different time, possibly while the live schedule is running.** It is the ultimate stress test of idempotency.

The dangerous scenario: the live run fires `2026-01-15` at 02:00; you backfill `2026-01-10..2026-01-14` at 14:00; the backfill's `MERGE` and the live run's `MERGE` interleave.

Six rules: (1) pause the schedule or set `max_active_runs=1`; (2) backfill into the **same partitioned destination**; (3) never backfill into a table the live schedule appends to without a partition scope; (4) `depends_on_past=False` unless the pipeline accumulates state; (5) keep `max_active_runs` low enough not to starve the live schedule; (6) know your idempotency story first.

**Failure story:** a 30-day backfill into an unpartitioned table with `WRITE_APPEND`, while the live schedule ran. Every day loaded twice and the live run overwrote the backfill's row for the current date. The table ended at ~1.9× the correct row count with no way to identify which copy was authoritative. Recovery: a full rebuild — 3 days.

### 33. ⭐ What are the four requirements for a re-runnable DAG?

**Clearing and re-running any task must produce the same final state — four requirements get you there.**

1. **Every write is scoped to a deterministic destination** — partitions, not appends.
2. **Every read filter matches the half-open data interval exactly.**
3. **Intermediate state is either absent or reset** — a staging table must be scoped to the run, or a retry reads yesterday's staging mixed with today's.
4. **No external side effects that are not idempotent** — emails, webhooks, PagerDuty, Slack need a dedup key.

Plus: the output row count is checked against an expected value, and a backfill of any range produces the same result as 30 sequential runs.

**Failure story:** a team cleared and re-ran a single task from the UI — the "just re-run this one" operation the runbook called safe. The task appended to an unpartitioned table, so the day was duplicated. The assumption was embedded in the runbook, not just the code. The whole checklist went into the DAG review template afterwards.

---

## Production: testing, cost, security & troubleshooting (9)

### 34. ⭐ What are the three layers of Airflow testing, and why do teams get the ratio wrong?

**Three layers with wildly different cost-to-value ratios, and most teams spend the budget on the wrong one.**

```text
Layer 1 — Pure logic    : "Is the transformation correct?"  pytest, no Airflow, <1s, catches 90% of bugs
Layer 2 — DAG structure : "Is the graph wired as I intended?"  Airflow installed, ~5s
Layer 3 — Integration   : "Does it work against real GCS/BQ?"  GCP project, credentials, money, minutes
```

The dominant mistake is spending the budget on Layer 3 and discovering that a `>` should have been a `>=`.

The course's architecture is the fix: `project/core/pipeline_logic.py` imports nothing from Airflow, so `pytest` runs it in milliseconds. The DAG file is thin.

**Failure story:** a team had a nightly "test DAG" running the real pipeline against real BigQuery and it caught nothing useful for 8 months — the logic was correct and the *wiring* was wrong in the same way the live DAG was. A task rename broke a downstream XCom pull and the nightly test broke identically. Fix: Layer 2 structure tests, 5 seconds each.

### 35. ⭐ What should a DAG structure test assert, and what is the single most valuable assertion?

**Assert things about the graph, not about behaviour — and the exact task-set comparison is the one that catches the most.**

| Assertion | Catches |
|---|---|
| `set(dag.task_ids) == {...}` | **the whole-task-set guard** — catches deletions *and* additions |
| `dag.catchup is False` | catchup turned on accidentally |
| `dag.get_task("x").trigger_rule == "none_failed"` | a join point lost its trigger rule |
| `dag.get_task("load").retries == 3` | a retry policy lost in a copy-paste |
| `dag.task_dict["aggregate"].upstream_task_ids == {...}` | a dependency changed by accident |
| `isinstance(dag.get_task("load"), BigQueryInsertJobOperator)` | someone swapped the operator for a no-op |

The most valuable *overall* check is **`bag.import_errors`**: a DAG that fails to import appears in `bag.import_errors`, not `bag.dags`. Checking only "does the DAG exist" turns an import error into a confusing "DAG not found".

**Failure story:** a merge conflict set `catchup=True`. Nobody noticed for 3 weeks, because catchup only matters when there is a schedule gap — and there was not. Then an 11-day environment outage meant the scheduler created **11 extra runs** that overwrote 3 days of corrected data with the original logic. One CI line would have caught it.

### 36. What are `dag.test()` and `dag.run()`, and what is the surprise?

**`dag.test()` (Airflow 2.5+) runs a DAG's tasks locally, in the current process, in dependency order, with no scheduler or worker.** `dag.run()` runs a range of logical dates — `dag.test()` over a date range, which is why it exists (to run a backfill locally).

**The surprise: `dag.test()` executes the *real* operators.** A `BigQueryInsertJobOperator` will attempt a **real BigQuery load**. It is a local executor, not a mock.

```python
dag.test(execution_date=timezone.datetime(2026, 1, 15))  # 2.5–2.9 name
```

**Failure story:** a developer ran `dag.test()` on a DAG with `BigQueryInsertJobOperator` pointed at production and `WRITE_APPEND`. The test loaded 1,245 rows into production for `2026-01-15`; the live run appended them again. The table had **2,490 rows** for that day, and recovery required deleting by `load_ts` because there was no partition decorator. New rule: **`dag.test()` only against a dev project**, enforced by a `params`-driven `target_dataset` defaulting to a `dev_` prefix.

### 37. ⭐ A nightly DAG "succeeded" but the dashboard was empty. What monitoring signals do you actually need?

**Five signals, and the fifth is the one people forget.**

Five, and the fifth is the one people forget:

1. **DAG run state** — the baseline.
2. **SLA compliance rate over a window**, not per-run booleans.
3. **Output row counts / volume vs an expectation** — this is the signal that catches "green but empty".
4. **Task duration vs a baseline** — 4 minutes → 40 minutes is a signal even when it succeeds.
5. **The scheduler heartbeat** — a stalled scheduler means no new runs are created, which looks *identical* to "the DAG is not scheduled".

The empty-dashboard case is exactly what signal 3 exists for: the run was green because the load found an empty upstream file and loaded 0 rows — a legitimate outcome for the code, given the input.

**Failure story:** 3 days of missing data, invisible, because the health check was "did the DAG go green". Fix: a row-count assertion plus a volume metric with an expected range. Signal 3 caught in 4 minutes what signal 1 could not catch at all.

### 38. ⭐ A Composer environment costs $700/month. Is that too expensive?

**Compare the fixed environment cost against the job cost it enables — and check whether the DAGs need Airflow at all.**

| Approach | Cost/mo (approx) | Latency |
|---|---|---|
| Airflow + BigQuery scheduled query | **$150 – $300** | 2–5 min |
| Airflow + BigQuery partitioned (~30 GB/day scanned) | **$50 – $100** | 2–5 min |
| Airflow + Dataflow batch job | $300 – $800 | 10–30 min |
| Airflow + Spark on Dataproc | $400 – $1,200 | 15–45 min |
| Airflow + a PythonOperator doing it all | $30 – $60 | 40 min |
| The same at 10 TB/mo | **$500+**, plus a redesign | 6 hours |

**Sizing rule:** *if your DAG is mostly issuing queries, size the environment small* — the query runs server-side. *If it is mostly running Python, size it for the concurrency you need.*

The trap is the last two rows: the Airflow+Python row is cheap only while the data is small. At 10 TB/month it becomes 6 hours a night on one worker, with no parallelism, no checkpointing, and a retry that costs 6 hours.

**Failure story:** 40 scheduled queries plus 2 genuinely dependent DAGs on a 6-worker environment, $700/month. Moving 11 queries to BigQuery scheduled queries and dropping to 2 workers brought it to $280/month. Then they moved a *dependent* DAG too and broke the dependency. Correct split: dependencies → Airflow; everything else → scheduled queries.

### 39. ⭐ Variable vs param vs Connection — the decision procedure and the security consequence.

**Variable = differs per environment. param = differs per run. Connection = holds credentials.**

```text
Is it a credential?  → Connection. Always.
Does it differ per RUN?  → param
Does it differ per ENVIRONMENT?  → Variable
Neither?  → a constant in dag_config.py
```

| | Storage | Encrypted? | In UI? | In run history forever? |
|---|---|---|---|---|
| Variable | metadata DB | **no — plaintext** | yes | no |
| param | `dag_run.conf` | no | yes | **yes** |
| Connection `password` | metadata DB | **yes** (Fernet) | masked | no |
| Connection `extra` | metadata DB | **no** in Airflow 2.x | yes | no |

Only `password` is encrypted. Do not put a private key in `extra`; use the environment's attached service account.

**Failure story:** a team stored a service-account JSON key in a Variable named `gcp_key`. The Variable list page showed the full private key to every engineer with UI access; it was in the metadata DB in the clear, and in the DB's GCS backups. Rotating it took a week of coordinated work. Fix: the attached service account, so no credential material exists in Airflow at all.

### 40. ⭐ Why does Airflow guarantee at-least-once rather than exactly-once?

**Because the side effect and the state record live in two different systems with no transaction spanning both.** The metadata DB records "task succeeded"; BigQuery records "rows written". Nothing makes those facts atomic.

So Airflow's contract is: *a task instance may execute more than once; your task must tolerate that.* And "tolerate that" means **idempotency**.

```text
exactly-once:  "the side effect happened one time, guaranteed"   ← not achievable
idempotent:    "if the side effect happened three times, the result
                 is indistinguishable from it happening once"    ← achievable, sufficient
```

**Failure story:** a team added an at-least-once "safety net" — a downstream job that deduplicated on `(order_id, load_ts)` because the source could re-deliver. When a retry produced the same rows with a *different* `load_ts`, the dedup key did not match and both copies survived. The correct key was data-derived: `f"{partition}:{order_id}"`.

### 41. A Composer environment is shared by 14 DAGs from 4 teams. What is the security model?

**Composer 2.x uses IAM-based access control** instead of Airflow's own RBAC (Composer 3 adds built-in RBAC). Consequence: **there is no in-Airflow permission boundary between teams** unless you use Composer 3's RBAC or separate environments. So IAM is the boundary:

| Role | Grants |
|---|---|
| `roles/composer.user` | view the UI, browse DAGs, view logs |
| `roles/composer.worker` | run tasks against GCP resources |
| `roles/composer.admin` | edit config, delete the environment |
| Environment **service agent** | the identity the environment runs as |

**The service account's permissions are the environment's real blast radius.** Project-wide `roles/bigquery.dataEditor` on the service agent means every DAG — including an experimental one — can write to every table.

**Failure story:** a data-science team's experimental DAG truncated the production revenue table (`WRITE_TRUNCATE`, no partition decorator) because the Composer service agent had project-wide BigQuery data-editor access, granted early on for convenience. Recovery: 5 hours and a full 90-day rebuild. Fix: per-dataset IAM, plus a structure test asserting every `BigQueryInsertJobOperator` has a partition decorator.

### 42. A task is queued and never starts. What are the causes and how do you tell them apart?

**Five causes, and the distinguishing evidence is in the UI and the metadata DB, not in the DAG file.**

| Cause | Evidence |
|---|---|
| No worker available | other tasks are also queued; the pool is exhausted |
| Concurrency limit | `max_active_tasks` or environment `parallelism` reached |
| Dependencies not met | an upstream is still `running`/`queued` — look **upstream** |
| Trigger rule | an upstream was `skipped` and this task uses `all_success` |
| Scheduler stalled | no new runs for *any* DAG; check the heartbeat |

The most confusing is the **trigger rule**, because the task looks right. The course's runner prints it:

```text
✗ extract          failed
⊘ transform        upstream_failed
⊘ load             upstream_failed
```

`failed` = ran and raised (may have written partial data). `upstream_failed` = never ran. Conflating them produces false "task failed" pages for tasks that never started.

**Failure story:** a final task appeared "queued" in the UI for hours. Its upstream branch had chosen the *other* path, so the chosen path was `skipped`, and the final task used the default `all_success` — so it was skipped too. In a list view, skipped and queued look similar. The team spent 3 hours investigating worker capacity. Fix: `none_failed` on the join, and a dashboard that distinguishes `skipped` from `queued`.

---

## Composer on GCP (8)

### 43. What happens when you delete a Composer environment, and what do you take with you first?

**Destroyed:** the Composer-managed **DAG bucket and every DAG file in it**, the web server, scheduler, workers, and the environment's metadata DB (the Cloud SQL instance Composer created for it).

**Survives:** your BigQuery tables and datasets, your other GCS buckets, and **your code if it is in Git**.

The safe pattern: **your DAGs live in Git; the Composer bucket is a deployment target.** Then deleting an environment is a non-event and "what was running last Tuesday?" is answered by `git log`.

Before deleting, take: (1) a DAG export or Git confirmation; (2) `airflow connections list` and `airflow variables list` — they live in the metadata DB and go with it; (3) `gcloud composer environments describe` for the image version and size, so you can recreate it identically.

**Failure story:** a team deleted an environment during cost cutting and lost every DAG — they had been editing files in the Composer UI's DAG editor, which exists, is convenient, and is a trap. Two months later they rewrote 34 DAG files from screenshots. Fix: a mandatory "no DAG edits in the UI" policy and Git from day one.

### 44. ⭐ How do you size a Composer environment, and what does the size control?

**The worker pool and the Cloud SQL instance shape** — the two things that scale with your workload. Small = 1–2 workers (a few light DAGs, mostly BigQuery queries); Medium = 3–6; Large = 7–15; Custom = your numbers.

**Sizing rule:** *mostly issuing queries → size small* (the query runs server-side; the worker only issues it). *Mostly running Python → size for the concurrency you need.*

The other effect: the size and the environment-wide `parallelism` together set the **concurrency ceiling** — which is why a DAG with 50 poke-mode sensors can starve a DAG with 3 tasks. **Worker sizing is per-environment, not per-DAG.**

**Failure story:** an environment sized Large (12 workers) because two DAGs had heavy Python tasks. After migrating 30 of 40 workflows to BigQuery scheduled queries, the environment was idle 22 hours a day and still costing $900/month. Dropping to Small (2 workers) → $280/month, with the two heavy DAGs still fitting because they ran sequentially at 02:00.

### 45. What are the Composer image versions, and why is a version bump the most dangerous operation?

**An image version pins both the Composer version and the Airflow version** — `composer-2.9.3-airflow-2.9.3`. Composer 2 environments pin Airflow 2.x releases (2.8.2, 2.9.3, 2.10.x); Composer 3 is the newer GKE-based generation.

Breaking changes to check before upgrading:

| Change | Version |
|---|---|
| `schedule_interval` → `schedule` | 2.4 (removed in Airflow 3) |
| `execution_date` → `logical_date` | 2.2 |
| Datasets replace data-aware scheduling | 2.4 |
| `DummyOperator` deprecated → use `EmptyOperator` | 2.x, removed in 3 |
| `GCSOperator` renamed | 2.x |
| `SubDagOperator` removed | 2.0 |
| `extra` **not** encrypted | 2.x |

**This is what Environment Versioning is for:** clone the environment, bump the copy, test there, then promote.

**Failure story:** a team upgraded a production environment from Airflow 2.6.3 to 2.8.2 in place on a Friday with 40 DAGs. Two broke; one failed to import and **vanished from the UI** — and nothing alerted on "DAG count decreased". Four days unnoticed. Fix: clone-then-promote, and make the DAG count itself an alert.

### 46. What is the `airflow` CLI inside Composer for, and what should you *not* do with it?

**It is the same Airflow CLI you would use on a self-managed install**, reached via `gcloud composer environments run <env> --command "..."`.

Useful: `airflow dags list-import-errors` (the `import_error` table), `airflow dags backfill -s ... -e ...`, `airflow dags trigger --conf '...'`, `airflow dags test`, `airflow tasks states-for-dag-run`, `airflow connections list`, `airflow variables list`.

**What it is not:** a deployment mechanism. Do not use `airflow dags deploy` — in Composer, deployment is uploading to the DAG bucket. And **`airflow dags test` runs the real operators** against real GCP, so it writes real data.

**Failure story:** a team ran `airflow dags test etl_orders_to_bigquery 2026-01-15` inside a Composer environment pointed at production. `WRITE_APPEND`, no partition decorator → 1,245 production rows written for a date the live pipeline was about to process, then appended again. Fix: a `params`-driven `target_dataset` defaulting to a `dev_` prefix.

### 47. ⭐ When is Airflow the wrong answer entirely, and what do you use instead?

**When the pipeline needs no dependency management.** A BigQuery scheduled query runs on a schedule, writes to a destination table, and emails on failure — inside BigQuery, with BigQuery's SLA, no environment to size, no IAM to manage.

Use a scheduled query when: the job is **one SQL statement**; there are **no cross-DAG dependencies**; the failure handling you need is **"email me"**; or the environment cost exceeds the savings.

Use Airflow when: the job depends on another DAG; you need retries with backoff and alerting; there is an SLA to track; there are more than a handful of steps; or you need XCom / dynamic fan-out.

The decision tree is ordered by **need for coordination first**, because that is what Airflow uniquely provides:

```text
Does it need to coordinate with other pipelines?
├── NO → Is it a single SQL statement?
│         ├── YES → BigQuery scheduled query. Stop here.
│         └── NO  → Airflow + BigQuery operator, or a Dataflow job.
└── YES → Does it need batch AND stream with the same code?
          ├── YES → Airflow (orchestration) + Beam (processing)
          └── NO  → Is the transformation heavy?
                    ├── YES → Airflow + Spark/Dataproc, or Beam on Dataflow
                    └── NO  → Airflow + BigQuery, or Airflow + a Python task
```

**Failure story:** a team had one Composer environment for 40 workflows, 11 of which had no dependencies at all. Moving those 11 to scheduled queries cut the bill from $700 to $280/month — and then the team moved a *genuinely dependent* DAG too and broke the dependency. The split is not "big vs small", it is "dependent vs independent".

### 48. ⭐ Composer or self-managed Airflow on Kubernetes?

**Composer unless you have a specific requirement it cannot meet.**

Composer wins on: time to first DAG (minutes, not days), no cluster to operate, autoscaling workers, IAM-native access, Environment Versioning for safe Airflow upgrades, and GCP-native operators.

Self-managed wins on: a specific Airflow version or an unpackaged provider, unusual networking (private ranges Composer cannot use, VPC-SC constraints), a per-task resource shape Composer does not offer, or full control of the metadata DB and DAG storage.

**The pragmatic recommendation:** *if your tasks are ordinary — queries, API calls, moderate Python — use Composer with the default executor.* The KubernetesExecutor's benefits are real but usually not worth the ~45 s startup tax at typical task durations. Composer's default CeleryExecutor has **no startup tax**.

**Failure story:** a team moved 60 DAGs to Composer and hit two problems *after* the migration. One DAG needed a custom provider image Composer could not package; a compliance requirement mandated the metadata DB in a specific region with CMEK, which the Composer-managed instance could not do. Both were knowable *before* migrating. Lesson: **check provider availability, network placement, and encryption before you migrate.**

### 49. ⭐ Airflow as a processing engine: what are the five things that break, and what is the one-line test?

**The five things:** no parallelism (one task = one process); no autoscaling (fixed worker shape); catastrophic retries (a failure at minute 35 of 40 restarts from 0, so `retries=2` costs 120 minutes); no checkpointing (a crash at minute 39 loses 39 minutes); and a worker slot held for the whole run. Plus: the logic is untestable because it lives in a DAG file.

**The one-line test:** *if the task takes more than a few minutes, or holds more than a few hundred megabytes, it belongs in a processing engine.*

Instead of: a Python task processing 2B rows → a BigQuery query. A Python task doing heavy joins → BigQuery or Dataflow/Spark. A Python task looping over files → `SparkSubmitOperator` / `DataflowCreateJobOperator`, or dynamic task mapping. A Python task holding a big intermediate → write to GCS/BigQuery, pass the *reference* through XCom.

**Failure story:** a team moved a 2-billion-row join into a `PythonOperator`. The task OOMed at 8 GB, retried twice, failed after 90 minutes with `MemoryError`. The fix was a BigQuery query: **4 minutes and $3** instead of 3 hours of a worker.

### 50. ⭐ What are the five things to check when you are asked "did yesterday's data land correctly"?

**The complete answer to the 3am question, in order:**

The complete answer to the 3am question, in order:

1. **Did the run exist?** Check `dag_run` for the logical date and its `run_type` (`scheduled__` vs `backfill__` vs `manual__`).
2. **Did it succeed?** Check the *task instance* states, and distinguish `failed` (ran and raised) from `upstream_failed` (never ran) from `skipped`.
3. **Did it write the right rows?** Check the **row count and value** against an expectation — not just the state. This is the step that catches "green but empty".
4. **Did it write to the right destination?** Confirm the partition or path came from `{{ ds }}`/`data_interval_start`, not `{{ run_id }}` or `now()`.
5. **Did it meet the deadline?** The SLA deadline is `data_interval_end + sla` — and backfill runs should be excluded from compliance.

**The mechanism that makes this one lookup rather than a forensic investigation:** Airflow records the logical date on the run, the task instances, every log line, every XCom, and every rendered template. The logical date is the primary key of "which run am I talking about".

**Failure story:** a DAG went green for 3 days while loading 0 rows, and the health check was "did the DAG go green". Steps 3 and 5 of this list are what were missing — and step 3 is a *value* check, not a *state* check.

---

## Related material

- The module files — [01](01-orchestration-fundamentals.md) · [02](02-dags-scheduling-and-templates.md) · [03](03-tasks-xcom-and-branching.md) · [04](04-reliability-and-production.md) · [05](05-composer-and-gcp.md)
- The study plan — [README.md](README.md)
- The chapters — [../chapters/](../chapters/)
- The runnable project — [../project/](../project/)
