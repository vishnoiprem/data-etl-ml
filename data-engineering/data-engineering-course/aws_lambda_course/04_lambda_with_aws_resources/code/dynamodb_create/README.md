# dynamodb_create — Lambda that creates a DynamoDB table and puts items (L18)

> Companion code for L18 — AWS Lambda with DynamoDB (Create Table and Put Items).

## Files

- `create_table_put_items.py` — the Lambda handler module.
- `test_script.py` — `moto`-based tests.

## IAM permissions required (real AWS)

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowDDB",
    "Effect": "Allow",
    "Action": [
      "dynamodb:CreateTable",
      "dynamodb:DescribeTable",
      "dynamodb:PutItem",
      "dynamodb:ListTables"
    ],
    "Resource": "arn:aws:dynamodb:*:*:table/<your-table-name>"
  }]
}
```

## Run the tests

```bash
cd 04_lambda_with_aws_resources/code/dynamodb_create
pytest test_script.py -v
```

## Try it against real AWS

```bash
export AWS_PROFILE=lambda-dev
export AWS_REGION=us-east-1
python create_table_put_items.py
aws dynamodb list-tables
```