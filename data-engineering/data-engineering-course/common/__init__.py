"""Shared utilities for the Data Engineering tracks.

This package is the data engineering equivalent of the
``system_design/common/`` library. It is intentionally separate so
the two tracks can evolve independently. Tracks that depend on
this package:

  * ``data_modeling/``
  * ``data_pipeline_design/``
  * ``sql_interviews/``
  * ``coding_interviews/``

Public API re-exports live here so the typical import is just::

    from common import QueryRunner, Table, Column, make_orders
"""

from .analytics import (
    dedupe_by_key,
    group_count,
    p50_p95_p99,
    rank_desc,
    running_total,
    safe_div,
    top_k_by,
)
from .csv_utils import read_csv, read_jsonl, stream_csv, write_csv, write_jsonl
from .data_gen import (
    make_events,
    make_orders,
    make_products,
    make_users,
    seed_all,
)
from .fixtures import SAMPLE_DATA_DIR, fixture_path, list_fixtures
from .jinja_helpers import render_sql
from .pipeline import Pipeline, PipelineError, with_idempotency
from .query import QueryRunner
from .schema import (
    Column,
    Table,
    add_foreign_keys,
    create_index_sqlite,
    create_table_sqlite,
    drop_table_sqlite,
)

__all__ = [
    # schema
    "Column",
    "Table",
    "create_table_sqlite",
    "create_index_sqlite",
    "drop_table_sqlite",
    "add_foreign_keys",
    # query
    "QueryRunner",
    # data_gen
    "make_users",
    "make_products",
    "make_orders",
    "make_events",
    "seed_all",
    # pipeline
    "Pipeline",
    "PipelineError",
    "with_idempotency",
    # csv
    "read_csv",
    "write_csv",
    "stream_csv",
    "read_jsonl",
    "write_jsonl",
    # analytics
    "running_total",
    "rank_desc",
    "dedupe_by_key",
    "p50_p95_p99",
    "top_k_by",
    "group_count",
    "safe_div",
    # fixtures
    "SAMPLE_DATA_DIR",
    "fixture_path",
    "list_fixtures",
    # jinja
    "render_sql",
]
