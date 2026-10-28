# Module 4 — Reliability & Production

> **16 questions · Module 4 · SLAs, retries, idempotency, backfills, testing, monitoring, cost, security, troubleshooting**

Every question in this module is about what happens **after** the DAG file is written: the run is late, the task failed, the retry corrupted the table, the environment is too expensive, the DAG will not parse. These are the questions that separate someone who has *read* about Airflow from someone who has been paged for it.

---

## SLAs and timeliness

### 1. Airflow gives you five timing knobs. Name them, and say what each one actually bounds.

**`sla`, `execution_timeout`, `retries`, `retry_delay`, `delay`.** Nearly every Airflow confusion in this area comes from mixing them up.

| Knob | Scope | What it bounds | What happens when exceeded |
|---|---|---|---|
| **`sla`** | task or DAG | time from the **reference point** | SLA is **missed**; a callback fires; **the task keeps running** |
| **`execution_timeout`** | task | wall-clock time of the callable | the task **fails** with `AirflowTaskTimeout` |
| **`retries`** | task | how many attempts after a failure | — |
| **`retry_delay`** | task | how long between attempts | — |
| **`delay`** | task | how long before the task may start | the task stays `scheduled` |

`execution_timeout` is a **resource guard** — it stops a task hanging forever and holding a worker slot. `sla` is about **business timeliness**. `delay` exists for exactly one reason: staggering load on a downstream system so five DAGs all firing at 02:00 do not create a thundering herd.

The interaction people miss: **`execution_timeout` applies per attempt, not to the task as a whole.** A task with `execution_timeout=30min` and `retries=2` can occupy a worker for up to **90 minutes** plus two retry delays. That is a real cost trap.

```python
load = BigQueryInsertJobOperator(
    task_id="load_to_bigquery",
    execution_timeout=timedelta(minutes=30),
)
# failure: airflow.exceptions.AirflowTaskTimeout: Task timed out after 0:30:00
```

**The failure story:** a task had `execution_timeout=30min` and `retries=2`. It had a memory leak that made it hit 30 minutes at ~95% of the job. So each attempt burned 30 minutes, and three attempts burned 90 minutes of a worker plus 10 minutes of retry delays — while producing nothing. The team had assumed the timeout was a total budget. The fix: `execution_timeout` set to the *real* expected duration (12 minutes) and the leak fixed; the timeout then acted as an alarm rather than a schedule.

### 2. Airflow's SLA is measured against something surprising. What is it, and what does that mean for a run that starts late?

**It is measured from the end of the data interval, not from the start of the DAG run.** This is the detail that trips everyone up.

For a daily DAG with a logical date of `2026-01-15`, the data interval is `[2026-01-15, 2026-01-16)`. The SLA deadline is `2026-01-16 00:00` **plus the SLA duration**. It is not measured from when the task happened to start.

```text
DAG: etl_orders_to_bigquery
  data interval : [2026-01-15T00:00:00+00:00, 2026-01-16T00:00:00+00:00)
  sla           : 2 hours
  deadline      : 2026-01-16T02:00:00+00:00
  actual start  : 2026-01-16T01:30:00+00:00   ← the run started LATE
  actual finish : 2026-01-16T01:45:00+00:00

  Did it miss the SLA?  NO.
  Why? 15 minutes of headroom remained against the 02:00 deadline.
```

This is exactly what the course's `03_etl_bigquery.py` documents:

```python
#: The SLA is measured from the **end of the data interval**, not from the
#: wall-clock start of the run. A 02:00 run whose interval ended at 00:00
#: has two hours of SLA headroom, regardless of when it actually started.
DAG_SLA = timedelta(hours=2)
```

The course's pure helper makes it testable:

```python
from sla_logic import sla_deadline, sla_met

sla_deadline("2026-01-15", timedelta(hours=2))
# 2026-01-16 02:00:00+00:00
```

**The failure story:** a team configured `sla=timedelta(hours=1)` on a DAG that normally ran at 02:30, because they measured the SLA against the run's start time. Every single run "missed its SLA" — because the deadline was computed as `interval_end + 1h` = 01:00, and the run finished at 02:45. 100% SLA miss rate, zero actual business impact. The fix was `sla=timedelta(hours=4)`, giving a deadline of 04:00, and then the metric became meaningful enough to alert on.

### 3. What is `sla_miss_callback` for, and why is it *not* an alerting system?

**It is a hook Airflow calls when the SLA is missed — it is not a notification system.** It receives the task context and is typically used to log, to write a marker, or to call out to something else.

