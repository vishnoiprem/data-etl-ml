# L21 — Spot Instances

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 04
> **Duration target:** 10:00
> **Lecture ID:** L21

## Status

Authored.

## Prereqs

- L19 (the five-model overview) and L20 (on-demand, RI, Savings Plans).

## Key terms

- **Spot Instance** — an EC2 instance running on spare AWS capacity at a market-clearing price, usually 60–90% below on-demand. AWS can reclaim it with a 2-minute warning.
- **Spot price** — the current per-hour price for a given instance type + AZ. Set by AWS, varies with supply and demand, capped at the on-demand price.
- **Interruption** — when AWS needs the capacity back. AWS sends a 2-minute warning, then stops or terminates the instance. The exact signal is a rebalance recommendation (start draining work) followed by an interruption notice (finish and exit).
- **Spot Fleet** — a deprecated-but-still-available API for requesting a mix of instance types and purchase models (lowest price, diversified, capacity-optimized) under one logical pool.
- **EC2 Auto Scaling with mixed instances** — the modern way to use spot. You set a desired capacity, a minimum on-demand count, and a list of allowed instance types; Auto Scaling fills the rest with spot and replaces interrupted instances automatically.

## Lecture

Spot is the most misunderstood of the five pricing models, and also the one with the largest potential discount. Done right, it cuts compute cost by 60–90%. Done wrong, it cuts your availability with it.

**How spot pricing works.** Each instance type, in each AZ, has a spot price. AWS sets the spot price based on the long-run supply and demand for spare capacity in that pool. When many people want the same type, the spot price goes up; when nobody wants it, the spot price is low. The spot price is *capped at the on-demand price*, so you never pay more per hour than you would on-demand — if the spot price would otherwise be higher, AWS just lets the spot pool empty rather than charge above on-demand.

In practice, the spot price for popular Linux instance types in popular regions is roughly 60–70% off on-demand most of the time, and is stable hour to hour. Less popular types or unusual regions can be 90% off but are also more volatile. The price you see in the console is the *current* price; the price you actually pay is the price at the moment each hour starts.

**Interruption behavior.** This is the part that matters. When AWS needs the capacity back, you do not get to keep the instance. The contract is:

1. AWS sends a **rebalance recommendation** signal — this is a heads-up that spot demand for your instance type is rising, and you should consider proactively moving your work elsewhere. You can react to this if you want; nothing happens automatically.
2. About 2 minutes later, AWS sends an **interruption notice** — at this point the instance is going away, no matter what. The instance gets a stop or terminate event, and the EC2 metadata service exposes the termination time.
3. After 2 minutes from the interruption notice, the instance is stopped or terminated.

If your workload can handle being killed and restarted, this is fine. If your workload cannot, spot is the wrong model.

**Workload types that fit spot.** The standard list:

- **Batch jobs** — anything that processes a queue. If a worker is interrupted, the work item is still in the queue and another worker picks it up. This is the canonical spot use case.
- **CI/CD runners** — a build is short, the queue is durable, and losing a runner mid-build is no different from losing it to a network blip. Most CI providers (GitHub Actions self-hosted runners, GitLab runners, Buildkite agents) have native spot support.
- **Stateless web/API tiers** — put your spot instances behind a load balancer (NLB or ALB, which we cover in Sections 6 and 7). When a spot instance is interrupted, the load balancer drains it and the rest of the fleet takes over. AWS Auto Scaling can be configured to maintain a minimum count of on-demand and a maximum of mixed, so capacity is preserved even when spot is volatile.
- **Big-data workers** — Hadoop, Spark, Presto, EMR tasks. Checkpoint to S3; workers can be lost without losing the job.
- **Image, video, and ML training jobs** — long, parallelizable, often checkpointable. Spot is standard for this category.

**Workload types that do not fit spot.** The list is shorter but the trade-off is sharp:

- **Databases** — primary or replica, relational or NoSQL. The interruption window and the failover time usually do not fit. (Some teams do run read-only spot replicas for analytics; that is niche.)
- **Long-running stateful services** — anything that needs to be up for hours or days with no migration story. If the interruption is rare, the cost of occasional downtime is real.
- **Anything on the critical path of an SLA you cannot miss** — APIs that must respond in <100 ms, payment processing, etc. Spot introduces 2-minute interruption windows that violate hard SLAs.

**The mix-and-match pattern.** Most production setups do not run on spot alone. The standard pattern is a baseline of on-demand (or Savings Plan) instances for guaranteed capacity, with a spot layer on top for the elastic portion. AWS Auto Scaling handles the orchestration: you specify a *minimum on-demand count* and the rest is filled with spot from a list of instance types. Auto Scaling also uses a feature called *capacity-optimized* allocation, which picks the spot pool that is least likely to be interrupted — usually the most stable spot type in the region.

**Practical tips.**

- Use **multiple instance types** in your spot request. The more types you allow, the more likely AWS is to find capacity. Cores, memory, and network should be similar across the types.
- Set up a **graceful shutdown handler** in your application that catches the interruption notice and finishes in-flight work, drains connections, and uploads any checkpoint before exit.
- Use **Spot Placement Score** in the console to estimate the likelihood of a successful request before you commit.
- For long-running batch jobs, write **checkpoints to S3** every few minutes so a restart does not lose progress.
- Monitor **Spot Instance Interruption** events in EventBridge and CloudWatch. Treat them like any other operational signal.

**Pricing math.** The price you pay for a spot hour is the spot price at the start of the hour — even if AWS interrupts you 30 seconds in. So the effective per-compute-second cost is even lower than the headline spot price when you factor in the interruption window. In `pricing_calc.py`, we model spot at 30% of on-demand by default, which is in the right ballpark for many stable Linux types in us-east-1.

## Hands-on

None. We use `pricing_calc.py` in L22 to compare.

## Quiz prep

- What is the interruption warning time for a spot instance?
- Name three workload types that are well-suited to spot.
- What is the difference between a rebalance recommendation and an interruption notice?
- How does the *capacity-optimized* allocation strategy differ from *lowest-price*?
- What is the typical discount for spot versus on-demand for a popular Linux type in us-east-1?

## Further reading

- AWS Spot Instances — https://aws.amazon.com/ec2/spot/
- Spot Instance interruption handling — https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-interruptions.html
- EC2 Auto Scaling with mixed instances — https://docs.aws.amazon.com/autoscaling/ec2/userguide/asg-purchase-options.html
