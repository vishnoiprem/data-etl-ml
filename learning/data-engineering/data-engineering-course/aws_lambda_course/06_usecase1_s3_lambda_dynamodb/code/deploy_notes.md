# Deploy Notes — S3 -> Lambda -> DynamoDB Pipeline

This file walks through the manual deploy of the `s3_to_dynamodb_lambda`
function. We cover two paths: the **console** (good for first-time setup)
and a **`boto3` script** (good for repeatable CI/CD).

The full IaC version of this stack — CloudFormation and CDK — is covered in
sections 12 and 13 of the course. For this section we keep the deploy
explicit so you can see every moving part.

## Prerequisites

- AWS account with permission to create S3 buckets, IAM roles, Lambda
  functions, and DynamoDB tables
- AWS CLI v2 configured with a profile (`aws configure sso` or
  `aws configure`)
- Python 3.11+ with `boto3` installed
- A region; this doc uses `us-east-1`

## Resources we will create

| Resource | Name | Purpose |
|---|---|---|
| S3 bucket | `banking-transactions-ingest` | Landing zone for the JSON feed |
| DynamoDB table | `transactions` | Stores the parsed rows |
| IAM role | `s3_to_dynamodb_lambda_role` | Lambda execution role |
| IAM policy | inline (see `iam_policy.json`) | Least-privilege permissions for the role |
| Lambda function | `s3_to_dynamodb_lambda` | The handler from `s3_to_dynamodb_lambda.py` |
| S3 event notification | `ObjectCreated:Put` on `raw/` prefix | Wires the bucket to the function |

---

## Path A — Console (10 min)

### 1. Create the DynamoDB table

DynamoDB → Tables → **Create table**.

- Table name: `transactions`
- Partition key: `transaction_id` (String)
- Billing mode: On-demand (we have a tiny feed, no need to size capacity)
- Create.

### 2. Create the S3 bucket

S3 → **Create bucket**.

- Name: `banking-transactions-ingest` (must be globally unique; you may
  have to append a suffix like `-use1-2026`).
- Region: `us-east-1`.
- Block all public access: on.
- Create.

### 3. Create the Lambda execution role

IAM → Roles → **Create role**.

- Trusted entity: AWS service → Lambda.
- Permissions: do not attach anything yet.
- Name: `s3_to_dynamodb_lambda_role`.

Now attach the inline policy. Open the role → **Add permissions** → **Create
inline policy** → JSON. Paste the contents of `iam_policy.json` and replace
the `123456789012` account id with your own. Review the ARNs and create.

### 4. Create the Lambda function

Lambda → **Create function**.

- Author from scratch.
- Name: `s3_to_dynamodb_lambda`.
- Runtime: Python 3.11.
- Execution role: use existing → `s3_to_dynamodb_lambda_role`.
- Create.

In the function view → **Upload from** → `.zip` or **Code** tab → **Upload
from** → `.zip` file. Zip the contents of `code/lambda_function/`:

```bash
cd code/lambda_function
zip -j s3_to_dynamodb_lambda.zip s3_to_dynamodb_lambda.py
```

Then upload the zip and set the handler to `s3_to_dynamodb_lambda.handler`.

### 5. Configure environment variables

Configuration → Environment variables:

- `TABLE_NAME` = `transactions`
- `LOG_LEVEL` = `INFO`

### 6. Wire S3 to the function

Open the `banking-transactions-ingest` bucket → **Properties** → **Event
notifications** → **Create event notification**.

- Name: `ingest-to-dynamodb`
- Prefix: `raw/`
- Event types: `s3:ObjectCreated:Put`
- Destination: Lambda function → `s3_to_dynamodb_lambda`
- Save.

### 7. Test the pipeline

Upload the sample file:

```bash
aws s3 cp code/sample_data/sample_transactions.json \
    s3://banking-transactions-ingest/raw/2026-10-10/sample_transactions.json
```

Within a few seconds the function fires. Open CloudWatch → Log groups →
`/aws/lambda/s3_to_dynamodb_lambda` and you should see the structured
`invoke.start`, five `record.persisted` lines, and an `invoke.done` summary.

Verify in DynamoDB:

```bash
aws dynamodb scan --table-name transactions --max-items 10
```

You should see the five `TXN-1001`…`TXN-1005` rows.

---

## Path B — boto3 (CI-friendly)

The snippet below is the same deploy, scripted. It assumes an AWS CLI
profile is configured.

