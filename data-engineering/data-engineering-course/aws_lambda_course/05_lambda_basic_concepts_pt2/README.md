# Section 5 — AWS Lambda Basic Concepts (Part 2): Invocation Model & Limits (L19–L22, 15 min)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

Section 5 is the **theoretical bridge** between the Lambda foundation in
Section 2, the hands-on boto3 work in Section 4, and the enterprise
use case that follows in Section 6. After four lectures of writing
handlers and pointing them at S3, EC2, and DynamoDB, we pause to look
upstream and ask: **how was my function actually called, and what are
the hard limits I have to design around?**

Two concepts drive the section:

1. **The Invocation Model** — there are exactly four ways AWS Lambda
   can be invoked (synchronous, asynchronous, event-source mapping /
   poll-based, and direct invocations from other services such as
   API Gateway or Step Functions). Each behaves differently with
   respect to retries, error handling, concurrency, and the
   `event` payload your handler receives. Mixing them up is one of
   the most common sources of subtle production bugs.
2. **Lambda Limits** — Lambda is not an EC2 instance. There are
   hard service-level caps (timeout, memory, payload size,
   concurrent executions, deployment-package size, ephemeral
   disk, etc.) that you must design within. This section focuses on
   **timeout** — the limit students hit first and the one that
   determines whether your function ever returns a response at all.

## What you'll learn

- Name the **4 invocation models** Lambda supports and describe how
  each one returns results, retries on failure, and consumes concurrency.
- Decide **which invocation model to choose** for a given integration
  (API Gateway vs EventBridge vs S3 events vs Kinesis).
- **Deploy an async Lambda and trigger it from EventBridge**, then
  invoke the same function **synchronously from a REST call**, and
  observe the difference in the response shape.
- Understand the **15-minute hard timeout** limit, what happens when
  your handler exceeds it, and the **best practices** for designing
  around it (raise it where you can, offload long work to Step
  Functions or ECS, make handlers idempotent, use DLQs).

## Lecture map

| L# | Title | Min | File |
|---|---|---|---|
| L19 | AWS Lambda — Basic Concepts Part 2 — Section Overview | 0:32 | `lecture_scripts/L19_section_overview.md` |
| L20 | AWS Lambda Invocation Model — Theory | 3:33 | `lecture_scripts/L20_invocation_model_theory.md` |
| L21 | AWS Lambda Invocation Model — Hands On | 7:16 | `lecture_scripts/L21_invocation_model_hands_on.md` |
| L22 | Lambda Limits — Timeout | 4:06 | `lecture_scripts/L22_lambda_limits_timeout.md` |

## Code layout

```
05_lambda_basic_concepts_pt2/code/
└── invocation_demo/             ← L21  — async + sync invoke examples
    ├── README.md
    ├── async_handler.py         # event-source-mapping style handler
    ├── sync_handler.py          # API-Gateway / boto3 invoke style
    └── invoke_demo.py           # boto3 invoke vs invoke_async walkthrough
```

All scripts are runnable from your laptop using `moto` for the
Lambda API and the AWS CLI for the real account. The lecture file
walks you through both paths.

## Where this section leads

Section 6 (L23–L24) takes the S3 + DynamoDB primitives from
Section 4 and the invocation understanding from this section and
wires them into a real **S3 → Lambda → DynamoDB** banking JSON
pipeline. The pipeline uses the **S3 event-source mapping** you
learned about in L20 — so if the distinction between sync, async,
and poll-based invocations is not yet automatic, work through
L20–L21 again before moving on.
