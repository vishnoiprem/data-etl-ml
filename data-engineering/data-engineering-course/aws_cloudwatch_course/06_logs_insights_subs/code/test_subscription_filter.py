"""Tests for subscription_filter.py.

Run with:  python3 -m pytest 06_logs_insights_subs/code/test_subscription_filter.py -v
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

import subscription_filter as sf  # noqa: E402


@pytest.fixture
def clients():
    with mock_aws():
        logs = boto3.client("logs", region_name="us-east-1")
        kinesis = boto3.client("kinesis", region_name="us-east-1")
        yield logs, kinesis


def test_create_subscription_filter(clients):
    """1) After the run, a subscription filter is in place."""
    logs, kinesis = clients
    sf.ensure_log_group(logs, dry_run=False)
    stream_arn = sf.ensure_stream(kinesis, dry_run=False)
    sf.ensure_subscription_filter(logs, stream_arn, dry_run=False)
    filters = sf.describe_filters(logs, dry_run=False)
    names = {f["filterName"] for f in filters}
    assert sf.FILTER_NAME in names


def test_subscription_filter_destination_attached(clients):
    """2) The filter's destinationArn matches the stream ARN."""
    logs, kinesis = clients
    sf.ensure_log_group(logs, dry_run=False)
    stream_arn = sf.ensure_stream(kinesis, dry_run=False)
    sf.ensure_subscription_filter(logs, stream_arn, dry_run=False)
    filters = sf.describe_filters(logs, dry_run=False)
    [flt] = [f for f in filters if f["filterName"] == sf.FILTER_NAME]
    assert flt["destinationArn"] == stream_arn


def test_subscription_filter_pattern_matches(clients):
    """3) The filter's filterPattern is 'ERROR'."""
    logs, kinesis = clients
    sf.ensure_log_group(logs, dry_run=False)
    stream_arn = sf.ensure_stream(kinesis, dry_run=False)
    sf.ensure_subscription_filter(logs, stream_arn, dry_run=False)
    filters = sf.describe_filters(logs, dry_run=False)
    [flt] = [f for f in filters if f["filterName"] == sf.FILTER_NAME]
    assert flt["filterPattern"] == "ERROR"


def test_dry_run_does_not_call_put_subscription_filter(clients):
    """4) --dry-run suppresses the put_subscription_filter call."""
    logs, kinesis = clients
    sf.ensure_log_group(logs, dry_run=False)
    stream_arn = sf.ensure_stream(kinesis, dry_run=False)
    sf.ensure_subscription_filter(logs, stream_arn, dry_run=True)
    filters = sf.describe_filters(logs, dry_run=False)
    assert filters == []
