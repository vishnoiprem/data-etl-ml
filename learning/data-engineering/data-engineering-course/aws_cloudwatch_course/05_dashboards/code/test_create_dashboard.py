"""Tests for create_dashboard.py.

Run with:  python3 -m pytest 05_dashboards/code/test_create_dashboard.py -v
"""

from __future__ import annotations

import os
import sys

import boto3
import pytest
from moto import mock_aws

os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import create_dashboard as cd  # noqa: E402


@pytest.fixture
def cw():
    with mock_aws():
        yield boto3.client("cloudwatch", region_name="us-east-1")


def test_create_dashboard_creates_three_widgets(cw):
    """1) The dashboard body has exactly 3 widgets."""
    body = cd.build_body()
    assert len(body["widgets"]) == 3


def test_get_dashboard_returns_expected_body(cw):
    """2) After put_dashboard, get_dashboard returns the same body."""
    body = cd.build_body()
    cd.upsert_dashboard(cw, cd.DASHBOARD_NAME, body, dry_run=False)
    got = cd.get_dashboard(cw, cd.DASHBOARD_NAME, dry_run=False)
    assert got is not None
    assert len(got["widgets"]) == 3
    titles = [w["properties"].get("title", "") for w in got["widgets"]]
    assert any("p99" in t for t in titles)
    assert any("ERROR" in t or "Recent" in t for t in titles)
    # The text widget's identifying content is in the markdown, not the title.
    markdowns = [w["properties"].get("markdown", "") for w in got["widgets"]]
    assert any("Runbook" in m for m in markdowns)


def test_widget_types_are_correct(cw):
    """3) Widget types are metric, log, text."""
    body = cd.build_body()
    types = [w["type"] for w in body["widgets"]]
    assert "metric" in types
    assert "log" in types
    assert "text" in types


def test_dry_run_does_not_call_put_dashboard(cw):
    """4) --dry-run suppresses the put_dashboard call."""
    body = cd.build_body()
    cd.upsert_dashboard(cw, cd.DASHBOARD_NAME, body, dry_run=True)
    # The dashboard should not be retrievable.
    got = cd.get_dashboard(cw, cd.DASHBOARD_NAME, dry_run=False)
    assert got is None
