# L28 — Target Groups and Health Checks

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 06
> **Duration target:** 12:00
> **Lecture ID:** L28

## Status

Authored.

## Prereqs

- L27 (What is a Load Balancer). You should know that a load balancer
  sits in front of a pool of backends and gives them a stable name.

## Key terms

- **Target group** — a named bag of backend targets (EC2 instances,
  IPs, or Lambda functions) that an AWS load balancer routes traffic
  to. Every listener has at least one default target group.
- **Health check** — a periodic probe (HTTP, HTTPS, or TCP) that the
  load balancer runs against each registered target to decide
  whether it is healthy enough to receive traffic.
- **Healthy threshold** — the number of consecutive successful probes
  required to mark an `unhealthy` target as `healthy` again.
- **Unhealthy threshold** — the number of consecutive failed probes
  required to mark a `healthy` target as `unhealthy`.
- **Matcher** — for HTTP/HTTPS health checks, the response code (or
  range) that counts as a success (e.g. `200-399`).
- **Deregistration delay** — the time the load balancer continues to
  route to a target after it has been deregistered, used to drain
  in-flight requests gracefully.

## Lecture

A target group is the indirection layer between the load balancer
and your backends. You do not register an EC2 instance with a load
balancer directly. You register the instance with a **target group**,
and the load balancer routes to the target group. This lets a single
load balancer route different URLs (or different ports) to different
pools of instances — Section 7 (ALB) makes heavy use of this. For an
NLB, the rule is simpler: one listener, one default target group, and
every request goes to that group. But the target group itself is
still the unit of "which instances are alive right now".

A target group has two important lives. There is the **configuration
life** (what type of targets, what port, what health check) and the
**runtime life** (which registered targets are currently healthy).
You can have a target group with five registered instances, three of
which are healthy and two of which are unhealthy. The load balancer
only sends traffic to the three healthy ones.

Health checks are the heartbeat that powers this. The load balancer
periodically asks each registered target a question. For an NLB, the
default question is a TCP SYN — "can I open a TCP socket to port 80?"
For an ALB, the question is usually an HTTP GET — "does `GET /health`
return a 200?" — which is why the target's application code has to
implement a `/health` endpoint that returns 200 only when the
application is fully ready to serve.

There are five knobs you will tune on every health check in real life.

The **protocol**. For an NLB, the choice is TCP, HTTP, or HTTPS. For
an ALB, it is HTTP or HTTPS. Most beginners use TCP for NLBs and
HTTP for ALBs.

The **path**. For HTTP/HTTPS checks, this is the URL the load
balancer hits — typically `/health` or `/healthz`. The application
serves this path with a 200 only when it is fully bootstrapped.

The **interval** (in seconds). How often the load balancer probes.
AWS default is 30 seconds. Production systems often lower this to
10 seconds for faster failure detection; the trade-off is more probe
traffic against your targets.

The **timeout** (in seconds). How long the load balancer waits for a
response. Default 5 seconds for HTTP. A path that is genuinely slow
should be tuned carefully — too short and healthy targets will look
unhealthy; too long and you detect failures slowly.

The **healthy / unhealthy threshold counts**. The number of consecutive
probes required to flip a target's state. A common production setting
is `HealthyThresholdCount=3, UnhealthyThresholdCount=3`. That means
three consecutive failures mark a target unhealthy, and three
consecutive successes bring it back. AWS default is 5 healthy / 2
unhealthy. The defaults are fine; the setting above is faster on
recovery and slower on flapping.

Finally, the **matcher** (HTTP only). The HTTP status code (or range)
that counts as success. The matcher `200` matches only `200 OK`. The
matcher `200-399` matches any 2xx or 3xx. Production health checks
almost always use `200-399` so that HTTP 301 redirects to a
canonical URL do not mark a healthy target as unhealthy.

The health check state machine has two transitions worth remembering.
A target starts in `initial` state. After `HealthyThresholdCount`
consecutive successful probes, it transitions to `healthy`. After
`UnhealthyThresholdCount` consecutive failed probes, it transitions
to `unhealthy`. From `unhealthy`, after `HealthyThresholdCount`
consecutive successes, it returns to `healthy`. The load balancer
stops routing to `unhealthy` targets; it resumes routing the moment
they become `healthy` again.

## Hands-on

Read the health-check block at the top of `code/nlb_create/nlb_create.py`
in L30. Notice that we set the **target-group** health check to HTTP
on `/health`, even though the load balancer itself is a TCP NLB. This
is a common pattern: the NLB does a TCP-level pass-through, but the
target group uses HTTP so we get a real liveness signal from the
application, not just "the kernel is up".

## Quiz prep

- A **target group** is the indirection layer; the load balancer
  never knows about specific instances, only about target groups.
- Health-check parameters: **protocol, path, interval, timeout,
  healthy threshold, unhealthy threshold, matcher**.
- `initial → healthy` after N consecutive successes; `healthy →
  unhealthy` after M consecutive failures.
- A target in `unhealthy` state receives **zero** traffic from the
  load balancer.
- For an NLB, the health check protocol can differ from the listener
  protocol (TCP listener, HTTP health check is a real pattern).

## Further reading

- AWS Docs — *Target groups for your Network Load Balancers*
  <https://docs.aws.amazon.com/elasticloadbalancing/latest/network/load-balancer-target-groups.html>
- AWS Docs — *Health checks for your target groups*
  <https://docs.aws.amazon.com/elasticloadbalancing/latest/network/target-group-health-checks.html>
- boto3 — `create_target_group` reference
  <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.create_target_group>
