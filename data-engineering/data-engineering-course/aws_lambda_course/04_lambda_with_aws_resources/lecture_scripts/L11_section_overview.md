---
l_id: L11
title: Section Overview
duration_min: 1.18
prereqs: []
---

# L11 — Section 4 Overview

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 4 — AWS Lambda with S3, EC2, DynamoDB
> **Duration target:** 1:18

## Prereqs

- Sections 1–3 completed (L01–L10). You should already know what AWS
  Lambda is, what the execution role does, and how to write a basic
  Python function.

## Key terms

- **boto3** — the AWS SDK for Python. Every Lambda in this section
  imports it.
- **Handler** — the entry point AWS Lambda invokes. Always
  `def handler(event, context)`.
- **EventBridge schedule** — a cron-like trigger we will use in L17 to
  start and stop EC2 instances automatically.

## Lecture

> "Welcome to Section 4. So far you've learned what Lambda *is* and
> how to write Python. Now we're going to point Lambda at real AWS
> services. In the next seven lectures you'll write six production
> Lambda handlers from scratch: create an S3 bucket, delete an S3
> bucket, list S3 buckets, create and start and stop an EC2 instance,
> put DynamoDB items, and finally wire it all up to an EventBridge
> schedule so the EC2 instance starts every morning at 8 and stops
> every evening at 8. The same handler signature every time —
> `def handler(event, context)` — and the same boto3 import. After
> this section, the words 'Lambda with S3' or 'Lambda with DynamoDB'
> won't be scary. They will be recipes you can copy."

That is the whole section in one paragraph. The rest of the lectures
fill in the recipes. L12 is the theory lecture — the handler
contract, `boto3.client` versus `boto3.resource`, sessions, and
regions. L13 through L15 are three short S3 Lambdas. L16 and L17 are
the EC2 pair. L18 closes with DynamoDB.

## Hands-on

There is no separate hands-on for L11. Your first action item is to
clone the repo, create the virtualenv, and run the test suite end to
end so you know the test rig works before you start editing code.

```bash
cd aws_lambda_course
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest 04_lambda_with_aws_resources/code -q
```

You should see all tests passing. If any fail, fix the environment
before you start L12.

## Quiz prep

- The handler function is named `handler` and takes `(event, context)`.
- Every script in this section uses `boto3.client`, not `boto3.resource`.
- The tests use `moto` to mock AWS — no real credentials required.

## Further reading

- `04_lambda_with_aws_resources/README.md` — full section layout
- `02_lambda_basic_concepts/lecture_scripts/L06_console_walkthrough.md`
  — Lambda console refresher
- `03_python_basics/lecture_scripts/L09_python_basics_pt1.md` — Python
  refresher if you need it
