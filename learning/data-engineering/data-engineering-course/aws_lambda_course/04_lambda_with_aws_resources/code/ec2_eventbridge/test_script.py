"""Tests for the L17 EventBridge wrapper.

Run with:  pytest test_script.py -v

These tests assert event-shape normalization. They use moto's EC2
mock so the delegated L16 handler can run end to end.
"""

import os
import sys

# The wrapper imports the L16 handler from the sibling directory.
# Add the sibling dir to sys.path so the import resolves.
_SIBLING = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ec2_lifecycle")
sys.path.insert(0, _SIBLING)

import boto3  # noqa: E402
import pytest  # noqa: E402
from moto import mock_aws  # noqa: E402

os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

import eventbridge_scheduled_start_stop as wrapper  # noqa: E402
import start_stop_ec2  # noqa: E402  -- imported by the wrapper


@mock_aws
def test_handler_unwraps_detail_payload():
    # Spin up an instance so the delegated L16 handler has something to start.
    create_result = start_stop_ec2.handler({"action": "create", "name": "demo"}, None)
    instance_id = create_result["instance_id"]
    start_stop_ec2.handler({"action": "stop", "instance_id": instance_id}, None)

    eb_event = {
        "version": "0",
        "id": "demo-event-id",
        "detail-type": "Scheduled Event",
        "source": "aws.events",
        "time": "2026-10-10T08:00:00Z",
        "region": "us-east-1",
        "resources": ["arn:aws:events:us-east-1:123456789012:rule/StartRule"],
        "detail": {"action": "start", "instance_id": instance_id},
    }

    result = wrapper.handler(eb_event, None)
    assert result["action"] == "start"
    assert result["state"] == "running"
    assert result["instance_id"] == instance_id


@mock_aws
def test_handler_passes_through_flat_payload():
    create_result = start_stop_ec2.handler({"action": "create", "name": "demo"}, None)
    instance_id = create_result["instance_id"]

    flat_event = {"action": "stop", "instance_id": instance_id}
    result = wrapper.handler(flat_event, None)
    assert result["action"] == "stop"
    assert result["state"] == "stopped"


@mock_aws
def test_handler_raises_when_action_missing():
    with pytest.raises(ValueError):
        wrapper.handler({"detail": {}}, None)
