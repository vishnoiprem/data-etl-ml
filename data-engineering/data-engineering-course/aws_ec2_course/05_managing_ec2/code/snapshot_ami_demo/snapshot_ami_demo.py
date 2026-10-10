"""Snapshot an EBS volume and register the result as a new AMI.

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 05 — Managing EC2
> **Companion to:** L24 (EBS Snapshots) + L25 (Custom AMIs) + L26 (recap).

What this script does
---------------------
1. Calls ``ec2.create_snapshot(VolumeId=...)`` to start a point-in-time
   copy of an EBS volume. The call returns immediately with the snapshot
   id in ``pending`` state.
2. Polls ``ec2.describe_snapshots(...)`` until ``State == "completed"``.
3. Calls ``ec2.register_image(Name=..., BlockDeviceMappings=[...])`` to
   register a new AMI whose only device is the completed snapshot.
   (``create_image`` would also work, but it requires an
   ``InstanceId``; for the "register a new AMI from an existing
   snapshot" path, the right call is ``register_image``.)
4. Polls ``ec2.describe_images(...)`` until ``State == "available"``.
5. Tags the new AMI with ``Name`` (the value passed in), ``CreatedBy``,
   and ``CourseSection``.
6. Returns the snapshot id and the AMI id.

Usage
-----
    python snapshot_ami_demo.py --volume-id vol-0123456789abcdef0 \\
        --ami-name my-golden-image

Required IAM permissions
------------------------
- ec2:CreateSnapshot
- ec2:DescribeSnapshots
- ec2:RegisterImage
- ec2:DescribeImages
- ec2:CreateTags
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger("snapshot_ami_demo")

DEFAULT_REGION = "us-east-1"
DEFAULT_POLL_INTERVAL_SECONDS = 5
DEFAULT_TIMEOUT_SECONDS = 600
COURSE_TAG_CREATED_BY = "aws_ec2_course"
COURSE_TAG_SECTION = "5"

DEVICE_NAME = "/dev/sda1"
ROOT_DEVICE_NAME = "/dev/sda1"


# ---------------------------------------------------------------------------
# Waiters (poll-and-sleep loop — fine for moto + small real workloads)
# ---------------------------------------------------------------------------
def _wait_for_snapshot(
    ec2_client: Any,
    snapshot_id: str,
    *,
    poll_interval: int = DEFAULT_POLL_INTERVAL_SECONDS,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Block until the snapshot reaches ``completed`` (or fail loudly)."""
    LOG.info("waiting for snapshot %s to reach 'completed'", snapshot_id)
    deadline = time.monotonic() + timeout
    while True:
        resp = ec2_client.describe_snapshots(SnapshotIds=[snapshot_id])
        snapshots = resp.get("Snapshots", [])
        if not snapshots:
            raise RuntimeError(f"snapshot {snapshot_id} disappeared")
        snap = snapshots[0]
        state = snap.get("State", "")
        if state == "completed":
            LOG.info("snapshot %s is completed", snapshot_id)
            return snap
        if state == "error":
            raise RuntimeError(
                f"snapshot {snapshot_id} entered error state: {snap.get('StateMessage')}"
            )
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"timed out after {timeout}s waiting for snapshot {snapshot_id}; "
                f"last state={state}"
            )
        time.sleep(poll_interval)


def _wait_for_image(
    ec2_client: Any,
    image_id: str,
    *,
    poll_interval: int = DEFAULT_POLL_INTERVAL_SECONDS,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Block until the AMI reaches ``available`` (or fail loudly)."""
    LOG.info("waiting for image %s to reach 'available'", image_id)
    deadline = time.monotonic() + timeout
    while True:
        resp = ec2_client.describe_images(ImageIds=[image_id])
        images = resp.get("Images", [])
        if not images:
            raise RuntimeError(f"image {image_id} disappeared")
        image = images[0]
        state = image.get("State", "")
        if state == "available":
            LOG.info("image %s is available", image_id)
            return image
        if state in ("failed", "error", "deregistered"):
            raise RuntimeError(f"image {image_id} entered terminal state {state!r}")
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"timed out after {timeout}s waiting for image {image_id}; "
                f"last state={state}"
            )
        time.sleep(poll_interval)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def snapshot_to_ami(
    volume_id: str,
    ami_name: str,
    *,
    region: str = DEFAULT_REGION,
    description: str | None = None,
) -> dict[str, str]:
    """Snapshot ``volume_id`` and register a new AMI from the snapshot.

    Returns a dict with ``snapshot_id`` and ``ami_id``.
    """
    ec2 = boto3.client("ec2", region_name=region)

    snap_description = description or f"snapshot of {volume_id} for AMI {ami_name}"
    LOG.info("creating snapshot of volume %s", volume_id)
    snap_resp = ec2.create_snapshot(
        VolumeId=volume_id,
        Description=snap_description,
    )
    snapshot_id = snap_resp["SnapshotId"]
    LOG.info("snapshot %s created in state %s", snapshot_id, snap_resp.get("State"))

    _wait_for_snapshot(ec2, snapshot_id)

    # ``ec2.create_image`` always requires an InstanceId, so for the
    # "register a new AMI from an existing snapshot" path we use the
    # lower-level ``register_image`` API. This is the same code path
    # that the EC2 console's "Create image" -> "from snapshot" flow
    # takes internally.
    LOG.info("registering AMI %s from snapshot %s", ami_name, snapshot_id)
    try:
        image_resp = ec2.register_image(
            Name=ami_name,
            Description=f"AMI registered from snapshot {snapshot_id}",
            Architecture="x86_64",
            RootDeviceName=ROOT_DEVICE_NAME,
            VirtualizationType="hvm",
            BlockDeviceMappings=[
                {
                    "DeviceName": DEVICE_NAME,
                    "Ebs": {
                        "SnapshotId": snapshot_id,
                        "DeleteOnTermination": True,
                        "VolumeType": "gp3",
                    },
                }
            ],
        )
    except ClientError as exc:
        raise RuntimeError(f"register_image failed: {exc}") from exc
    ami_id = image_resp["ImageId"]
    LOG.info("image %s registered", ami_id)

    _wait_for_image(ec2, ami_id)

    LOG.info("tagging AMI %s with course tags", ami_id)
    ec2.create_tags(
        Resources=[ami_id],
        Tags=[
            {"Key": "Name", "Value": ami_name},
            {"Key": "CreatedBy", "Value": COURSE_TAG_CREATED_BY},
            {"Key": "CourseSection", "Value": COURSE_TAG_SECTION},
        ],
    )

    return {"snapshot_id": snapshot_id, "ami_id": ami_id}


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------
def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Snapshot an EBS volume and register the result as a new AMI.",
    )
    parser.add_argument(
        "--volume-id",
        required=True,
        help="EBS volume id to snapshot (e.g. vol-0123456789abcdef0).",
    )
    parser.add_argument(
        "--ami-name",
        required=True,
        help="Name for the new AMI (e.g. my-golden-image).",
    )
    parser.add_argument(
        "--region",
        default=DEFAULT_REGION,
        help=f"AWS region (default: {DEFAULT_REGION}).",
    )
    parser.add_argument(
        "--description",
        default=None,
        help="Optional description for the snapshot.",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help="Seconds between state polls (default: 5).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    args = _parse_args(argv)

    result = snapshot_to_ami(
        volume_id=args.volume_id,
        ami_name=args.ami_name,
        region=args.region,
        description=args.description,
    )
    print(f"snapshot_id={result['snapshot_id']}")
    print(f"ami_id={result['ami_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
