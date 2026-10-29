"""
dag_config.py — shared configuration for the Composer course DAGs.

Every value here can be overridden by an **Airflow Variable**, which is the
point: the same DAG file runs in a dev environment and a prod environment
without being edited. A Variable is the right tool for a value that differs
per environment; a `params` entry is the right tool for a value that differs
per *run*.

The pattern used throughout the course:

    # hard-coded default  →  Variable override  →  param override
    BUCKET = "{{ params.bucket | default(var.value.gcs_bucket) }}"

Where to put things:

    * ``params``    — differs per DAG *run* (e.g. a backfill date range).
    * ``Variables`` — differs per *environment* (bucket names, project IDs).
    * ``Connections`` — holds *credentials*. Never put a password in a
      Variable; Variables are visible in the UI to anyone with access.
    * DAG file     — logic, structure, and the schedule.

The module has **no Airflow import**, so it can be imported by the local
runner and the tests as well as by the DAGs.
"""
from __future__ import annotations

import datetime as dt

# --------------------------------------------------------------------------
# Environment configuration (overridable by Airflow Variables)
# --------------------------------------------------------------------------

#: GCP project ID. In Composer this is usually available from the
#: metadata server, but an explicit Variable is clearer in a DAG.
GCP_PROJECT_ID = "{{ var.value.gcp_project_id | default('') }}"

#: Source bucket holding the raw CSVs.
SOURCE_BUCKET = "{{ var.value.source_bucket | default('') }}"

#: Destination bucket for transformed data.
TARGET_BUCKET = "{{ var.value.target_bucket | default('') }}"

#: BigQuery dataset the pipeline writes to.
BQ_DATASET = "{{ var.value.bq_dataset | default('analytics') }}"

#: BigQuery table the pipeline writes to.
BQ_TABLE = "{{ var.value.bq_table | default('orders_enriched') }}"

#: BigQuery table the pipeline reads from.
SOURCE_BQ_TABLE = "{{ var.value.source_bq_table | default('raw.orders') }}"

#: Dead-letter table for rejected rows.
REJECT_BQ_TABLE = "{{ var.value.reject_bq_table | default('analytics.orders_rejected') }}"

#: Maximum number of rows after which the pipeline switches to the
#: full-load path rather than the incremental path.
FULL_LOAD_THRESHOLD = "{{ var.value.full_load_threshold | default(1000000) }}"

# --------------------------------------------------------------------------
# Schedule and policy defaults
# --------------------------------------------------------------------------

#: The pipeline processes a daily window. The DAG's ``schedule`` matches.
SCHEDULE = "@daily"

#: How long the DAG is allowed to take before it is considered late.
#: Airflow's SLA is measured against the *data interval end*, not the
#: wall-clock start time.
DEFAULT_SLA = dt.timedelta(hours=2)

#: Retry policy applied to tasks that talk to remote systems.
DEFAULT_RETRIES = 2
DEFAULT_RETRY_DELAY = dt.timedelta(minutes=5)

#: The date the sample dataset is generated for. The DAGs default to
#: "yesterday", and the local runner overrides this.
SAMPLE_DATE = "2026-01-15"

#: Number of rows in the sample dataset, used by the local runner and the
#: branching DAG to exercise the full-load / incremental decision.
SAMPLE_ORDER_COUNT = 5000
