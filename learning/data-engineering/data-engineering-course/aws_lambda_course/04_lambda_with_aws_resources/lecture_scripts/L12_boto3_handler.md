---
l_id: L12
title: AWS Lambda Basics — Boto3, Client and Resource, Lambda function handler
duration_min: 9.06
prereqs: [L06, L07, L09]
---

# L12 — AWS Lambda Basics: Boto3, Client vs Resource, and the Handler Contract

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 4 — AWS Lambda with S3, EC2, DynamoDB
> **Duration target:** 9:06

## Prereqs

- L06 (Lambda console walkthrough) — you should know what a Lambda
  function *looks like* in the AWS console.
- L07 (Lambda execution role) — you should know why every Lambda needs
  an IAM role and what the trust policy looks like.
- L09 (Python basics part 1) — functions, args, modules.

## Key terms

- **handler** — the Python function AWS Lambda invokes. Always
  `def handler(event, context): ...`.
- **event** — the JSON payload that triggered the Lambda. S3 event,
  API Gateway request, EventBridge schedule — they all arrive as a
  Python `dict`.
- **context** — the runtime object AWS gives you. Holds
  `function_name`, `aws_request_id`, `get_remaining_time_in_millis()`,
  and so on. You almost never need it for the first 5 sections.
- **boto3.client** — low-level AWS service client. 1-to-1 with the
  AWS REST API. Returns *untyped* `dict` responses.
- **boto3.resource** — higher-level, object-oriented wrapper. Returns
  *Python objects* (`s3.Bucket`, `ec2.Instance`) you can iterate. Not
  every service has a resource interface (no `resource('lambda')` for
  example).
- **Session** — a boto3 *Session* holds config, credentials, and the
  region. A Lambda's default session is created by the runtime; you
  almost never create one by hand.

## Lecture

> "Before we write our first Lambda that touches S3, I want to lock
> down the three things every Lambda in this section will share. The
> first is the **handler signature**. The second is how **boto3**
> builds an AWS client. The third is the difference between a
> **client** and a **resource**."

### 1. The handler contract

When AWS invokes your Lambda, it calls the function whose name is set
as the *handler* in the console. The default in this course is
`script.handler` — that means "the `handler` function in `script.py`".
The signature is always the same:

```python
def handler(event, context):
    ...
    return some_dict
```

`event` is a `dict`. Its shape depends on the trigger: S3 gives you
the bucket and object key, API Gateway gives you the HTTP request,
EventBridge gives you the event payload. `context` is a runtime
metadata object — its only commonly-used method is
`context.get_remaining_time_in_millis()`.

Your function must return a value. For S3/EC2/DynamoDB handlers
(returned value doesn't matter) we return a small dict so the test
suite can assert on it. For API Gateway handlers (Section 8) the
return value must be a `{statusCode, body, headers}` dict.

### 2. Boto3 client and resource

Boto3 is the AWS SDK for Python. It is pre-installed in every
Lambda runtime that supports Python (3.9, 3.10, 3.11, 3.12). You
import it once, and you can talk to every AWS service from the same
module.

```python
import boto3

# Low-level client: 1-to-1 with the AWS REST API
s3_client = boto3.client("s3")

# Higher-level resource: object-oriented wrapper
s3_resource = boto3.resource("s3")
```

The difference matters:

| | client | resource |
|---|---|---|
| Returns | `dict` (raw AWS JSON) | Python objects (e.g. `s3.Bucket`) |
| Coverage | Every AWS service | Selected services (S3, EC2, DynamoDB, SNS, SQS, …) |
| Style | Imperative: `s3.list_buckets()` | Object-oriented: `for b in s3.buckets.all():` |
| Pagination helpers | Manual (`get_paginator`) | Built-in (`buckets.all()`) |

For this section we use the **client** everywhere. The client is
predictable, it is what the AWS console SDKs show, and it makes
errors easier to read. We switch to the resource once in L18 for
DynamoDB *batch* writes where the object API is genuinely nicer.

### 3. Regions and the AWS_REGION env var

A Lambda always runs in **one region**. The runtime sets the
`AWS_REGION` environment variable automatically. You should not
hardcode regions; read it from the env:

```python
import os
import boto3

region = os.environ.get("AWS_REGION", "us-east-1")
s3 = boto3.client("s3", region_name=region)
```

The `us-east-1` fallback is for local testing — when you run the
script outside Lambda, `AWS_REGION` is unset, and we want a sensible
default. **Important quirk**: S3 buckets are global in name, but the
*create_bucket* call is region-specific. For `us-east-1` you do not
pass a `LocationConstraint`; for every other region you must. L13
covers this in detail.

### 4. Why every script in this section looks the same

```python
import json
import logging
import os

import boto3

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)


def handler(event, context):
    LOG.info("received event: %s", json.dumps(event))
    # ... service-specific work ...
    return {"status": "ok"}
```

That is the whole skeleton. The only thing that changes between L13
and L18 is the body of the `handler`. Logging, region handling, and
the return dict are constant. By the end of L18 you will be able to
write this skeleton in your sleep.

## Hands-on

Open `code/create_s3/create_s3_bucket.py` (we will write the body in
L13). Notice the structure: `boto3.client`, the `region_name` from
the env var, the `LOG.info` call, the return dict. This file is the
template; every other script in this section copies it.

```bash
cd 04_lambda_with_aws_resources/code/create_s3
python create_s3_bucket.py
```

You should see a log line for the empty event. The body of the
handler is a no-op stub for now; we fill it in during L13.

## Quiz prep

- The handler function must be named `handler` and take `(event, context)`.
- `boto3.client` returns raw dicts; `boto3.resource` returns Python objects.
- The Lambda runtime sets the `AWS_REGION` env var; you should read
  it via `os.environ.get`.
- S3 buckets are global in name but per-region in location.

## Further reading

- AWS docs: [boto3 client vs resource](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/clients.html)
- AWS docs: [Lambda handler context object](https://docs.aws.amazon.com/lambda/latest/dg/python-context.html)
- `code/create_s3/create_s3_bucket.py` — the canonical template
