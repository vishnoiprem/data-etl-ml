---
l_id: L05
title: "What is an Event Bus?"
duration: "6:00"
prereqs:
  - L04 (Why EventBridge?)
---

# L05 — What is an Event Bus?

> **Section:** 2 — EventBus Basics
> **Duration:** 6:00

## Prereqs

- L04 — Why EventBridge?
- General familiarity with AWS regions and accounts

## Key terms

- **Event bus** — a logical router inside EventBridge that receives
  events and evaluates them against rules. Every event bus has an ARN.
- **Default bus** — the bus that exists automatically in every AWS
  account. It receives events from AWS services in that account.
- **Custom bus** — a bus you create explicitly, named whatever you
  want. Useful for isolating teams or environments.
- **Partner bus** — a bus dedicated to receiving events from a
  registered SaaS partner (Zendesk, Datadog, etc.).
- **Regional resource** — EventBridge is a regional service. Buses
  live in one region; events do not cross regions automatically.
- **Account-scoped** — buses are owned by one AWS account; cross-account
  access is granted via a resource policy.

## Lecture

The **event bus** is the central object in EventBridge. Everything
else — rules, targets, archives — hangs off a bus. If you remember
one thing from this lecture, remember this: **the bus is the
namespace, the rules are the matching logic, and the targets are
where the work happens.**

### A bus is a logical router, not a queue

A common misconception is that an event bus "stores" events. It
doesn't, at least not by default — it's a router. Events come in,
rules are evaluated synchronously, and matching events are
synchronously dispatched to their targets. If you turn on an
**archive**, then a copy is durably stored — but that's a separate
feature we'll cover in section 6.

```text
   AWS services         partner SaaS          custom app
   (default bus)        (partner bus)         (custom bus)
        │                     │                     │
        ▼                     ▼                     ▼
   ┌──────────────────────────────────────────────────────┐
   │  EventBridge bus  (rules + targets inside)          │
   │                                                      │
   │   rule A: $.source == "aws.ec2"   →  Lambda          │
   │   rule B: $.detail-type == …    →  SQS + SNS         │
   │   rule C: …                     →  Step Functions   │
   └──────────────────────────────────────────────────────┘
```

You can have up to **100 event buses per account per region** by
default (a soft limit you can raise). In practice, most accounts
have 2–10: the default bus, maybe one per team or environment, and
zero or more partner buses.

### Account-level and regional — both at once

An event bus is **regional**: it lives in one AWS region. If your
producer is in `us-east-1` and your consumer is in `eu-west-1`, you
need a cross-region rule (covered in section 3) or a cross-account
event bus (covered in section 7).

An event bus is also **account-scoped**: it's owned by one AWS
account. To allow another account or another AWS service (like a
SaaS partner) to put events onto your bus, you attach a **resource
policy**. We see that in L08.

```text
   AWS account 111122223333, us-east-1
   ┌──────────────────────────────────────┐
   │ default bus                           │
   │ custom bus "acme-orders"             │
   │ custom bus "acme-billing"            │
   │ partner bus "aws.partner/zendesk.com" │
   └──────────────────────────────────────┘

   AWS account 111122223333, eu-west-1
   ┌──────────────────────────────────────┐
   │ default bus  (DIFFERENT from above)   │
   │ custom bus "acme-orders"             │
   └──────────────────────────────────────┘
```

Same account, different region → different bus. The bus name is
only unique within (account, region).

### The ARN — how you address a bus

Every bus has an ARN, and you'll see it everywhere in the console
and in `boto3` responses:

```text
arn:aws:events:us-east-1:111122223333:event-bus/default
arn:aws:events:us-east-1:111122223333:event-bus/acme-orders
arn:aws:events:us-east-1:111122223333:event-bus/aws.partner/zendesk.com
```

The format is `arn:aws:events:<region>:<account>:event-bus/<name>`.
Partner buses prefix the name with `aws.partner/`. You'll need this
ARN when you attach a resource policy or when another account
targets your bus as a destination.

### Buses vs. topics vs. queues — naming confusion

EventBridge calls them **buses**. SNS calls them **topics**. SQS
calls them **queues**. Kafka calls them **topics**. The naming is
historical, not technical — they're all "named pub/sub
destinations" with different semantics. When you read AWS docs,
translate:

- EventBridge *event bus* ↔ SNS *topic* (both = fanout router)
- EventBridge *rule* ↔ SNS *subscription filter policy* (both = match
  predicate)
- EventBridge *target* ↔ SNS *subscriber endpoint* (both = where the
  work goes)

### What's in a bus?

When you create a bus, you start with an empty box: a name, an ARN,
and a (usually empty) resource policy. You then attach **rules**
and (optionally) **archives**. Rules and archives are sub-objects
of the bus; deleting the bus cascades and deletes them too.

In L06 we look at the **default bus** (which already exists in
every account), and from L07 onward we start creating our own
**custom** and **partner** buses — and writing the boto3 code to
do it idempotently.

## Hands-on

Optional: open the EventBridge console and click **Event buses →
default**. You'll see the default bus already exists, with no rules
attached. Don't add anything yet — that's L07.

## Quiz prep

- Is an event bus a queue, a router, or a stream? (Router.)
- True or false: an event bus is global (one per AWS account). (False
  — it's regional, one per account per region.)
- What's the ARN format for a custom bus? (`arn:aws:events:<region>:<account>:event-bus/<name>`)

## Key takeaways

- An **event bus** is a *logical router* — not a queue, not a stream.
- Buses are **regional and account-scoped**; same name in two regions
  is two different buses.
- A bus has a **name, an ARN, and a resource policy**. Rules and
  archives are sub-objects.
- EventBridge bus = SNS topic = Kafka topic in role; the only
  difference is the surrounding semantics.
- You can have up to ~100 buses per (account, region) by default.

## Further reading

- _Amazon EventBridge User Guide_ — "Event buses"
- L06 — The Default Event Bus
- L07 — Custom Event Buses
