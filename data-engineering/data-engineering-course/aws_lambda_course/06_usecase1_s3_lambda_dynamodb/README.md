# Section 6 — Enterprise Use Case 1: S3, AWS Lambda, DynamoDB

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 06
> **Lectures:** L23–L24
> **Total runtime:** 20 min (11:24 + 8:27)

This section is the first of three end-to-end **enterprise use cases** in the
course. We build a small but realistic data pipeline inspired by a banking /
retail scenario: a partner sends a regular batch of transactions as a JSON
file; the file lands in an S3 bucket; S3 fires an event notification; a Lambda
function reads the JSON, validates each record, and writes the rows into a
DynamoDB table.

The use case is intentionally simple in scope but production-shaped in
discipline. We will touch on every concept you need to repeat the pattern in
your own org:

- a clean **event-driven architecture** (no polling, no EC2)
- a **least-privilege IAM execution role** for Lambda
- an **S3 event notification** wired to a Lambda destination
- a **DynamoDB** write with an `attribute_not_exists` condition to make the
  pipeline idempotent
- **structured CloudWatch logs** so you can grep, filter and alarm on
  what the function actually did
- a `pytest` test suite using `moto.mock_aws` so the same code runs locally
  without touching AWS

By the end of these two lectures you will have a working pipeline you can
deploy from the console or with `boto3` in roughly ten minutes.

## Lecture map

| L# | Title | Min | File |
|---|---|---|---|
| L23 | Enterprise Use Case using S3, AWS Lambda and DynamoDB — Part 1 | 11:24 | `lecture_scripts/L23_usecase1_pt1.md` |
| L24 | Enterprise Use Case using S3, AWS Lambda and DynamoDB — Part 2 | 8:27 | `lecture_scripts/L24_usecase1_pt2.md` |

## Code layout

```
06_usecase1_s3_lambda_dynamodb/
├── README.md                           ← this file
├── lecture_scripts/
│   ├── L23_usecase1_pt1.md
│   └── L24_usecase1_pt2.md
├── code/
│   ├── lambda_function/
│   │   ├── s3_to_dynamodb_lambda.py     ← the handler (deploy this)
│   │   └── test_s3_to_dynamodb_lambda.py
│   ├── sample_data/
│   │   └── sample_transactions.json
│   ├── iam_policy.json                 ← the IAM policy for the execution role
│   └── deploy_notes.md                 ← console + boto3 deploy steps
└── assignments/                        ← (none for L23–L24)
```

## Running the lab locally

```bash
cd 06_usecase1_s3_lambda_dynamodb/code
python -m venv .venv && source .venv/bin/activate
pip install -r ../../requirements.txt

# Run the unit tests against moto (no AWS account required)
pytest lambda_function/test_s3_to_dynamodb_lambda.py -v
```

## What you build

A Lambda function `s3_to_dynamodb_lambda` that:

1. is triggered by S3 `ObjectCreated:Put` events on a specific prefix;
2. downloads the JSON file from S3;
3. parses an array of transaction objects;
5. validates each record (skips rows missing `transaction_id`);
6. calls DynamoDB `PutItem` against a table `transactions` with partition key
   `transaction_id` and `ConditionExpression="attribute_not_exists(transaction_id)"`
   so re-deliveries cannot create duplicates;
7. emits one structured JSON log line per record plus a summary line; and
8. returns `{processed, skipped, errors}` to the caller.

## Matching quiz

`quizzes/section_6.md` — 10 questions on S3 event notifications, Lambda IAM,
DynamoDB write semantics and idempotency.