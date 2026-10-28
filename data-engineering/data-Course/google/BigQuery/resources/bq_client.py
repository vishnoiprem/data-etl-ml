"""
bq_client.py — a production-grade BigQuery client for the course.

Copy this file into your project (or the notebooks/ directory) and use it
throughout. It provides:

    get_client()        - a configured, reused client (singleton)
    run_query()         - a query helper with a byte cap and typed parameters
    run_to_dataframe()  - the same, returning a DataFrame
    estimate_cost()     - a free, exact cost estimate
    dataset_exists()    - an existence check
    query_bytes()       - a lightweight "run this and tell me the bytes" helper

Usage:
    from bq_client import get_client, run_query, estimate_cost

    client = get_client()
    rows = run_query("SELECT 1 AS n")
"""
from __future__ import annotations

import datetime
import logging
import os
from typing import Any, Sequence

from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError, NotFound

log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

DEFAULT_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "YOUR_PROJECT_ID")
DEFAULT_LOCATION = os.environ.get("BQ_LOCATION", "US")
DEFAULT_MAX_BYTES = int(os.environ.get("BQ_MAX_BYTES_BILLED", 10 * 1024**4))
DEFAULT_ENV = os.environ.get("ENV", "dev")

# $6.25 per TiB on-demand
ON_DEMAND_PRICE_PER_TIB = 6.25

_client: bigquery.Client | None = None


# --------------------------------------------------------------------------
# Client
# --------------------------------------------------------------------------


def get_client(
    project: str = DEFAULT_PROJECT,
    location: str = DEFAULT_LOCATION,
    max_bytes_billed: int = DEFAULT_MAX_BYTES,
) -> bigquery.Client:
    """Return a configured BigQuery client. Reused across the process."""
    global _client
    if _client is not None:
        return _client

    job_config = bigquery.QueryJobConfig(
        maximum_bytes_billed=max_bytes_billed,
        labels={"env": DEFAULT_ENV},
        use_legacy_sql=False,
    )

    _client = bigquery.Client(
        project=project,
        location=location,
        default_query_job_config=job_config,
    )
    log.info("BigQuery client ready: project=%s location=%s", project, location)
    return _client


# --------------------------------------------------------------------------
# Type inference for parameters
# --------------------------------------------------------------------------


def infer_sql_type(value: Any) -> str:
    """Map a Python value to an explicit BigQuery SQL type."""
    if isinstance(value, bool):
        return "BOOL"
    if isinstance(value, int):
        return "INT64"
    if isinstance(value, float):
        return "FLOAT64"
    if isinstance(value, datetime.datetime):
        return "TIMESTAMP"
    if isinstance(value, datetime.date):
        return "DATE"
    if isinstance(value, (list, tuple)):
        return "STRING"
    if isinstance(value, dict):
        return "JSON"
    return "STRING"


def build_parameters(params: dict[str, Any] | None) -> list[bigquery.ScalarQueryParameter]:
    """Build typed query parameters from a dict."""
    if not params:
        return []
    return [
        bigquery.ScalarQueryParameter(name, infer_sql_type(value), value)
        for name, value in params.items()
    ]


# --------------------------------------------------------------------------
# Running queries
# --------------------------------------------------------------------------


def run_query(
    sql: str,
    params: dict[str, Any] | None = None,
    max_bytes_billed: int = DEFAULT_MAX_BYTES,
    client: bigquery.Client | None = None,
    labels: dict[str, str] | None = None,
) -> list[bigquery.Row]:
    """Run a query and return all rows as a list.

    Raises on error. Always applies a byte cap so a runaway query fails
    fast instead of billing.
    """
    client = client or get_client()

    job_config = bigquery.QueryJobConfig(
        maximum_bytes_billed=max_bytes_billed,
        use_query_cache=True,
        use_legacy_sql=False,
        query_parameters=build_parameters(params),
    )
    if labels:
        job_config.labels = {**job_config.labels, **labels} if job_config.labels else labels

    try:
        job = client.query(sql, job_config=job_config)
        rows = list(job.result())
        log.info(
            "Query ok: %s bytes, %s rows, cache_hit=%s",
            job.total_bytes_billed,
            len(rows),
            job.cache_hit,
        )
        return rows
    except GoogleCloudError as exc:
        log.error("Query failed: %s", exc)
        raise


