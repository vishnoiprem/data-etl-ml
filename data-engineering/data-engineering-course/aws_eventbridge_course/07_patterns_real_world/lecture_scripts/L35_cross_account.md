---
lecture: L35
title: "Cross-Account + Cross-Region Fan-Out"
duration: "11:30"
section: 7
prereqs:
  - L14
  - L30
downloads: []
---

# L35 — Cross-Account + Cross-Region Fan-Out

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 7 — Patterns + Real-World
> **Duration:** 11:30

## Key terms

- **Resource-based policy** — a JSON policy attached to a resource
  (in our case, an event bus) that says "this principal in this
  account may PutEvents to this bus." Every custom event bus in
  EventBridge has one.
- **Event bus resource policy** — the JSON policy on a custom event
  bus that gates cross-account PutEvents. It looks like an S3
  bucket policy.
- **Organization-wide event bus** — a feature added in 2023. You
  create a single bus in the org management account and every
  member account can put events onto it without any resource
  policy edits.
- **Cross-region event bus target** — a target that points to a
  bus in a different region. EventBridge handles the cross-region
  replication transparently; you do not see the hop.
- **RAM (Resource Access Manager)** — the AWS service for sharing
  resources across accounts in the same organization. EventBridge
  buses are one of the resource types RAM supports.

## Lecture

Pattern #7 in the catalog is **cross-account fan-out** — the
EventBridge topology you ship when you have more than one AWS
account. If you are a single-account shop, this lecture is still
worth watching (you will eventually be multi-account) but you can
skim.

The shape is:

```
Account A (workload)               Account B (events/observability)
   S3 → default bus                      ↑
        │                                │
        └──→ cross-region custom bus ────┘
                  ↓
              Archive (90 days)
                  ↓
             Lambda: audit log
             Lambda: SIEM shipping
             SNS: cross-account paging
```

There are **three** independent axes of fan-out in EventBridge, and
they combine:

1. **Cross-bus** — same account, two different buses.
2. **Cross-account** — different accounts, two different buses.
3. **Cross-region** — different regions, two different buses
   (EventBridge replicates the event internally).

We will cover each, then look at the **organization-wide event
bus** feature, which is the simplest way to do (2) at scale.

### The event bus resource policy (the foundational concept)

Every custom event bus has a **resource policy** that controls who
can call `PutEvents` on it. The policy looks like an S3 bucket
policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowAccountAProductionToPut",
    "Effect": "Allow",
    "Principal": { "AWS": "arn:aws:iam::111122223333:root" },
    "Action": "events:PutEvents",
    "Resource": "arn:aws:events:us-east-1:444455556666:event-bus/prod-events-bus",
    "Condition": {
      "StringEquals": {
        "events:detail-type": ["Order Created", "Order Shipped"]
      }
    }
  }]
}
```

A few things to notice:

- `Principal` is an IAM principal in the **producer** account
  (111122223333 in this example). The bus lives in
  account 444455556666.
- `Resource` is the **bus** ARN, not the rule ARN. The resource
  policy on the bus is what gates cross-account PutEvents; the
  rules on the bus (in the consumer account) decide what to do
  with the events.
- The `Condition` restricts which `detail-type` values the
  producer can send. This is the **blast-radius limiter** — if a
  producer's IAM credentials are compromised, the worst they can
  do is send events of types you pre-approved.
- You can scope the principal further with a `aws:SourceAccount`
  or `aws:SourceArn` condition if you want the bus to only accept
  events from a specific rule in the producer account.

### Pattern 1 — Same-account, cross-bus

The simplest fan-out. In one account, you have:

- `default` bus — for AWS service events (S3, CW, etc.)
- `prod-app-events` — for application events (`PutEvents` from
  your own services)

You put a rule on `prod-app-events` that targets an SQS queue
in the same account, and a second rule on `default` that targets
the same queue. The queue is in account 111122223333, both buses
are in account 111122223333, and no resource policy is needed
because `events:PutEvents` is allowed by default within the same
account.

The bus-to-bus target is set up by selecting "EventBridge event
bus" as the target type and choosing the destination bus ARN.
The rule is then evaluated on the destination bus. This is how
you can, for example, centralize all AWS service events from the
default bus onto a custom `prod-aggregated-events` bus, and have
one set of rules do all the work.

### Pattern 2 — Cross-account, single region

You have a workload in account A and a centralized observability
stack in account B. The pattern is:

1. **In account A**, the workload bus has rules that target
   account B's bus ARN. EventBridge automatically assumes a
   service role to call `PutEvents` in account B.
2. **In account B**, the centralized bus has a **resource
   policy** that allows account A's role to `PutEvents`. The
   rules on the bus then fan out to SQS, Lambda, SNS, etc. in
   account B.

The same account-A → account-B pattern can also be reversed: the
rules in account A target a bus in account B, and account B
listens. The direction of the rule target is what matters, not
the direction of the event flow.

### Pattern 3 — Cross-region

EventBridge supports cross-region targets natively for buses and
SQS. The target ARN includes a region:

```yaml
Targets:
  - Id: "cross-region-bus"
    Arn: "arn:aws:events:eu-west-1:111122223333:event-bus/eu-prod-events"
