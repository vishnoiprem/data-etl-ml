# Assignment 6 — CDK v2 Stack: Bedrock + API Gateway

> **Section:** 12 (CDK v2) + 10 (Generative AI Bedrock)
> **Estimated time:** 8 hours
> **Deliverable:** A CDK v2 stack (Python or TypeScript — your choice) that deploys the Bedrock Lambda from section 10 and exposes it behind an API Gateway endpoint.
> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

## Learning objectives

By the end of this assignment you will be able to:

1. Use the **AWS CDK v2** (Python or TypeScript) to model a complete serverless stack: Lambda, API Gateway, IAM role, log group.
2. Take a hand-written Lambda from section 10 and integrate it into a CDK app.
3. Wire **Amazon Bedrock** (Cohere Command or another text model) as the backing model and grant the Lambda the right `bedrock:InvokeModel` permission.
4. Add a **Lambda integration** to API Gateway with `AWS_PROXY` and a payload format version 2.0.
5. Manage CDK **assets** (the Lambda zip) with `BundlingOptions` or `Code.from_asset`.
6. Run `cdk synth`, `cdk diff`, and `cdk deploy` confidently and read the diff.

## Background

Section 10 walks through a manufacturing-defect summarizer: a user POSTs a defect description to a Lambda, the Lambda calls Bedrock (Cohere Command), and the response is the summary. The lecture is console-driven. This assignment ports the same architecture to CDK and puts a public REST endpoint in front of it.

## Architecture

```
Client ──POST /summarize {defect_text}──▶ API Gateway ──▶ BedrockLambda ──▶ Bedrock (Cohere)
                                                                                  ▲
                                                                                  │ bedrock:InvokeModel
                                                                       granted on: arn:aws:bedrock:...::foundation-model/cohere.command-text-v14
```

See `assets/architecture_bedrock.mmd`.

## Step-by-step tasks

### Step 1 — Pick the language

You can write the CDK app in Python or TypeScript. The Lambda handler itself is Python (the section 10 code is Python). Choose one:

- **Python CDK** — single language, fastest to scaffold. The CDK app and the handler are both Python.
- **TypeScript CDK** — matches the lecture's CDK section. Use `aws-cdk-lib` 2.150+.

Either choice is graded at parity. **The instructions below use Python**; if you choose TypeScript, translate the constructs (the CDK API is identical).

### Step 2 — Scaffold the project

```bash
mkdir bedrock_cdk && cd bedrock_cdk
cdk init app --language python
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
pip install aws-cdk-lib constructs
```

Add a `lambda/` directory with `handler.py` and `requirements.txt` (the lambda deps, separate from the CDK app deps).

### Step 3 — Bring the Bedrock handler from section 10

Reuse the handler from L44. The minimum handler interface is:

```python
import json, os, boto3

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "cohere.command-text-v14")
bedrock = boto3.client("bedrock-runtime")

def handler(event, context):
    body = json.loads(event.get("body", "{}"))
    prompt = body.get("defect_text", "").strip()
    if not prompt:
        return {"statusCode": 400, "body": json.dumps({"error": "defect_text required"})}

    body = {
        "prompt": f"Summarize this manufacturing defect in 2 sentences:\n\n{prompt}",
        "max_tokens": 200,
        "temperature": 0.3,
    }
    resp = bedrock.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )
    payload = json.loads(resp["body"].read())
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"summary": payload.get("generations", [{}])[0].get("text", "")}),
    }
```

Adjust the response parsing to the actual Cohere payload shape (`generations[0].text`).

### Step 4 — Add the CDK stack

`bedrock_cdk/bedrock_cdk_stack.py`:

```python
from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_iam as iam,
    BundlingOptions,
)
from constructs import Construct

class BedrockCdkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # ---- Lambda role: logs + bedrock:InvokeModel on the specific model
        role = iam.Role(self, "BedrockLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_arn(
                    "service-role/AWSLambdaBasicExecutionRole"),
            ],
        )
        role.add_to_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=[f"arn:aws:bedrock:{self.region}::foundation-model/cohere.command-text-v14"],
        ))

        # ---- Lambda
        fn = _lambda.Function(self, "BedrockSummarizer",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="handler.handler",
            code=_lambda.Code.from_asset("lambda"),
            role=role,
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={"BEDROCK_MODEL_ID": "cohere.command-text-v14"},
        )

        # ---- API Gateway
        api = apigw.RestApi(self, "BedrockApi",
            rest_api_name="Bedrock Summarizer",
            description="Manufacturing defect summarizer backed by Bedrock",
            deploy_options=apigw.StageOptions(stage_name="prod"),
        )
        summarize = api.root.add_resource("summarize")
        summarize.add_method("POST", apigw.LambdaIntegration(fn, proxy=True))
```

