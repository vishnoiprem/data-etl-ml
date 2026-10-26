# app/ — AWS SAM hello-world (Lambda + API Gateway)

> **The standard `sam init` Node.js 24 + Lambda + API
> Gateway scaffold, kept here as a known-good starting
> point for any serverless work in the portfolio.** One
> function (`HelloWorldFunction`), one route
> (`GET /hello`), one test event. The pattern is
> correct; the engineering is the bare minimum.

The value of keeping this scaffold in the repo is that
it's the answer to "show me a working SAM project
from scratch." Most serverless work in this portfolio
(under `agentic-ai/5-amazon-transcribe/`, the AWS
projects in `aws/ecs-data-ingestion/`, the data
pipelines in `data-engineering/`) starts from a
similar shape and adds domain logic on top.

---

## What's in this directory

| Path | What it is |
|------|------------|
| `template.yaml` | The SAM template: defines the Lambda function, the IAM role, and the API Gateway route |
| `samconfig.toml` | The `sam deploy` config (stack name, region, capabilities) |
| `hello-world/app.mjs` | The Lambda handler (24 lines, returns `{message: 'hello world'}`) |
| `hello-world/package.json` | The Node deps (none beyond the Lambda runtime) |
| `hello-world/tests/` | Mocha unit tests for the handler |
| `events/event.json` | A sample API Gateway event for `sam local invoke` |
| `output.yaml` | The last `sam deploy` output (the API Gateway endpoint URL) |

The whole project fits in ~10 files. It's the
smallest possible SAM app that's still a real SAM
app.

---

## The shape

```
   ┌──────────────────────────────────────────────────┐
   │  API Gateway (REST API)                           │
   │  GET /hello → HelloWorldFunction                  │
   └──────────────────────┬───────────────────────────┘
                          │
                          ▼
   ┌──────────────────────────────────────────────────┐
   │  Lambda: HelloWorldFunction                       │
   │  - Runtime: nodejs24.x                           │
   │  - Handler: app.lambdaHandler                     │
   │  - Returns: { message: "hello world" }            │
   └──────────────────────────────────────────────────┘
```

`template.yaml` defines all three: the function, the
API route, and the IAM role that lets the function
log to CloudWatch. The handler returns a 200 with a
JSON body — that's it.

---

## How to run it

### 1. Prerequisites

- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- [Node.js 24](https://nodejs.org/en/) + npm
- [Docker](https://hub.docker.com/search/?type=edition&offering=community)
  (for `sam local`)

### 2. Build + deploy (first time)

```bash
cd app
sam build
sam deploy --guided
# -> answers to: stack name, region, confirm changes,
#    allow SAM CLI IAM role creation, save args to samconfig
```

After deploy, the API Gateway endpoint URL is printed
to the console and saved to `output.yaml`.

### 3. Test locally

```bash
# Run a single invocation against a test event
sam local invoke HelloWorldFunction --event events/event.json

# Or emulate the full API on port 3000
sam local start-api
# In another terminal:
curl http://localhost:3000/hello
# -> {"message":"hello world"}
```

### 4. Unit tests

```bash
cd hello-world
npm install
npm run test
# -> mocha picks up tests/
```

### 5. Tail logs

```bash
sam logs -n HelloWorldFunction --stack-name app --tail
```

### 6. Cleanup

```bash
sam delete --stack-name app
```

---

## How to extend it

The pattern for adding resources to the SAM template:

```yaml
Resources:
  MyNewFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: my-handler.lambdaHandler
      Runtime: nodejs24.x
      Events:
        MyApi:
          Type: Api
          Properties:
            Path: /my-route
            Method: get
```

For resources outside the
[SAM specification](https://github.com/awslabs/serverless-application-model/blob/master/versions/2016-10-31.md)
(e.g. S3 buckets, DynamoDB tables, SQS queues), use
standard
[CloudFormation resource types](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-reference.html)
— SAM is a superset of CloudFormation.

---

## What this is NOT

- **Not a real product.** The handler returns
  `{"message": "hello world"}` and does nothing else.
  It's a starting point, not a finished app.
- **Not a TypeScript build.** The handler is plain
  `.mjs`; there's no transpile step. For a TS SAM
  project, use `sam init --runtime nodejs24.x
  --dependency-manager npm` and pick the TypeScript
  template.
- **Not the only serverless build in the repo.** The
  AWS Transcribe + Polly pipeline
  ([`../agentic-ai/5-amazon-transcribe/`](../agentic-ai/5-amazon-transcribe/))
  is a more complete serverless build (Transcribe +
  Comprehend PII + Polly + S3). It includes a
  **security warning** about hardcoded AWS keys in
  the source that you should read before using the
  pattern.

---

## Related directories

- [`../agentic-ai/5-amazon-transcribe/`](../agentic-ai/5-amazon-transcribe/) —
  a more complete serverless audio pipeline (S3 →
  Transcribe → Comprehend → Polly). Builds on this
  pattern.
- [`../aws/ecs-data-ingestion/`](../aws/ecs-data-ingestion/) —
  the ECS / Fargate cousin (compute-shaped, not
  event-shaped).
- [`../sam-installation/`](../sam-installation/) —
  the SAM CLI v2 source tree (a fork of the
  AWS SAM CLI; the install that drives this
  `sam build` / `sam deploy` flow).
- [The AWS SAM developer guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html)
  for the long-form SAM reference.
