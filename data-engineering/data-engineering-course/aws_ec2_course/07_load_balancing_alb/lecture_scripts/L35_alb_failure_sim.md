# L35 — ALB Failure Simulation + `alb_create.py` + tests

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 07
> **Duration target:** 12:00
> **Lecture ID:** L35

## Status

Authored.

## Prereqs

- L31–L34.
- `moto[ec2,elb]>=5.0` installed (see `requirements.txt`).

## Key terms

- **Deregistration delay (connection draining)** — when a target is
  deregistered, the ALB stops sending it **new** requests but lets
  in-flight requests finish for up to this many seconds. Default
  300 s.
- **Unhealthy target** — a target whose health check has failed at
  least `unhealthy_threshold` times in a row. Excluded from
  rotation.
- **503 Service Unavailable** — the response an ALB returns when
  no healthy targets exist for the target group a rule selected.
- **404 from a fixed-response rule** — the response we configure
  in `alb_create.py` for any path that does not match `/api/*`.
- **`moto`** — a Python library that mocks AWS services for
  testing. `@mock_aws` (or the older `@mock_elbv2`) intercepts
  `boto3.client("elbv2", ...)` calls and returns deterministic
  responses without contacting AWS.

## Lecture

This is the wrap-up lecture. We do three things:

1. **Recap** the four lectures in this section in five bullets.
2. **Walk through `alb_create.py` line by line** so you can read
   the boto3 calls and match each one to a console step.
3. **Walk through `test_alb_create.py`** so you can see how
   `moto` lets us assert ALB structure without a single real AWS
   call.

### Recap (5 bullets)

- **L31** — ALB is Layer 7; it parses the HTTP request and routes
  by host, path, or header. NLB is Layer 4 and routes by IP+port.
- **L31** — `Scheme` is `internet-facing` (public) or `internal`
  (private). You cannot change it after creation.
- **L32** — Four-step creation: SG → target group → load balancer
  → listener.
- **L33** — Rules are `(priority, conditions, actions)` triples;
  the default action is the fallback. Use host-based or path-based
  conditions; combine with a fixed 404 to lock down the public
  surface.
- **L34** — Cross-zone is always on for ALB (free, not
  configurable) and off by default for NLB (paid when enabled).

### `alb_create.py` walkthrough

Open `code/alb_create/alb_create.py`. The script exposes a single
function `create_alb_and_rules(...)` that takes:

- `vpc_id` — the VPC to deploy into.
- `subnet_ids` — **at least two** subnets in two different AZs.
- `security_group_id` — the SG to attach to the ALB.
- `region` — defaults to `us-east-1`.

It returns a dict with the listener ARN and the two rule ARNs.

#### Step 1 — Create the target group

```python
tg = elbv2.create_target_group(
    Name="tg-alb-demo",
    Protocol="HTTP",
    Port=80,
    VpcId=vpc_id,
    HealthCheckProtocol="HTTP",
    HealthCheckPath="/health",
    HealthCheckIntervalSeconds=30,
    HealthCheckTimeoutSeconds=5,
    HealthyThresholdCount=2,
    UnhealthyThresholdCount=2,
    TargetType="instance",
)
```

This is step 2 from **L32**. We do not register any targets here
because `alb_create.py` is about the load balancer plumbing, not
about specific EC2 instances. The targets would be registered with
`register_targets` after the EC2 instances exist.

#### Step 2 — Create the load balancer

```python
alb = elbv2.create_load_balancer(
    Name="alb-demo",
    Type="application",                  # <- this is the ALB
    Scheme="internet-facing",            # <- public, not internal
    IpAddressType="ipv4",
    Subnets=subnet_ids,                  # <- must be 2+ in 2 AZs
    SecurityGroups=[security_group_id],
)
```

Three of the four fields here are unique to ALB:
- `Type="application"` — distinguishes from `network` (NLB) and
  `gateway` (GWLB).
- `Scheme="internet-facing"` — the alternative is `internal`.
- `IpAddressType="ipv4"` — or `dualstack` for IPv6.

There is no cross-zone attribute (see **L34**).

#### Step 3 — Create the default listener

```python
listener = elbv2.create_listener(
    LoadBalancerArn=alb_arn,
    Protocol="HTTP",
    Port=80,
    DefaultActions=[
        {
            "Type": "fixed-response",
            "FixedResponseConfig": {
                "StatusCode": "404",
                "ContentType": "text/html",
                "MessageBody": "<h1>Not Found</h1>",
            },
        }
    ],
)
```

We make the **default action** a fixed 404. This is the fallback
when no other rule matches — exactly the pattern from **L33**.

#### Step 4 — Add the path-based rule

```python
api_rule = elbv2.create_rule(
    ListenerArn=listener_arn,
    Priority=10,
    Conditions=[
        {"Field": "path-pattern", "Values": ["/api/*"]}
    ],
    Actions=[
        {"Type": "forward", "TargetGroupArn": tg_arn}
    ],
)
```

Priority 10 is the only rule. Because the default action is a
fixed 404, every URL that does **not** start with `/api/` gets
the 404 page.

#### Return value

