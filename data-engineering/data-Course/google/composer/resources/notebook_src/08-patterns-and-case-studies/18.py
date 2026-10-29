"""Case study A: the daily orders ETL, end to end in the mini-runner."""

from local_runner import DAG, Task, run_dag
from pipeline_logic import (
    logical_date_window,
    partition_for_date,
    render_summary_csv,
)

LOGICAL_DATE = "2026-01-15"


def read_orders(run, context):
    """Read the raw orders.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        The raw CSV lines.
    """
    path = COURSE_ROOT / "sample_data" / "orders.csv"
    return path.read_text(encoding="utf-8").splitlines()


def validate_and_stage(run, context):
    """Validate the rows and stage them, pushing a reference downstream.

    Note what crosses the task boundary: the *count*, not the rows. In
    Airflow the staged data lives in BigQuery and the task pushes the
    table name; here the staged rows live in XCom because they are small
    enough to be a teaching example. The shape is the same.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        A dict describing the staging.
    """
    from pipeline_logic import summarise_by_region, transform_orders

    raw = run.pull("read_orders") or []
    accepted, rejected = transform_orders(raw)
    run.xcom.push("validate_and_stage", "accepted", accepted)
    run.xcom.push("validate_and_stage", "rejected", rejected)
    run.xcom.push("validate_and_stage", "summary", summarise_by_region(accepted))
    partition = partition_for_date(context["ds"])
    return {
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "staging_table": "analytics.orders_enriched_staging",
        "partition": partition,
        "partition_decorator": f"analytics.orders_enriched${partition}",
    }


def load_to_bigquery(run, context):
    """Load the staged partition, idempotently.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        A description of the load.
    """
    staging = run.pull("validate_and_stage") or {}
    return (
        f"loaded {staging.get('accepted_count', 0)} rows into "
        f"{staging.get('partition_decorator', '?')} with WRITE_TRUNCATE"
    )


def aggregate_by_region(run, context):
    """Aggregate the loaded rows.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        The region summary.
    """
    summary = run.pull("validate_and_stage", "summary") or {}
    run.xcom.push("aggregate_by_region", "summary", summary)
    return summary


def publish_summary(run, context):
    """Publish the summary to a GCS-shaped path.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        The published URI.
    """
    summary = run.pull("aggregate_by_region", "summary") or {}
    bucket = context["__variables__"].get("target_bucket", "demo-target-bucket")
    uri = f"gs://{bucket}/{{dag.dag_id}}/{{ds}}/summary.csv"
    return {
        "uri": f"gs://{bucket}/etl_orders_to_bigquery/{context['ds']}/summary.csv",
        "template": uri,
        "csv": render_summary_csv(summary),
    }


def build_daily_etl_dag():
    """Build the daily ETL DAG.

    Returns:
        The DAG.
    """
    return DAG(
        "case_study_daily_etl",
        tasks=[
            Task("read_orders", read_orders),
            Task("validate_and_stage", validate_and_stage,
                 dependencies=["read_orders"]),
            Task("load_to_bigquery", load_to_bigquery,
                 dependencies=["validate_and_stage"]),
            Task("aggregate_by_region", aggregate_by_region,
                 dependencies=["load_to_bigquery"]),
            Task("publish_summary", publish_summary,
                 dependencies=["aggregate_by_region"]),
        ],
        schedule="@daily",
        start_date="2026-01-01",
        description="Read, validate, load, aggregate, publish.",
    )


DAILY_ETL_DAG = build_daily_etl_dag()
print(DAILY_ETL_DAG.describe())
print()

# ---------------------------------------------------------------------
# The half-open interval, verified
# ---------------------------------------------------------------------
print("=" * 70)
print("The half-open data interval")
print("=" * 70)
start, end = logical_date_window(LOGICAL_DATE)
print(f"  logical date       : {LOGICAL_DATE}")
print(f"  data_interval_start: {start}")
print(f"  data_interval_end  : {end}   (exclusive)")
print(f"  partition decorator: {partition_for_date(LOGICAL_DATE)}")
print()
print("  The SQL filter must be:")
print(f"    WHERE order_ts >= '{start}'")
print(f"      AND order_ts <  '{end}'")
print()
print("  A filter using '<=' would double-count the row at exactly midnight.")
print()

run = run_dag(DAILY_ETL_DAG, LOGICAL_DATE, verbose=True)
print()
print("=" * 70)
print("The result")
print("=" * 70)
published = run.pull("publish_summary")
print(f"  published to : {published['uri']}")
print()
print(published["csv"], end="")

EXPECTED = {
    "AMER": {"order_count": 318, "revenue_eur": 113592.19},
    "APAC": {"order_count": 285, "revenue_eur": 108194.92},
    "EMEA": {"order_count": 322, "revenue_eur": 118423.22},
    "LATAM": {"order_count": 320, "revenue_eur": 110646.18},
}
staging = run.pull("validate_and_stage")
summary = run.pull("aggregate_by_region", "summary")
assert summary == EXPECTED, f"summary changed: {summary}"
assert staging["accepted_count"] == 1245, staging
assert staging["rejected_count"] == 0, staging
print("PASS: the daily ETL produces the expected summary, "
      "accepted=1245 rejected=0.")