```python
def on_sla_miss(context, **kwargs) -> None:
    log.error("DAG %s missed its SLA at %s", context["dag"].dag_id, context["logical_date"])
    log.error("downstream data may be late; alert the owner")
```

Three reasons it is not an alerting system:

1. **It fires at most once per task per run.** A DAG with a task-level SLA and a DAG-level SLA fires twice for the same incident.
2. **It is measured on the scheduler's polling loop.** A miss is detected on the next scheduler cycle, so the callback can be minutes late.
3. **It does not distinguish severity.** An SLA miss on a backfill run and an SLA miss on a live run are the same event to Airflow.

Real alerting needs to know the *run type* and the *business impact*, so it belongs outside Airflow. The course's `sla_tracker.py` shows the shape of the thing you build outside Airflow:

```python
tracker = SlaTracker(sla=timedelta(hours=2))
tracker.record("2026-01-15", finished_at)
tracker.compliance()   # a fraction, computed over a period
tracker.report()
```

**The failure story:** a team wired `sla_miss_callback` straight to PagerDuty. On the first deployment, a 30-day backfill created 30 backfill runs, all of which finished long after their original deadlines, so all 30 fired the callback — 30 PagerDuty pages at 2am for a recovery that was working perfectly. The fix was two-fold: exclude `backfill__` run types from the compliance metric (as the course's chapter says: *a backfill is a recovery, not a fresh miss*), and route the callback to a log line while the real alerting came from a scheduled job that read the metadata DB.

### 4. What is the difference between an SLA and an SLO, and what is the mistake teams make by treating them as the same?

**An SLA is a contractual commitment with consequences. An SLO is an internal objective you measure against.** The mistake is setting the SLA equal to the SLO — usually at 100% — and then discovering that the engineering effort to hit 100% is unbounded and the alert volume is useless.

The practical structure:

| | SLA | SLO |
|---|---|---|
| Audience | the customer / the business | you |
| Number | e.g. "daily orders ready by 06:00, 99.5%" | e.g. "99.9% of daily runs meet their deadline" |
| Consequence | credits, escalation, a phone call | a ticket, a metric, a backlog item |
| Failure handling | page | investigate |

The measurable version is what the course's `SlaTracker` computes: a **compliance rate over a period**, not a boolean. `compliance()` returns a fraction; `report()` prints runs recorded, on time, missed, and the percentage. The point of computing it over a window is that it makes "99.5%" an observable number rather than an aspiration.

**The failure story:** a team set an SLA of "100% of daily reports delivered before 09:00" and alerted on every miss. There were 2–3 misses a month — all caused by a genuine upstream dependency being late, not by anything the team could fix. Each miss was a 3am page, and each page generated a full incident review. Over 6 months the on-call rotation burned **~120 hours** investigating 17 misses, 15 of which were upstream-caused and none of which had a real remedy. The fix was to renegotiate the SLA to 99.5%, alert only on the *rate* breaching 99.5% over a rolling 30 days, and to page separately when the *cause* is in our own systems.

---

## Retries and idempotency

### 5. Define "idempotent" for an Airflow task, and give me the test to apply to any task before you enable retries on it.

**A task is idempotent if running it N times produces the same result as running it once.** That is the whole definition, and it is the property that makes Airflow's retry, backfill, and re-run features safe.

For HTTP, idempotency is about the verb. For an Airflow task, it is about whatever side effect the task's code performs.

| Task | Idempotent? | Why |
|---|---|---|
| `SELECT count(*) FROM raw.orders` | yes | reads only |
| `INSERT INTO orders_enriched SELECT ...` | **no** | a second run adds the rows again |
| `MERGE INTO orders_enriched USING ...` | yes | keyed upsert; second run is a no-op |
| `CREATE OR REPLACE TABLE summary AS SELECT ...` | yes | replaces |
| `BigQueryInsertJobOperator` with `WRITE_TRUNCATE` + partition decorator | yes | replaces the same partition |
| `BigQueryInsertJobOperator` with `WRITE_APPEND` | **no** | appends again |
| Writing to `gs://bucket/{{ ds }}/summary.csv` | yes | same path, overwritten |
| Writing to `gs://bucket/{{ run_id }}/summary.csv` | **no** | new path each time |
| `ti.xcom_push(key="count", value=n)` | yes | same key, overwritten |
| Sending an email | **no** | a second run sends a second email |
| Posting to a webhook | **no** | same |

**The test:** *if this task fails halfway and Airflow retries it in five minutes, what is in the target?* If the answer is "more than before", the task is not idempotent and you have a bug waiting for a bad day.

**The failure story:** a daily ETL loaded yesterday's orders into BigQuery with `writeDisposition: "WRITE_APPEND"` and `retries=3`. On a partial failure the retry re-appended the rows already written. The revenue table for that day had **1.9× the correct rows**. The fix was `WRITE_TRUNCATE` with a partition decorator, which is what the course's `03_etl_bigquery.py` uses — and the course's `dedup_key(order_id, partition)` gives the alternative for non-partitioned tables.

### 6. A retry re-executes your task. What does it *not* undo, and why is that the source of most Airflow corruption?

**A retry re-executes the task's code. It does not undo what the task already did.** Airflow does not checkpoint inside your callable; it does not resume a partially-completed function. Each attempt starts from the beginning.

```text
attempt 1 ──fail──▶ wait 5 min ──▶ attempt 2 ──fail──▶ wait 5 min ──▶ attempt 3 ──fail──▶ task failed
                                                                                                   │
                                                                                    downstream: upstream_failed
```

So if your task wrote 800 of 1,000 rows to BigQuery and then failed, the retry writes all 1,000 rows again. Those 800 are now duplicated — unless the write is idempotent.

This is why `retries` is simultaneously the most valuable and the most dangerous parameter in Airflow: it turns transient failures into successes, and it turns non-idempotent tasks into corruption engines.

The formal model is **at-least-once execution**, and every mechanism that can cause a task to run twice is worth knowing:

| Mechanism | Why it runs twice |
|---|---|
| `retries` | the first attempt failed *after* the side effect but before the result was recorded |
| Worker pre-emption | the worker died mid-task; the task is requeued |
| KubernetesExecutor pod eviction | the pod was evicted; a new pod re-runs the task |
| Scheduler restart | the task was queued but the "running" state was lost |
| Manual re-run of a task | obviously |
| `airflow tasks clear` + re-run | obviously |
| Backfill overlapping a live run | two runs of the same logical date |

**The critical honesty about exactly-once:** it is not achievable in general, because the side effect (a BigQuery load) and the state record (the Airflow metadata DB) are two different systems with no transaction spanning both. You can get "effectively once" with an idempotent write; you cannot get "literally once" without a distributed transaction.

> **Exactly-once is the wrong goal. Idempotency is the right one.**

**The failure story:** a team set `retries=3` on a DAG whose load task used `WRITE_APPEND`. A BigQuery quota error occurred at 92% through the load. The retry appended all 1,245 rows again. The team reconciled it by running a `DELETE` on the duplicate `order_id`s — but a *second* failure occurred the same week on a different DAG, and the reconciliation was missed. Two weeks later the monthly revenue report was 14% high. The root cause was a single missing `writeDisposition`.

### 7. Why does Airflow guarantee at-least-once rather than exactly-once, and what design makes "effectively once" true?

**Because the side effect and the state record live in two different systems with no transaction spanning them.** The metadata DB records "task succeeded"; BigQuery records "rows written". Nothing makes those two facts atomic.

The mechanisms that cause a double execution are all *environmental* — worker death, pod eviction, scheduler restart, an operator clearing a task — and no amount of Airflow configuration eliminates them. Airflow's contract is: *a task instance may execute more than once; your task must tolerate that.*

The design that makes "effectively once" true is to make the **effect itself idempotent**, keyed on data rather than on time:

1. **Partition-scoped writes.** `WRITE_TRUNCATE` with a partition decorator derived from `{{ ds }}`. A retry replaces the partition instead of appending to it.
2. **Keyed upserts.** `MERGE` on a business key — `dedup_key(order_id, partition)` = `f"{partition}:{order_id}"`.
3. **Deterministic paths.** `gs://bucket/{{ ds }}/file.csv`, never `gs://bucket/{{ run_id }}/file.csv`.
4. **Idempotent notifications.** A GCS marker object checked before sending, so a retry does not re-send.

The course's `dedup_load.py` shows the keyed version:

```python
def dedup_rows(rows, partition):
    seen = {}
    order = []
    for row in rows:
        key = dedup_key(str(row.get("order_id", "")), partition)
        if key not in seen:
            order.append(key)
        seen[key] = dict(row)
    return [seen[key] for key in order]
```

**The failure story:** a team added a `CURRENT_TIMESTAMP()` column to their load table, "just for debugging". The row's *business* key was still `order_id`, but the dedup job keyed on `(order_id, load_ts)` — so a retry produced a *different* key and the deduplication silently stopped working. The fix was to key on data-derived identity only: `dedup_key(order_id, partition)`. The docstring says it precisely: *"The identity must be derived from the data, never from arrival time. A load-time timestamp would make a retry produce different rows rather than the same rows, which defeats deduplication entirely."*

### 8. `depends_on_past=True` — what does it actually guarantee, and when does it hurt?

**It guarantees that a task instance will not run until the previous run of the same DAG (by logical date) has reached a successful state for that task.** It orders runs *within* one DAG's history.

**What it does not guarantee:**

- It does not make a task idempotent.
- It does not prevent a *backfill* from racing a *live* run — both have the same logical dates, and `depends_on_past` only orders runs by logical date within the DAG's own history.
- It does not survive a task that is `cleared` and re-run.
- It does not protect against a run being re-triggered manually.

**Where it hurts:** a daily batch that reads an independent slice of data. For that, `depends_on_past=False` (the course's default) is correct, because it allows a backfill to run 30 days in parallel instead of serially.

**Where it helps:** a pipeline that genuinely accumulates state — a cumulative table, a running model, a "snapshot the previous day" task.

**The dangerous combination:** `depends_on_past=True` on a task that *appends* to a cumulative table. A retry of day N re-appends day N's rows, and day N+1 (waiting on it) proceeds happily. The pipeline "works" and the table is corrupt.

The interaction with `max_active_runs` matters too: with `depends_on_past=True` and `max_active_runs=1`, runs are serialised by construction. With `max_active_runs=5`, five days can be in flight, and `depends_on_past` orders them.

**The failure story:** a cumulative revenue table used `depends_on_past=True` and `WRITE_APPEND`. Day 14's load failed transiently at 60%, retried, and appended the full day's rows — so the table had 1.4× day 14's revenue. Day 15 waited for day 14, saw it succeed, and appended normally. The error propagated forward: every cumulative total from day 14 onward was inflated, and there was no way to tell from the table which days were wrong. The fix was `MERGE` on a deterministic key, and `depends_on_past=False` with partition-scoped writes.

---

## Backfills

### 9. Walk me through how to run a safe backfill, and what specifically makes a backfill dangerous?

**A backfill re-runs the same logical dates, in a different order, at a different time, possibly while the live schedule is also running.** It is the ultimate stress test of idempotency.

The dangerous scenario:

```text
Live schedule fires the 2026-01-15 run at 02:00.
You backfill 2026-01-10 .. 2026-01-14 at 14:00.
The backfill's last day writes to the same partition the live run just wrote.
Or: the backfill's MERGE and the live run's MERGE interleave.
```

**The rules for a safe backfill:**

1. **Turn off the schedule while backfilling**, or set `max_active_runs=1` on the backfill and confirm the live run has finished.
2. **Backfill into the same partitioned destination.** Then `WRITE_TRUNCATE` per partition means each backfilled day replaces only its own partition, and the live run's partition is untouched.
3. **Never backfill into a table the live schedule also appends to without a partition scope.** This is the `WRITE_APPEND` catastrophe.
4. **Use `depends_on_past=False`** unless the pipeline genuinely accumulates state — otherwise the backfill is serialised and takes 30 days' worth of runtime.
5. **Backfill with `max_active_runs` low enough that the backfill does not starve the live schedule.**
6. **Know your idempotency story before you start.** "If I run it twice, what happens?" must have an answer.

In Airflow 2.x, `airflow dags backfill` and the UI's "Create backfill" both respect `max_active_runs`. On Composer, use the UI's backfill feature or `gcloud composer environments run backfill`.

**The failure story:** a team backfilled 30 days into an unpartitioned table with `WRITE_APPEND`, while the live schedule was running. Every day got loaded twice within the hour — once by the backfill and once by the live run — and the live run for the *current* day overwrote rows the backfill had written for that same logical date. The table ended with ~1.9× the correct row count and no way to identify which copy was authoritative. Recovering took a full rebuild from source: 3 days of work, and the incident report was 6 pages.

### 10. Why is `catchup=True` worse than a backfill job, given that both re-run historical dates?

**Because `catchup=True` is unbounded, unmonitored, and starts immediately — while a backfill job is bounded, visible, and scheduled.**

| | `catchup=True` | A backfill job |
|---|---|---|
| Date range | every missed interval back to `start_date` | the range you specify |
| Starts | immediately on deploy | when you say |
| Concurrency | the DAG's `max_active_runs` | also respects it, but you choose the window |
| Visibility | looks like normal scheduled runs | distinguishable by `run_type=backfill` |
| Reversibility | you have to pause the DAG | you can cancel the backfill |
| Historical-data fit | assumed to work | you can test one day first |

The additional reason `catchup=True` is worse: **the historical data often does not exist in the form the pipeline expects.** A pipeline written in 2026 may reference a column added in 2026; backfilling to 2024 fails on every run. A pipeline reading a partner API may find the partner only retains 90 days of history. A backfill job lets you run one date, look at it, and adjust.

**The failure story:** a team deployed a DAG with `catchup=True` and `start_date=datetime(2024, 1, 1)`. Within four minutes, 730 runs existed and ~200 started concurrently. Each of the 200 opened a connection to the source API, which has a rate limit of 20 requests/second. The live run for that morning could not get through, and the DAG that was supposed to be on time missed its SLA — because of history it did not need. The fix was `catchup=False`, a deliberate backfill job for the 8 days actually needed, and a source-API quota that the backfill respected.

---

## Testing

### 11. What are the three layers of Airflow testing, and why do teams get the ratio wrong?

**Three layers, with wildly different cost-to-value ratios.**

```text
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1 — Pure logic                                             │
│   "Is the transformation correct?"                               │
│   Tests: pipeline_logic.py, templating.py                        │
│   Needs: pytest. No Airflow. Runs in < 1 second.                 │
│   Catches: 90% of real bugs.                                     │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2 — DAG structure                                          │
│   "Is the graph wired the way I intended?"                        │
│   Needs: Airflow installed (or a parser). Runs in ~5 seconds.     │
│   Catches: wiring mistakes, renames, missing tasks.              │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3 — Integration                                             │
│   "Does it work against real GCS / BigQuery / APIs?"             │
│   Needs: a GCP project, credentials, money. Runs in ~minutes.    │
│   Catches: credential problems, IAM gaps, API contract changes.  │
└─────────────────────────────────────────────────────────────────┘
```

The dominant mistake is spending the testing budget on Layer 3 and discovering that a `>` should have been a `>=`.

**The failure story:** a team had no automated tests and relied on a nightly "test DAG" running the real pipeline against the real BigQuery. It caught nothing useful for 8 months — because the logic was correct and the *wiring* was wrong in ways the live DAG also had. Then a rename of a task broke a downstream XCom pull, and the nightly test DAG broke identically. The team had been testing *whether the pipeline works*, not *whether the DAG is the shape they think it is*. The fix was Layer 2 structure tests, which cost 5 seconds and caught the rename.

### 12. What should a DAG structure test assert, and what is the single most valuable assertion?

**Assert things about the graph, not about behaviour.** They are cheap, run in CI on every commit, and catch a specific and surprisingly common class of bug: **the wiring is wrong.**

| Assertion | Catches |
|---|---|
| `len(dag.tasks) == 5` | a task was deleted or duplicated during a refactor |
| `dag.task_dict["aggregate"].upstream_task_ids == {"transform_orders"}` | a dependency was changed by accident |
| `isinstance(dag.get_task("load"), BigQueryInsertJobOperator)` | someone swapped the operator for a no-op |
| `dag.get_task("load").retries == 3` | a retry policy was lost in a copy-paste |
| `dag.get_task("x").trigger_rule == "none_failed"` | a join point lost its trigger rule |
| `dag.schedule == "@daily"` | the schedule changed |
| `dag.catchup is False` | **catchup was turned on accidentally** |
| `"{{ ds }}" in dag.get_task("x").bash_command` | a template was hard-coded |
| `set(dag.task_ids) == {...}` | a whole-task-set guard against accidental additions |

The last one is the most valuable and the least used: **an exact set comparison catches both deletions and additions.**

And the assertion that catches the most: **`bag.import_errors`**. A DAG that fails to import does not appear in `bag.dags` — it appears in `bag.import_errors`. If your test only checks that a DAG *exists*, an import error shows up as "DAG not found", which is a confusing failure. Checking `bag.import_errors` first gives you the real traceback.

```python
from airflow.models import DagBag

bag = DagBag(dag_folder=DAGS_DIR, include_examples=False)
if bag.import_errors:
    raise AssertionError(f"import errors: {bag.import_errors}")
```

**The failure story:** a DAG's `catchup` was set to `True` in a merge conflict. Nobody noticed for 3 weeks, because catchup only matters when there is a gap in the schedule — and there was not. Then the Composer environment had an 11-day outage (a Cloud SQL incident). When it came back, the scheduler created **11 extra DAG runs** that nobody had intended, and those runs overwrote three days of corrected data with the original logic. The fix was a CI assertion `assert dag.catchup is False` — one line, and it would have caught the merge conflict.

### 13. What are `dag.test()` and `dag.run()`, and what is the surprise most people hit?

**`dag.test()` (Airflow 2.5+) runs a DAG's tasks locally, in the current process, in dependency order, without a scheduler or a worker.** `dag.run()` runs a DAG for a *range* of logical dates — essentially `dag.test()` over a date range, which is why it exists: to run a backfill locally.

```python
from airflow.models.dagbag import DagBag
from airflow.utils import timezone

dagbag = DagBag(dag_folder="project/dags", include_examples=False)
dag = dagbag.get_dag("etl_orders_to_bigquery")

dag.test(execution_date=timezone.datetime(2026, 1, 15))
```

**The surprise: `dag.test()` executes the *real* operators.** A `BigQueryInsertJobOperator` in a `dag.test()` call will attempt a **real BigQuery load**. `dag.test()` is not a mock — it is a local executor. If your DAG talks to GCP, it either talks to GCP (and needs credentials) or fails with an auth error.

Note the parameter name: in Airflow 2.5–2.9 it is `execution_date`; `logical_date` is the newer name.

**The mitigation** is to override the operator's callable before running, or — much better — to test the DAG's *logic* through a `PythonOperator` that calls a pure function, and test the operator wiring separately. Which is exactly the course's design: `project/core/pipeline_logic.py` imports nothing from Airflow, so `pytest` runs it in milliseconds.

**The failure story:** a developer ran `dag.test()` on a DAG containing `BigQueryInsertJobOperator` pointed at the production table. The `writeDisposition` was `WRITE_APPEND`. The test run loaded 1,245 rows into production for logical date `2026-01-15` — a date the real pipeline was about to load. The real run then appended them again. The production table had 2,490 rows for that day, and the fix required deleting by `load_ts` because there was no partition decorator. The review afterwards produced a rule: **`dag.test()` runs against a dev project only, and the DAG must use a partition-scoped write.**

---

## Monitoring, security, troubleshooting

### 14. A nightly DAG "succeeded" but the dashboard was empty. What are the monitoring signals you actually need, and what does the scheduler's health look like?

**Five signals, and the fifth is the one people forget.**

1. **DAG run state** — success/failed per logical date. The baseline.
2. **SLA compliance rate over a window**, not per-run booleans. A 99.5% commitment needs a rate.
3. **Output row counts / volume**, compared against an expectation. This is the signal that catches "green but empty".
4. **Task duration**, compared against a baseline. A task that goes from 4 minutes to 40 minutes is a signal even when it succeeds.
5. **The scheduler heartbeat.** A stalled scheduler means no new runs are created, which looks *identical* to "the DAG is not scheduled" and is much more confusing to debug.

The empty-dashboard case above is exactly what signal 3 exists for. The run was green because the load found an empty upstream file and loaded 0 rows — a *legitimate* outcome for the code, given the input.

**The failure story:** a nightly ETL ran every day and went green. For 3 days the upstream export was two hours late, so the run found an empty file, loaded 0 rows, and the dashboard's health check — "did the DAG go green" — said everything was fine. The data was silently missing for 3 days until a finance reconciliation caught it. The fix was an explicit row-count assertion in the load task plus a volume metric with an expected range. Signal 3 caught in 4 minutes what signal 1 could not catch at all.

**On the scheduler heartbeat specifically:** Composer exposes the scheduler's health through the environment's monitoring, and the symptom of a stalled scheduler is that *no new DAG runs are created* while *existing runs continue to finish*. If your DAGs are all "late" but their tasks are completing fine, check the scheduler before you check your DAGs.

**On cost — the other half of "the DAG is fine".** A Composer environment is a roughly fixed monthly cost regardless of how many jobs run through it, so the question is whether that fixed cost is buying dependency management. The course's comparison for a nightly aggregation over ~100 GB:

| Approach | Cost/mo (approx) | Latency |
|---|---|---|
| **BigQuery scheduled query** (no Airflow) | **$150 – $300** | 2–5 min |
| **BigQuery partitioned (~30 GB/day scanned)** | **$50 – $100** | 2–5 min |
| **Dataflow batch job** | **$300 – $800** | 10–30 min |
| **Spark on Dataproc** | **$400 – $1,200** | 15–45 min |
| **A single PythonOperator doing it all** | **$30 – $60** | 40 min |

**Sizing rule:** *if your DAG is mostly issuing queries, size the Composer environment small — the query runs server-side and the environment only orchestrates. If it is mostly running Python, size it for the concurrency you need.*

**The failure story:** a team ran 40 small BigQuery scheduled queries *and* had a Composer environment for two DAGs that genuinely needed dependencies. The environment had 6 workers and cost $700/month. Moving 11 of the queries to BigQuery scheduled queries and shrinking to 2 workers brought it to $280/month — with no loss of functionality, because those 11 jobs had no dependencies. The lesson: *one Composer environment for everything is usually right, but only if everything genuinely belongs in it.* The next failure was that the team then *also* moved a genuinely dependent DAG to a scheduled query, breaking the dependency. The correct split was: dependencies → Airflow; everything else → scheduled queries.

### 15. A Variable is plaintext, a Connection's password is encrypted, and params live in `dag_run.conf`. Where do credentials go, and what is the encryption story precisely?

**Credentials go in Connections — always, with no exceptions.** The precise encryption story matters because "encrypted" is often over-claimed:

| Mechanism | Stored | Encrypted? | Visible in UI? | Persisted in run history? |
|---|---|---|---|---|
| **Variable** | metadata DB | **No — plaintext** | Yes, to anyone with Variable-read | No |
| **param** | `dag_run.conf` | No | Yes, in the run's config tab | **Yes, forever** |
| **Connection `password`** | metadata DB | **Yes** (Fernet, from `airflow.cfg`) | Masked | No |
| **Connection `extra`** | metadata DB | **No — not encrypted by default in Airflow 2.x** | Yes | No |

The `extra` caveat is the one people miss: **only `password` is encrypted in Airflow 2.x.** Do not put a private key in `extra`. In Composer, the right answer for GCP credentials is usually the **environment's attached service account** (the Composer service agent) rather than any credential you create at all.

The logging pattern that keeps this safe — from `02_templating_and_variables.py`:

```python
# Reading the host is safe; reading a password into a log is not.
conn = context["conn"].get("http_orders_api")
if conn is not None:
    log.info("api host     : %s", conn.host)
```

Never `log.info("password: %s", conn.password)`.

**The failure story:** a team stored a service-account JSON key in a Variable named `gcp_key`. The Variable list page showed the full private key to every engineer with UI access; the key was written to the metadata DB in the clear; and the metadata DB is backed up to GCS, so the key was in the backups too. Rotating it took a week of coordinated work across every environment. The fix was moving it to the environment's attached service account, so no credential material existed in Airflow at all.

**The multi-team security model.** Composer 2.x uses IAM-based access control rather than Airflow's own RBAC (Composer 3 adds built-in RBAC). This has a concrete consequence: **there is no in-Airflow permission boundary between teams.** Anyone who can reach the Composer UI can typically trigger any DAG in the environment unless you have restricted IAM on the environment itself.

So the IAM split is the real boundary, and it should be layered:

| Role | What they get |
|---|---|
| **Composer user** | can view the UI, list DAGs, see logs |
| **Composer editor / DAG run trigger** | can trigger DAGs and clear tasks — grant per-team |
| **Composer admin** | can change environment configuration — platform team only |
| **Service account (Composer service agent)** | the identity the *environment* runs as; it needs BigQuery/GCS/Dataflow access |

The critical design point: **the service account's permissions are the environment's real blast radius.** If the Composer service agent has `roles/bigquery.dataEditor` on every dataset in the project, then every DAG — including a team's experimental one — can write to every table. The narrower fix is to give the environment service account access only to the datasets and buckets the environment needs, and to keep per-team write access in the individual connections.

Also: **never put a service-account key in the DAG bundle.** Composer gives each environment a managed identity; use it.

**The failure story:** a data-science team uploaded an experimental DAG that wrote to `analytics.revenue_enriched` "just to test". The Composer service agent had project-wide BigQuery data-editor access because it had been granted project-wide access early on for convenience. The experimental DAG truncated the production revenue table — `WRITE_TRUNCATE` with no partition decorator — and the nightly pipeline's next run reloaded one day of data into an otherwise empty table. Recovery took 5 hours and a full 90-day rebuild. The fix was a per-dataset IAM grant and a structure test asserting every `BigQueryInsertJobOperator` has a partition decorator.

---

## Troubleshooting

### 16. A DAG is missing from the UI, or a task sits queued and never starts. Give me the ordered triage for both.

**Two different symptoms, one discipline: check from cheapest to most likely, and read the evidence in the UI and metadata DB rather than re-reading the DAG file.**

*This is the question that gets asked with a live incident on the caller's screen — "it's not showing up" and "it's stuck" are the two most common Airflow pages.*

**Symptom A — the DAG is not in the UI:**

1. **Does the file exist in the DAGs bucket?** Composer only parses files under the configured DAGs folder. A file uploaded to the wrong prefix is invisible.
2. **Is there an import error?** Look at **Browse → DAGs → <filename>** in the Composer UI — it shows the traceback. `airflow.exceptions.DagFileExists` means a duplicate `dag_id`; in Airflow 2.x **neither** DAG registers.
3. **Has the scheduler re-parsed?** Composer re-parses on a timer (typically 1–3 minutes). Force it from the UI or wait.
4. **Is the DAG paused?** A paused DAG appears in the UI but does not schedule. `dag.is_paused` is the check.
5. **Is `schedule=None`?** A DAG with `schedule=None` never runs automatically — it is manual-trigger only. The course's `branching_and_xcom` DAG is exactly this.
6. **Is `max_active_runs` saturated?** The DAG is queued but not started because earlier runs are still going.
7. **Is the start date in the future?** `start_date` after now means nothing is eligible.

For the local equivalent, the course's runner gives you a quick check:

```bash
python project/local_runner.py --list
python project/local_runner.py --dag etl_to_gcs --describe
```

**Symptom B — a task is queued and never starts.** Five causes, and the distinguishing evidence is in the UI and the metadata DB, not in the DAG file:

| Cause | Evidence |
|---|---|
| **No worker available** | other tasks in the environment are also queued; the worker pool is exhausted |
| **Concurrency limit** | `max_active_tasks` for the DAG, or the environment-wide `parallelism`, is reached |
| **Dependencies not met** | an upstream task is still `running` or `queued` — look *upstream*, not at this task |
| **Trigger rule** | an upstream was `skipped`, and this task's `trigger_rule="all_success"` means it skips too |
| **The scheduler is stalled** | no new runs created for any DAG; check the scheduler heartbeat |

The one that causes the most confusion is **the trigger rule**, because the task looks correct. The course's `local_runner.py` prints the dependency states for exactly this reason:

```text
    ✗ extract                failed
    ⊘ transform              upstream_failed
    ⊘ load                   upstream_failed
```

Two states, two meanings:

- **`failed`** — this task ran and raised. It may have written partial data before dying.
- **`upstream_failed`** — this task **never ran**; a dependency failed.

Conflating them in your alerting produces false "task failed" pages for tasks that never started.

**The failure stories.** First: a team spent 40 minutes checking IAM, bucket permissions, and the parse interval for a DAG that did not appear. The cause was a duplicate `dag_id`: a new file `04_branching_and_xcom.py` was added while `04_branching.py` still existed with the same `dag_id="branching_and_xcom"`. In Airflow 2.x this raises `DagFileExists` at import and **neither** DAG registers — so the team had *zero* DAGs where they expected one. The fix was renaming one file, plus a CI check: `grep -h 'dag_id=' project/dags/*.py | sort | uniq -c | sort -rn`.

Second: a team had a DAG whose final task appeared "queued" in the UI for hours. The upstream branch task had chosen the *other* path, so the chosen path was `skipped` — and the final task used the default `trigger_rule="all_success"`, so it was `skipped` too. In the UI, a skipped task and a queued task look similar in a list view. The team read "queued" and spent 3 hours investigating worker capacity. The fix was a trigger rule of `none_failed` on the join, and a dashboard that distinguished `skipped` from `queued`.

---

## Next module

→ [Module 5 — Composer & GCP](05-composer-and-gcp.md)

---

## Related chapters

| Module section | Chapter |
|---|---|
| SLAs (1–4) | [11-slice-and-slas](../chapters/11-slice-and-slas.md) |
| Retries, idempotency (5–8) | [12-idempotency-and-reliability](../chapters/12-idempotency-and-reliability.md) |
| Backfills (9–10) | [03-dags-and-scheduling](../chapters/03-dags-and-scheduling.md) |
| Testing (11–13) | [13-testing-dags](../chapters/13-testing-dags.md) |
| Monitoring, cost, orchestration patterns (14) | [14-orchestration-patterns](../chapters/14-orchestration-patterns.md), [15-airflow-vs-beam-vs-spark](../chapters/15-airflow-vs-beam-vs-spark.md) |
| Security (15) | [06-variables-params-and-connections](../chapters/06-variables-params-and-connections.md) |
| Troubleshooting (16) | [01-what-is-orchestration-and-why-airflow](../chapters/01-what-is-orchestration-and-why-airflow.md), [02-airflow-architecture-and-concepts](../chapters/02-airflow-architecture-and-concepts.md) |