def run_to_dataframe(
    sql: str,
    params: dict[str, Any] | None = None,
    max_bytes_billed: int = DEFAULT_MAX_BYTES,
    client: bigquery.Client | None = None,
    max_results: int | None = None,
) -> "Any":
    """Run a query and return the results as a pandas DataFrame."""
    client = client or get_client()

    job_config = bigquery.QueryJobConfig(
        maximum_bytes_billed=max_bytes_billed,
        use_query_cache=True,
        use_legacy_sql=False,
        query_parameters=build_parameters(params),
    )

    job = client.query(sql, job_config=job_config)
    return job.to_dataframe(
        max_results=max_results,
        progress_bar_type=None,
        create_bqstorage_client=False,
    )


# --------------------------------------------------------------------------
# Cost estimation
# --------------------------------------------------------------------------


def estimate_cost(
    sql: str,
    params: dict[str, Any] | None = None,
    client: bigquery.Client | None = None,
) -> dict[str, float]:
    """Estimate the cost of a query without running it. Free and exact."""
    client = client or get_client()

    job_config = bigquery.QueryJobConfig(
        dry_run=True,
        use_query_cache=False,
        use_legacy_sql=False,
        query_parameters=build_parameters(params),
    )
    job = client.query(sql, job_config=job_config)

    total_bytes = job.total_bytes_processed or 0
    tib = total_bytes / (1024**4)

    return {
        "bytes_processed": total_bytes,
        "tib": round(tib, 6),
        "estimated_cost_usd": round(tib * ON_DEMAND_PRICE_PER_TIB, 6),
    }


def query_bytes(sql: str, client: bigquery.Client | None = None) -> int:
    """Return the exact number of bytes a query would process."""
    return int(estimate_cost(sql, client=client)["bytes_processed"])


# --------------------------------------------------------------------------
# Datasets and tables
# --------------------------------------------------------------------------


def dataset_exists(dataset_id: str, client: bigquery.Client | None = None) -> bool:
    """Return True if the dataset exists."""
    client = client or get_client()
    try:
        client.get_dataset(dataset_id)
        return True
    except NotFound:
        return False


def table_exists(table_id: str, client: bigquery.Client | None = None) -> bool:
    """Return True if the table exists."""
    client = client or get_client()
    try:
        client.get_table(table_id)
        return True
    except NotFound:
        return False


def list_datasets_summary(client: bigquery.Client | None = None) -> list[dict]:
    """Return a summary of every dataset in the project."""
    client = client or get_client()
    summary = []
    for dataset in client.list_datasets(project=client.project):
        labels = dataset.labels or {}
        summary.append(
            {
                "dataset_id": dataset.dataset_id,
                "location": dataset.location,
                "description": dataset.description,
                "owner": labels.get("owner", "-"),
                "tier": labels.get("tier", "-"),
                "table_expiration_days": (
                    round(dataset.default_table_expiration_ms / 86_400_000)
                    if dataset.default_table_expiration_ms
                    else None
                ),
            }
        )
    return summary


# --------------------------------------------------------------------------
# Convenience
# --------------------------------------------------------------------------


def scalar(sql: str, params: dict[str, Any] | None = None, **kwargs) -> Any:
    """Run a query and return the first column of the first row."""
    rows = run_query(sql, params=params, **kwargs)
    if not rows:
        return None
    return list(rows[0].values())[0]


def count_rows(
    table_id: str,
    where: str | None = None,
    params: dict[str, Any] | None = None,
    **kwargs,
) -> int:
    """Count rows in a (optionally filtered) table."""
    sql = f"SELECT COUNT(*) FROM `{table_id}`"
    if where:
        sql += f" WHERE {where}"
    return int(scalar(sql, params=params, **kwargs) or 0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    client = get_client()
    print(f"Project: {client.project}")
    print(f"Location: {client.location}")
    print(f"Datasets: {len(list_datasets_summary(client))}")
