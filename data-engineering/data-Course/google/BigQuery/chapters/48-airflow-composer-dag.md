# 8.3 — Airflow / Cloud Composer: The Orchestration DAG

> **Section 8 · Case Study · Lecture 8.3 · 6:05**

## 🎯 What you will learn

- The Airflow model: DAGs, operators, sensors, XComs, and execution dates
- Building the RetailMart orchestration DAG in Airflow
- Cloud Composer specifics: environments, workers, and the managed runtime
- Idempotency, backfills, and retries in a real DAG
- Testing and debugging DAGs

---

## 🧠 Concept

Airflow is a workflow orchestrator: it decides **what runs when**, not **how the data moves**.

```
DAG file (Python)  →  Airflow scheduler  →  Workers execute tasks  →  Metadata DB
```

| Concept | What it is |
|---------|-----------|
| **DAG** | A collection of tasks with dependencies |
| **Operator** | The type of work (run a query, call an API, run a shell command) |
| **Task** | One node in the DAG — an operator instance with a callable |
| **Execution date** | The logical run time (`data_interval_start` / `data_interval_end`) |
| **Sensor** | Waits for a condition (file exists, table ready) |
| **XCom** | A small key-value store for passing data between tasks |
| **Schedule interval** | How often the DAG runs (cron) |
| **Catchup** | Whether to backfill missed runs |
| **SLAs** | Missed deadlines that trigger alerts |

💡 **In Airflow 2, use `data_interval_start` / `data_interval_end`, not `execution_date`.** The
old name is deprecated and confusing.

---

## 🧠 The RetailMart DAG graph

```
daily_pos_extract ──▶ daily_conform ──▶ daily_curate ──▶ daily_marts ──▶ dq_checks ──▶ publish_marts
        │                    │                  │                 │              │
        ▼                    ▼                  ▼                 ▼              ▼
   GCS + raw.pos_orders  staging.*         curated.orders      mart.*         Looker Studio
```

---

## 🛠️ Hands-On

### 1. Cloud Composer environment (Terraform)

```hcl
resource "google_composer_environment" "retailmart" {
  name    = "retailmart-composer"
  region  = "europe-west1"
  project = var.project_id

  config {
    environment_size = "ENVIRONMENT_SIZE_MEDIUM"

    software_config {
      image_version {
        environment_image = "composer-2.9.9-airflow-2.9.3"
      }
      python_version = "3.11"
      env_variables = {
        PROJECT_ID        = var.project_id
        BUCKET            = "gs://${var.project_id}-retailmart"
        CURATED_DATASET   = "retailmart.curated"
        MART_DATASET      = "retailmart.mart"
        DQ_TOLERANCE_PCT  = "0.5"
      }
    }

    node_config {
      service_account = google_service_account.composer[0].email

      # Composer 2 scales the web server and worker independently
      node_count = {
        web_server = 1
        worker     = 1
      }

      machine_type = "n1-standard-2"
    }
  }
}
```

### 2. The DAG file

