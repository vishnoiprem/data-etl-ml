---
l_id: L16
title: AWS Lambda with EC2 (Create EC2, Start EC2 and Stop EC2)
duration_min: 12.59
prereqs: [L12, L15]
---

# L16 — AWS Lambda with EC2: Create, Start, and Stop

> **Author:** Prem Vishnoi &lt;prem.vishnoi.example.com&gt;
> **Section:** 4 — AWS Lambda with S3, EC2, DynamoDB
> **Duration target:** 12:59

## Prereqs

- L12 — handler contract, boto3 client construction.
- L15 — the L15 lecture is *not* strictly required, but the S3
  pattern (idempotency, structured response, paginator) carries
  over.

## Key terms

- **AMI** — Amazon Machine Image. The template for the EC2
  instance's root volume. `amazon-linux-2` is the easiest free-tier
  AMI; we look it up by name.
- **Instance type** — the VM size. `t2.micro` / `t3.micro` are
  free-tier eligible.
- **Subnet + VPC** — every EC2 instance lives in a subnet, which
  lives in a VPC. For this lecture we create a *default VPC* subnet
  so the test rig and the live AWS account both work without
  parameterization.
- **Instance state** — `pending | running | shutting-down |
  stopping | stopped | terminated`. Lambda is most often used to
  toggle between `running` and `stopped`.
- **`start_instances` / `stop_instances`** — the boto3 calls that
  toggle power state. Both are idempotent: starting a running
  instance is a no-op; stopping a stopped instance is a no-op.

## Lecture

> "Now we move from S3 to EC2. The shape of the handler is
> identical: read from `event`, build a boto3 client, do the work,
> return a small dict. The two new things to learn are: how to find
> an AMI by name (so you don't hardcode an AMI ID that becomes
> stale), and how to wait for an instance to reach a stable state
> (so the next call — start or stop — has something to act on)."

### The handler

```python
import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

AMI_NAME = "amzn2-ami-hvm-2.0.*-x86_64-gp2"  # Amazon Linux 2, free tier
INSTANCE_TYPE = "t2.micro"


def _resolve_ami(ec2_client, ami_name: str) -> str:
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


def create(event, context):
    """Create a single EC2 instance and wait until it's 'running'."""
    LOG.info("create: received event %s", json.dumps(event))
    region = event.get("region") or os.environ.get("AWS_REGION", "us-east-1")
    name = event.get("name", "lambda-demo-ec2")

    ec2 = boto3.client("ec2", region_name=region)
    ami_id = _resolve_ami(ec2, AMI_NAME)
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
    waiter = ec2.get_waiter("instance_running")
    waiter.wait(InstanceIds=[instance_id])

    LOG.info("create: instance %s is running", instance_id)
    return {"action": "create", "instance_id": instance_id, "state": "running"}


def start(event, context):
    LOG.info("start: received event %s", json.dumps(event))
    region = event.get("region") or os.environ.get("AWS_REGION", "us-east-1")
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
    region = event.get("region") or os.environ.get("AWS_REGION", "us-east-1")
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
    logging.basicConfig(level=logging.INFO)
    print(handler({"action": "create", "name": "demo-instance"}, None))
```

### Walkthrough

1. **Why a `handler` that dispatches.** Lambdas are usually deployed
   one-action-per-function in production. For *learning*, it is far
   cheaper to put create / start / stop behind a single handler and
   switch on `event["action"]`. In Section 13 we will refactor this
   into 3 separate Lambdas in a CloudFormation template. For now, one
   handler with three branches.

2. **Resolving the AMI by name.** AMI IDs change every time Amazon
   publishes a new image. Hardcoding `"ami-0abcdef1234567890"` will
   break within months. Instead we look up the *latest* Amazon
   Linux 2 image at create time. The filter is a glob
   (`amzn2-ami-hvm-2.0.*-x86_64-gp2`); we sort the result by
   `CreationDate` descending and take the first one. This is the
   same pattern used by AWS CDK and Terraform.

3. **Default VPC + subnet.** We deliberately create the instance in
   the default VPC's first subnet. That keeps the Lambda parameters
   tiny — you don't need a subnet ID, a security group, or a key
   pair in the event. (In a real deployment you'd pass these in via
   environment variables; for the demo, the default VPC is enough.)

4. **Tagging.** Every instance gets a `Name` tag. This is the only
   *free* way to identify an EC2 instance in the console. The
   `Name` tag does not affect anything else, but you should always
   set it.

5. **Waiters.** `run_instances` returns when the instance is in
   `pending` state. To confirm it actually booted, we use the
   `instance_running` waiter. Waiters are the boto3-native way to
   poll for a stable state. They are idempotent and respect your
   function's timeout.

6. **Idempotency.** Starting an already-running instance and
   stopping an already-stopped instance both raise
   `IncorrectInstanceState`. We catch it and continue — the handler
   is then safe to call repeatedly. This matters for L17's
   EventBridge schedule.

### IAM permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowEC2Lifecycle",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeImages",
        "ec2:DescribeVpcs",
        "ec2:DescribeSubnets",
        "ec2:DescribeInstances",
        "ec2:RunInstances",
        "ec2:StartInstances",
        "ec2:StopInstances",
        "ec2:CreateTags"
      ],
      "Resource": "*"
    }
  ]
}
```

In production you would scope `RunInstances` to a specific AMI and
instance type using `iam:ResourceTag` conditions. For learning we
grant the broad action.

## Hands-on

```bash
cd 04_lambda_with_aws_resources/code/ec2_lifecycle
pytest test_script.py -v
```

You should see at least 3 tests:
- `test_handler_creates_instance` — runs the create branch against
  `moto`
- `test_handler_starts_instance` — starts a stopped fixture
- `test_handler_stops_instance` — stops a running fixture

## Quiz prep

- EC2 instance states: `pending | running | shutting-down | stopping
  | stopped | terminated`.
- `start_instances` and `stop_instances` raise
  `IncorrectInstanceState` if the instance is already in the desired
  state. Catch it for idempotency.
- The boto3 way to wait for a state transition is a `get_waiter(...)`
  call, not a `time.sleep` loop.
- AMI IDs change. Look up the latest AMI by name pattern at
  create time, not by hardcoded ID.

## Further reading

- AWS docs: [RunInstances API](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_RunInstances.html)
- AWS docs: [EC2 instance lifecycle](https://docs.aws.amazon.com/AWSEC2/latest/InstanceGuide/ec2-instance-lifecycle.html)
- `code/ec2_lifecycle/README.md`
- `code/ec2_lifecycle/start_stop_ec2.py` — the full module