# 06 — Tradeoff Frameworks: Latency vs Cost vs Consistency

> **Lesson 6 of 7 — Technical Questions for SAs** · ~15 min

The 3-axis tradeoff (latency, cost, consistency) that
underlies every architecture decision. The "it depends"
answer that actually works. Worked examples for 4 common
service choices.

This lesson is the *theory* under Lesson 07 (the 30-
second decision tree). If you internalize the framework
here, the decision tree becomes intuitive.

---

## 1. The 3-axis tradeoff

Every major architecture decision trades off 3 things:

1. **Latency.** How fast does the system respond?
   (Sub-millisecond, milliseconds, seconds, minutes?)
2. **Cost.** How much does it cost to build and run?
   (Dollars/month, dollars/million requests, engineering
   effort?)
3. **Consistency.** How consistent is the data?
   (Strong consistency, eventual consistency, what
   happens when a write happens across regions?)

These 3 axes are in tension:

- **Lower latency often costs more.** Sub-millisecond
  caches (Redis, ElastiCache) cost more than second-
  latency databases (RDS, Aurora).
- **Higher consistency costs more.** Strong consistency
  across regions costs more than eventual consistency
  (cross-region replication, conflict resolution).
- **Lower latency and higher consistency together cost
  the most.** Spanner (Google's globally strongly
  consistent database) is one of the most expensive
  databases in the world.

The interview question is always some version of:
"Given these constraints, which service and why?" The
answer is the service that *minimizes the pain on the
axis that matters most*, given the tradeoffs on the
other two.

---

## 2. The "it depends" answer that actually works

The "it depends" answer is the senior SA move. The
*junior* SA avoids "it depends" because it sounds
weak. The *senior* SA uses it deliberately, with
specifics:

The wrong "it depends" answer:

> "It depends on the workload."

This is generic and unhelpful. The interviewer reads it
as "I don't know."

The right "it depends" answer:

> "It depends on 3 specific constraints. First, if
> the workload requires sub-millisecond latency, the
> right answer is [service X], because [reason]. The
> tradeoff is [Y]. Second, if the workload can tolerate
> milliseconds and needs strong consistency, the right
> answer is [service Z], because [reason]. The
> tradeoff is [Y]. Third, if the workload is read-heavy
> and can tolerate eventual consistency, the right
> answer is [service W], because [reason]. The
> tradeoff is [Y]."

The "it depends" answer with 3 specific branches is the
senior SA move. It shows the candidate can think about
the problem space, not just answer a question.

---

## 3. The decision framework

The 3-step framework for any tradeoff question:

| Step | What to do |
|---|---|
| **1. Identify the constraint** | What's the latency requirement? What's the consistency requirement? What's the cost ceiling? |
| **2. Map to the services** | Which services match each constraint? Which fall short? |
| **3. Articulate the tradeoff** | For each service chosen, name what's given up (latency for cost, consistency for cost, etc.). |

The 3-step framework is the *spine* of the answer. Each
worked example below follows the framework.

---

## 4. Worked example 1: DynamoDB vs Aurora

The question: "Design the database for a real-time
feature store with 100k reads/sec, 1k writes/sec, and
5-second staleness tolerance."

### Step 1: Identify the constraint

- **Latency:** 100k reads/sec → need horizontal scalability.
- **Consistency:** 5-second staleness → eventual consistency
  is acceptable.
- **Cost:** Cost-sensitive → want pay-per-use, not
  always-on capacity.

### Step 2: Map to the services

| Service | Matches? | Notes |
|---|---|---|
| **DynamoDB** | Yes | Sub-10ms latency, auto-scaling, pay-per-use. |
| **Aurora** | No | Strong consistency, but limits on horizontal scalability; always-on cost. |
| **ElastiCache Redis** | Partial | Sub-millisecond, but loses data on cluster failure (RPO = 0). |

### Step 3: Articulate the tradeoff

**DynamoDB is the right answer.**

The choice is DynamoDB because:
- The 100k reads/sec latency requirement is sub-10ms, which
  DynamoDB provides.
- The 5-second staleness tolerance allows DynamoDB's
  eventually consistent reads.
- The cost profile (pay-per-use) matches the
  cost-sensitive requirement.

The tradeoffs:
- DynamoDB's query patterns are limited (no joins, no SQL).
  If the team needs complex queries, Aurora is the better
  answer.
- DynamoDB's strongly consistent reads cost 2x the read
  capacity. The 5-second staleness tolerance allows the
  cheaper eventually consistent reads.

---

## 5. Worked example 2: Lambda vs EKS

The question: "Design the compute layer for a workload
that processes 10M events/day with spiky traffic
(10x spikes during business hours) and runs long-running
batch jobs at midnight."

### Step 1: Identify the constraint

- **Latency:** For the event processing, sub-second is
  fine. For the batch job, hours is fine.
- **Consistency:** Eventual consistency for events;
  transactional for the batch job.
- **Cost:** Cost-sensitive → minimize idle capacity.

### Step 2: Map to the services

| Service | Matches? | Notes |
|---|---|---|
| **Lambda** | Yes (events) | Sub-second latency, pay-per-invocation, no idle cost. |
| **EKS** | Yes (batch) | Long-running, stateful, complex runtime. |
| **EC2** | Partial | Always-on, manual scaling. |

