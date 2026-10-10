"""Tests for 19_section/code/transactions_snapshot.sql."""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

SQL_PATH = pathlib.Path(__file__).resolve().parent / "transactions_snapshot.sql"


def _sql() -> str:
    return SQL_PATH.read_text()


def test_uses_snapshot_block():
    s = _sql()
    assert "{% snapshot" in s
    assert "{% endsnapshot %}" in s


def test_uses_timestamp_strategy():
    s = _sql()
    assert "strategy='timestamp'" in s


def test_declares_unique_key():
    s = _sql()
    assert "unique_key='tx_hash'" in s


def test_declares_updated_at():
    s = _sql()
    assert "updated_at='block_timestamp'" in s


def test_includes_invalidate_hard_deletes():
    s = _sql()
    assert "invalidate_hard_deletes=True" in s


def test_references_upstream_model():
    assert "{{ ref(" in _sql()


def test_author_signature():
    s = _sql()
    assert "Prem Vishnoi" in s
    assert "pvishnoi@avilx.com" in s
    assert "pvilx.com" not in s