If you need to bundle extra Python deps into the Lambda (e.g., `requests`), use `BundlingOptions`:

```python
fn = _lambda.Function(self, "BedrockSummarizer",
    runtime=_lambda.Runtime.PYTHON_3_12,
    handler="handler.handler",
    code=_lambda.Code.from_asset("lambda", bundling=BundlingOptions(
        image=_lambda.Runtime.PYTHON_3_12.bundling_image,
        command=["bash", "-c", "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output"],
    )),
    ...
)
```

### Step 5 — Bedrock model access

In the AWS console, go to **Bedrock > Model access** and request access to `Cohere Command` (or `Claude 3 Sonnet` if you switch). Until access is granted, the Lambda will receive an `AccessDeniedException` from `bedrock-runtime`. Document the exact step in the README.

### Step 6 — Deploy and test

```bash
cdk bootstrap
cdk synth
cdk diff
cdk deploy
```

`cdk diff` should show the new resources. `cdk deploy` should print the API URL as an output.

Test:

```bash
API=$(aws cloudformation describe-stacks --stack-name BedrockCdkStack \
  --query 'Stacks[0].Outputs[?OutputKey==`BedrockApiEndpoint...].OutputValue' --output text)
# or just cdk deploy prints it
curl -i -X POST -H "Content-Type: application/json" \
  -d '{"defect_text":"Weld seam on the rear quarter panel shows porosity along 30cm of the lower flange. Operator noticed after primer."}' \
  "$API/summarize"
```

You should see a 200 with a JSON body containing a `summary` field.

### Step 7 — Add observability

- `tracing=_lambda.Tracing.ACTIVE` on the Lambda.
- `apigw.RestApi(... deploy_options=apigw.StageOptions(tracing_enabled=True, ...))`.
- Add a CloudWatch dashboard with three widgets: invocations, errors, throttles.
- Add a CloudWatch alarm on `Errors >= 1` over 1 minute.

### Step 8 — README

Required sections:

1. **Architecture** — embed `assets/architecture_bedrock.mmd`.
2. **Prereqs** — Node 20+ (for CDK CLI), Python 3.11+, Bedrock model access.
3. **Local dev** — `cdk synth` command, expected output file.
4. **Deploy** — `cdk deploy` and what the outputs look like.
5. **Invoke** — sample `curl`.
6. **Troubleshoot** — `AccessDeniedException` from Bedrock (no model access), `ModelTimeoutException`, `ThrottlingException`.
7. **Cleanup** — `cdk destroy`.

## Deliverables

- [ ] CDK project (Python or TypeScript) with `app.py` (or `app.ts`) and stack file.
- [ ] `lambda/handler.py` and `lambda/requirements.txt`.
- [ ] `cdk synth` output (paste the relevant section of the CloudFormation template, ~200 lines).
- [ ] `cdk diff` output showing a clean diff against a fresh stack.
- [ ] `curl` transcript of a successful `POST /summarize`.
- [ ] CloudWatch dashboard JSON (export from the console or `aws cloudwatch get-dashboard`).
- [ ] `README.md` (all 7 sections).

## Grading rubric (100 points)

| Category | Points | What we look for |
|---|---|---|
| CDK app boots | 10 | `cdk synth` produces a valid CloudFormation template. |
| Lambda is wired | 15 | `cdk deploy` creates the function and the role. |
| Bedrock permission | 15 | IAM policy grants `bedrock:InvokeModel` on the specific model ARN (not `*`). |
| API endpoint works | 25 | `POST /summarize` returns 200 with a `summary` field. |
| Observability | 10 | X-Ray + CloudWatch dashboard + alarm. |
| README | 15 | All 7 sections, including a "no model access" troubleshoot snippet. |
| Cleanup | 10 | `cdk destroy` removes every resource, including the log group. |

Deductions:

- `-15` if the IAM policy is `Resource: "*"` for Bedrock (use the model ARN).
- `-10` if the Lambda has no timeout (default 3s is too low for Bedrock).
- `-10` if `cdk diff` after a no-op edit is non-empty.
- `-5` if `cdk destroy` leaves the log group behind.

## Stretch goals (optional, +10 each, capped at +20)

- Add a **WAFv2 WebACL** with a `RateBasedStatement` (200 / 5 min) attached to the API Gateway stage.
- Add a **Lambda Authorizer** (assignment 4) in front of `/summarize`.
- Add a **DynamoDB table** that logs every prompt + response for offline evaluation.
- Switch the backing model to **Claude 3 Sonnet** and compare response quality in the README.