# `nlb_create/` — Network Load Balancer setup

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 6 (L27–L30)
> **What it does:** Creates a target group, an internet-facing NLB,
> and a TCP/80 listener that forwards to the target group. Optionally
> registers a list of EC2 instance IDs with the target group.

## Files

- `nlb_create.py` — the boto3 script. Three API calls
  (`create_target_group`, `create_load_balancer`, `create_listener`)
  plus an optional `register_targets` call.
- `test_nlb_create.py` — 4 pytest tests using `moto`'s `@mock_aws`
  decorator. All four pass offline in under 1 second.

## Run the tests (no AWS account needed)

```bash
cd 06_load_balancing_nlb/code/nlb_create
python -m pytest test_nlb_create.py -v
```

Expected:

```
test_create_target_group_returns_arn PASSED
test_create_nlb_returns_dns PASSED
test_listener_forward_to_target_group PASSED
test_nlb_type_is_network PASSED
4 passed in ~0.5s
```

## Run it for real (AWS account required)

```bash
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...

python nlb_create.py \
  --nlb-name demo-nlb \
  --vpc-id vpc-0123456789abcdef0 \
  --subnet-ids subnet-aaaaaaaaaaaaaaa subnet-bbbbbbbbbbbbbbb \
  --instance-ids i-0123456789abcdef0 i-0123456789abcdef1
```

Sample output:

```
NLB DNS NAME       : demo-nlb-1234567890abcdef.elb.us-east-1.amazonaws.com
TARGET GROUP ARN   : arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/demo-nlb-tg/...
NLB ARN            : arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/net/demo-nlb/...
LISTENER ARN       : arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/net/demo-nlb/...
```

Point a CNAME (or A record using the static IPs) for your domain at
`demo-nlb-...elb.us-east-1.amazonaws.com`.

## Required IAM permissions

The minimal IAM policy for the IAM principal running this script is:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowNlbCreate",
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:CreateTargetGroup",
        "elasticloadbalancing:CreateLoadBalancer",
        "elasticloadbalancing:CreateListener",
        "elasticloadbalancing:RegisterTargets",
        "elasticloadbalancing:DescribeTargetGroups",
        "elasticloadbalancing:DescribeLoadBalancers",
        "elasticloadbalancing:DescribeListeners"
      ],
      "Resource": "arn:aws:elasticloadbalancing:*:*:*"
    },
    {
      "Sid": "AllowReadSubnets",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs"
      ],
      "Resource": "*"
    }
  ]
}
```

## Architecture

```
                         +-------------------+
   Internet  ────────►   │   NLB (2+ AZs)    │   (one node per subnet)
                         │   DNS: demo-nlb-  │
                         │   ...elb.region.  │
                         │   amazonaws.com   │
                         +---------+---------+
                                   │ TCP/80
                                   ▼
                         +---------+---------+
                         │  Target Group     │
                         │  TCP/80, health   │
                         │  check HTTP /health│
                         +---------+---------+
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
         +---------+          +---------+          +---------+
         │  EC2 #1 │          │  EC2 #2 │          │  EC2 #3 │
         +---------+          +---------+          +---------+
```

The NLB has one node per subnet, each in a different AZ. The target
group is the indirection layer; the NLB only ever sees the target
group, not specific instances.
