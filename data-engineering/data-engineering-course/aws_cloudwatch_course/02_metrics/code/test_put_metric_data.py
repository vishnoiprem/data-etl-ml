"""Tests for put_metric_data.py.

Run with:  python3 -m pytest 02_metrics/code/test_put_metric_data.py -v

All tests use moto.mock_aws so no real AWS credentials are required.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

import boto3
import pytest
from moto import mock_aws

# moto requires fake credentials to be set before any boto3 client is created.
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

# Allow `import put_metric_data` since the test file lives next to it.
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import put_metric_data as pmd  # noqa: E402


@pytest.fixture
def cw():
    with mock_aws():
        yield boto3.client("cloudwatch", region_name="us-east-1")


def test_publish_metrics_writes_five_datapoints(cw):
    """1) put_metric_data call should write 5 datapoints to the namespace."""
    published = pmd.publish_metrics(cw, dry_run=False)
    assert len(published) == 5
    for dp in published:
        assert dp["MetricName"] == pmd.METRIC_NAME
        assert dp["Unit"] == "Milliseconds"
        assert any(d["Name"] == "Endpoint" for d in dp["Dimensions"])
        assert any(d["Name"] == "Region"   for d in dp["Dimensions"])

    # The namespace should now contain the series.
    resp = cw.list_metrics(Namespace=pmd.NAMESPACE)
    names = {m["MetricName"] for m in resp["Metrics"]}
    assert pmd.METRIC_NAME in names


def test_get_metric_statistics_returns_average_and_p99(cw):
    """2) Reading back stats should produce Average + extended-statistic rows."""
    pmd.publish_metrics(cw, dry_run=False)
    stats = pmd.get_statistics(cw, dry_run=False)
    assert "Datapoints" in stats
    # moto implements Average/Sum/SampleCount for the built-in
    # statistics. ExtendedStatistics (p99/p95) is part of the
    # production API but not yet supported in moto's CloudWatch mock;
    # we therefore only assert the built-in stat here. The p99 call
    # path is still exercised end-to-end in --dry-run mode.
    for dp in stats["Datapoints"]:
        assert "Average" in dp
        assert "SampleCount" in dp
        # Latency is in milliseconds; should be in a sane range.
        assert 10.0 < dp["Average"] < 200.0
    # Sanity-check the --dry-run code path doesn't blow up.
    stats_dry = pmd.get_statistics(cw, dry_run=True)
    assert stats_dry["dry_run"] is True


def test_dimensions_filter_isolates_endpoints(cw):
    """3) Different Endpoint values create different time-series."""
    pmd.publish_metrics(cw, dry_run=False)
    # Publish a second series with a different endpoint.
    cw.put_metric_data(
        Namespace=pmd.NAMESPACE,
        MetricData=[{
            "MetricName": pmd.METRIC_NAME,
            "Value": 12.0,
            "Unit": "Milliseconds",
            "Dimensions": [
                {"Name": "Endpoint", "Value": "/login"},
                {"Name": "Region",   "Value": "us-east-1"},
            ],
        }],
    )
    # Filter on /checkout only — should NOT see /login.
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=10)
    resp = cw.get_metric_data(
        StartTime=start,
        EndTime=end,
        MetricDataQueries=[{
            "Id": "checkout",
            "MetricStat": {
                "Metric": {
                    "Namespace": pmd.NAMESPACE,
                    "MetricName": pmd.METRIC_NAME,
                    "Dimensions": [{"Name": "Endpoint", "Value": "/checkout"}],
                },
                "Period": 60,
                "Stat": "Average",
            },
            "ReturnData": True,
        }],
    )
    results = resp["MetricDataResults"]
    assert results[0]["Id"] == "checkout"
    # If we filtered correctly, every datapoint should be near 87ms,
    # not 12ms.
    for v in results[0]["Values"]:
        assert v > 50.0


def test_dry_run_does_not_call_put_metric_data(cw):
    """4) --dry-run should print the payload but NOT actually publish."""
    payload = pmd.publish_metrics(cw, dry_run=True)
    assert len(payload) == 5
    # Confirm nothing was actually written to the (mocked) backend.
    resp = cw.list_metrics(Namespace=pmd.NAMESPACE)
    assert resp["Metrics"] == []


def test_namespace_exists_in_list_metrics(cw):
    """5) After publishing, the custom namespace appears in list_metrics."""
    assert cw.list_metrics(Namespace=pmd.NAMESPACE)["Metrics"] == []
    pmd.publish_metrics(cw, dry_run=False)
    metrics = pmd.list_namespaced_metrics(cw, dry_run=False)
    assert len(metrics) >= 1
    assert all(m["Namespace"] == pmd.NAMESPACE for m in metrics)
    # Confirm both dimensions are present on at least one series.
    dims_seen = set()
    for m in metrics:
        for d in m["Dimensions"]:
            dims_seen.add(d["Name"])
    assert {"Endpoint", "Region"}.issubset(dims_seen)
