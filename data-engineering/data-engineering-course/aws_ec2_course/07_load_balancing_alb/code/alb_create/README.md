# alb_create — Section 7 working demo

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 7 — Application Load Balancer
> **Lecture:** L35

This directory contains the boto3 script and the moto-backed pytest
tests for Section 7. The script mirrors the 4-step ALB creation flow
from L32 and the two-rule layout from L33.

## Files

```
alb_create/
├── README.md              ← you are here
├── alb_create.py          ← boto3 script with create_alb_and_rules()
└── test_alb_create.py     ← 4 moto-backed pytest tests
```

## What the script does

`create_alb_and_rules(vpc_id, subnet_ids, security_group_id, ...)` does
the four things from L32 in the same order:

1. Creates a **target group** with HTTP 80, health check `/health`, and
   30 s interval / 5 s timeout / 2 healthy / 2 unhealthy thresholds.
2. Creates an **Application Load Balancer** — `Type="application"`,
   `Scheme="internet-facing"`, 2 subnets in 2 AZs, the supplied
   security group.
3. Creates a **default listener** on HTTP 80 whose default action is a
   fixed 404 with body `<h1>Not Found</h1>`.
4. Adds a **priority-10 rule** that forwards `path-pattern=/api/*` to
   the target group.

It returns the four ARNs the caller is most likely to need.

## How the script maps to the lectures                         | L35 call

| boto3 call                                  | Console step          | Lecture              |
| ------------------------------------------- | -------------------- | -------------------- |
| `create_target_group(...)`                  | Step 2 — target group | L32                  |
| `create_load_balancer(...)`                 | Step 3 — load balancer | L32                |
| `create_listener(... DefaultActions=[fixed-response 404])` | Step 4 — listener (default action) | L33 |
| `create_rule(... Priority=10, path-pattern /api/*)`         | Step 4 — path-based rule | L33        |

## Cross-zone load balancing

The script does **not** set any cross-zone attribute on the ALB
because cross-zone is always on for ALB and is not user-configurable
(see L34). If you ever copy this pattern to an NLB, you must set
`LoadBalancerAttributes=[{"Key": "load_balancing.cross_zone.enabled",
"Value": "true"}]` explicitly.

## Running the tests

```bash
cd 07_load_balancing_alb/code/alb_create
python -m pytest -v
```

Expected output (truncated):

```
test_alb_create.py::test_alb_type_is_application            PASSED
test_alb_create.py::test_default_listener_exists            PASSED
test_alb_create.py::test_path_rule_forwards_to_target_group PASSED
test_alb_create.py::test_default_action_is_fixed_404        PASSED

4 passed in 0.6s
```

The tests use `@mock_aws` from `moto>=5`. No AWS account, no AWS
calls, no credentials required. If you do not have a `~/.aws/credentials`
file, that is fine — `moto` returns a mock response to every boto3
call.

## Running against real AWS (optional)

```bash
export AWS_REGION=us-east-1
export VPC_ID=vpc-0123456789abcdef0
export SUBNET_IDS=subnet-aaa,subnet-bbb
export SECURITY_GROUP_ID=sg-0123456789abcdef0
python alb_create.py
```

The script prints a JSON blob with the four ARNs. Clean up with:

```bash
aws elbv2 delete-load-balancer --load-balancer-arn <alb_arn>
aws elbv2 delete-target-group    --target-group-arn    <tg_arn>
```

## Failure simulation

The lecture L35 walks through two failure modes:

1. **In AWS** — register two healthy targets, stop the app on one,
   wait 60 s, watch the target move from `healthy` to `unhealthy`.
2. **In moto** — call `create_alb_and_rules` without registering any
   targets; the target group is empty; the ALB returns 503 for any
   `/api/*` URL.

Both paths are useful. The moto path is what the unit tests
implicitly exercise; the AWS path is the canonical
"unhealthy-target" demo.