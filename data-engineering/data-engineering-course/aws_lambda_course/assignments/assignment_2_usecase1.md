# Assignment 2 — Deploy Use Case 1 (S3 + Lambda + DynamoDB) with Alarm + DLQ

> **Section:** 6 (Enterprise Use Case 1)
> **Estimated time:** 6 hours
> **Deliverable:** Working end-to-end stack + `README.md` with deploy / invoke / cleanup steps
> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

## Learning objectives

By the end of this assignment you will be able to:

1. Package a Lambda function (handler + dependency) and deploy it from a `sam` template or `cdk` (your choice — see Step 2).
2. Wire an **S3 event notification** to a Lambda function with a managed event-source mapping.
3. Build a CloudWatch **metric filter** + **alarm** for `Errors >= 1` over a 1-minute window.
4. Configure an **SQS dead-letter queue** as a Lambda `DeadLetterConfig` and prove it catches a deliberately malformed record.
5. Write a runnable `README.md` a teammate can follow without context.

## Background

In L23–L24 you walked through the banking/retail use case: an S3 bucket receives a daily JSON file, an S3 event notification triggers a Lambda, and the Lambda writes each record to a DynamoDB table. The lecture material is intentionally console-heavy. This assignment asks you to take that same code, deploy it as code, and harden it with two production requirements:

- A CloudWatch alarm that pages on Lambda errors.
- An SQS DLQ that captures records the Lambda could not process.

## Architecture

```
S3 bucket (incoming JSON) ──s3:ObjectCreated:*──▶ Lambda ──▶ DynamoDB table
                                                  │
                                                  └──async error──▶ SQS DLQ
                                                                          ▲
CloudWatch Alarm (Errors>=1, 1 period) ───SNS topic (email opt) ──────────┘  notification
```

See `assets/architecture_usecase1.mmd` for the Mermaid version.

## Step-by-step tasks

### Step 1 — Take the lecture code

Start from `06_usecase1_s3_lambda_dynamodb/code/` (L23, L24). The handler reads the S3 event, downloads the object, parses each line as a JSON record, and `put_item`s into DynamoDB. The expected record shape (banking/retail feed) is:

```json
{"transaction_id": "txn-001", "customer_id": "c-1", "amount": 49.99, "currency": "USD", "ts": "2026-01-15T10:00:00Z"}
```

If the section's `code/` directory is empty in your local checkout, re-derive the handler from the lecture (or open the Udemy transcript — the function is ~40 lines).

### Step 2 — Choose a deploy mechanism

Pick **one** of the two. SAM is the simpler option for a single Lambda; CDK is more idiomatic if you plan to grow the stack.

#### Option A — AWS SAM

`sam/template.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Parameters:
  BucketName:
    Type: String
    Default: usecase1-incoming-<your-initials>
Resources:
  IncomingBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Ref BucketName
      NotificationConfiguration:
        LambdaConfigurations:
          - Event: s3:ObjectCreated:*
            Function: !GetAtt ProcessFunction.Arn
  ProcessFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: ../handler
      Handler: app.handler
      Runtime: python3.12
      MemorySize: 256
      Timeout: 30
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref RecordsTable
        - S3ReadPolicy:
            BucketName: !Ref IncomingBucket
        - SQSSendMessagePolicy:
            QueueName: !GetAtt Dlq.QueueName
      DeadLetterQueue: !Ref Dlq
      Events:
        BucketEvent:
          Type: S3
          Properties:
            Bucket: !Ref IncomingBucket
            Events: s3:ObjectCreated:*
  RecordsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: usecase1-records
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - {AttributeName: transaction_id, AttributeType: S}
      KeySchema:
        - {AttributeName: transaction_id, KeyType: HASH}
  Dlq:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: usecase1-dlq
      MessageRetentionPeriod: 1209600  # 14 days
  ErrorAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: usecase1-lambda-errors
      Namespace: AWS/Lambda
      MetricName: Errors
      Dimensions:
        - {Name: FunctionName, Value: !Ref ProcessFunction}
      Statistic: Sum
      Period: 60
      EvaluationPeriods: 1
      Threshold: 1
      ComparisonOperator: GreaterThanOrEqualToThreshold
      TreatMissingData: notBreaching
Outputs:
  BucketName:  {Value: !Ref IncomingBucket}
  FunctionName: {Value: !Ref ProcessFunction}
  TableName:    {Value: !Ref RecordsTable}
  DlqUrl:       {Value: !Ref Dlq}
```

> Note: SAM's `S3` event type on a `Serverless::Function` creates the bucket notification for you — the explicit `NotificationConfiguration` on the bucket is therefore optional but shown for clarity.

#### Option B — CDK v2 (Python)

