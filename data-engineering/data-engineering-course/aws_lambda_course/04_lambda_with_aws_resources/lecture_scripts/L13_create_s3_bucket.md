---
l_id: L13
title: Create S3 Bucket with AWS Lambda and Boto3
duration_min: 15.00
prereqs: [L12]
---

# L13 — Create S3 Bucket with AWS Lambda and Boto3

> **Author:** Prem Vishnoi &lt;prem.vishnoi.example.com&gt;
> **Section:** 4 — AWS Lambda with S3, EC2, DynamoDB
> **Duration target:** 15:00

## Prereqs

- L12 — handler contract, `boto3.client`, regions, the canonical
  template.

## Key terms

- **S3 bucket** — a flat container of objects. Globally unique in
  *name*; physically stored in a single *region*.
- **LocationConstraint** — the boto3 parameter that sets the bucket's
  region. Not required for `us-east-1`. Required for every other
  region.
- **BucketAlreadyExists** — the `ClientError` code you get when the
  bucket name is taken. Always handle it gracefully.
- **Bucket name rules** — 3–63 chars, lowercase, no underscores,
  start with lowercase letter or number, not an IP address.

## Lecture

> "Our first real Lambda. We're going to write a function that takes
> a bucket name and a region from the event, and creates that bucket
> in S3. The handler is 12 lines of code. The boto3 call is one line.
> The reason this is a 15-minute lecture is the *gotchas* — the
> region quirk for `us-east-1`, the error handling for
> `BucketAlreadyExists`, the IAM permission your Lambda needs, and
> the three ways to test it (real AWS, `moto`, `localstack`)."

### The handler

```python
import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)


def handler(event, context):
    """Create an S3 bucket.

    Expected event:
        {"bucket_name": "my-bucket-<unique-suffix>",
         "region": "us-east-1" (optional; defaults to AWS_REGION)}
    """
    LOG.info("received event: %s", json.dumps(event))

    bucket_name = event["bucket_name"]
    region = event.get("region") or os.environ.get("AWS_REGION", "us-east-1")

    s3 = boto3.client("s3", region_name=region)

    # us-east-1 does not accept a LocationConstraint; every other
    # region does, and you must pass it.
    create_kwargs = {"Bucket": bucket_name}
    if region != "us-east-1":
        create_kwargs["CreateBucketConfiguration"] = {
            "LocationConstraint": region
        }

    try:
        s3.create_bucket(**create_kwargs)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in ("BucketAlreadyExists", "BucketAlreadyOwnedByYou"):
            LOG.warning("bucket %s already exists", bucket_name)
            return {"status": "exists", "bucket": bucket_name, "region": region}
        raise

    LOG.info("created bucket %s in %s", bucket_name, region)
    return {"status": "created", "bucket": bucket_name, "region": region}


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    sample = {
        "bucket_name": f"my-demo-bucket-{os.getpid()}",
        "region": "us-east-1",
    }
    print(handler(sample, None))
    sys.exit(0)
```

### Walkthrough

Line by line:

1. **Imports.** `boto3` for AWS, `ClientError` from `botocore` to
   catch AWS errors. The other modules (`json`, `logging`, `os`) are
   standard library.

2. **Logger.** Set up at module import. Lambda's runtime pre-configures
   the root logger, so `LOG.info` lands in CloudWatch.

3. **Event shape.** We read `bucket_name` from the event. We *also*
   read `region` from the event, but fall back to `AWS_REGION` from
   the env. This makes the same handler usable as a one-off from the
   console (region from env) and as part of a pipeline (region from
   the event).

4. **Client construction.** `boto3.client("s3", region_name=region)`.
   Note: passing `region_name` explicitly is *recommended* even though
   the runtime sets a default. It makes the script portable to local
   testing and to the `moto` mocks.

5. **The us-east-1 quirk.** If you pass `LocationConstraint: us-east-1`
   to `create_bucket`, AWS returns `InvalidLocationConstraint`. The
   rule is: `us-east-1` → no `CreateBucketConfiguration` parameter at
   all. Any other region → must include it. This is a famous
   foot-gun. L13 remembers it for you.

6. **Error handling.** Bucket names are globally unique. We use a
   two-step idempotency check: first `head_bucket` returns 404 if the
   bucket doesn't exist; if it does, we return `"exists"`. Then we
   call `create_bucket`, and if some *other* invoker won the race
   between our `head_bucket` and our `create_bucket`, AWS returns
   `BucketAlreadyExists` / `BucketAlreadyOwnedByYou` — we catch those
   and also return `"exists"`. Every other `ClientError` (permissions,
   throttling, network) is re-raised so Lambda's retry/DLQ logic sees
   it.

7. **Return value.** A small dict with `status`, `bucket`, `region`.
   The handler *must* return something (or `None`); returning a dict
   is the convention because it serializes cleanly.

### IAM permissions the Lambda needs

Attach this policy to the Lambda's execution role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCreateBucket",
      "Effect": "Allow",
      "Action": ["s3:CreateBucket", "s3:HeadBucket"],
      "Resource": "*"
    }
  ]
}
```

`HeadBucket` is included because it's the canonical
"does-this-bucket-exist-anywhere" check and is the cheapest way to
verify the create succeeded.

### Test it locally with `moto`

The companion `test_script.py` uses the `mock_aws` decorator from
`moto` to intercept every boto3 call. Run it with:

```bash
cd 04_lambda_with_aws_resources/code/create_s3
pytest test_script.py -v
```

You should see 3 tests pass:
- `test_handler_creates_bucket_us_east_1` — happy path
- `test_handler_creates_bucket_in_explicit_region` — exercises the
  `LocationConstraint` branch
- `test_handler_returns_exists_when_bucket_already_owned` — exercises
  the idempotency branch

### Test it for real

If you have an AWS account, deploy the script as a Lambda, set the
handler to `create_s3_bucket.handler`, set `AWS_REGION=us-east-1`,
and invoke it with a test event:

```json
{ "bucket_name": "lambda-create-demo-<your-initials>-2026" }
```

Then check the S3 console. The bucket will be there.

## Hands-on

1. Open `code/create_s3/create_s3_bucket.py`. Walk through the code
   with L13's walkthrough.
2. Run `pytest -v` and confirm all 3 tests pass.
3. Edit the test event in the `__main__` block to use a unique
   bucket name and run `python create_s3_bucket.py` against your
   real AWS account (only if you have one configured).

## Quiz prep

- The bucket name `MyBucket` is invalid (uppercase).
- The bucket name `192.168.5.5` is invalid (looks like an IP).
- `us-east-1` is the only region where `CreateBucketConfiguration`
  must be **omitted**; every other region requires it.
- The `ClientError` codes to catch for idempotency are
  `BucketAlreadyExists` and `BucketAlreadyOwnedByYou`.

## Further reading

- AWS docs: [CreateBucket API](https://docs.aws.amazon.com/AmazonS3/latest/API/API_CreateBucket.html)
- AWS docs: [S3 bucket naming rules](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html)
- `code/create_s3/README.md` — run-it-locally steps
- `code/create_s3/create_s3_bucket.py` — the full module
- `code/create_s3/test_script.py` — the `moto`-based tests
