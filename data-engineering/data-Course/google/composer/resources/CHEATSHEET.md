# Cheatsheet — Google Cloud Composer & Apache Airflow

---

## The CLI (no Airflow needed)

```bash
python project/local_runner.py --list                    # list the DAGs
python project/local_runner.py --dag etl_to_gcs           # run one
python project/local_runner.py --dag all                 # run every DAG
python project/local_runner.py --dag etl_to_gcs --describe # show the graph
python project/local_runner.py --dag etl_to_gcs --verbose # per-task logging
python project/local_runner.py --dag etl_to_gcs --date 2026-01-15
python project/local_runner.py --dag etl_to_gcs --vars '{"target_bucket":"my-bucket"}'
python project/local_runner.py --dag etl_to_gcs --params '{"audience":"team"}'

python resources/check_notebooks.py                      # execute every notebook
python resources/check_notebooks.py 04                   # one notebook
python -m pytest project/tests/ -q                       # the test suite
python resources/sample_data.py --output-dir ./sample_data
```

---

## The Jinja context

| Template | Value | Example |
|---|---|---|
| `{{ ds }}` | Logical date, `YYYY-MM-DD` | `2026-01-15` |
| `{{ ts }}` | Logical date, full timestamp | `2026-01-15T00:00:00+00:00` |
| `{{ ds_nodash }}` | Logical date, no dashes | `20260115` |
| `{{ prev_ds }}` | Previous day | `2026-01-14` |
| `{{ next_ds }}` | Next day | `2026-01-16` |
| `{{ data_interval_start }}` | Interval start (inclusive) | `2026-01-15T00:00:00+00:00` |
| `{{ data_interval_end }}` | Interval end (**exclusive**) | `2026-01-16T00:00:00+00:00` |
| `{{ logical_date }}` | Same as `ts` | |
| `{{ run_id }}` | The run identifier | |
| `{{ dag.dag_id }}` | The DAG's id | |
| `{{ task.task_id }}` | The task's id | |
| `{{ ti.task_id }}` | The task instance's id | |
| `{{ params.x }}` | A DAG-run parameter | |
| `{{ var.value.x }}` | An Airflow Variable | |
| `{{ var.x }}` | Same Variable, other spelling | |
| `{{ conn.my_conn.host }}` | A Connection field | |
| `{{ conn.my_conn.extra_dejson.timeout }}` | Connection extra, as JSON | |
| `{{ macros.ds_add(ds, -1) }}` | Date arithmetic | `2026-01-14` |

### The data interval — the rule that matters

Airflow's interval is **half-open**: `[start, end)`.

```text
The 2026-01-15 run  ->  [2026-01-15, 2026-01-16)
```

```sql
-- CORRECT
WHERE order_ts >= '{{ data_interval_start }}' AND order_ts < '{{ data_interval_end }}'

-- WRONG: double-counts the midnight row
WHERE order_ts BETWEEN '{{ data_interval_start }}' AND '{{ data_interval_end }}'
```

---

## Where configuration lives

| Need | Use | Why |
|---|---|---|
| Differs per **run** | `params` | A backfill date range, a flag |
| Differs per **environment** | `Variable` | Bucket names, project IDs |
| Holds **credentials** | `Connection` | Encrypted; not visible in the UI |
| Logic and structure | The DAG file | |

```python
# Variable with a fallback — always use one
BUCKET = "{{ var.value.target_bucket | default('my-fallback-bucket') }}"

# A param overrides a Variable
BUCKET = "{{ params.bucket | default(var.value.target_bucket) }}"
```

---

## Trigger rules

| Rule | Runs when | Use for |
|---|---|---|
| `all_success` (default) | All upstream tasks succeeded | The normal case |
| `none_failed` | Nothing upstream **failed** | A join point after a branch |
| `all_done` | All upstream tasks finished, any outcome | Cleanup, always-run reporting |
| `none_failed_min_one_success` | Nothing failed, at least one succeeded | A guarded join point |
| `always` | Always | Fire-and-forget notifications |

> **The branch bug.** A task depending on two branches, where only one runs, is
> **skipped** under `all_success` — because one dependency was skipped. Use
> `none_failed`.

---

## Operators — choosing one

| Operator | Use it for |
|---|---|
| `PythonOperator` | Business logic; anything with a rule in it |
| `BashOperator` | Shell commands; `gsutil`, `bq` |
| `EmptyOperator` | A join point with no work |
| `BigQueryExecuteQueryOperator` | Running SQL |
| `BigQueryInsertJobOperator` | Loading data |
| `BigQueryToGCSOperator` | Exporting a table |
| `GCSCreateEmptyBucketOperator` | Bucket setup |
| `BranchOperator` | Choosing between two paths |
| `ShortCircuitOperator` | Skipping everything downstream |
| `PythonSensor` / `ExternalTaskSensor` | Waiting for a condition |

---

## Sensors

