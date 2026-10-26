---
l_id: L19
title: AWS Lambda — Basic Concepts Part 2 — Section Overview
duration: 0:32
prereqs:
  - L08 (Section 2 — Conceptual Review)
  - L18 (Lambda with DynamoDB)
---

# L19 — Section Overview

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 5 — AWS Lambda Basic Concepts (Part 2)
> **Duration:** 0:32

## Prereqs

- L08 — Section 2 conceptual review (mental model of what Lambda is)
- L11–L18 — Section 4, where you wrote real handlers against S3,
  EC2, EventBridge, and DynamoDB
- Comfortable with the Lambda execution role and the
  `handler(event, context)` contract

## Key terms

- **Invocation model** — the mechanism by which your Lambda function
  is actually called (sync, async, poll-based, or direct from a
  service such as API Gateway).
- **Event-source mapping (ESM)** — a Lambda resource that polls an
  event source (SQS, Kinesis, DynamoDB Streams, Kafka, etc.) and
  invokes your function for each batch.
- **Timeout** — the maximum wall-clock seconds Lambda will let a
  single invocation run before forcibly terminating it.

## Lecture

Welcome to Section 5 — **AWS Lambda Basic Concepts (Part 2)**.
This is a short, theory-leaning bridge section — only 15 minutes
across four lectures — and it focuses on two things the rest of the
course assumes you understand:

- **L20** — the four invocation models: synchronous, asynchronous,
  event-source mapping (poll-based), and direct service-to-service
  invocation. We will draw a single diagram that you should be able
  to reproduce from memory.
- **L21** — hands on. We will deploy an async Lambda, wire it up to
  an EventBridge schedule, then call the same function synchronously
  from a REST call. You will see the difference in the response
  payload, the retries, and how CloudWatch logs each one.
- **L22** — Lambda limits, with the spotlight on **timeout** (15
  minutes max). We will look at what AWS does when your function
  exceeds the limit, and the four best practices for designing
  around it.

Section 6 then takes these concepts and uses them in the
S3 → Lambda → DynamoDB banking pipeline, where the S3 event-source
mapping is what actually fires the handler.

Let's start with L20 and the four invocation models.

## Hands-on

None for this lecture — it is a roadmap.

## Quiz prep

No quiz questions on this lecture specifically, but the section
quiz (`quizzes/section_5.md`) covers every lecture in the section.

## Further reading

- `05_lambda_basic_concepts_pt2/README.md` — section overview
- `SYLLABUS.md` — authoritative L-ID map
