"""Lambda handler: create, start, and stop an EC2 instance.

Companion to L16.

Required IAM permissions:
    ec2:DescribeImages
    ec2:DescribeVpcs
    ec2:DescribeSubnets
    ec2:DescribeInstances
    ec2:RunInstances
    ec2:StartInstances
    ec2:StopInstances
    ec2:CreateTags
"""

import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

AMI_NAME_PATTERN = "amzn2-ami-hvm-2.0.*-x86_64-gp2"  # Amazon Linux 2
INSTANCE_TYPE = "t2.micro"


def _resolve_ami(ec2_client, ami_name: str = AMI_NAME_PATTERN) -> str:
    """Return the latest AMI ID matching the given name pattern."""
    images = ec2_client.describe_images(
        Filters=[{"Name": "name", "Values": [ami_name]}],
        Owners=["amazon"],
    )["Images"]
    if not images:
        raise RuntimeError(f"no AMI found for pattern {ami_name!r}")
    return sorted(images, key=lambda img: img["CreationDate"], reverse=True)[0]["ImageId"]


def _default_subnet(ec2_client) -> str:
    """Return the first available subnet in the account's default VPC."""
    vpcs = ec2_client.describe_vpcs(
        Filters=[{"Name": "isDefault", "Values": ["true"]}]
    )["Vpcs"]
    if not vpcs:
        raise RuntimeError("no default VPC in this account/region")
    vpc_id = vpcs[0]["VpcId"]
    subnets = ec2_client.describe_subnets(
        Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
    )["Subnets"]
    if not subnets:
        raise RuntimeError("default VPC has no subnets")
    return subnets[0]["SubnetId"]


def _resolve_region(event: dict) -> str:
    return (
        event.get("region")
        or os.environ.get("AWS_REGION")
        or "us-east-1"
    )


def create(event, context):
    """Create a single EC2 instance and wait until it's 'running'."""
    LOG.info("create: received event %s", json.dumps(event))
    region = _resolve_region(event or {})
    name = (event or {}).get("name", "lambda-demo-ec2")

    ec2 = boto3.client("ec2", region_name=region)
    ami_id = _resolve_ami(ec2)
    subnet_id = _default_subnet(ec2)

    resp = ec2.run_instances(
        ImageId=ami_id,
        InstanceType=INSTANCE_TYPE,
        SubnetId=subnet_id,
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[{
            "ResourceType": "instance",
            "Tags": [{"Key": "Name", "Value": name}],
        }],
    )
    instance_id = resp["Instances"][0]["InstanceId"]
    ec2.get_waiter("instance_running").wait(InstanceIds=[instance_id])

    LOG.info("create: instance %s is running", instance_id)
    return {"action": "create", "instance_id": instance_id, "state": "running"}


def start(event, context):
    LOG.info("start: received event %s", json.dumps(event))
    region = _resolve_region(event or {})
    instance_id = event["instance_id"]

    ec2 = boto3.client("ec2", region_name=region)
    try:
        ec2.start_instances(InstanceIds=[instance_id])
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "IncorrectInstanceState":
            LOG.warning("start: instance %s already in desired state", instance_id)
        else:
            raise
    ec2.get_waiter("instance_running").wait(InstanceIds=[instance_id])
    return {"action": "start", "instance_id": instance_id, "state": "running"}


def stop(event, context):
    LOG.info("stop: received event %s", json.dumps(event))
    region = _resolve_region(event or {})
    instance_id = event["instance_id"]

    ec2 = boto3.client("ec2", region_name=region)
    try:
        ec2.stop_instances(InstanceIds=[instance_id])
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "IncorrectInstanceState":
            LOG.warning("stop: instance %s already in desired state", instance_id)
        else:
            raise
    ec2.get_waiter("instance_stopped").wait(InstanceIds=[instance_id])
    return {"action": "stop", "instance_id": instance_id, "state": "stopped"}


def handler(event, context):
    """Dispatch on event['action'] -> 'create' | 'start' | 'stop'."""
    action = (event or {}).get("action", "create").lower()
    if action == "create":
        return create(event, context)
    if action == "start":
        return start(event, context)
    if action == "stop":
        return stop(event, context)
    raise ValueError(f"unknown action {action!r}; expected create|start|stop")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    print(handler({"action": "create", "name": "demo-instance"}, None))