```python
from airflow.sensors.python import PythonSensor

wait = PythonSensor(
    task_id="wait_for_data",
    python_callable=check_ready,     # returns True when ready
    mode="reschedule",               # releases the worker slot — use for long waits
    poke_interval=300,               # 5 minutes
    timeout=3600,                    # give up after an hour
    soft_fail=True,                  # do not fail the DAG on timeout
)
```

| Mode | Behaviour | Use for |
|---|---|---|
| `poke` | Holds the worker slot | Short waits (< 1 minute) |
| `reschedule` | Releases the slot, re-checks later | Long waits (minutes+) |

---

## SLAs, timeouts and retries

| Setting | Meaning |
|---|---|
| `sla` | When the task should have finished, measured from the **data interval end** |
| `execution_timeout` | How long the task may run |
| `retries` | How many times to retry after a failure |
| `retry_delay` | How long to wait between retries |
| `timeout` (sensors) | How long to wait for the condition |

```python
from airflow.utils.trigger_rule import TriggerRule

task = PythonOperator(
    task_id="load",
    python_callable=load_orders,
    sla=timedelta(hours=2),          # late if not done within 2h of interval end
    execution_timeout=timedelta(hours=1),
    retries=3,
    retry_delay=timedelta(minutes=10),
    trigger_rule=TriggerRule.NONE_FAILED,
)
```

---

## Idempotency — the BigQuery decision

| Write disposition | On retry | Use when |
|---|---|---|
| `WRITE_APPEND` | **Duplicates the rows** | The target is empty and unique |
| `WRITE_TRUNCATE` | Replaces the partition | The daily partition is the unit |
| `WRITE_EMPTY` | No-op on an existing partition | Append-only, guarded |

```python
"writeDisposition": "WRITE_TRUNCATE",
"createDisposition": "CREATE_IF_NEEDED",
```

**Deterministic identity** — never use a load timestamp:

```python
# WRONG — a retry produces different rows
"load_ts": CURRENT_TIMESTAMP()

# RIGHT — a retry produces the same rows
"row_id": f"{partition}:{order_id}"
```

---

## `gcloud composer`

```bash
# Create
gcloud composer environments create ENV_NAME \
  --location=REGION \
  --environment-size=SMALL \
  --image-version=composer-2.9.7-airflow-2.9.3 \
  --dag-bucket=gs://BUCKET \
  --description="..."

# Update (image version, size, config)
gcloud composer environments update ENV_NAME \
  --location=REGION \
  --image-version=composer-2.10.5-airflow-2.10.5

# List and describe
gcloud composer environments list --location=REGION
gcloud composer environments describe ENV_NAME --location=REGION

# Run a DAG
gcloud composer environments run ENV_NAME \
  --location=REGION \
  --dag DAG_ID

# Upload DAGs
gcloud storage cp --recursive project/dags/* gs://BUCKET/

# Delete — BILL STOPS ONLY WHEN YOU DO THIS
gcloud composer environments delete ENV_NAME --location=REGION
```

| Environment size | Workers (Composer 2) | Typical use |
|---|---|---|
| `SMALL` | 1–2 | Learning, low concurrency |
| `MEDIUM` | 3–6 | A team, a dozen daily DAGs |
| `LARGE` | 7–15 | Many concurrent DAGs, heavy tasks |

---

## Composer 2 vs Composer 3

| | Composer 2 | Composer 3 |
|---|---|---|
| Executor | Celery | Kubernetes |
| Isolation | Worker pool | Pod per task |
| Scaling | Vertically, within the pool | Horizontally, via pods |
| Startup cost | Worker reuse | ~30–60 s per pod |
| Best for | Steady, moderate concurrency | Bursty, high concurrency |

---

## Local runner states

| State | Meaning |
|---|---|
| `success` | Completed |
| `failed` | Raised, after exhausting retries |
| `skipped` | Trigger rule or branch said no |
| `upstream_failed` | An upstream task failed |

---

## Errors and their causes

| Message | Cause | Fix |
|---|---|---|
| `DagNotFound: DAG: [x] not found` | Not parsed yet, or not in the DAG bucket | Wait 1–2 min; check import errors |
| `DagFileExists` | Two files define the same `dag_id` | Rename one |
| `jinja2.exceptions.UndefinedError` | A missing Variable or param | Add it, or use `\| default(...)` |
| `Task is in the 'upstream_failed' state` | An upstream task failed | Read the upstream failure |
| `Task is in the 'skipped' state` | A branch or trigger rule skipped it | Check the trigger rule |
| `Timeout: 3600.0s` | A sensor gave up | Raise the timeout, or fix the upstream |
| `KeyError: 'x'` | A Column not found in BigQuery | Check the schema |
| `Could not connect to the broker` | Celery broker unreachable (self-managed) | Check Redis/RabbitMQ |
| `403 Forbidden` (K8s API) | The service account lacks RBAC | Grant the role |
