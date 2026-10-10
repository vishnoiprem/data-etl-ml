---
l_id: L04
title: "Why EventBridge? (and where CloudWatch Events fits)"
duration: "7:00"
prereqs:
  - L03 (The Pub/Sub Pattern)
---

# L04 — Why EventBridge? (and where CloudWatch Events fits)

> **Section:** 1 — Foundations
> **Duration:** 7:00

## Prereqs

- L03 — The Pub/Sub Pattern (and how it differs from a queue)

## Key terms

- **CloudWatch Events** — the predecessor of EventBridge. Launched
  2016. Limited to AWS service events and scheduled rules. Replaced
  by EventBridge in 2019; the old API still works but new features
  land on EventBridge only.
- **Event source** — the system that *emits* an event. Three
  categories: AWS services, SaaS partners, and your own apps
  (`PutEvents` API).
- **SaaS partner event source** — a pre-built integration from a
  third-party SaaS provider (Datadog, Zendesk, Auth0, PagerDuty,
  etc.) that publishes events into your bus.
- **Schema registry** — a built-in catalog of event schemas
  (versioned JSON Schema documents) that you can download as code
  bindings (Python, Java, TypeScript).
- **Event bus** — the named router that holds rules and receives
  events. Every AWS account has a `default` bus automatically.

## Lecture

There are now half a dozen ways to wire AWS services together:
CloudWatch Events, SNS, SQS, EventBridge, Step Functions, Lambda
event-source mappings, MSK Connect, AppFlow. Why a new one? What
problem is EventBridge actually solving that the others don't?

### The pre-EventBridge world (2014–2019)

In 2016 AWS launched **CloudWatch Events**. It did two things:

1. **Schedule** — cron-style rules that fire on a timer ("every 5
   minutes, run this Lambda").
2. **React to AWS service events** — "when an EC2 instance changes
   state, send to this SNS topic."

That covered maybe 70% of what people actually wanted. The other 30%
had to be hand-rolled:

- A third-party SaaS (Zendesk, Datadog) wanted to push events into
  your AWS account. You wrote a public API Gateway → Lambda → SNS
  pipeline and bolted on an HMAC signature check. Every team built
  the same fragile webhook receiver.
- You wanted to **filter on the body** of an event ("only fire when
  `$.detail.amount > 100`"). CloudWatch Events supported a subset
  of JSON pattern matching; complex logic required a Lambda in the
  middle.
- You wanted to **debug** a production incident by replaying the
  last hour of events. There was no archive feature; you grepped
  CloudWatch Logs and hoped.
- You wanted to share a single bus across many accounts. You stood
  up cross-account SNS topics and event-source-mapped Lambda
  consumers. Doable, but ugly.

### Enter Amazon EventBridge (July 2019)

EventBridge is "CloudWatch Events, but it's the real thing." Same
schedule + same AWS event source coverage, plus four new
capabilities:

1. **SaaS partner event sources.** Pre-built integrations from
   30+ partners (Datadog, Zendesk, Auth0, PagerDuty, Shopify,
   Stripe, …) that publish events into a dedicated *partner event
   bus* in your account. The auth is done via a resource policy;
   no public webhook receiver needed.
2. **Schema registry.** Every event that flows through your bus is
   inspected; you can download a versioned JSON Schema or a
   language binding (Python, Java, TypeScript) for any event
   type. Goodbye, hand-written dicts.
3. **Archives & replay.** Turn on an archive on a bus; events are
   stored for up to 365 days. Replay them to a *different* bus or
   a *different* time range. This is the killer feature for
   retroactive debugging and backfills.
4. **Cross-account / cross-region buses.** A first-class way to
   share an event bus across many accounts and regions via a
   resource policy, with optional resource-based access controls.

EventBridge is the *pub/sub* tier; it does not replace SQS, Kinesis,
or Step Functions. Those become **targets** on a rule, which is the
topic of section 4.

### The 3 categories of events

EventBridge routes events from three categories of sources:

```text
  ┌──────────────────────────────────────────────────────────┐
  │                    EVENT BRIDGE BUS                       │
  │                                                          │
  │   ┌──────────┐    ┌──────────┐    ┌──────────┐           │
  │   │ AWS      │    │ SaaS     │    │ Custom   │           │
  │   │ services │    │ partners │    │ apps     │           │
  │   └──────────┘    └──────────┘    └──────────┘           │
  │   e.g. EC2        e.g. Zendesk     e.g. your app        │
  │   state change    ticket.created   via PutEvents API    │
  └──────────────────────────────────────────────────────────┘
```

1. **AWS services.** When something happens inside AWS — an EC2
   instance stops, an S3 object is created, a CodeBuild build
   fails — the service publishes an event to your `default` bus.
   These are the events you'd have seen in CloudWatch Events.
2. **SaaS partners.** A registered SaaS partner (Zendesk,
   PagerDuty, Datadog, Auth0, Shopify, Stripe, …) can publish
   events directly to a *partner event bus* in your account, with
   auth handled by a resource policy you control. You don't have
   to expose a public API endpoint.
3. **Custom applications.** Your own code publishes events with
   the `PutEvents` API. The `source` is typically your own
   reverse-DNS-style identifier (e.g. `com.acme.orders`).

These three categories all share the same **event envelope** — a
common set of top-level fields (`version`, `id`, `source`,
`detail-type`, `time`, `resources`, `region`, `account`) wrapping
a `detail` JSON object that's free-form per source. This envelope
is what lets one rule engine and one pattern language work for
every category.

### When to pick EventBridge vs. SNS / SQS

A pragmatic rule of thumb:

- **Need fanout, schema discovery, archive/replay, or a SaaS
  integration?** EventBridge.
- **Need one consumer per message with back-pressure, or exactly-once
  work distribution?** SQS (or SQS FIFO).
- **Need raw pub/sub fanout at very high TPS with no schema
  ceremony?** SNS (it's cheaper per million publishes).
- **Need ordered stream processing with offset replay?** Kinesis
  Data Streams.
- **Need a multi-step workflow with retries and human approval?**
  Step Functions, often with EventBridge as the trigger.

Most production systems end up using several of these together —
EventBridge as the front door, SQS as a buffer, Lambda as the
worker, Step Functions for the long-running jobs.

## Hands-on

Nothing to do for this lecture — it is conceptual. In L05 we open
the EventBridge console and you'll see the three categories of
events for yourself.

## Quiz prep

- Name the four capabilities EventBridge added on top of CloudWatch
  Events.
- What are the three categories of event sources?
- When would you pick EventBridge over SNS?

## Key takeaways

- **CloudWatch Events** (2016) is the predecessor; it still works,
  but new features land on **EventBridge** (2019) only.
- EventBridge added **SaaS partner sources, schema registry,
  archives/replay, and cross-account buses** on top of CW Events.
- The three event categories are: **AWS services, SaaS partners,
  custom apps** — all share the same envelope.
- EventBridge is the *pub/sub* tier; it complements SQS, Kinesis,
  SNS, and Step Functions, it does not replace them.
- Pick EventBridge when you need fanout + filtering + replay;
  pick SQS when you need one consumer per message; pick Kinesis
  when you need ordered replay; pick SNS when you need cheap raw
  fanout with no schema ceremony.

## Further reading

- _AWS What's New_ — Amazon EventBridge launch announcement (July 2019)
- _AWS re:Invent 2019_ — "Intro to Amazon EventBridge" (SVS218)
- L05 — What is an Event Bus?
- Section 6 — Archives + Replay (the killer feature)