```python
return {
    "alb_arn": alb_arn,
    "target_group_arn": tg_arn,
    "listener_arn": listener_arn,
    "api_rule_arn": api_rule["Rules"][0]["RuleArn"],
}
```

We return the four ARNs the caller is most likely to need for
follow-up calls (modify rules, register targets, delete the
load balancer).

### `test_alb_create.py` walkthrough

The test file uses `@mock_aws` from `moto` to mock both EC2
(needed to create a VPC and two subnets) and ELBv2. The fixture
in `conftest.py` (or inline in the test file) provisions a VPC
and two subnets in two AZs, then calls `create_alb_and_rules`.

| Test                                | Asserts                                                   |
| ----------------------------------- | --------------------------------------------------------- |
| `test_alb_type_is_application`      | `Type == 'application'` on the load balancer             |
| `test_default_listener_exists`      | Listener on port 80 with the expected protocol            |
| `test_path_rule_forwards_to_target_group` | Rule with priority 10 + path-pattern `/api/*`        |
| `test_default_action_is_fixed_404`  | The default action is a fixed-response 404                |

Run them with:

```bash
cd 07_load_balancing_alb/code/alb_create
python -m pytest -v
```

You should see 4 passed in under 2 seconds. Zero AWS calls.

### Simulating a target failure

A real failure simulation has two flavors: **in AWS** and **in
moto**. They are different exercises.

#### Flavor 1 — In AWS (the production version)

1. Create two EC2 instances, register them in the target group,
   wait for them to become `healthy`.
2. Hit the ALB and confirm traffic hits both instances (check the
   access logs in S3, or your app's metrics).
3. SSH into one of the instances and `sudo systemctl stop <app>`.
4. Wait 60 s (one health-check interval + the unhealthy threshold).
5. In the console, the target moves from `healthy` to `unhealthy`.
6. Hit the ALB again — only the surviving instance responds.
7. Restart the app: `sudo systemctl start <app>`. Wait 60 s. The
   target returns to `healthy`.

This is the canonical "what does an unhealthy target look like?"
exercise. The 502 you get when the target **was** healthy but
suddenly goes dark is different from the 503 you get when the
target group is empty.

#### Flavor 2 — In moto (the unit-test version)

You do not need real EC2 instances. The script targets a target
group that has **no targets registered**. From the ALB's point of
view, that target group is in the "no healthy targets" state. Any
URL that hits the `/api/*` rule gets a 503.

```python
import boto3, json
from moto import mock_aws
from alb_create import create_alb_and_rules

@mock_aws
def test_path_pattern_503_when_no_healthy_targets():
    # ... set up VPC, subnets, SG ...
    result = create_alb_and_rules(vpc_id, subnet_ids, sg_id)
    # No targets registered.
    resp = elbv2.describe_target_health(TargetGroupArn=result["target_group_arn"])
    assert all(t["TargetHealth"]["State"] == "unused" for t in resp["TargetHealthDescriptions"])
```

In other words: empty target group + path-pattern rule = 503
when the path matches. The four tests in `test_alb_create.py`
focus on the **load balancer shape** (type, listener, rules), not
on health-check transitions, because the latter is more useful as
a manual console exercise than a unit test.

### The two failure modes side by side

| Failure                            | HTTP status from the ALB | Where to look                       |
| ---------------------------------- | ------------------------ | ----------------------------------- |
| No targets registered, target group exists | **503** ("no healthy targets") | Target group → Targets tab      |
| Targets registered but unhealthy   | **503**                  | Target group → Health check status  |
| Target healthy but app crashed     | **502** ("bad gateway")  | The app's own logs                  |
| Path does not match any rule       | **404** (fixed response) | The listener's default action       |
| Hostname does not match any rule   | **404** (fixed response) | The listener's default action       |
| TLS handshake failed               | **ERR_TLS_CERT_ALTNAME_INVALID** in the browser, no HTTP status | ACM certificate / SNI config |

Knowing which of these you are seeing is half the battle. The
other half is knowing which tab in the console to click.

## Hands-on

1. Read `code/alb_create/alb_create.py` end to end.
2. Read `code/alb_create/test_alb_create.py` end to end.
3. Run `pytest -v` and confirm **4 passed**.
4. If you have an AWS account, do Flavor 1 of the failure
   simulation above with two `t3.micro` instances in two AZs.
5. If you do not, do Flavor 2 — the boto3 script is enough to
   see the "no healthy targets" state.

## Quiz prep

- Name the four ARNs returned by `create_alb_and_rules` and what
  each one is for.
- What is the default action of the listener created by
  `alb_create.py`, and why is it a 404 instead of a forward?
- What HTTP status does the ALB return for `/api/anything` when
  the target group has no healthy targets?
- What HTTP status does the ALB return for `/` (which does not
  match `/api/*`)?
- What is the difference between a 502 and a 503 from an ALB?

## Further reading

- AWS docs — [Troubleshoot your ALB](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-troubleshooting.html)
- AWS docs — [moto elbv2 reference](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html)
- L32 — ALB creation (the 4 console steps)
- L33 — ALB rules (the rules we encode)
- L34 — cross-zone (what `alb_create.py` does not need to set)