```

EventBridge handles the cross-region replication internally. You
do not need a Lambda "bridge" function or a cross-region SNS
topic. The latency is roughly 200–500 ms added per event, which
is fine for observability but too much for synchronous workflows.

The constraint: the rule itself must be in the same region as
the rule's targets (other than the bus/SQS cross-region target).
So you cannot have one rule in `us-east-1` that targets two
different regions' Lambda functions directly — you would need two
rules, one per region.

### Pattern 4 — Organization-wide event bus (the modern default)

If you are on AWS Organizations, this is the cleanest pattern for
multi-account fan-out. The setup is:

1. **In the management account**, create a single bus called
   `organization-events-bus`.
2. **Enable** the organization-wide feature on the bus.
3. **Every member account** can now `PutEvents` to that bus
   without any resource policy edits. The `aws:PrincipalOrgID`
   condition in the bus's policy is set to your org ID
   automatically.
4. **In the management account**, write rules on the
   organization-events bus that fan out to SQS, Lambda, SNS, etc.

The blast-radius is exactly the same as the resource-policy
approach, but the **operational** cost is dramatically lower
because you do not edit the bus policy every time a new workload
account is added. The "events" account is the only place the
rules and targets live.

The same pattern is available cross-region: you can have one
`organization-events-bus` in `us-east-1` and a second in
`eu-west-1`, and the rules in each region are independent.

### IAM for cross-account rules

The cross-account rule in the consumer account needs a role
EventBridge can assume to call `events:PutEvents` on the remote
bus. The role's trust policy looks like:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Service": "events.amazonaws.com" },
    "Action": "sts:AssumeRole",
    "Condition": {
      "StringEquals": {
        "sts:ExternalId": "111122223333"
      }
    }
  }]
}
```

The `ExternalId` is the optional but recommended safeguard
against the "confused deputy" problem. For a single-account
fan-out it is overkill; for an organization-wide bus it is
required.

### Common pitfalls

1. **Forgetting the resource policy on the bus.** The error
   message is opaque (`AccessDenied` on `events:PutEvents` with
   no further detail), so this one costs hours. Always set the
   policy and test it from the producer account with
   `aws events put-events --bus-name ...` before you trust the
   wiring.
2. **Same `Source` value in two different accounts.** Every event
   has a `source` field. If account A and account B both emit
   `source: "acme.api"`, you cannot distinguish them in the
   pattern. Convention: include the account ID in the source
   (e.g. `acme.api.acct-A`, `acme.api.acct-B`).
3. **No DLQ on the cross-account rule.** Same lesson as L34. The
   cross-account hop is exactly the place where transient network
   errors are most likely; the DLQ is your safety net.
4. **Organization-wide bus with no rule on it.** The events still
   flow, but they vanish into the bus with no consumer. Always
   have at least one archival rule (so the events are stored) and
   at least one alerting rule (so DLQ-depth alarms fire).

## Hands-on

No code in this lecture. The natural next step is to set up the
organization-wide bus in your own sandbox org (or in a personal
AWS account) and write the resource policy by hand. Then put
events from a second account and watch them arrive on the bus.

## Quiz prep

The quiz will test:

- The role of the event bus resource policy.
- The `events:detail-type` condition as a blast-radius limiter.
- When to use the organization-wide bus vs the resource-policy
  approach.

## Further reading

- AWS docs: "Cross-account event bus":
  <https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-cross-account.html>
- AWS docs: "Organization-wide event bus":
  <https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-organization-event-bus.html>
- EventBridge FAQs:
  <https://aws.amazon.com/eventbridge/faqs/>

## What's next

L36 is the **course wrap-up**. We recap what you have built, point
you at the docs to keep learning, and sign off.

**Ready? Let's close out the course.**
