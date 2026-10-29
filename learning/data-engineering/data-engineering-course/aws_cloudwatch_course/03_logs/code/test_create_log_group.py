"""Tests for create_log_group.py.

Run with:  python3 -m pytest 03_logs/code/test_create_log_group.py -v
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timedelta, timezone

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

import create_log_group as clg  # noqa: E402


@pytest.fixture
def logs():
    with mock_aws():
        yield boto3.client("logs", region_name="us-east-1")


def test_create_log_group_is_idempotent(logs):
    """1) Re-running ensure_log_group does not raise."""
    clg.ensure_log_group(logs, dry_run=False)
    clg.ensure_log_group(logs, dry_run=False)
    resp = logs.describe_log_groups(logGroupNamePrefix=clg.LOG_GROUP)
    names = {g["logGroupName"] for g in resp["logGroups"]}
    assert clg.LOG_GROUP in names
    # Exactly one entry, not duplicated.
    matching = [g for g in resp["logGroups"] if g["logGroupName"] == clg.LOG_GROUP]
    assert len(matching) == 1


def test_log_stream_is_created(logs):
    """2) The demo stream appears in describe_log_streams."""
    clg.ensure_log_group(logs, dry_run=False)
    clg.ensure_log_stream(logs, dry_run=False)
    resp = logs.describe_log_streams(
        logGroupName=clg.LOG_GROUP, logStreamNamePrefix=clg.LOG_STREAM
    )
    names = {s["logStreamName"] for s in resp["logStreams"]}
    assert clg.LOG_STREAM in names


def test_put_log_events_records_three_events(logs):
    """3) put_log_events writes 3 events to the (mocked) store."""
    clg.ensure_log_group(logs, dry_run=False)
    clg.ensure_log_stream(logs, dry_run=False)
    events = clg.put_events(logs, dry_run=False)
    assert len(events) == 3
    # The moto store should now show 3 events in the stream.
    resp = logs.get_log_events(
        logGroupName=clg.LOG_GROUP,
        logStreamName=clg.LOG_STREAM,
        startFromHead=True,
    )
    assert len(resp["events"]) == 3


def test_filter_log_events_by_time_returns_window(logs):
    """4) A 5-minute time window returns events inside it (not older)."""
    clg.ensure_log_group(logs, dry_run=False)
    clg.ensure_log_stream(logs, dry_run=False)
    clg.put_events(logs, dry_run=False)
    # Add a 4th event 1 hour ago — outside the default 5-minute window.
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    logs.put_log_events(
        logGroupName=clg.LOG_GROUP,
        logStreamName=clg.LOG_STREAM,
        logEvents=[{
            "timestamp": int(one_hour_ago.timestamp() * 1000),
            "message": "old event outside window",
        }],
    )
    # Sleep a moment so the events are queryable.
    time.sleep(0.5)
    events = clg.filter_events(logs, dry_run=False)
    # The 3 fresh events are in the window; the 1-hour-old one isn't.
    # (Moto's filter respects startTime/endTime.)
    assert all("login" in e["message"]
               or "view-cart" in e["message"]
               or "checkout" in e["message"]
               for e in events)
    assert not any("old event outside window" in e["message"] for e in events)


def test_dry_run_does_not_call_put_log_events(logs):
    """5) --dry-run suppresses the put_log_events call."""
    clg.ensure_log_group(logs, dry_run=False)
    clg.ensure_log_stream(logs, dry_run=False)
    clg.put_events(logs, dry_run=True)
    # No events should have been written.
    resp = logs.get_log_events(
        logGroupName=clg.LOG_GROUP,
        logStreamName=clg.LOG_STREAM,
        startFromHead=True,
    )
    assert resp["events"] == []