```python
"""
retailmart_daily.py — the RetailMart daily pipeline.

Schedule: 01:30 UTC daily
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryExecuteQueryOperator,
    BigQueryInsertJobOperator,
)
from airflow.providers.google.cloud.operators.gcs import GCSListObjectsOperator
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.providers.google.cloud.transfers.gcs_to_gcs import GCSToGCSOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

log = logging.getLogger(__name__)

PROJECT_ID = "{{ var.value.project_id }}"
BUCKET = "{{ var.value.bucket }}"
CURATED = "retailmart.curated"
MART = "retailmart.mart"

default_args = {
    "owner": "data-eng",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
    "email_on_failure": True,
    "email_on_retry": True,
}

with DAG(
    dag_id="retailmart_daily",
    description="Daily RetailMart ingest, transform, and publish",
    schedule_interval="30 1 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,          # never overlap daily runs
    default_args=default_args,
    tags=["retailmart", "daily", "bigquery"],
    params={
        "target_date": days_ago(1),   # yesterday by default
    },
) as dag:

    # ------------------------------------------------------------------
    # 0. Resolve the target date
    # ------------------------------------------------------------------
    resolve_date = PythonOperator(
        task_id="resolve_target_date",
        python_callable=_resolve_target_date,
        op_kwargs={"params": "{{ params }}"},
    )

    # ------------------------------------------------------------------
    # 1. Wait for the POS file to land
    # ------------------------------------------------------------------
    wait_for_pos_file = GCSObjectExistenceSensor(
        task_id="wait_for_pos_file",
        bucket="{{ var.value.bucket_name }}",
        object_name="staging/pos/orders_{{ params.target_date }}.csv",
        poke_interval=60,
        timeout=3600,
        mode="reschedule",           # free the worker slot while waiting
    )

    # ------------------------------------------------------------------
    # 2. Copy the file to the raw landing zone
    # ------------------------------------------------------------------
    land_pos_file = GCSToGCSOperator(
        task_id="land_pos_file",
        source_bucket="{{ var.value.bucket_name }}",
        source_object="staging/pos/orders_{{ params.target_date }}.csv",
        destination_bucket="{{ var.value.bucket_name }}",
        destination_object="raw/pos/orders_{{ params.target_date }}.csv",
    )

    # ------------------------------------------------------------------
    # 3. Load raw POS orders into BigQuery
    # ------------------------------------------------------------------
    load_pos_orders = BigQueryInsertJobOperator(
        task_id="load_pos_orders",
        configuration={
            "load": {
                "sourceUris": [f"{BUCKET}/raw/pos/orders_{{{{ params.target_date }}}}.csv"],
                "destinationTable": {
                    "projectId": "{{ var.value.project_id }}",
                    "datasetId": "retailmart",
                    "tableId": "pos_orders",
                },
                "sourceFormat": "CSV",
                "skipLeadingRows": 1,
                "schema": {
                    "fields": [
                        {"name": "order_id", "type": "STRING", "mode": "REQUIRED"},
                        {"name": "store_id", "type": "STRING", "mode": "REQUIRED"},
                        {"name": "order_ts", "type": "TIMESTAMP", "mode": "REQUIRED"},
                        {"name": "amount_local", "type": "NUMERIC", "mode": "REQUIRED"},
                        {"name": "currency", "type": "STRING", "mode": "REQUIRED"},
                        {"name": "status", "type": "STRING", "mode": "REQUIRED"},
                        {"name": "line_count", "type": "INTEGER", "mode": "REQUIRED"},
                    ]
                },
                "writeDisposition": "WRITE_APPEND",
                "createDisposition": "CREATE_IF_NEEDED",
            }
        },
    )

    # ------------------------------------------------------------------
    # 4. Conform: raw -> staging
    # ------------------------------------------------------------------
    conform_orders = BigQueryExecuteQueryOperator(
        task_id="conform_orders",
        sql=f"""
        CREATE OR REPLACE TABLE `{PROJECT_ID}.retailmart.staging.orders`
        PARTITION BY order_date
        AS
        SELECT
          order_id,
          customer_id,
          TIMESTAMP(order_ts) AS order_ts,
          DATE(order_ts) AS order_date,
          channel,
          region,
          currency,
          CAST(amount_local AS NUMERIC) AS amount_local,
          status,
          line_count,
          source_system,
          CURRENT_TIMESTAMP() AS ingested_at
        FROM (
          SELECT
            order_id,
            -- POS has no customer id; use the store as the surrogate
            COALESCE(customer_id, CONCAT('store_', store_id)) AS customer_id,
            order_ts,
            'store' AS channel,
            store_id AS region,
            currency,
            amount_local,
            status,
            line_count,
            'pos' AS source_system
          FROM `{PROJECT_ID}.retailmart.raw.pos_orders`
          WHERE DATE(order_ts) = DATE(@target_date)

          UNION ALL

          SELECT
            order_id, customer_id, order_ts, DATE(order_ts) AS order_date,
            channel, region, currency, amount_local, status, line_count,
            'app' AS source_system
          FROM `{PROJECT_ID}.retailmart.raw.app_orders`
          WHERE DATE(order_ts) = DATE(@target_date)
        )
        """,
        parameters={"target_date": "{{ params.target_date }}"},
    )

    # ------------------------------------------------------------------
    # 5. Curate: staging -> curated (append, partitioned, clustered)
    # ------------------------------------------------------------------
    curate_orders = BigQueryExecuteQueryOperator(
        task_id="curate_orders",
        sql=f"""
        INSERT INTO `{PROJECT_ID}.{CURATED}.orders`
        (order_id, customer_id, order_ts, order_date, channel, region,
         currency, amount_local, amount_eur, status, line_count,
         source_system, ingested_at)
        SELECT
          o.order_id, o.customer_id, o.order_ts, o.order_date,
          o.channel, o.region, o.currency, o.amount_local,
          ROUND(o.amount_local * fx.rate_to_eur, 2) AS amount_eur,
          o.status, o.line_count, o.source_system, o.ingested_at
        FROM `{PROJECT_ID}.retailmart.staging.orders` o
        JOIN `{PROJECT_ID}.retailmart.raw.fx_rates` fx
          ON o.currency = fx.currency
         AND fx.rate_date = o.order_date
        WHERE o.order_date = DATE(@target_date)
        """,
        parameters={"target_date": "{{ params.target_date }}"},
    )

    # ------------------------------------------------------------------
    # 6. Build the marts
    # ------------------------------------------------------------------
    build_marts = BigQueryExecuteQueryOperator(
        task_id="build_marts",
        sql=f"""
        CREATE OR REPLACE TABLE `{PROJECT_ID}.{MART}.daily_revenue`
        PARTITION BY order_date
        CLUSTER BY region
        AS
        SELECT
          order_date,
          region,
          channel,
          COUNT(*) AS order_count,
          COUNT(DISTINCT customer_id) AS customer_count,
          SUM(amount_eur) AS revenue_eur,
          SAFE_DIVIDE(SUM(amount_eur), COUNT(*)) AS aov_eur
        FROM `{PROJECT_ID}.{CURATED}.orders`
        WHERE order_date = DATE(@target_date)
        GROUP BY order_date, region, channel
        """,
        parameters={"target_date": "{{ params.target_date }}"},
    )

    # ------------------------------------------------------------------
    # 7. Data quality gate
    # ------------------------------------------------------------------
    dq_checks = BigQueryExecuteQueryOperator(
        task_id="dq_checks",
        sql=f"""
        CREATE OR REPLACE TABLE `{PROJECT_ID}.retailmart.dq_results`
        AS
        WITH control AS (
          SELECT COUNT(*) AS n, SUM(amount_local) AS total
          FROM `{PROJECT_ID}.retailmart.raw.pos_orders`
          WHERE DATE(order_ts) = DATE(@target_date)
        ),
        curated AS (
          SELECT COUNT(*) AS n, SUM(amount_eur) AS total
          FROM `{PROJECT_ID}.{CURATED}.orders`
          WHERE order_date = DATE(@target_date) AND source_system = 'pos'
        )
        SELECT
          DATE(@target_date) AS check_date,
          'pos_row_count_parity' AS check_name,
          control.n AS control_value,
          curated.n AS actual_value,
          ABS(control.n - curated.n) AS diff,
          SAFE_DIVIDE(ABS(control.n - curated.n), control.n) * 100 AS diff_pct,
          IF(ABS(control.n - curated.n) = 0, 'PASS', 'FAIL') AS status
        FROM control, curated
        """,
        parameters={"target_date": "{{ params.target_date }}"},
    )

    # The gate task fails the DAG if the check failed
    enforce_dq = PythonOperator(
        task_id="enforce_dq",
        python_callable=_enforce_dq,
        op_kwargs={"target_date": "{{ params.target_date }}"},
    )

    # ------------------------------------------------------------------
    # 8. Publish
    # ------------------------------------------------------------------
    publish_marts = PythonOperator(
        task_id="publish_marts",
        python_callable=_publish_marts,
        op_kwargs={"target_date": "{{ params.target_date }}"},
    )

    # ------------------------------------------------------------------
    # Dependencies
    # ------------------------------------------------------------------
    (
        resolve_date
        >> wait_for_pos_file
        >> land_pos_file
        >> load_pos_orders
        >> conform_orders
        >> curate_orders
        >> build_marts
        >> dq_checks
        >> enforce_dq
        >> publish_marts
    )
```

