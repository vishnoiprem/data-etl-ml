---
lecture: L36
title: "Course Wrap-Up + What to Read Next"
duration: "8:45"
section: 7
prereqs:
  - L35
downloads: []
---

# L36 — Course Wrap-Up + What to Read Next

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 7 — Patterns + Real-World
> **Duration:** 8:45

## Prereqs

- Sections 1 through 7, including the patterns catalog in L30 and
  the cross-account / DLQ deep dives in L34–L35.

## Key terms

- **AWS What's New** — the AWS blog post feed for service launches.
  EventBridge posts there quarterly (sometimes more often); it is
  the single best way to keep up with new features.
- **CDK v2 `events` module** — the AWS CDK construct library for
  EventBridge. The `events.Rule`, `events.EventBus`, and
  `events.Archive` constructs cover 95% of what you will ever
  need.
- **EventBridge Schema Registry** — a service that lets you
  discover, generate, and version the schemas of events on your
  buses. A free-by-default feature, worth turning on.
- **SAA-C03 / SAP-C02** — the AWS Solutions Architect Associate and
  Professional exams. EventBridge is a tested topic on both.

## Lecture

We are at the end. Thirty-six lectures, seven sections, five
working code samples, four diagrams, and seven quizzes. You have
the mental model and the production patterns; the rest is
practice. This lecture is short. It has three parts: what you
built, what to read next, and a personal sign-off.

### What you built

A quick recap, section by section:

| Section | Lectures | What you can do now |
|---|---|---|
| 1 — Foundations | L01–L04 | Explain event-driven architecture, pub/sub, and why EventBridge exists |
| 2 — EventBus basics | L05–L09 | Create custom event buses with resource policies; choose default vs custom vs partner |
| 3 — Rules + patterns | L10–L15 | Write event patterns with content filters, prefix matches, and cross-account predicates |
| 4 — Targets | L16–L20 | Wire Lambda, SQS, SNS, Step Functions, and 10+ other targets; configure DLQ + retry |
| 5 — Scheduler | L21–L24 | Replace CloudWatch Events schedules with EventBridge Scheduler; use cron + rate + one-off |
| 6 — Pipes + Archives + Replay | L25–L29 | Build source→filter→enrich→target pipelines; archive events; replay failed invocations |
| 7 — Patterns | L30–L36 | Ship 10 production patterns: S3→Lambda, CW→SNS+SSM, APIGW→Step Functions, DLQ strategies, cross-account fan-out |

You have the vocabulary. You have the diagrams. You have five
`boto3` scripts that pass `pytest` against `moto[events]` with
zero AWS calls. That is enough to ship a production EventBridge
topology on Monday morning.

### What to read next

In rough order of priority:

1. **EventBridge FAQs** — the single most under-read AWS doc.
   It is short, it is dense, and it answers 80% of the questions
   you will have in your first month:
   <https://aws.amazon.com/eventbridge/faqs/>

2. **AWS What's New for EventBridge** — subscribe to the RSS
   feed. New event sources, new targets, and new pattern
   capabilities land here first. The 2023 org-wide bus feature,
   the 2024 SQS Re-drive, and the 2025 schema-registry updates
   were all announced there before the docs caught up:
   <https://aws.amazon.com/about-aws/whats-new/analytics/>

3. **AWS CDK v2 `events` module** — the CDK is the most
   productive way to ship EventBridge in a real codebase. The
   `events.Rule` construct alone replaces about 100 lines of
   CloudFormation YAML. The docs include a full "EventBridge
   bus per microservice" pattern that is worth copying:
   <https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_events-readme.html>

4. **EventBridge Schema Registry** — turn it on. Once enabled,
   your events get versioned schemas for free, and you can
   generate strongly-typed code bindings in TypeScript, Python,
   and Java. The cost is zero and the payoff is large:
   <https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-schema.html>

5. **AWS Well-Architected Framework — "Event-Driven Architecture"
   lens** — the new (2025) lens. It codifies the patterns we
   covered in L30 and the failure modes we covered in L34:
   <https://docs.aws.amazon.com/wellarchitected/latest/framework/event-driven-architecture-lens.html>

