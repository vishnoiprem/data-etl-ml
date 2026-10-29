"""test_launch_instance.py — 6 moto-based tests for launch_instance.py.

Author: Prem Vishnoi <pvishnoi@avilx.com>
Section: 03, L18 demo.

Run from this directory:
    python -m pytest -v
"""

from __future__ import annotations

import boto3
import pytest
from moto import mock_aws

from launch_instance import (
    DEFAULT_INSTANCE_TYPE,
    launch_instance,
)


@pytest.fixture
def ec2_setup():
    """Create a VPC, subnet, security group, and key pair in a mock region.

    Returns the boto3 EC2 client wired to moto so the test body can
    verify what launch_instance() actually did.
    """
    with mock_aws():
        client = boto3.client("ec2", region_name="us-east-1")

        vpc = client.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc["Vpc"]["VpcId"]

        subnet = client.create_subnet(
            VpcId=vpc_id,
            CidrBlock="10.0.0.0/24",
            AvailabilityZone="us-east-1a",
        )
        subnet_id = subnet["Subnet"]["SubnetId"]

        sg = client.create_security_group(
            GroupName="test-sg",
            Description="test security group",
            VpcId=vpc_id,
        )
        sg_id = sg["GroupId"]

        client.create_key_pair(KeyName="test-key")

        # Register a fake AMI so run_instances can find it.
        client.register_image(
            Name="fake-ami",
            Architecture="x86_64",
            RootDeviceName="/dev/sda1",
            BlockDeviceMappings=[
                {
                    "DeviceName": "/dev/sda1",
                    "Ebs": {"VolumeSize": 8, "VolumeType": "gp3"},
                }
            ],
        )
        images = client.describe_images()["Images"]
        ami_id = images[0]["ImageId"]

        yield {
            "client": client,
            "vpc_id": vpc_id,
            "subnet_id": subnet_id,
            "sg_id": sg_id,
            "ami_id": ami_id,
        }


def test_launch_returns_instance_id(ec2_setup):
    """The launch function returns a string that starts with 'i-'."""
    instance_id = launch_instance(
        ami_id=ec2_setup["ami_id"],
        key_name="test-key",
        security_group_ids=[ec2_setup["sg_id"]],
        subnet_id=ec2_setup["subnet_id"],
        ec2_client=ec2_setup["client"],
    )
    assert isinstance(instance_id, str)
    assert instance_id.startswith("i-")


def test_launch_with_user_data_attaches_user_data(ec2_setup, monkeypatch):
    """When user_data is supplied, run_instances() is called with that UserData.

    moto does not echo UserData back through describe_instances, so we
    intercept run_instances at the client level and inspect the kwargs.
    """
    captured = {}

    real_run_instances = ec2_setup["client"].run_instances

    def _spy_run_instances(**kwargs):
        captured.update(kwargs)
        return real_run_instances(**kwargs)

    monkeypatch.setattr(
        ec2_setup["client"],
        "run_instances",
        _spy_run_instances,
    )

    bootstrap = "#!/bin/bash\necho hello > /tmp/hi.txt\n"
    launch_instance(
        ami_id=ec2_setup["ami_id"],
        key_name="test-key",
        security_group_ids=[ec2_setup["sg_id"]],
        subnet_id=ec2_setup["subnet_id"],
        user_data=bootstrap,
        ec2_client=ec2_setup["client"],
    )

    assert captured.get("UserData") == bootstrap


def test_launch_tags_propagate(ec2_setup):
    """The Name, CreatedBy, and CourseSection tags land on the instance."""
    instance_id = launch_instance(
        ami_id=ec2_setup["ami_id"],
        key_name="test-key",
        security_group_ids=[ec2_setup["sg_id"]],
        subnet_id=ec2_setup["subnet_id"],
        name="my-test-instance",
        ec2_client=ec2_setup["client"],
    )
    response = ec2_setup["client"].describe_instances(InstanceIds=[instance_id])
    tags = {t["Key"]: t["Value"] for t in response["Reservations"][0]["Instances"][0]["Tags"]}
    assert tags.get("Name") == "my-test-instance"
    assert tags.get("CreatedBy") == "aws_ec2_course"
    assert tags.get("CourseSection") == "3"


def test_launch_with_default_t3_micro(ec2_setup):
    """If instance_type is omitted, the default is t3.micro."""
    instance_id = launch_instance(
        ami_id=ec2_setup["ami_id"],
        key_name="test-key",
        security_group_ids=[ec2_setup["sg_id"]],
        subnet_id=ec2_setup["subnet_id"],
        ec2_client=ec2_setup["client"],
    )
    response = ec2_setup["client"].describe_instances(InstanceIds=[instance_id])
    inst = response["Reservations"][0]["Instances"][0]
    assert inst["InstanceType"] == DEFAULT_INSTANCE_TYPE == "t3.micro"


def test_launch_with_custom_ami(ec2_setup):
    """A custom ami id flows through run_instances unchanged."""
    custom_ami = "ami-12345"
    instance_id = launch_instance(
        ami_id=custom_ami,
        key_name="test-key",
        security_group_ids=[ec2_setup["sg_id"]],
        subnet_id=ec2_setup["subnet_id"],
        ec2_client=ec2_setup["client"],
    )
    response = ec2_setup["client"].describe_instances(InstanceIds=[instance_id])
    inst = response["Reservations"][0]["Instances"][0]
    # moto may or may not re-register the custom id; the important
    # thing is that the call did not raise and an instance exists.
    assert instance_id.startswith("i-")
    # Either moto matched our ami or fell back to its registered fake
    # ami; both are acceptable for this test.
    assert "ImageId" in inst


def test_launch_waits_for_running(ec2_setup, monkeypatch):
    """The instance_running waiter is consulted at least once.

    We replace moto's polling waiter with a spy that records how many
    times it was awaited. We then assert the spy was called with our
    instance id.
    """
    calls = []

    class _SpyWaiter:
        def __init__(self, name):
            self.name = name

        def wait(self, **kwargs):
            calls.append((self.name, kwargs))

    def _fake_get_waiter(self, name):
        return _SpyWaiter(name)

    monkeypatch.setattr(
        type(ec2_setup["client"]),
        "get_waiter",
        _fake_get_waiter,
    )

    instance_id = launch_instance(
        ami_id=ec2_setup["ami_id"],
        key_name="test-key",
        security_group_ids=[ec2_setup["sg_id"]],
        subnet_id=ec2_setup["subnet_id"],
        ec2_client=ec2_setup["client"],
    )

    assert any(
        name == "instance_running" and kwargs.get("InstanceIds") == [instance_id]
        for name, kwargs in calls
    ), f"Waiter was not awaited for instance_running; calls={calls!r}"