```python
# scripts/deploy_usecase1.py
import json
from pathlib import Path

import boto3

REGION = "us-east-1"
BUCKET = "banking-transactions-ingest"
TABLE = "transactions"
ROLE_NAME = "s3_to_dynamodb_lambda_role"
FUNCTION_NAME = "s3_to_dynamodb_lambda"
ACCOUNT_ID = boto3.client("sts").get_caller_identity()["Account"]

iam = boto3.client("iam")
s3 = boto3.client("s3")
ddb = boto3.client("dynamodb")
lam = boto3.client("lambda")

# 1. S3 bucket
try:
    s3.create_bucket(Bucket=BUCKET)
except s3.exceptions.BucketAlreadyOwnedByYou:
    pass

# 2. DynamoDB table
try:
    ddb.create_table(
        TableName=TABLE,
        AttributeDefinitions=[{"AttributeName": "transaction_id", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "transaction_id", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
    )
    ddb.get_waiter("table_exists").wait(TableName=TABLE)
except ddb.exceptions.ResourceInUseException:
    pass

# 3. IAM role + inline policy
assume_role_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }
    ],
}
try:
    iam.create_role(
        RoleName=ROLE_NAME,
        AssumeRolePolicyDocument=json.dumps(assume_role_policy),
    )
except iam.exceptions.EntityAlreadyExistsException:
    pass

policy = json.loads(Path("code/iam_policy.json").read_text())
policy["Statement"][1]["Resource"] = [
    f"arn:aws:dynamodb:{REGION}:{ACCOUNT_ID}:table/{TABLE}"
]
iam.put_role_policy(
    RoleName=ROLE_NAME,
    PolicyName="s3-to-dynamodb-inline",
    PolicyDocument=json.dumps(policy),
)

# 4. Lambda function
role_arn = iam.get_role(RoleName=ROLE_NAME)["Role"]["Arn"]
with open("code/lambda_function/s3_to_dynamodb_lambda.zip", "rb") as fh:
    zipped = fh.read()

try:
    lam.create_function(
        FunctionName=FUNCTION_NAME,
        Runtime="python3.11",
        Role=role_arn,
        Handler="s3_to_dynamodb_lambda.handler",
        Code={"ZipFile": zipped},
        Environment={"Variables": {"TABLE_NAME": TABLE, "LOG_LEVEL": "INFO"}},
        Timeout=60,
        MemorySize=256,
    )
except lam.exceptions.ResourceConflictException:
    lam.update_function_code(FunctionName=FUNCTION_NAME, ZipFile=zipped)

# 5. S3 -> Lambda notification
lam.add_permission(
    FunctionName=FUNCTION_NAME,
    StatementId="s3-invoke",
    Principal="s3.amazonaws.com",
    Action="lambda:InvokeFunction",
    SourceArn=f"arn:aws:s3:::{BUCKET}",
)
s3.put_bucket_notification_configuration(
    Bucket=BUCKET,
    NotificationConfiguration={
        "LambdaFunctionConfigurations": [
            {
                "LambdaFunctionArn": lam.get_function(FunctionName=FUNCTION_NAME)["Configuration"]["FunctionArn"],
                "Events": ["s3:ObjectCreated:Put"],
                "Filter": {"Key": {"FilterRules": [{"Name": "prefix", "Value": "raw/"}]}},
            }
        ]
    },
)
print("Deploy complete")
```

Run with:

```bash
python scripts/deploy_usecase1.py
```

---

## Verifying idempotency in production

S3 will retry event notifications if Lambda returns an error. To make sure
duplicates do not double-charge a customer, the handler uses
`ConditionExpression="attribute_not_exists(transaction_id)"`. You can prove
this by:

1. Re-uploading the same JSON file to the `raw/` prefix.
2. Watching the CloudWatch logs — you should see `record.duplicate` for
   every row, no `record.persisted`.
3. Running `aws dynamodb scan --table-name transactions --select COUNT` —
   the row count is unchanged.

## Cleaning up

To avoid charges while you experiment:

```bash
aws s3 rm s3://banking-transactions-ingest --recursive
aws s3api delete-bucket --bucket banking-transactions-ingest
aws dynamodb delete-table --table-name transactions
aws lambda delete-function --function-name s3_to_dynamodb_lambda
aws iam delete-role-policy --role-name s3_to_dynamodb_lambda_role \
    --policy-name s3-to-dynamodb-inline
aws iam delete-role --role-name s3_to_dynamodb_lambda_role
```

## Further reading

- AWS docs: [Using AWS Lambda with Amazon S3](https://docs.aws.amazon.com/lambda/latest/dg/with-s3.html)
- AWS docs: [Condition expressions in DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html)
- Section 12 of this course: deploying the same stack with AWS CDK
- Section 13 of this course: deploying the same stack with CloudFormation
