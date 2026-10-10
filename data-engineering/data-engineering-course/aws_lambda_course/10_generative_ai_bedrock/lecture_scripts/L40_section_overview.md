---
title: L40 — Section Overview
author: Prem Vishnoi <prem.vishnoi@example.com>
section: 10
duration: 0:26
---

# L40 — Section Overview

> Welcome to **Section 10** — the generative-AI capstone of the course.
> Across the next 40 minutes you will build a production-ready
> serverless GenAI application end-to-end on AWS.

## Prereqs

- Sections 1–9 completed (Lambda, IAM, API Gateway, JSON event handling).
- AWS account with Bedrock model access enabled (see L43).
- Python 3.11+ and `boto3 >= 1.34`.

## Key terms

- **Foundational Model (FM)** — a large pre-trained model (Cohere, Anthropic, Meta, AI21, Stability) you can call via Bedrock without training your own.
- **AWS Bedrock** — fully managed serverless service that exposes FMs through a single `InvokeModel` API.
- **Prompt engineering** — the discipline of crafting inputs that coerce a generative model into the exact output schema you need.
- **Structured output** — a response that the model returns as JSON (or another parseable format) instead of free text.

## What you will build

A **manufacturing defect summarizer** for a factory floor:

```
client → API Gateway → Lambda → Bedrock (Cohere Command) → Lambda → client
```

A line operator pastes a free-text defect description into a UI (or a
mobile app `POST`s one). The API returns a structured JSON object:

```json
{ "summary": "...", "category": "mechanical", "severity": "high" }
```

The end-to-end round-trip — including the model call — typically
completes in **1.5 to 2.5 seconds**.

## Lecture map

| L# | Topic | Min |
|---|---|---|
| L41 | Use case and architecture | 4:01 |
| L42 | AWS Bedrock overview (models, pricing, RAG) | 2:24 |
| L43 | Lambda prerequisites — IAM and model access | 5:50 |
| L44 | Write the Lambda that calls Bedrock | 20:36 |
| L45 | Wire the API Gateway REST API | 5:34 |
| L46 | End-to-end demo | 1:13 |

## Quiz prep

You will be tested on the Bedrock IAM actions, the `InvokeModel` request
shape, prompt engineering for structured output, and API Gateway
CORS/throttling trade-offs.

## Further reading

- AWS Bedrock — [User Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html)
- Cohere on Bedrock — [Supported models](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html)
- Bedrock pricing — [https://aws.amazon.com/bedrock/pricing/](https://aws.amazon.com/bedrock/pricing/)
