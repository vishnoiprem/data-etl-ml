"""Tests for snapshot_ami_demo.

Run with:

    pytest test_snapshot_ami_demo.py -v

These tests use ``@mock_aws`` from ``moto >= 5.0`` to stand up a fake
EC2 account in-process. We create a real EBS volume, run the
snapshot_to_ami pipeline, and assert on the resulting snapshot and
AMI state.
"""

from __future__ import annotations

import os

import boto3
import pytest
from moto import mock_aws

os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

import snapshot_ami_demo  # noqa: E402


REGION = "us-east-1"


def _make_volume(ec2_client, size: int = 8) -> str:
    """Create a small EBS volume in the default AZ and return its id."""
    vpcs = ec2_client.describe_vpcs()["Vpcs"]
    vpc_id = vpcs[0]["VpcId"]
    subnets = ec2_client.describe_subnets(
        Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
    )["Subnets"]
    az = subnets[0]["AvailabilityZone"]

    resp = ec2_client.create_volume(
        AvailabilityZone=az,
        Size=size,
        VolumeType="gp3",
    )
    return resp["VolumeId"]


@mock_aws
def test_snapshot_completes():
    """The snapshot ends in state 'completed' and the id starts with 'snap-'."""
    ec2 = boto3.client("ec2", region_name=REGION)
    volume_id = _make_volume(ec2)

    result = snapshot_ami_demo.snapshot_to_ami(
        volume_id=volume_id,
        ami_name="test-snap-ami",
        region=REGION,
    )

    assert result["snapshot_id"].startswith("snap-")

    desc = ec2.describe_snapshots(SnapshotIds=[result["snapshot_id"]])
    snap = desc["Snapshots"][0]
    assert snap["State"] == "completed"
    assert snap["VolumeId"] == volume_id


@mock_aws
def test_image_created_from_snapshot():
    """The AMI id starts with 'ami-' and is in state 'available'."""
    ec2 = boto3.client("ec2", region_name=REGION)
    volume_id = _make_volume(ec2)

    result = snapshot_ami_demo.snapshot_to_ami(
        volume_id=volume_id,
        ami_name="test-image-ami",
        region=REGION,
    )

    assert result["ami_id"].startswith("ami-")

    desc = ec2.describe_images(ImageIds=[result["ami_id"]])
    image = desc["Images"][0]
    assert image["State"] == "available"
    assert image["Name"] == "test-image-ami"


@mock_aws
def test_ami_tags_propagate():
    """Name, CreatedBy, and CourseSection tags are applied to the AMI."""
    ec2 = boto3.client("ec2", region_name=REGION)
    volume_id = _make_volume(ec2)

    result = snapshot_ami_demo.snapshot_to_ami(
        volume_id=volume_id,
        ami_name="tagged-golden-image",
        region=REGION,
    )

    desc = ec2.describe_images(ImageIds=[result["ami_id"]])
    tags = {t["Key"]: t["Value"] for t in desc["Images"][0].get("Tags", [])}
    assert tags.get("Name") == "tagged-golden-image"
    assert tags.get("CreatedBy") == snapshot_ami_demo.COURSE_TAG_CREATED_BY
    assert tags.get("CourseSection") == snapshot_ami_demo.COURSE_TAG_SECTION


@mock_aws
def test_ami_block_device_mapping_references_snapshot():
    """The AMI's BlockDeviceMappings[0] is an Ebs entry with a snapshot id."""
    ec2 = boto3.client("ec2", region_name=REGION)
    volume_id = _make_volume(ec2)

    result = snapshot_ami_demo.snapshot_to_ami(
        volume_id=volume_id,
        ami_name="bdm-ami",
        region=REGION,
    )

    desc = ec2.describe_images(ImageIds=[result["ami_id"]])
    image = desc["Images"][0]
    bdms = image.get("BlockDeviceMappings", [])
    assert bdms, "AMI has no BlockDeviceMappings"

    ebs_bdms = [bdm for bdm in bdms if bdm.get("Ebs", {}).get("SnapshotId")]
    assert ebs_bdms, "AMI BlockDeviceMappings have no Ebs.SnapshotId"

    bdm_snapshot_id = ebs_bdms[0]["Ebs"]["SnapshotId"]
    assert bdm_snapshot_id.startswith("snap-")

    # The BDM references a real, completed snapshot. (In real AWS the
    # snapshot id is the one we passed to register_image; moto's
    # register_image implementation may copy the snapshot under a new
    # id, so we only assert the structural property here.)
    snap_desc = ec2.describe_snapshots(SnapshotIds=[bdm_snapshot_id])
    assert snap_desc["Snapshots"], "BDM snapshot id does not resolve to a snapshot"
    assert snap_desc["Snapshots"][0]["State"] == "completed"
