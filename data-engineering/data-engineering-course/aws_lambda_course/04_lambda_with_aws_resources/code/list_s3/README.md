# list_s3 — Lambda that lists all S3 buckets with creation dates (L15)

> Companion code for L15 — List S3 Bucket with AWS Lambda and Boto3.

## Files

- `list_s3_buckets.py` — the Lambda handler module.
- `test_script.py` — `moto`-based tests.

## IAM permissions required (real AWS)

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowList",
    "Effect": "Allow",
    "Action": ["s3:ListAllMyBuckets", "s3:GetBucketLocation"],
    "Resource": "*"
  }]
}
```

## Run the tests

```bash
cd 04_lambda_with_aws_resources/code/list_s3
pytest test_script.py -v
```

## Try it against real AWS

```bash
export AWS_PROFILE=lambda-dev
export AWS_REGION=us-east-1
python list_s3_buckets.py
# -> {"count": N, "buckets": [{"name": ..., "region": ..., "created_at": ...}, ...]}
```
