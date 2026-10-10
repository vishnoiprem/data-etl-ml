---
l_id: L21
title: AWS Lambda Invocation Model — Hands On
duration: 7:16
prereqs:
  - L20 (Invocation Model — Theory)
  - L17 (EventBridge + Lambda)
---

# L21 — AWS Lambda Invocation Model — Hands On

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 5 — AWS Lambda Basic Concepts (Part 2)
> **Duration:** 7:16

## Prereqs

- L20 — the four invocation models and the diagram
- L17 — how EventBridge schedules trigger Lambda
- L07 — Lambda execution role
- AWS CLI v2 configured; `us-east-1`; an IAM user with
  `AdministratorAccess` for the lab

## Key terms

- **`invoke`** — `boto3` (and the AWS CLI) call to invoke a
  function. `InvocationType='RequestResponse'` is **synchronous**;
  `InvocationType='Event'` is **asynchronous**.
- **`invoke_async`** — legacy async invocation API. Still works,
  but limited to a 128 KB payload and no destination support.
  Prefer `invoke(InvocationType='Event')` for new code.
- **EventBridge rule** — the resource that matches events and
  routes them to a target (in our case, a Lambda function).
- **`--payload` / `--cli-binary-format raw-in-base64-out`** — the
  AWS CLI v2 default. Required to pass JSON payloads without
  base64-encoding them.

## Lecture

In L20 we drew the four-invocation-models diagram. In this
lecture we make two of those models **concrete** on a real AWS
account:

1. **Async** — an EventBridge rule fires every 5 minutes and
   invokes a Lambda that logs the event.
2. **Sync** — the **same** Lambda is also called synchronously
   from a REST call, using `boto3 client.invoke` with
   `InvocationType='RequestResponse'`.

The goal: see the difference in the response, in CloudWatch
Logs, and in the `event` payload that the handler receives.

### Step 1 — Create the Lambda function

The handler logs the event and returns a small JSON envelope.
The exact same code path works for both async and sync
invocation — the only difference is what the caller sees on
the other side.

```python
# 05_lambda_basic_concepts_pt2/code/invocation_demo/async_handler.py
import json
import datetime
import logging

log = logging.getLogger()
log.setLevel(logging.INFO)


def handler(event, context):
    log.info("invoked at %s", datetime.datetime.utcnow().isoformat())
    log.info("event payload: %s", json.dumps(event))
    # In an async invocation, this return value is discarded.
    # In a sync invocation, it is returned to the caller.
    return {
        "ok": True,
        "echoed_event_size": len(json.dumps(event)),
        "function_name": context.function_name,
        "request_id": context.aws_request_id,
    }
```

Package and deploy (assumes the IAM role `lambda_basic_exec`
was created in L07):

```bash
cd 05_lambda_basic_concepts_pt2/code/invocation_demo
zip -r function.zip async_handler.py

aws lambda create-function \
  --function-name invocation-demo \
  --runtime python3.11 \
  --handler async_handler.handler \
  --role arn:aws:iam::$(aws sts get-caller-identity \
       --query Account --output text):role/lambda_basic_exec \
  --zip-file fileb://function.zip \
  --region us-east-1
```

### Step 2 — Async trigger via EventBridge

Create a rule that fires every 5 minutes. This is the
**asynchronous** model — the rule hands the event to Lambda
and moves on; Lambda is responsible for retries and DLQ.

```bash
aws events put-rule \
  --name "invocation-demo-5min" \
  --schedule-expression "rate(5 minutes)" \
  --region us-east-1

aws events put-targets \
  --rule "invocation-demo-5min" \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:$(aws sts get-caller-identity --query Account --output text):function:invocation-demo" \
  --region us-east-1

aws lambda add-permission \
  --function-name invocation-demo \
  --statement-id "AllowEventBridgeInvoke" \
  --action "lambda:InvokeFunction" \
  --principal events.amazonaws.com \
  --source-arn "arn:aws:events:us-east-1:$(aws sts get-caller-identity --query Account --output text):rule/invocation-demo-5min" \
  --region us-east-1
```

Wait five minutes, then look in CloudWatch Logs:

```bash
aws logs tail /aws/lambda/invocation-demo --follow
```

You will see one log stream per invocation. Each one contains
the `event` payload — but the rule never *sees* a response,
because there is no caller waiting for one.

### Step 3 — Synchronous invocation via boto3 / REST

Now invoke the **same** function synchronously. The
`InvocationType` is the only thing that changes.

```python
# 05_lambda_basic_concepts_pt2/code/invocation_demo/invoke_demo.py
import json
import boto3

lambda_client = boto3.client("lambda", region_name="us-east-1")

# --- Synchronous invocation ---
# Caller blocks until the function returns. Response is the
# function's return value, base64-decoded if necessary.
sync_resp = lambda_client.invoke(
    FunctionName="invocation-demo",
    InvocationType="RequestResponse",   # <-- SYNC
    Payload=json.dumps({"order_id": 42, "amount": 199.95}),
)
sync_payload = json.loads(sync_resp["Payload"].read())
print("SYNC response:", json.dumps(sync_payload, indent=2))
print("SYNC status code:", sync_resp["StatusCode"])  # 200 on success

# --- Asynchronous invocation ---
# Caller continues immediately. Lambda is responsible for
# retries and the DLQ. There is no response payload.
async_resp = lambda_client.invoke(
    FunctionName="invocation-demo",
    InvocationType="Event",             # <-- ASYNC
    Payload=json.dumps({"source": "manual-test", "msg": "hi"}),
)
print("ASYNC status code:", async_resp["StatusCode"])  # 202
# Note: there is no Payload to read for an async invocation.
```

Run it:

```bash
python 05_lambda_basic_concepts_pt2/code/invocation_demo/invoke_demo.py
```

The **synchronous** call prints the handler's return value
(echoed event size, function name, request ID). The
**asynchronous** call returns HTTP **202** with no payload —
the caller is already on the next line of code while Lambda
is asynchronously running the handler.

### Step 4 — Sync over a real REST call

If you have an API Gateway in your account from Section 7/8,
swap the `boto3` call for an HTTPS POST. The behavior is
identical: API Gateway invokes Lambda **synchronously** with
`RequestResponse`, and your HTTP client gets the handler's
return value back as the response body.

### What to look for

- **Response shape** — sync returns your handler's return
  value; async returns 202 and nothing else.
- **CloudWatch Logs** — both invocations land in the same log
  group, one stream per request, with the same `aws_request_id`
  pattern.
- **Retries** — if your handler raises, only the async
  invocation is retried by Lambda (2 by default). The sync
  caller sees the exception once and is on its own.
- **DLQ** — attach an SQS queue as the function's
  `OnFailure` destination and watch a forced failure land in
  the queue.

## Hands-on

- `code/invocation_demo/async_handler.py` — the handler
- `code/invocation_demo/invoke_demo.py` — the boto3 sync/async
  walkthrough
- `code/invocation_demo/README.md` — run-it-locally steps
  including `moto` and the AWS CLI commands

## Quiz prep

- Q1, Q2, Q3 of `quizzes/section_5.md` test the response
  shape and retry behavior you just observed in the console.
- Be ready to explain in one sentence why `InvocationType='Event'`
  returns 202 with no payload.

## Further reading

- AWS docs: [`Invoke`](https://docs.aws.amazon.com/lambda/latest/dg/API_Invoke.html)
- AWS docs: [EventBridge → Lambda](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-targets.html)
- AWS docs: [Lambda destinations (for DLQ-style routing)](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html#invocation-async-destinations)
- `lecture_scripts/L20_invocation_model_theory.md` — the theory
  this lecture makes concrete
