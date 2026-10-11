# create_s3 — Lambda that creates an S3 bucket (L13)

> Companion code for L13 — Create S3 Bucket with AWS Lambda and Boto3.

## Files

- `create_s3_bucket.py` — the Lambda handler module.
- `test_script.py` — `moto`-based tests.

## IAM permissions required (real AWS)

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowCreateBucket",
    "Effect": "Allow",
    "Action": ["s3:CreateBucket", "s3:HeadBucket"],
    "Resource": "*"
  }]
}
```

## Run it locally (no AWS)

```bash
cd 04_lambda_with_aws_resources/code/create_s3
python create_s3_bucket.py
# -> {"status": "created", "bucket": "my-demo-bucket-<pid>", "region": "us-east-1"}
```

The handler talks to the AWS API. Without `moto` it will try to
reach real AWS — set `AWS_ACCESS_KEY_ID=testing` etc. if you want
it to fail predictably rather than hanging.

## Run the tests

```bash
pytest test_script.py -v
```

3 tests, ~1 second. They use the `@mock_aws` decorator from `moto`
so no real AWS credentials are needed.

## Try it against real AWS

```bash
export AWS_PROFILE=lambda-dev
export AWS_REGION=us-east-1
python create_s3_bucket.py
aws s3 ls
```

You should see the bucket from the `__main__` block in the S3
console / `aws s3 ls` output.
