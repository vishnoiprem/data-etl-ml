# delete_s3 — Lambda that force-empties and deletes an S3 bucket (L14)

> Companion code for L14 — Delete S3 Bucket with AWS Lambda and Boto3.

## Files

- `delete_s3_bucket.py` — the Lambda handler module.
- `test_script.py` — `moto`-based tests.

## IAM permissions required (real AWS)

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowDeleteBucket",
    "Effect": "Allow",
    "Action": [
      "s3:ListBucket",
      "s3:ListBucketVersions",
      "s3:DeleteObject",
      "s3:DeleteObjectVersion",
      "s3:DeleteBucket",
      "s3:HeadBucket"
    ],
    "Resource": [
      "arn:aws:s3:::<your-bucket>",
      "arn:aws:s3:::<your-bucket>/*"
    ]
  }]
}
```

## Run the tests

```bash
cd 04_lambda_with_aws_resources/code/delete_s3
pytest test_script.py -v
```

## Try it against real AWS

```bash
export AWS_PROFILE=lambda-dev
export AWS_REGION=us-east-1
# Pre-create a bucket + add an object so we can test force-empty.
aws s3 mb s3://my-demo-bucket-to-delete
echo "hello" > /tmp/hello.txt
aws s3 cp /tmp/hello.txt s3://my-demo-bucket-to-delete/hello.txt
python delete_s3_bucket.py
aws s3 ls | grep my-demo-bucket-to-delete || echo "bucket is gone"
```
