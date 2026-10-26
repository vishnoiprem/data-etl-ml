"""launch_instance.py — boto3 script that launches an EC2 instance.

Author: Prem Vishnoi <pvishnoi@avilx.com>
Section: 03 (Creating an EC2 Instance), demo for L18.

Usage (against real AWS):
    python launch_instance.py \\
        --ami-id ami-0abcdef1234567890 \\
        --instance-type t3.micro \\
        --key-name my-key \\
        --security-group-ids sg-0123456789abcdef0 \\
        --subnet-id subnet-0123456789abcdef0 \\
        --user-data-file ./bootstrap.sh \\
        --name demo-instance

Usage (against moto for tests):
    See test_launch_instance.py.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Optional

import boto3
from botocore.exceptions import ClientError

DEFAULT_REGION = os.environ.get("AWS_REGION", "us-east-1")
DEFAULT_INSTANCE_TYPE = "t3.micro"


def _boto_ec2(region_name: str = DEFAULT_REGION):
    """Return a low-level EC2 client.

    Tests monkeypatch this to inject a @mock_aws client.
    """
    return boto3.client("ec2", region_name=region_name)


def launch_instance(
    *,
    ami_id: str,
    instance_type: str = DEFAULT_INSTANCE_TYPE,
    key_name: str,
    security_group_ids: list[str],
    subnet_id: str,
    user_data: Optional[str] = None,
    name: str = "ec2-course-instance",
    region_name: str = DEFAULT_REGION,
    ec2_client=None,
) -> str:
    """Launch a single EC2 instance and return its instance id.

    The instance is tagged with Name, CreatedBy, and CourseSection so
    it is easy to find and to clean up afterwards.

    Parameters
    ----------
    ami_id : str
        AMI id (e.g. ``ami-0abcdef1234567890``).
    instance_type : str
        Instance type (default ``t3.micro``).
    key_name : str
        Name of an existing EC2 KeyPair in the target region.
    security_group_ids : list[str]
        One or more security group ids (e.g. ``["sg-0123..."]``).
    subnet_id : str
        Subnet id where the instance will be launched.
    user_data : str, optional
        A cloud-init script (bash). Will be base64-encoded by boto3.
    name : str
        Value for the ``Name`` tag.
    region_name : str
        AWS region. Defaults to ``AWS_REGION`` env var or ``us-east-1``.
    ec2_client : boto3 EC2 client, optional
        Inject a custom client (used by tests with ``@mock_aws``).
    """
    client = ec2_client or _boto_ec2(region_name=region_name)

    run_kwargs: dict = {
        "ImageId": ami_id,
        "InstanceType": instance_type,
        "KeyName": key_name,
        "SecurityGroupIds": security_group_ids,
        "SubnetId": subnet_id,
        "MinCount": 1,
        "MaxCount": 1,
        "TagSpecifications": [
            {
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "Name", "Value": name},
                    {"Key": "CreatedBy", "Value": "aws_ec2_course"},
                    {"Key": "CourseSection", "Value": "3"},
                ],
            }
        ],
    }
    if user_data:
        run_kwargs["UserData"] = user_data

    response = client.run_instances(**run_kwargs)
    instance_id = response["Instances"][0]["InstanceId"]

    # Wait for the instance to enter "running" state. boto3 ships a
    # waiter specifically for this; using the waiter means we don't
    # have to hand-roll a poll loop.
    waiter = client.get_waiter("instance_running")
    waiter.wait(InstanceIds=[instance_id])

    return instance_id


def get_public_dns_name(instance_id: str, region_name: str = DEFAULT_REGION) -> Optional[str]:
    """Return the public DNS name of an instance, or None if not yet assigned."""
    client = _boto_ec2(region_name=region_name)
    try:
        response = client.describe_instances(InstanceIds=[instance_id])
    except ClientError:
        return None
    reservations = response.get("Reservations", [])
    if not reservations:
        return None
    instances = reservations[0].get("Instances", [])
    if not instances:
        return None
    return instances[0].get("PublicDnsName") or None


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch a single EC2 instance with boto3.")
    parser.add_argument("--ami-id", required=True, help="AMI id, e.g. ami-0abcdef1234567890")
    parser.add_argument(
        "--instance-type",
        default=DEFAULT_INSTANCE_TYPE,
        help=f"Instance type (default: {DEFAULT_INSTANCE_TYPE})",
    )
    parser.add_argument("--key-name", required=True, help="EC2 KeyPair name")
    parser.add_argument(
        "--security-group-ids",
        nargs="+",
        required=True,
        help="One or more security group ids",
    )
    parser.add_argument("--subnet-id", required=True, help="Subnet id")
    parser.add_argument(
        "--user-data-file",
        default=None,
        help="Path to a file containing a cloud-init / bash user-data script",
    )
    parser.add_argument("--name", default="ec2-course-instance", help="Name tag value")
    parser.add_argument(
        "--region",
        default=DEFAULT_REGION,
        help=f"AWS region (default: {DEFAULT_REGION})",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    user_data = None
    if args.user_data_file:
        with open(args.user_data_file, "r", encoding="utf-8") as fh:
            user_data = fh.read()

    instance_id = launch_instance(
        ami_id=args.ami_id,
        instance_type=args.instance_type,
        key_name=args.key_name,
        security_group_ids=args.security_group_ids,
        subnet_id=args.subnet_id,
        user_data=user_data,
        name=args.name,
        region_name=args.region,
    )

    public_dns = get_public_dns_name(instance_id, region_name=args.region)
    print(f"Instance id: {instance_id}")
    print(f"Public DNS : {public_dns or '(not yet assigned)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