### 3. The helper functions

```python
def _resolve_target_date(params: dict) -> str:
    """Return the target date, allowing manual override."""
    target = params.get("target_date")
    if isinstance(target, str):
        return target
    if hasattr(target, "strftime"):
        return target.strftime("%Y-%m-%d")
    return target


def _enforce_dq(target_date: str, **context) -> None:
    """Raise if any DQ check for the date failed."""
    from google.cloud import bigquery
    client = bigquery.Client()

    rows = client.query(
        f"""
        SELECT check_name, diff_pct
        FROM `{{PROJECT_ID}}.retailmart.dq_results`
        WHERE check_date = DATE('{target_date}') AND status = 'FAIL'
        """
    ).result()

    failures = list(rows)
    if failures:
        raise ValueError(
            f"DQ gate failed for {target_date}: "
            + "; ".join(f"{r.check_name} ({r.diff_pct:.3f}%)" for r in failures)
        )
    log.info("DQ gate passed for %s", target_date)


def _publish_marts(target_date: str, **context) -> None:
    """Notify the BI layer that the marts are fresh."""
    import requests
    requests.post(
        "https://your-webhook.example.com/bigquery/publish",
        json={"target_date": target_date, "mart": "daily_revenue"},
        timeout=30,
    )
```

### 4. Using XComs to pass values between tasks