6. **The ServerlessLand EventBridge workshop** — a free,
   browser-based, hands-on workshop that builds the S3 → Lambda
   and APIGW → Step Functions patterns from L31 and L33:
   <https://serverlessland.com/eventbridge>

7. **SAA-C03 / SAP-C02 study guides** — if you are going for
   the AWS Solutions Architect certifications, EventBridge is
   on both exams. The patterns from L30 are the most-tested
   topic; the cross-account material from L35 is the second.

### What to do in your own account

Three concrete next steps, in order:

1. **Stand up the S3 → Lambda pattern from L31 in your own
   account.** Use CDK. Drop a file in the bucket, watch the
   Lambda fire, add a DLQ, force the Lambda to fail, watch the
   message land in the DLQ. The "feeling" of the pattern is
   different from reading about it; the muscle memory is what
   you want.
2. **Add an organization-wide event bus** (or, if you are
   single-account, a cross-bus fan-out) and put the S3 event on
   it. Add an archive. Replay an event. That exercises L27–L28
   and L35 in one go.
3. **Wire a real CW Alarm → SNS + SSM runbook** for one of
   your own services. Pick a noisy alarm (e.g. `RDS CPU > 80%`)
   and put the SSM runbook on the alarm that resets the RDS
   connection pool. Watch the alarm go ALARM, watch the runbook
   succeed, watch the on-call not get paged. That is the
   payoff of the whole course.

### What I will not cover

In the interest of time, this course does not go deep on:

- **EventBridge Pipes** beyond the L25–L26 overview. The Pipes
  service has more knobs (enrichment with Lambda, API
  destinations, etc.) that are worth a course of their own.
- **EventBridge Schema Registry** beyond the L30 mention. The
  code-binding generation is a separate workflow.
- **API destinations** — the EventBridge feature that lets a
  rule target an external HTTPS endpoint (e.g. a webhook in
  another cloud). It is in the AWS CDK docs and worth reading.
- **Partner events** beyond the L08 overview. Auth0, Datadog,
  and Zendesk have their own onboarding flows; the EventBridge
  side is uniform but the partner side varies.

These are all reasonable next courses.

### A personal note

EventBridge is the AWS service I have changed my mind on the
most. In 2019 I called it "CloudWatch Events with a new name." In
2022 I shipped my first org-wide bus and realized the multi-account
fan-out was the real story. In 2024 I shipped my first Pipes
pipeline and realized the killer feature was partial batch
response, not the enrichment.

The point is: the service is moving. The patterns in L30 are
durable. The specific feature names and quotas shift every
quarter. Treat the patterns as the foundation and the feature
list as the texture. Re-read the FAQ once a year; it is the
single best investment of an hour you can make.

If you have feedback, corrections, or a pattern I should add to
the L30 catalog, my email is at the top of every lecture. I read
every message.

### Thank you

That is the course. Thank you for spending thirty-six lectures
with me. Go build something.

— Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

## Hands-on

None. This is the wrap-up.

## Quiz prep

This is the wrap-up. The section 7 quiz (and the broader course
quiz you can write yourself by combining sections 1–7) tests the
patterns from L30–L35. If you can sketch the topology of all
seven patterns from memory, you are done.

## Further reading

- EventBridge FAQs:
  <https://aws.amazon.com/eventbridge/faqs/>
- AWS What's New:
  <https://aws.amazon.com/about-aws/whats-new/analytics/>
- CDK v2 `events` module:
  <https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_events-readme.html>
- Schema Registry:
  <https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-schema.html>
- Well-Architected "Event-Driven Architecture" lens:
  <https://docs.aws.amazon.com/wellarchitected/latest/framework/event-driven-architecture-lens.html>
- ServerlessLand EventBridge workshop:
  <https://serverlessland.com/eventbridge>
- The full course `SYLLABUS.md` for cross-references.

## What's next

Nothing — you have finished the course. Welcome to the next
pattern you build.
