# ec2_lifecycle — Lambda that creates / starts / stops EC2 (L16)

> Companion code for L16 — AWS Lambda with EC2 (Create EC2, Start EC2 and Stop EC2).

## Files

- `start_stop_ec2.py` — the dispatching Lambda handler module.
- `test_script.py` — `moto`-based tests.

## IAM permissions required (real AWS)

```json
{
  "Version": "2012-10-17",
  "Statement": [{
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
  }]
}
```

In production, scope `RunInstances` to a specific AMI and instance
type using `iam:ResourceTag` conditions.

## Event shapes

```json
// create
{"action": "create", "name": "demo-instance"}

// start
{"action": "start", "instance_id": "i-0123456789abcdef0"}

// stop
{"action": "stop",  "instance_id": "i-0123456789abcdef0"}
```

## Run the tests

```bash
cd 04_lambda_with_aws_resources/code/ec2_lifecycle
pytest test_script.py -v
```

## Try it against real AWS

The `create` branch will spin up a `t2.micro` in your default VPC.
Be sure to clean up afterwards (call the `stop` branch then
terminate the instance manually).
