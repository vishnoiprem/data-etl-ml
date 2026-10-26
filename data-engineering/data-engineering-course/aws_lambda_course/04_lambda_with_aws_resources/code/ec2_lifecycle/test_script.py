"""Tests for start_stop_ec2.handler.

Run with:  pytest test_script.py -v
"""

import os

import boto3
import pytest
from moto import mock_aws

os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

import start_stop_ec2  # noqa: E402


@mock_aws
def test_handler_creates_instance():
    result = start_stop_ec2.handler({"action": "create", "name": "demo"}, None)
    assert result["action"] == "create"
    assert result["state"] == "running"
    assert result["instance_id"].startswith("i-")

    ec2 = boto3.client("ec2", region_name="us-east-1")
    desc = ec2.describe_instances(InstanceIds=[result["instance_id"]])
    instance = desc["Reservations"][0]["Instances"][0]
    assert instance["State"]["Name"] == "running"

    tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}
    assert tags.get("Name") == "demo"


@mock_aws
def test_handler_starts_instance():
    # Create + stop, then start.
    create_result = start_stop_ec2.handler({"action": "create", "name": "demo"}, None)
    instance_id = create_result["instance_id"]
    start_stop_ec2.handler({"action": "stop", "instance_id": instance_id}, None)

    result = start_stop_ec2.handler({"action": "start", "instance_id": instance_id}, None)
    assert result["action"] == "start"
    assert result["state"] == "running"
    assert result["instance_id"] == instance_id


@mock_aws
def test_handler_stops_instance():
    create_result = start_stop_ec2.handler({"action": "create", "name": "demo"}, None)
    instance_id = create_result["instance_id"]

    result = start_stop_ec2.handler({"action": "stop", "instance_id": instance_id}, None)
    assert result["action"] == "stop"
    assert result["state"] == "stopped"
    assert result["instance_id"] == instance_id


@mock_aws
def test_handler_rejects_unknown_action():
    with pytest.raises(ValueError):
        start_stop_ec2.handler({"action": "reboot"}, None)