Create `app.py` with three constructs: `s3.Bucket`, `dynamodb.Table`, `lambda_.Function` with `dead_letter_queue_enabled=True` and a `lambda_.Function.from_function_arn` reference. Add an `cloudwatch.Alarm`.

> Either option is fine. SAM is graded at parity with CDK.

### Step 3 — Add the DLQ wiring

- Set the Lambda's `DeadLetterConfig` to the SQS queue ARN.
- The DLQ must be in the **same region** as the Lambda.
- Confirm that when a record fails to parse, Lambda retries twice and then sends the event to the DLQ. (You can prove this by uploading `bad.json` with the literal string `not-json` and then running `aws sqs receive-message --queue-url $DLQ_URL`.)

### Step 4 — Add the CloudWatch alarm

The alarm in the SAM template above watches the AWS/Lambda `Errors` metric. In CDK:

```python
cloudwatch.Alarm(self, "ErrorAlarm",
    metric=lambda_fn.metric_errors(period=Duration.minutes(1)),
    threshold=1,
    evaluation_periods=1,
    comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
    treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
)
```

**Optional but recommended:** add an SNS topic and email subscription so you actually get paged. Document the email confirmation step in the README.

### Step 5 — Deploy, invoke, verify

```bash
# SAM
sam build && sam deploy --guided --capabilities CAPABILITY_IAM

# CDK
cdk bootstrap
cdk synth
cdk deploy
```

Then:

```bash
BUCKET=$(aws cloudformation describe-stacks --stack-name usecase1 \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' --output text)
aws s3 cp sample.json s3://$BUCKET/incoming/2026-01-15.json
aws dynamodb scan --table-name usecase1-records --max-items 5
```

Verify in the CloudWatch console that:

- A new log group `/aws/lambda/usecase1-ProcessFunction-XXXX` exists.
- The `Errors` metric is `0` (good path).
- After uploading a malformed file, the metric goes to `1` and the alarm transitions to `IN_ALARM`.

### Step 6 — Write the README

Your `README.md` must contain exactly these sections, in this order:

1. **Architecture** — embed the Mermaid diagram from `assets/architecture_usecase1.mmd`.
2. **Prereqs** — AWS CLI v2, Python 3.11+, SAM CLI or Node 20+ (CDK).
3. **Deploy** — copy-pasteable command block.
4. **Invoke** — how to upload a test record + the expected DynamoDB response.
5. **Trigger the alarm on purpose** — how to upload a malformed file and observe the alarm.
6. **Inspect the DLQ** — the exact `aws sqs receive-message` command.
7. **Cleanup** — `sam delete` or `cdk destroy` and any manual resources to remove (e.g., the S3 bucket if it retained objects).

## Deliverables

- [ ] Source tree (`sam/` or `cdk/` + `handler/`).
- [ ] `README.md` (≥ 7 sections above).
- [ ] Screenshot or `aws logs tail` output showing the handler ran.
- [ ] `aws cloudformation describe-stack-events --stack-name usecase1 --max-items 5` output showing `CREATE_COMPLETE` (SAM) or `cdk deploy` summary (CDK).
- [ ] DLQ proof: an SQS `receive-message` call that returns the malformed record.
- [ ] Alarm proof: a `aws cloudwatch describe-alarms` snippet showing `StateValue: IN_ALARM` after the bad upload.

## Grading rubric (100 points)

| Category | Points | What we look for |
|---|---|---|
| Stack deploys cleanly | 25 | `sam deploy` / `cdk deploy` succeeds on the first try. No manual console fixes. |
| Lambda processes good record | 15 | `sample.json` ends up in DynamoDB with all expected fields. |
| DLQ catches bad record | 20 | Malformed upload is visible in the SQS queue within 60 s. |
| Alarm fires | 15 | `IN_ALARM` state with the right metric dimension. |
| README quality | 15 | All 7 sections present, copy-pasteable, no `TODO`. |
| Idempotency / cleanup | 10 | `sam delete` / `cdk destroy` removes every resource, including the bucket when empty. |

Deductions:

- `-10` per resource that has to be deleted manually in the AWS console.
- `-10` if the alarm watches the wrong metric (e.g., `Invocations` instead of `Errors`).
- `-5` if the DLQ is in a different region from the Lambda.

## Stretch goals (optional, +10 each, capped at +20)

- Add a Lambda **destination** (`on_failure: sqs`) **in addition to** the DLQ and document the difference.
- Add a **DLQ redrive** Lambda that consumes the DLQ, posts to an SNS topic, and re-uploads the record with a `_replay_count` attribute.
- Add a CloudWatch dashboard with three widgets: invocations, errors, DLQ age.
