# Section 1 — Foundations

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Lectures:** L01–L04
> **Duration:** ~24 min

This section is the shortest in the course but it sets the vocabulary
for everything that follows. We start with a course overview (the 7
sections, the 5 working demos, the 1 downloadable cheat sheet), then
define what **event-driven architecture** actually means — producer,
consumer, broker, sync vs async, and *why* decoupling matters. We
contrast **pub/sub, message queues, and event streams** with a concrete
"order placed" example, and close with **why EventBridge** — how it
evolved from CloudWatch Events (2016) into the 2019 superset that added
SaaS partners, schema registry, archives/replay, and cross-account buses.

By the end of this section you should know the three categories of
events (AWS services, SaaS partners, custom apps), be able to tell
EventBridge apart from SQS / SNS / Kinesis at a one-sentence level, and
have the right mental model for everything that comes next.

| L# | Title | Min |
|---|---|---|
| L01 | Course Overview | 4:00 |
| L02 | What is Event-Driven Architecture? | 6:30 |
| L03 | The Pub/Sub Pattern (and how it differs from a queue) | 6:00 |
| L04 | Why EventBridge? (and where CloudWatch Events fits) | 7:00 |

## Key concepts you'll need later

- **Event** = past-tense JSON fact; producer doesn't know the consumer.
- **Pub/sub vs queue vs stream** — fanout vs work distribution vs
  ordered log. EventBridge is the pub/sub tier.
- **Three event sources** — AWS services, SaaS partners, your apps.
- **EventBridge vs CloudWatch Events** — same engine, more features
  (partners, schemas, archives, cross-account).

## What comes next

Section 2 is **EventBus Basics** — the first AWS resource we touch.
We create a custom event bus with `boto3`, attach a resource policy,
and verify it all with `moto` tests.
