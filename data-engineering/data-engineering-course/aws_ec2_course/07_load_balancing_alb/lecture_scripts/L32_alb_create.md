# L32 — ALB Hands-On: Create the Load Balancer

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 07
> **Duration target:** 10:00
> **Lecture ID:** L32

## Status

Authored.

## Prereqs

- L31 (ALB theory, internet-facing vs internal, subnets).
- L27–L28 (target groups, health checks).
- L29 (NLB comparison).

## Key terms

- **Security group** — a virtual firewall that controls inbound and
  outbound traffic at the **instance** or **ENI** level. For an
  ALB, the security group is attached to the **load balancer
  ENIs** in each subnet.
- **Target group health check** — protocol (HTTP/HTTPS), path
  (e.g. `/health`), port (defaults to traffic port), healthy
  threshold (2 consecutive 200s), unhealthy threshold (2
  consecutive failures), interval (30 s default), timeout (5 s
  default).
- **Listener** — process bound to a port + protocol on the ALB.
  Receives the connection, evaluates rules in priority order, and
  forwards to a target group or returns a fixed response.
- **Default action** — the action taken by a listener when no rule
  matched. It is also the action of the **last** rule (lowest
  priority) you create. Most beginners treat the default action
  as "fallback 404" — we will do exactly that in **L35**.

## Lecture

Creating an ALB feels like five steps in the AWS console but
collapses to four if you read carefully. We will use the same order
the console uses because the order matters: you cannot attach a
target group to a listener that does not exist yet, and you cannot
create a listener on a load balancer that does not exist yet.

### The 4-step ALB creation flow

```
1. Security group       ← ingress 0.0.0.0/0 :80 (and/or :443)
2. Target group         ← protocol, port, health check, target type
3. Load balancer        ← scheme, IP type, subnets, security group
4. Listener + rules     ← protocol, port, default action, rules
```

#### Step 1 — Security group

The security group attached to the ALB is **separate** from the
security group on your EC2 instances. The ALB SG controls who can
reach the ALB; the instance SG controls who can reach the instances.

For an internet-facing HTTP ALB:

```text
Inbound:
  Type: HTTP,  Protocol: TCP,  Port: 80,  Source: 0.0.0.0/0
  Type: HTTPS, Protocol: TCP,  Port: 443, Source: 0.0.0.0/0   (if you terminate TLS)
```

For an internal ALB on a private subnet, the source is your VPC CIDR
or a tighter security group reference — never `0.0.0.0/0`.

The ALB security group is **stateful**, so you do not need an
explicit outbound rule for traffic to reach your targets on port 80.

#### Step 2 — Target group

Create the target group **before** the load balancer so you can
attach it to the listener in step 4.

| Field                  | Value                                |
| ---------------------- | ------------------------------------ |
| Target type            | `instance` / `ip` / `lambda`         |
| Target group name      | `tg-alb-demo`                        |
| Protocol               | HTTP                                 |
| Port                   | 80                                   |
| VPC                    | the same VPC as the ALB              |
| Health check protocol  | HTTP                                 |
| Health check path      | `/health`                            |
| Healthy threshold      | 2 (2 consecutive 200s → healthy)     |
| Unhealthy threshold    | 2 (2 consecutive failures → unhealthy) |
| Timeout                | 5 s                                  |
| Interval               | 30 s                                 |
| Success codes          | 200–399                              |

After the target group exists, **register your targets**: pick the
EC2 instances (or IP addresses) that should receive traffic.

> **Health check is the part most people misconfigure.** If your
> `/health` endpoint returns 200 only when the database connection
> is alive, the ALB will mark every instance unhealthy the moment
> the database blips. Keep `/health` cheap and decoupled from
> downstream dependencies.

#### Step 3 — Load balancer

| Field                    | Value                            |
| ------------------------ | -------------------------------- |
| Load balancer type       | Application Load Balancer        |
| Name                     | `alb-demo`                       |
| Scheme                   | `internet-facing` (or `internal`)|
| IP address type          | IPv4 (or `dualstack`)            |
| VPC                      | the same VPC as the target group |
| Subnets                  | **at least 2 subnets in 2 AZs**  |
| Security groups          | the SG from step 1               |
| Listeners                | leave empty — we add in step 4   |
| Tags                     | e.g. `Environment=dev`           |

Once the ALB is created it gets a DNS name like
`alb-demo-1234567890.us-east-1.elb.amazonaws.com`. There is no
static IP. The DNS name resolves to the ALB nodes in your enabled
subnets. If you need a friendly hostname, point a Route 53 alias
record at it.

#### Step 4 — Listener + rules

The listener is the long-running process that watches a port on the
ALB. The default is HTTP on port 80.

| Field            | Value                                |
| ---------------- | ------------------------------------ |
| Protocol         | HTTP                                 |
| Port             | 80                                   |
| Default action   | Forward to `tg-alb-demo`             |

In the next lecture (**L33**) we will add two more rules: a
path-based rule that forwards `/api/*` to a second target group,
and a fixed-response rule that returns 404 for everything else.
For now, the single default-action rule is enough to see traffic
flow.

### Verify it works

Hit the ALB DNS name from a browser or with `curl`:

```bash
curl -v http://alb-demo-1234567890.us-east-1.elb.amazonaws.com/health
```

A healthy target returns a 2xx within a few hundred milliseconds.
A misconfigured health check returns 503 ("no healthy targets").

### boto3 preview

The boto3 script we walk through in **L35** collapses the four
console steps into a single function:

```python
import boto3

elbv2 = boto3.client("elbv2", region_name="us-east-1")

def create_alb_and_rules(...):
    tg = elbv2.create_target_group(
        Name="tg-alb-demo",
        Protocol="HTTP", Port=80,
        HealthCheckPath="/health",
        HealthCheckProtocol="HTTP",
        VpcId=...,
    )
    alb = elbv2.create_load_balancer(
        Name="alb-demo",
        Type="application",
        Scheme="internet-facing",
        Subnets=[subnet_a, subnet_b],
        SecurityGroups=[sg_id],
    )
    listener = elbv2.create_listener(
        LoadBalancerArn=alb["LoadBalancers"][0]["LoadBalancerArn"],
        Protocol="HTTP", Port=80,
        DefaultActions=[{"Type": "forward", "TargetGroupArn": tg["TargetGroups"][0]["TargetGroupArn"]}],
    )
    ...
```

Every one of those four calls has a `moto` mock, so the
`alb_create.py` script and its `test_alb_create.py` tests run with
zero AWS calls.

## Hands-on

Create an ALB in the console with these settings:

1. Security group: HTTP 80 from `0.0.0.0/0`.
2. Target group: HTTP 80, health check `/health`, 2 instances
   registered.
3. Load balancer: internet-facing, 2 subnets in 2 AZs, the SG
   from step 1.
4. Listener: HTTP 80, default action forward to the target group.

Hit the ALB DNS name from a browser. If you see your app, the
default route works. If you see 503, the targets are still
failing health checks — wait 60 s and try again.

## Quiz prep

- Why is the security group on the ALB separate from the security
  group on the targets?
- What is the minimum number of subnets an ALB must span, and why?
- What is the default action of a listener, and when does it run?
- What does the health check `/health` returning 200 mean to the
  ALB? What does 500 mean?
- Name two health-check fields and the value that beginners most
  often misconfigure.

## Further reading

- AWS docs — [Create an Application Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/create-application-load-balancer.html)
- AWS docs — [Health checks for your target groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html)
- L31 — ALB theory (the why behind the 4 steps)
- L33 — ALB rules (the why behind step 4)
- L35 — `alb_create.py` walkthrough (boto3 + moto)
