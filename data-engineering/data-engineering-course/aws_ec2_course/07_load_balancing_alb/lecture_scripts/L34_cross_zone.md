# L34 — Cross-Zone Load Balancing

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 07
> **Duration target:** 8:00
> **Lecture ID:** L34

## Status

Authored.

## Prereqs

- L31 (subnets and AZs).
- L27 (target groups).
- L29 (NLB theory — for the contrast).

## Key terms

- **Cross-zone load balancing** — the load balancer distributes
  traffic **evenly across all healthy targets in all enabled AZs**,
  regardless of which AZ the target is in.
- **Without cross-zone** — each load balancer node in an AZ sends
  traffic only to the targets **in its own AZ**. If AZ A has 6
  targets and AZ B has 2, the node in AZ A sends 100% of its
  traffic to those 6, and the node in AZ B sends 100% of its
  traffic to those 2.
- **Zonal isolation** — keeping traffic in the same AZ. Used for
  blast-radius reduction and data-residency reasons.

## Lecture

Cross-zone load balancing is one of those settings that looks
inert until 2 a.m. when a 5-target difference between two AZs
causes a 3x traffic spike on the smaller fleet. This lecture
covers what it does, how ALB and NLB differ, and when you would
ever want to turn it off.

### What "without cross-zone" actually does

Imagine an ALB with two enabled AZs:

```
AZ A: 6 healthy targets
AZ B: 2 healthy targets

ALB node in AZ A receives 50% of the traffic.
ALB node in AZ B receives 50% of the traffic.

Without cross-zone:
  AZ A node  → 6 targets in AZ A → each gets ~8.3% of total traffic
  AZ B node  → 2 targets in AZ B → each gets 25% of total traffic

With cross-zone:
  Both nodes treat the pool as 8 total targets:
  each target gets 12.5% of total traffic regardless of AZ
```

In other words, **without** cross-zone, a 3:1 imbalance in target
count becomes a 3:1 imbalance in per-target traffic. That is a
real outage waiting to happen if AZ A's fleet gets autoscaled
down to 2.

### How ALB and NLB differ

This is the single most important fact in this lecture.

| Load balancer | Cross-zone default | Toggle?                      | Cost to turn on? |
| ------------- | ------------------ | ---------------------------- | ---------------- |
| **ALB**       | **Always on**      | Cannot be turned off        | Free (included)  |
| **NLB**       | **Off by default** | Can be enabled per LB       | ~$0.025 / AZ-hour (~$18/AZ/month) |

For an **ALB**, you do not have to think about this. The setting
exists, the default is "on", there is no UI to turn it off, and
boto3 does not expose a flag. If you want cross-zone for an ALB
fleet, you have it. If you want to **avoid** cross-zone for an
ALB, you cannot.

For an **NLB**, you must make the decision explicitly. If you
leave it off (the default), each NLB node in an AZ only sends
traffic to the targets in that AZ. If you turn it on, AWS charges
you a small hourly fee per AZ to cover the inter-AZ data transfer
costs that AWS otherwise eats.

### When to turn cross-zone OFF (NLB only)

You almost never want to. The two real reasons:

1. **Strict data residency.** Some compliance regimes require
   traffic to a target to stay in the same AZ as the request.
   Cross-zone breaks that because the LB node in AZ A will
   forward to a target in AZ B, crossing the AZ boundary.
2. **Blast-radius reduction.** If you have many micro-services
   and one AZ goes bad, the cross-zone setting could pull
   traffic from the bad AZ out to the good AZ (good for
   availability) **or** spread the bad AZ's load onto the
   other AZs (bad for stability). Zonal isolation keeps each
   AZ's traffic self-contained.

For almost every other workload, leave cross-zone **on** for NLB
and accept the small fee.

### What this looks like in boto3

For an ALB, the `create_load_balancer` call has no cross-zone
parameter at all. The setting is fixed.

For an NLB, the `create_load_balancer` call has
`LoadBalancerAttributes=[{"Key": "load_balancing.cross_zone.enabled", "Value": "true"}]`.

You can also flip it after the fact:

```python
elbv2.modify_load_balancer_attributes(
    LoadBalancerArn=arn,
    Attributes=[{"Key": "load_balancing.cross_zone.enabled", "Value": "true"}],
)
```

The boto3 script in **L35** (`alb_create.py`) is an ALB, so we
do not pass any cross-zone attribute — there is nothing to pass.

### The asymmetric-scaling trap

The most common way cross-zone surprises people is **asymmetric
autoscaling**. Suppose you have an autoscaling group configured
to keep 4 instances in AZ A and 4 in AZ B. They drift to 4 and 2
because AZ A is cheaper for a while. The ALB with cross-zone
**on** sends traffic evenly to the 6 targets, and the 2 in AZ B
are suddenly handling 50% of the total load — three times what
they were sized for.

The fix is to set the autoscaling group to **balanced** scaling
(`AZRebalance: true` or per-AZ min capacity), not to fight the
load balancer. Cross-zone is doing the right thing; the autoscaling
is not.

### Quick reference for the quiz

- ALB cross-zone: **always on, not configurable, free**.
- NLB cross-zone: **off by default, configurable, ~$18/AZ/month to
  enable**.
- The default for both ALB and NLB target groups (health checks
  aside) is to use the cross-zone setting of the load balancer
  they are attached to.
- The setting lives on the load balancer, not the target group.

## Hands-on

There is no console toggle for ALB cross-zone, so there is
nothing to click. The boto3 equivalent is also a no-op. The
hands-on for this lecture is conceptual:

1. Open the AWS console, find the ALB you created in **L32**, and
   confirm there is no cross-zone setting in the Attributes tab.
2. Skim the **NLB** Attributes tab in the same console for
   contrast — you will see the `cross_zone.enabled` toggle
   there.
3. Read the autoscaling group docs for `AZRebalance` and note
   that it interacts with cross-zone.

## Quiz prep

- What is cross-zone load balancing in one sentence?
- What is the default for ALB? For NLB?
- Can you turn cross-zone off on an ALB? Why or why not?
- What asymmetric-scaling situation does cross-zone hide, and what
  is the actual fix?
- Why might you turn cross-zone **on** for an NLB despite the
  hourly fee?

## Further reading

- AWS docs — [Cross-zone load balancing for ALB](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/how-elastic-load-balancing-works.html#cross-zone-load-balancing)
- AWS docs — [NLB cross-zone load balancing](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/how-elastic-load-balancing-works.html#cross-zone-load-balancing)
- AWS docs — [NLB load balancer attributes](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/load-balancer-attributes.html)
- L31 — ALB theory (the AZ model)
- L29 — NLB theory (the contrast)
