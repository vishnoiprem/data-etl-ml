---
lecture: L14
title: "Cross-Account + Cross-Region Event Patterns"
duration: "10:00"
section: 3
prereqs: ["L13 (prefix + wildcards)"]
downloads:
  - "../../downloads/README.md"
---

# L14 — Cross-Account + Cross-Region Event Patterns

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 3 — Rules + Event Patterns
> **Duration:** 10:00

## Prereqs

- L13 — the operator forms, `exists`, `prefix`, `numeric`, `anything-but`.
- L07 — custom event buses and resource policies (from Section 2).

## Key terms

- **Resource policy** — an IAM-style JSON document attached to a
  resource (here, an event bus) that controls who can call which
  APIs against it.
- **Cross-account event source** — when an event is emitted into
  one AWS account's bus and consumed by a rule in a different
  account.
- **Cross-region event source** — when an event is emitted in one
  region and the rule lives in another.
- **Event bus ARN** — the unique identifier of a bus; for
  cross-account use you need the full ARN, not just the name.

## Lecture

Hi, I'm Prem Vishnoi. So far every rule we've written has been on
a bus in the same account and the same region as the events. In
production you'll often have a **central events account** that
ingests events from many **producer accounts**, and you'll often
have a **disaster-recovery region** that mirrors your primary
region. This lecture is about the patterns and policies that make
that work.

### Two patterns, two policies

There are two flavors of cross-account work:

1. **Producer account → central account.** The producer uses
   `PutEvents` to push events into a bus in the central account.
   The bus in the central account needs a **resource policy** that
   allows the producer's account to call `events:PutEvents`.
2. **Central account → another account's bus (or vice versa).** A
   rule in account A forwards events to a bus in account B by
   targeting that bus's ARN. Account B's bus needs a resource
   policy that allows account A to `PutEvents`.

Both work via the same mechanism: a **resource-based policy** on
the destination bus.

### Cross-account: producer → central bus

In the **central account** (account `111111111111`), you have a
bus `central-events`. You want account `222222222222` to be able
to push events into it:

```python
import boto3, json

events = boto3.client("events", region_name="us-east-1")

events.put_permission(
    EventBusName="central-events",
    Action="events:PutEvents",
    Principal="222222222222",
    StatementId="allow-producer-account",
)
```

In the **producer account** (`222222222222`), you push:

```python
producer = boto3.client("events", region_name="us-east-1")
producer.put_events(
    Entries=[{
        "EventBusName": "arn:aws:events:us-east-1:111111111111:event-bus/central-events",
        "Source": "my.app",
        "DetailType": "Order Placed",
        "Detail": json.dumps({"orderId": "O-1001"}),
    }]
)
```

Without the `put_permission` call, the producer's `PutEvents`
returns `AccessDenied`. With it, the events land on the central
bus and any rules there match and fire.

### Cross-region: same account, different region

If the producer and consumer are in the same account but different
regions, you have two options:

1. **Use the regional event bus in the producer region** — create
   rules in the same region as the events. No cross-region
   policy is needed.
2. **Forward to a bus in the other region** — add a target to the
   rule whose ARN is the bus in the other region. The destination
   bus needs a resource policy that allows the source region's
   bus to send.

```python
# In us-east-1: rule forwards to us-west-2 bus
events.put_targets(
    Rule="orders-placed-rule",
    EventBusName="orders-bus",
    Targets=[{
        "Id": "forward-west",
        "Arn": "arn:aws:events:us-west-2:123456789012:event-bus/orders-bus-mirror",
    }],
)
```

The destination bus's resource policy must allow `events:PutEvents`
from the source account. (The bus service principal handles the
cross-region piece.)

### Cross-account + cross-region: a full example

Central account `111111111111`, region `us-west-2`. Producer
account `222222222222`, region `us-east-1`. You want every
producer's `Order Placed` event to land in the central bus.

In the **central account**, on the bus `central-events`:

```python
events.put_permission(
    EventBusName="central-events",
    Action="events:PutEvents",
    Principal="222222222222",
    StatementId="allow-producer",
    # No Condition needed for same-account trust; add one for stricter policies.
)
```

In the **producer account**, in `us-east-1`:

```python
producer = boto3.client("events", region_name="us-east-1")
producer.put_events(
    Entries=[{
        "EventBusName": "arn:aws:events:us-west-2:111111111111:event-bus/central-events",
        "Source": "my.app",
        "DetailType": "Order Placed",
        "Detail": json.dumps({"orderId": "O-1001"}),
    }]
)
```

That's the full pattern. Two pieces of configuration, one in each
account, plus the event pattern on the central bus that does the
filtering.

### Tightening the resource policy

The simplest `put_permission` allows the entire producer account
to push. In production you'll want to lock it down. You can pass
a `Condition` to scope the policy:

```python
events.put_permission(
    EventBusName="central-events",
    Action="events:PutEvents",
    Principal="222222222222",
    StatementId="allow-producer-prod-only",
    Condition={
        "Type": "StringEquals",
        "Key": "aws:SourceAccount",
        "Value": "222222222222",
    },
)
```

You can also restrict by source IP, by MFA, by the specific
`events:PutEvents` API, or by the `aws:RequestedRegion`. See the
IAM Condition Keys reference for the full list.

### Limits and gotchas

- **Each bus allows up to 10 resource policy statements** in the
  console view. The underlying API allows more; the console just
  truncates the display.
- **Bus names are region-scoped**, not global. A bus named
  `orders-bus` in `us-east-1` is a different bus from one named
  `orders-bus` in `us-west-2`. Use the full ARN whenever you
  cross regions.
- **Event payload is not transformed in transit.** The destination
  bus receives the same envelope and `detail` as the producer
  emitted. If you need to rewrite, use EventBridge Pipes
  (Section 6) or a Lambda between the two.
- **`PutEvents` is a control-plane-ish call.** It costs $1 per
  million events (custom bus). It is also rate-limited per
  account; if you burst high, use the **partial batch response**
  pattern from EventBridge Pipes (L26) instead of `PutEvents`.

### When NOT to use cross-account event patterns

For many use cases, **EventBridge Pipes** (Section 6) is a
better fit. Cross-account event patterns are great when:

- You have a **small number of producer accounts** (single digits)
  and a **stable contract** (one event type per source).
- You need **lowest possible latency** (no Lambda hop).
- You're forwarding **AWS service events** (e.g. consolidating
  S3 events from many accounts into one audit bus).

For high-fanout, transformation, or enrichment, use Pipes.

## Hands-on

```bash
# Preview (after L15)
python3 -m pytest 03_rules/code/test_put_rule.py -v -k cross
```

## Quiz prep

- What's the resource policy on the destination bus called? (`put_permission`.)
- How do you refer to a bus in another region? (Full ARN, not name.)
- How many statements can a bus resource policy have? (Console
  shows 10; API allows more.)

## Further reading

- AWS docs: [Cross-account event bus access](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-cross-account.html)
- AWS docs: [Event bus resource policies](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-bus-perms.html)
- [`./L15_section_recap.md`](./L15_section_recap.md) — next lecture

## What's next

L15 — **Section 3 Recap + `put_rule.py` walk-through** — we tie
Sections 1–3 together, walk through the demo code, and run the
test suite.
