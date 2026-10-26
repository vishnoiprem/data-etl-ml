---
l_id: L08
title: "Partner Event Bus (SaaS events)"
duration: "7:00"
prereqs:
  - L07 (Custom Event Buses)
---

# L08 — Partner Event Bus (SaaS events)

> **Section:** 2 — EventBus Basics
> **Duration:** 7:00

## Prereqs

- L07 — Custom Event Buses

## Key terms

- **Partner event source** — a pre-built integration offered by a
  third-party SaaS provider (Zendesk, Datadog, Auth0, PagerDuty,
  Shopify, Stripe, …) that can publish events directly into your
  AWS account.
- **Partner event bus** — a bus whose name is prefixed
  `aws.partner/<source>/`. AWS auto-creates the bus when you
  associate with a partner event source.
- **Resource policy** — the JSON document on a bus that says *who*
  can call `PutEvents` on it. Required for partner sources; they
  authenticate as their own AWS service principal.
- **SaaS-on-AWS** — the model where a SaaS provider runs in their
  own AWS account and publishes cross-account to yours. Auth is
  handled by the resource policy, not by HMAC-signed webhooks.

## Lecture

In L04 we mentioned that one of the four things EventBridge added on
top of CloudWatch Events was **SaaS partner event sources**. In this
lecture we look at how that mechanism actually works.

### The old way: public webhook + HMAC

Before EventBridge, if you wanted Zendesk to push events into your
AWS account, you:

1. Stood up an API Gateway REST API with a public endpoint.
2. Wrote a Lambda that verified the HMAC signature Zendesk sends
   on every webhook.
3. Forwarded the event onto an SNS topic or a Lambda downstream.
4. Wrote the IAM policy, the throttle limits, the retry logic, and
   the dead-letter handling.
5. Did it again for Datadog, then for PagerDuty, then for Auth0.

Every team rebuilt the same fragile webhook receiver. The
operational cost was high and the security surface was wide (a
public endpoint is a public endpoint).

### The EventBridge way: partner event source + resource policy

With EventBridge, you:

1. Go to the EventBridge console → **Partner event sources** →
   find the SaaS you want (e.g. Zendesk).
2. Click **Associate** — this creates a partner event bus for you
   named `aws.partner/zendesk.com` and gives you an *association
   name* to hand to Zendesk.
3. The partner authenticates as their own AWS service principal
   (e.g. `zendesk.com`) and publishes events to that bus. You don't
   expose a public endpoint.
4. You attach rules to the bus like any other.

```text
   SaaS partner AWS account          Your AWS account
   ┌─────────────────────┐          ┌────────────────────────────┐
   │                     │          │                            │
   │  zendesk.com        │          │  partner bus               │
   │  service principal  │ ──IAM──► │  "aws.partner/zendesk.com" │
   │                     │  policy  │                            │
   │  (PutEvents allowed)│          │   rule: ticket.created    │
   └─────────────────────┘          │     → Lambda              │
                                    └────────────────────────────┘
```

The auth is done by a **resource policy** on the bus. The policy
grants `events:PutEvents` to the partner's AWS service principal,
optionally scoped to a specific `source` ARN. You can read the
policy in the console; you almost never need to write it by hand.

### Resource policy anatomy

A partner-bus resource policy looks like this (formatted for
readability):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowPartnerPrincipal",
    "Effect": "Allow",
    "Principal": {
      "Service": "zendesk.com"
    },
    "Action": "events:PutEvents",
    "Resource": "arn:aws:events:us-east-1:111122223333:event-bus/aws.partner/zendesk.com",
    "Condition": {
      "StringEquals": {
        "aws:SourceAccount": "444455556666"
      }
    }
  }]
}
```

Three things to note:

- **`Principal.Service`** is the partner's domain. Not an AWS
  account ID, not a role ARN — a service principal.
- **`Action`** is `events:PutEvents` — exactly what the partner
  needs, nothing more.
- **`Condition.aws:SourceAccount`** is the partner's AWS account.
  This is the cross-account guardrail that prevents the partner
  from being impersonated.

### A non-SaaS use: cross-account buses between two of your own
accounts

The same mechanism works for two AWS accounts *you* own. Account A
has the events; account B wants to consume them. You:

1. In account B, create a custom bus and attach a resource policy
   allowing `events:PutEvents` from account A's principal.
2. In account A, attach a **target** to a rule that points at
   account B's bus ARN (this is the *EventBridge bus-to-bus target*
   covered in section 4).
3. Events flow A → B without any public endpoint.

This pattern is the basis of multi-account event fanout in large
organizations; we'll see it again in section 7.

### How a partner bus differs from a custom bus

- **AWS creates the partner bus for you** when you associate with
  a partner event source. You can also create it manually with
  `create_event_bus(Name="aws.partner/zendesk.com")`, but the
  console flow is more common.
- **The name must start with `aws.partner/`** — that's how AWS
  recognizes it as a partner bus.
- **The resource policy is mostly pre-written** for the standard
  partner principals. You only edit it for cross-account use
  cases.
- **You can't rename or reparent it.** If the partner shuts down,
  AWS archives the bus; you can then delete it.

### Limits and gotchas

- Partner event sources are not free — you pay per event ingested
  from the partner, the same as custom events. Pricing is on the
  EventBridge pricing page.
- Not every SaaS you use is on the partner list. As of late 2025
  there are roughly 60 partners; if your vendor isn't there, you
  still have to fall back to a public webhook or a SaaS bridge.
- A single partner event source can only be associated with one
  bus at a time. If two teams want the same source, they need to
  either fan out with a rule (target = second bus) or each associate
  separately, which is not allowed.

In L09 we close the section with a recap and walk through the
`create_event_bus.py` script — which covers default + custom + the
resource policy work in code.

## Hands-on

Optional: in the EventBridge console, click **Partner event
sources** to see the list of currently registered partners. You
don't need to associate with any of them — that's a later lecture.

## Quiz prep

- How is a partner bus authenticated? (Resource policy allowing the
  partner's service principal.)
- What's the required name prefix for a partner bus? (`aws.partner/`)
- Why are partner sources better than public webhooks? (No public
  endpoint, no HMAC code, AWS-managed auth.)

## Key takeaways

- A **partner event bus** is auto-created when you associate with a
  SaaS partner event source; its name is `aws.partner/<vendor>`.
- Auth is a **resource policy** on the bus, granting the partner's
  service principal `events:PutEvents`.
- The same mechanism works for **cross-account buses between your
  own accounts** — no public endpoint, no HMAC code.
- Partner sources replace the old "API Gateway + Lambda + HMAC
  verification" webhook pattern.
- Not every SaaS is a partner; for those, you still need a webhook
  or a SaaS-bridge.

## Further reading

- _Amazon EventBridge User Guide_ — "Receiving events from a SaaS partner"
- _Amazon EventBridge User Guide_ — "Resource-based policies for Amazon EventBridge"
- L31 — Resource-Based Policies + Cross-Account Bus (section 7)
- Section 4 — Targets (bus-to-bus target is here)
