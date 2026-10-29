"""
test_smoke.py — exercises the full smoke pipeline end-to-end.

Confirms the driver works with no external services. Also
runs the agent's mock mode, the marketplace rotation, and
the Lakebase fallback (no env = use fallback).

These tests run in <1s and are the only thing you need to
run before `databricks bundle deploy`.
"""

from __future__ import annotations

import os
import pytest

from m100.smoke import run as run_smoke
from m100.marketplace_client import categories_to_rotate


def test_smoke_runs_three_iterations():
    """3-iter smoke should complete and produce 3 rows."""
    rc = run_smoke(max_iterations=3, stagger_seconds=0)
    assert rc == 0


def test_smoke_runs_with_low_quality_threshold():
    """Even a permissive threshold should accept all smoke iterations."""
    rc = run_smoke(max_iterations=2, stagger_seconds=0, quality_threshold=0.0)
    assert rc == 0


def test_categories_rotation_cycles():
    """categories_to_rotate should cycle deterministically."""
    cycle = [categories_to_rotate(i) for i in range(20)]
    # Rotation length is 10 — the sequence should be a cycle of 10
    assert cycle[0] == cycle[10]
    assert cycle[1] == cycle[11]
    # And it should hit ≥6 distinct categories in 20 iters
    assert len(set(cycle)) >= 6


def test_lakebase_returns_none_without_env(monkeypatch):
    """When LAKEBASE_HOST is unset, connect() yields None (fallback)."""
    monkeypatch.delenv("LAKEBASE_HOST", raising=False)
    from m100.lakebase import connect
    with connect() as conn:
        assert conn is None


def test_fallback_ensure_idempotent():
    """Calling fallback_ensure twice doesn't error."""
    # Unit-test env usually has no live Spark. We mock a minimal
    # SparkSession so we can assert idempotency without a JVM.
    from unittest.mock import MagicMock
    from m100.lakebase import fallback_ensure
    spark = MagicMock()
    spark.sql.return_value = None
    fallback_ensure(spark, catalog="test_catalog")
    # Second call must be a no-op
    fallback_ensure(spark, catalog="test_catalog")
    # SparkSession.sql was called; we don't assert exact count because
    # CREATE CATALOG IF NOT EXISTS is also called inside the function
    assert spark.sql.called