```python
def _get_row_count(**context):
    from google.cloud import bigquery
    client = bigquery.Client()
    n = client.query(
        f"SELECT COUNT(*) FROM `{{PROJECT_ID}}.retailmart.curated.orders` "
        f"WHERE order_date = DATE('{context['params']['target_date']}')"
    ).result().one()[0]
    return n


count_task = PythonOperator(task_id="get_row_count", python_callable=_get_row_count)

# Consume it
use_count = PythonOperator(
    task_id="use_row_count",
    python_callable=lambda n: print(f"Curated {n} orders"),
    op_args=[count_task.output],
)
```

💡 **XComs are for small values only** — a count, a date, a flag. Passing millions of rows
through XCom will break the metadata database. Large data goes through storage, not XCom.

### 5. Sensors — waiting for a condition

```python
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.providers.google.cloud.sensors.bigquery import BigQueryTableExistenceSensor
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor

wait_for_file = GCSObjectExistenceSensor(
    task_id="wait_for_file",
    bucket="my-bucket",
    object_name="staging/pos/orders_{{ params.target_date }}.csv",
    poke_interval=60,        # check every minute
    timeout=3600,            # give up after an hour
    mode="reschedule",       # free the worker slot while waiting
)

wait_for_table = BigQueryTableExistenceSensor(
    task_id="wait_for_table",
    project_id="my-project",
    dataset_id="retailmart",
    table_id="curated.orders",
    poke_interval=30,
    timeout=1800,
)
```

💡 **Always use `mode="reschedule"` for long waits.** In `poke` mode the worker slot is held
for the entire timeout, which can exhaust your Composer environment.

### 6. Backfill

```bash
# Backfill a date range
airflow dags backfill \
  -d retailmart_daily \
  -s 2026-01-01 \
  -e 2026-01-31

# With a custom config
airflow dags backfill \
  -d retailmart_daily \
  -s 2026-01-01 \
  -e 2026-01-31 \
  --reset-dagruns
```

```python
# Or trigger a one-off run from Python
from airflow.api.client.local_client import Client

client = Client()
client.trigger_dag(
    dag_id="retailmart_daily",
    conf={"target_date": "2026-01-15"},
)
```

💡 **Backfill only works if every task is parameterized by `target_date`.** A DAG that reads
`CURRENT_DATE()` cannot be backfilled — it will reprocess today for every historical run.

### 7. Debugging a failed task

```bash
# List recent runs
airflow dags list-runs -d retailmart_daily -sd 2026-01-01 -ed 2026-01-31

# Get the log for a failed task
airflow tasks logs retailmart_daily curate_orders 2026-01-15T01:30:00+00:00

# Clear and retry
airflow tasks clear retailmart_daily curate_orders \
  -d 2026-01-15T01:30:00+00:00

# Rerun from the CLI in a Composer environment
gcloud composer environments run retailmart-composer \
  --location europe-west1 \
  --command "airflow dags backfill -d retailmart_daily -s 2026-01-15 -e 2026-01-15"
```

