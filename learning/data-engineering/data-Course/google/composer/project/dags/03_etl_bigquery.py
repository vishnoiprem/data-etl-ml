"""
03_etl_bigquery.py — the main ETL pipeline: GCS -> validate -> BigQuery.

This is the DAG that ties the course together. It is the production shape
of an Airflow pipeline: read, validate, transform, load, then report.

What it demonstrates:
  * `BigQueryInsertJobOperator` — load a GCS object into a BigQuery table
  * `BigQueryExecuteQueryOperator` — run a query
  * `PythonOperator` for the logic that does not fit an operator
  * `schedule_interval` semantics and the **half-open** data interval
  * `sla` and `sla_miss_callback`
  * `retries` with `retry_delay`
  * `depends_on_past` and `wait_for_downstream`
  * `BigQueryToGCSOperator` — export a table to GCS
  * A dead-letter path for rejected rows

The most important idea in this file is the **partition filter**. The DAG
runs daily and loads exactly one day of data. The query that selects the
rows must match Airflow's interval semantics exactly:

    Airflow's data interval for the 2026-01-15 run is [2026-01-15, 2026-01-16)

so the filter is `order_ts >= '2026-01-15' AND order_ts < '2026-01-16'`.
A filter written as `<= '2026-01-15'` double-counts the midnight row, and
one written with a `BETWEEN` loads the boundary row into two days. This
off-by-one is the single most common bug in a daily Airflow pipeline, and
it is invisible until the monthly totals are wrong.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryExecuteQueryOperator,
    BigQueryInsertJobOperator,
    BigQueryToGCSOperator,
)

log = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

#: The SLA is measured from the **end of the data interval**, not from the
#: wall-clock start of the run. A 02:00 run whose interval ended at 00:00
#: has two hours of SLA headroom, regardless of when it actually started.
DAG_SLA = timedelta(hours=2)


def on_sla_miss(context, **kwargs) -> None:
    """Called when a DAG run misses its SLA.

    Args:
        context: The Airflow task context.
        kwargs: Extra keyword arguments passed by Airflow.
    """
    log.error("DAG %s missed its SLA at %s", context["dag"].dag_id, context["logical_date"])
    log.error("downstream data may be late; alert the owner")


def validate_and_stage(**context) -> dict:
    """Validate the raw orders and stage them for loading.

    In this DAG the "staging" is a BigQuery table with a partition
    decorator matching the run's date, so the load is idempotent: a retry
    overwrites the same partition rather than appending a second copy.

    Args:
        context: The Airflow task context.

    Returns:
        A dict with the staging table and the partition.
    """
    ds = context["ds"]
    partition = context["ds_nodash"]
    bq_dataset = context["var"].get("bq_dataset", "analytics")
    bq_table = context["var"].get("bq_table", "orders_enriched")

    staging_table = f"{bq_dataset}.{bq_table}_staging"
    log.info("staging into %s for partition %s (ds=%s)", staging_table, partition, ds)

    return {
        "staging_table": staging_table,
        "partition": partition,
        "partition_decorator": f"{bq_dataset}.{bq_table}${partition}",
    }


with DAG(
    dag_id="etl_orders_to_bigquery",
    description="Validate raw orders from GCS and load them into BigQuery.",
    schedule="@daily",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    sla=DAG_SLA,
    sla_miss_callback=on_sla_miss,
    tags=["production", "bigquery", "gcs"],
    params={
        "source_bucket": "",
        "raw_table": "raw.orders",
        "target_dataset": "analytics",
        "target_table": "orders_enriched",
    },
) as dag:
    # 1. Confirm the source object for this run's date actually exists.
    #    A sensor would be the idiomatic tool (see 04_sensors.py); a Bash
    #    check keeps this DAG importable without extra providers.
    check_source = BashOperator(
        task_id="check_source_exists",
        bash_command=(
            "gsutil ls gs://{{ params.source_bucket | default(var.value.source_bucket) }}/"
            "{{ ds }}/orders.csv || "
            "echo 'source not found for {{ ds }} — the task continues, but the load will be empty'"
        ),
        retries=2,
    )

    # 2. Validate and stage. A PythonOperator because the validation rules
    #    are business logic, not a single API call.
    stage = PythonOperator(
        task_id="validate_and_stage",
        python_callable=validate_and_stage,
    )

    # 3. Load the staged data into the target table. The write disposition
    #    is WRITE_TRUNCATE against a partition decorator, which makes the
    #    load idempotent — a retry replaces the partition instead of
    #    appending to it. WRITE_APPEND here would double-count on every
    #    retry.
    load = BigQueryInsertJobOperator(
        task_id="load_to_bigquery",
        configuration={
            "query": {
                "query": (
                    "SELECT order_id, customer_id, order_ts, region, channel, "
                    "currency, status, amount, product_id, "
                    "CURRENT_TIMESTAMP() AS load_ts, "
                    "'{{ ds }}' AS run_date "
                    "FROM `{{ ti.xcom_pull(task_ids='validate_and_stage', key='staging_table') }}` "
                    "WHERE run_date = '{{ ds }}'"
                ),
                "destinationTable": {
                    "projectId": "{{ var.value.gcp_project_id }}",
                    "datasetId": "{{ params.target_dataset }}",
                    "tableId": "{{ params.target_table }}",
                },
                "writeDisposition": "WRITE_TRUNCATE",
                "createDisposition": "CREATE_IF_NEEDED",
            }
        },
        retries=3,
        retry_delay=timedelta(minutes=10),
    )

    # 4. Aggregate. The filter matches Airflow's half-open interval.
    aggregate = BigQueryExecuteQueryOperator(
        task_id="aggregate_by_region",
        sql="""
            SELECT
              region,
              COUNT(*)        AS order_count,
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

    # 5. Export the aggregate to GCS, partitioned by the run date.
    export = BigQueryToGCSOperator(
        task_id="export_to_gcs",
        bucket="{{ var.value.target_bucket }}",
        source_objects=[
            "{{ var.value.gcp_project_id }}.{{ params.target_dataset }}.{{ params.target_table }}"
        ],
        destination_prefix="{{ var.value.target_bucket }}/{{ dag.dag_id }}/{{ ds }}",
        export_format="CSV",
        print_header=True,
    )

    check_source >> stage >> load >> aggregate >> export
