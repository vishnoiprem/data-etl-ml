"""Tests for put_metric_alarm.py.

Run with:  python3 -m pytest 04_alarms/code/test_put_metric_alarm.py -v
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

import put_metric_alarm as pma  # noqa: E402


@pytest.fixture
def clients():
    with mock_aws():
        sns = boto3.client("sns", region_name="us-east-1")
        cw = boto3.client("cloudwatch", region_name="us-east-1")
        yield sns, cw


def test_create_alarm_writes_alarm(clients):
    """1) After the run, the alarm is present in describe_alarms."""
    sns, cw = clients
    topic_arn = pma.ensure_topic(sns, dry_run=False)
    pma.ensure_alarm(cw, topic_arn, dry_run=False)
    desc = pma.describe_alarm(cw, dry_run=False)
    assert desc is not None
    assert desc["AlarmName"] == pma.ALARM_NAME
    assert desc["Namespace"] == "AWS/EC2"
    assert desc["MetricName"] == "CPUUtilization"
    assert desc["Threshold"] == 70.0
    assert desc["ComparisonOperator"] == "GreaterThanThreshold"
    assert desc["EvaluationPeriods"] == 3
    assert desc["DatapointsToAlarm"] == 3
    assert desc["Period"] == 60


def test_create_alarm_is_idempotent(clients):
    """2) Re-running ensure_alarm does not raise and leaves one alarm."""
    sns, cw = clients
    topic_arn = pma.ensure_topic(sns, dry_run=False)
    pma.ensure_alarm(cw, topic_arn, dry_run=False)
    pma.ensure_alarm(cw, topic_arn, dry_run=False)
    resp = cw.describe_alarms(AlarmNamePrefix=pma.ALARM_NAME)
    matching = [a for a in resp["MetricAlarms"] if a["AlarmName"] == pma.ALARM_NAME]
    assert len(matching) == 1


def test_alarm_has_sns_action(clients):
    """3) The alarm's AlarmActions include the topic ARN."""
    sns, cw = clients
    topic_arn = pma.ensure_topic(sns, dry_run=False)
    pma.ensure_alarm(cw, topic_arn, dry_run=False)
    desc = pma.describe_alarm(cw, dry_run=False)
    assert topic_arn in desc["AlarmActions"]


def test_alarm_is_enabled_and_insufficient_data(clients):
    """4) New alarms are enabled with TreatMissingData=notBreaching.

    Note: real AWS starts a new alarm in INSUFFICIENT_DATA until at
    least one datapoint arrives. moto 5.x's CloudWatch mock starts
    new alarms in OK. We therefore accept either initial state here —
    the canonical teaching in the lecture still holds.
    """
    sns, cw = clients
    topic_arn = pma.ensure_topic(sns, dry_run=False)
    pma.ensure_alarm(cw, topic_arn, dry_run=False)
    desc = pma.describe_alarm(cw, dry_run=False)
    assert desc["ActionsEnabled"] is True
    assert desc["StateValue"] in ("INSUFFICIENT_DATA", "OK")
    assert desc["TreatMissingData"] == "notBreaching"


def test_dry_run_does_not_call_put_metric_alarm(clients):
    """5) --dry-run suppresses the put_metric_alarm call."""
    sns, cw = clients
    pma.ensure_topic(sns, dry_run=False)
    pma.ensure_alarm(cw, "arn:aws:sns:us-east-1:111122223333:dry", dry_run=True)
    # No alarm should exist.
    resp = cw.describe_alarms(AlarmNamePrefix=pma.ALARM_NAME)
    assert resp["MetricAlarms"] == []