### 8. Testing a DAG without Airflow

```python
import pendulum
from airflow.models import DAG
from airflow.utils import timezone
from airflow.utils.state import State
from airflow.models import TaskInstance


def test_dag_dependencies():
    dag = retailmart_daily
    assert len(dag.tasks) == 9

    # Verify the chain
    expected = [
        "resolve_target_date", "wait_for_pos_file", "land_pos_file",
        "load_pos_orders", "conform_orders", "curate_orders",
        "build_marts", "dq_checks", "enforce_dq", "publish_marts",
    ]
    assert [t.task_id for t in dag.topological_sort()] == expected

    # No cycles
    dag.validate_schedule_and_params()


def test_target_date_resolution():
    assert _resolve_target_date({"target_date": "2026-01-15"}) == "2026-01-15"
```

```bash
# Airflow's DAG integrity test
airflow dags test retailmart_daily 2026-01-15
```

---

## 🛠️ Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `DagRun already exists` | Two runs of the same interval | `max_active_runs=1` and `catchup=False` |
| `Task failed: BigQuery job exceeded ... bytes` | Unbounded scan | Add a partition filter on `target_date` |
| `The task is not being executed` | Missing dependency | Add the `>>` operator |
| `Sensor timed out` | File never arrived | Increase `timeout`; check the upstream producer |
| `Composer worker out of memory` | Query too large | Increase `machine_type` or `worker` node count |
| `Composer environment is degraded` | Version upgrade failed | Check the environment's `image_version` and rollback |
| `XComArg` has no attribute `execute` | Using the XComArg where a value is needed | Use `.output` to reference, `.resolve()` to evaluate |
| `Backfill produced wrong data` | Task used `CURRENT_DATE()` | Parameterize every task by `target_date` |
| `AirflowTaskTimeout` | Long-running query | Raise `execution_timeout`, or use a BigQuery job that polls |

---

## 💡 Production Notes

- **Never use `CURRENT_DATE()` in a DAG task.** Use `data_interval_start` or a `target_date`
  param. This is the single rule that makes backfills possible.
- **Set `max_active_runs=1`** for daily pipelines — overlapping runs cause duplicate data.
- **Use `mode="reschedule"` on sensors** to avoid holding worker slots.
- **Set `retries`, `retry_delay`, and `retry_exponential_backoff`** on every task.
- **XComs are for small values only.** Large data moves through storage.
- **Use `CREATE OR REPLACE` for marts** and `INSERT` for append-only curated tables.
- **Make the DQ gate a task that raises**, not a query that just writes a result row.
- **Version the Composer environment image** — do not float to `latest`.

---

## 🔑 Key Takeaways

- Airflow orchestrates; it does not transform data. Keep the DAG thin.
- **`target_date` / `data_interval_start` instead of `CURRENT_DATE()`** — the backfill rule.
- `BigQueryExecuteQueryOperator` for SQL, `BigQueryInsertJobOperator` for loads,
  `GCSToGCSOperator` for file moves.
- Sensors wait for conditions; use `mode="reschedule"`.
- XComs carry small values only.
- The DQ gate must **raise** to fail the DAG.

---

## 📚 Practice Exercises

1. **Complete the DAG.** Add tasks for product master ingestion, FX rate ingestion, and a
   materialized view refresh. Wire the dependencies correctly.

2. **Idempotency test.** Run the same `target_date` twice. Prove no rows are duplicated. Fix
   whatever breaks.

3. **Backfill drill.** Backfill 2026-01-01 → 2026-01-31. Measure the wall-clock time, the
   BigQuery bytes, and the cost. Then design an optimization.

4. **SLA and alerting.** Add `sla_miss_callback` to every task. Design the alert routing: email
   for warnings, a PagerDuty webhook for the DQ gate, and a Slack channel for informational
   messages.

5. **Composer sizing.** Given the DAG above, size the Composer environment (web server, workers,
   machine type) for a 30-minute run at 06:00 with a 4-hour backfill tolerance. Justify every
   number.

---

## 📖 Further Reading

- Airflow concepts — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html
- Cloud Composer — https://cloud.google.com/composer/docs/composer-2/overview
- BigQuery operators — https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/bigquery.html
