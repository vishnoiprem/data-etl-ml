"""Tests for all five 20_extra_topics SQL demos:

  - create_task.sql
  - create_stream.sql
  - create_materialized_view.sql
  - masking_policy.sql
  - rbac_grants.sql
"""
from __future__ import annotations

from pathlib import Path

import pytest

from conftest import parse_sql_statements

HERE = Path(__file__).resolve().parent
TASK_FILE       = HERE / "create_task.sql"
STREAM_FILE     = HERE / "create_stream.sql"
MV_FILE         = HERE / "create_materialized_view.sql"
MASK_FILE       = HERE / "masking_policy.sql"
RBAC_FILE       = HERE / "rbac_grants.sql"


# ── fixtures ───────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def task_text()  : return TASK_FILE.read_text()
@pytest.fixture(scope="module")
def stream_text(): return STREAM_FILE.read_text()
@pytest.fixture(scope="module")
def mv_text()    : return MV_FILE.read_text()
@pytest.fixture(scope="module")
def mask_text()  : return MASK_FILE.read_text()
@pytest.fixture(scope="module")
def rbac_text()  : return RBAC_FILE.read_text()


# ── create_task.sql ────────────────────────────────────────────────────
def test_task_uses_warehouse(task_text):
    """Tasks need a warehouse to run on."""
    assert "WAREHOUSE" in task_text.upper()
    assert "COMPUTE_WH" in task_text


def test_task_uses_cron_schedule(task_text):
    assert "USING CRON" in task_text.upper()


def test_task_inserts_into_target(task_text):
    assert "INSERT INTO" in task_text.upper()
    assert "ORDERS_HOURLY_AGG" in task_text


def test_task_lifecycle_resume_suspend(task_text):
    upper = task_text.upper()
    assert "RESUME"  in upper
    assert "SUSPEND" in upper
    assert "EXECUTE TASK" in upper


def test_task_parses_cleanly(task_text):
    stmts = parse_sql_statements(task_text)
    assert len(stmts) >= 4


# ── create_stream.sql ──────────────────────────────────────────────────
def test_stream_uses_append_only(stream_text):
    """APPEND_ONLY streams are cheaper because they don't track updates."""
    assert "APPEND_ONLY" in stream_text.upper()


def test_stream_uses_system_stream_has_data(stream_text):
    assert "SYSTEM$STREAM_HAS_DATA" in stream_text.upper()


def test_stream_uses_metadata_columns(stream_text):
    """Streams expose METADATA$ACTION / METADATA$ISUPDATE / METADATA$ROW_ID."""
    assert "METADATA$ACTION" in stream_text.upper()
    assert "METADATA$ISUPDATE" in stream_text.upper()


def test_stream_consumes_into_landing_table(stream_text):
    """A stream must be DML'd to be consumed."""
    assert "INSERT INTO" in stream_text.upper()
    assert "ORDERS_LANDING" in stream_text


def test_stream_parses_cleanly(stream_text):
    stmts = parse_sql_statements(stream_text)
    assert len(stmts) >= 4


# ── create_materialized_view.sql ───────────────────────────────────────
def test_mv_creates_materialized_view(mv_text):
    assert "CREATE OR REPLACE MATERIALIZED VIEW" in mv_text.upper()


def test_mv_uses_cluster_by(mv_text):
    """MVs can carry their own clustering key."""
    assert "CLUSTER BY" in mv_text.upper()


def test_mv_uses_refresh_history(mv_text):
    assert "MATERIALIZED_VIEW_REFRESH_HISTORY" in mv_text.upper()


def test_mv_groups_by_region(mv_text):
    upper = mv_text.upper()
    assert "GROUP"  in upper
    assert "REGION" in upper


def test_mv_parses_cleanly(mv_text):
    stmts = parse_sql_statements(mv_text)
    assert len(stmts) >= 3


# ── masking_policy.sql ─────────────────────────────────────────────────
def test_masking_creates_policy(mask_text):
    assert "CREATE OR REPLACE MASKING POLICY" in mask_text.upper()


def test_masking_uses_current_role(mask_text):
    """Role-based policy logic is the most common pattern."""
    assert "CURRENT_ROLE()" in mask_text.upper()


def test_masking_attaches_with_alter(mask_text):
    assert "MODIFY COLUMN" in mask_text.upper()
    assert "SET MASKING POLICY" in mask_text.upper()


def test_masking_uses_regexp_for_partial(mask_text):
    """Email masking should partial-redact, not null out."""
    assert "REGEXP_REPLACE" in mask_text.upper()


def test_masking_parses_cleanly(mask_text):
    stmts = parse_sql_statements(mask_text)
    assert len(stmts) >= 3


# ── rbac_grants.sql ────────────────────────────────────────────────────
def test_rbac_creates_roles(rbac_text):
    assert "CREATE ROLE" in rbac_text.upper()
    assert "IF NOT EXISTS" in rbac_text.upper()


def test_rbac_grants_role_to_role(rbac_text):
    """Snowflake's role hierarchy is a DAG via GRANT ROLE."""
    assert "GRANT ROLE" in rbac_text.upper()


def test_rbac_grants_future_tables(rbac_text):
    assert "FUTURE TABLES" in rbac_text.upper()


def test_rbac_shows_grants(rbac_text):
    assert "SHOW GRANTS" in rbac_text.upper()


def test_rbac_parses_cleanly(rbac_text):
    stmts = parse_sql_statements(rbac_text)
    assert len(stmts) >= 6
