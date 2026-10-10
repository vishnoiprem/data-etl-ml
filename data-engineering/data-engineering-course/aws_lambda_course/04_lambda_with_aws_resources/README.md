# Section 4 — AWS Lambda with S3, EC2, DynamoDB (L11–L18, 76 min)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

Section 4 is the first **hands-on coding** section of the course. Sections
2 and 3 gave you the Lambda mental model and a Python refresher. This
section takes that foundation and points it at real AWS services: S3,
EC2, DynamoDB. Every lecture ships with a runnable Python module under
`code/` and a `moto`-based test that runs locally with no AWS account.

## What you build

| # | Working artifact | L-IDs |
|---|---|---|
| 1 | Lambda that creates an S3 bucket (region-aware) | L13 |
| 2 | Lambda that force-empties and deletes an S3 bucket | L14 |
| 3 | Lambda that lists all S3 buckets with creation dates | L15 |
| 4 | Lambda that creates / starts / stops an EC2 instance | L16 |
| 5 | EventBridge schedule that runs the start/stop Lambda on a cron | L17 |
| 6 | Lambda that creates a DynamoDB table and puts items | L18 |

By the end of L18 you will have written **6 production-shaped Lambda
handlers** plus the IAM and EventBridge plumbing that makes the EC2
automation work. L12 is the *theory* lecture that ties them together
(Boto3 client vs resource, the handler contract, sessions, regions).

## Lecture map

| L# | Title | Min | File |
|---|---|---|---|
| L11 | Section Overview | 1:18 | `lecture_scripts/L11_section_overview.md` |
| L12 | AWS Lambda Basics — Boto3, Client and Resource, Lambda function handler | 9:06 | `lecture_scripts/L12_boto3_handler.md` |
| L13 | Create S3 Bucket with AWS Lambda and Boto3 | 15:00 | `lecture_scripts/L13_create_s3_bucket.md` |
| L14 | Delete S3 Bucket with AWS Lambda and Boto3 | 6:07 | `lecture_scripts/L14_delete_s3_bucket.md` |
| L15 | List S3 Bucket with AWS Lambda and Boto3 | 8:39 | `lecture_scripts/L15_list_s3_buckets.md` |
| L16 | AWS Lambda with EC2 (Create EC2, Start EC2 and Stop EC2) | 12:59 | `lecture_scripts/L16_lambda_with_ec2.md` |
| L17 | AWS Lambda Automation Use Case — EC2, Lambda and EventBridge | 12:29 | `lecture_scripts/L17_lambda_eventbridge_ec2.md` |
| L18 | AWS Lambda with DynamoDB (Create Table and Put Items) | 10:52 | `lecture_scripts/L18_lambda_with_dynamodb.md` |

## Code layout

```
04_lambda_with_aws_resources/code/
├── create_s3/                ← L13  — create_s3_bucket.py + tests
├── delete_s3/                ← L14  — delete_s3_bucket.py + tests
├── list_s3/                  ← L15  — list_s3_buckets.py + tests
├── ec2_lifecycle/            ← L16  — start_stop_ec2.py + tests
├── ec2_eventbridge/          ← L17  — eventbridge_scheduled_start_stop.py + tests
└── dynamodb_create/          ← L18  — create_table_put_items.py + tests
```

Each subdirectory is a self-contained module: a `script.py` that
exports a Lambda-style `handler(event, context)`, a `test_script.py`
that uses `moto` to run the handler against an in-memory AWS API, and
a `README.md` with the run-it-locally steps.

## Conventions used in every script

- `boto3.client(...)` with `region_name=os.environ.get('AWS_REGION', 'us-east-1')`.
- `logging` (not `print`) so the output lands cleanly in CloudWatch.
- `handler(event, context)` is the Lambda entry point. The
  `if __name__ == "__main__":` block calls it with a fake event so you
  can `python script.py` from the terminal.
- The IAM permissions the Lambda needs are listed in the lecture file
  *and* in the module docstring. The tests mock the AWS API, so no IAM
  role is required to run `pytest`.

## Running the tests

```bash
cd aws_lambda_course
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # moto[dynamodb,s3,ec2,lambda,events] is included
pytest 04_lambda_with_aws_resources/code -q
```

All 12+ tests should pass in well under a minute. If you have AWS
credentials configured, `moto` still works — it transparently shadows
the real API.

## Where this section leads

Section 5 (L19–L22) goes back to Lambda theory: invocation model,
limits, timeout. Section 6 (L23–L24) takes the S3 + DynamoDB
primitives from L13–L18 and wires them into a real
**S3 → Lambda → DynamoDB** banking pipeline. The handlers you write
in L13–L15 and L18 are the building blocks.