### Step 3: Articulate the tradeoff

**Mixed: Lambda for events, EKS for batch.**

The choice is Lambda for the events and EKS for the batch
job, because:
- The event processing is spiky and short-lived;
  Lambda's pay-per-invocation model minimizes cost.
- The batch job is long-running and stateful;
  Lambda's 15-minute max duration is insufficient.

The tradeoffs:
- Lambda has cold start latency (~100-500ms). If the
  customer-facing latency is sub-100ms, Lambda isn't right.
- EKS has always-on cost for the minimum cluster size.
  If the batch job runs <30 minutes, EC2 spot instances
  might be cheaper.

---

## 6. Worked example 3: Kinesis vs SQS

The question: "Design the messaging layer for a real-
time analytics pipeline with 1M events/day, ordered by
user_id, and replayable for the last 7 days."

### Step 1: Identify the constraint

- **Latency:** Seconds is fine (analytics pipeline, not
  user-facing).
- **Consistency:** Ordered by user_id is critical.
- **Cost:** Pay-per-use, not always-on.

### Step 2: Map to the services

| Service | Matches? | Notes |
|---|---|---|
| **Kinesis** | Yes | Ordered by partition key, replayable, pay-per-shard-hour. |
| **SQS** | No | No ordering guarantee; no replay. |
| **EventBridge** | Partial | Ordered, replayable, but more focused on event routing than stream processing. |

### Step 3: Articulate the tradeoff

**Kinesis is the right answer.**

The choice is Kinesis, because:
- Kinesis provides ordering guarantee by partition key
  (user_id), which meets the ordering requirement.
- Kinesis retains messages for up to 365 days, which
  meets the 7-day replay requirement.
- Kinesis's pay-per-shard-hour matches the cost
  profile.

The tradeoffs:
- Kinesis has a fixed shard-based cost model; if the
  throughput is highly spiky (100x variation), Kinesis
  costs more than SQS during spikes.
- Kinesis requires partition key design; if the partition
  key is "hot" (one user_id with 50% of traffic), the
  pipeline bottlenecks on a single shard.

---

## 7. Worked example 4: Aurora Multi-Region vs Aurora Single-Region

The question: "Design the database for a global SaaS
application with users in the US, EU, and Asia, with
99.99% availability and 1-minute RTO."

### Step 1: Identify the constraint

- **Latency:** Sub-100ms for users in each region.
- **Consistency:** Eventually consistent across regions;
  strongly consistent within a region.
- **Cost:** Cost-sensitive; multi-region is expensive.

### Step 2: Map to the services

| Service | Matches? | Notes |
|---|---|---|
| **Aurora Global Database** | Yes | Cross-region replication with sub-second lag; multi-region failover. |
| **Aurora Multi-Region Cluster** | No | That's not a thing; use Global Database. |
| **DynamoDB Global Tables** | Yes | Multi-region strongly consistent; sub-10ms reads. |

### Step 3: Articulate the tradeoff

**Aurora Global Database is the right answer (if the
workload is relational).**

The choice is Aurora Global Database, because:
- Aurora's relational model fits the SaaS application's
  complex queries.
- Global Database's cross-region replication has
  sub-second lag, which meets the cross-region consistency
  requirement.
- Global Database's multi-region failover gives the 1-minute
  RTO.

The tradeoffs:
- Aurora Global Database costs ~2x Aurora single-region
  due to cross-region replication and storage.
- If the workload can tolerate eventual consistency
  within a region (rare), DynamoDB Global Tables is
  cheaper and faster.

---

## 8. The 4-step "answer template" for tradeoff questions

For any tradeoff question, use the 4-step template:

> **Step 1: "The constraints are X, Y, Z."** (Identify
> the 2-3 specific constraints from the question.)
>
> **Step 2: "Service A is the standard answer for [common
> case]."** (Name the most common service choice.)
>
> **Step 3: "Service B is the right answer if [constraint
> differs]."** (Name the alternative service for the
> different constraint.)
>
> **Step 4: "The tradeoff is X for Y."** (Name the tradeoff
> for the chosen service.)

The 4-step template is the senior SA move. A candidate
who can produce the 4 steps in 60 seconds for any
tradeoff question passes the round.

---

## 9. The 5 things the framework signals

If you use this framework in an interview, the 5 things
you signal:

1. **You think about constraints first.** Before naming a
   service, you identify what the customer actually needs.
2. **You know the services.** You can map any constraint
   to a specific service.
3. **You think about tradeoffs.** Every choice has a
   tradeoff; you name it.
4. **You think about alternatives.** You name what you
   *didn't* choose and why.
5. **You can adapt.** When the customer introduces a new
   constraint mid-conversation, you can re-evaluate.

The 5 signals are what every senior SA signals on every
architecture round. The framework is the *practice*; the
signals are the *outcome*.

---

## Try it

For each of the 4 worked examples, write your own 60-
second answer to the question. Time yourself out loud.

Then, for each, pick an *alternative* constraint set and
write a 60-second answer for that. For example, for
Worked Example 1 (DynamoDB vs Aurora), what if the
constraint is "strong consistency required"? Then
Aurora is the answer, and the tradeoffs change.

Run this exercise 10 times. By the 10th, you'll have
the 4-step template in muscle memory. That's the
tradeoff round of the interview.
