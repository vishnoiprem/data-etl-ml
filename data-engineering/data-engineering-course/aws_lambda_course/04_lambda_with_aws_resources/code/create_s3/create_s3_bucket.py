"""Lambda handler: create an S3 bucket (region-aware).

Companion to L13.

Required IAM permissions:
    s3:CreateBucket
    s3:HeadBucket
"""

import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)


def handler(event, context):
    """Create an S3 bucket.

    Event shape:
        {
          "bucket_name": "my-bucket",
          "region": "us-east-1"        # optional, defaults to AWS_REGION env
        }

    Returns:
        {"status": "created"|"exists", "bucket": str, "region": str}
    """
    LOG.info("received event: %s", json.dumps(event))

    bucket_name = event["bucket_name"]
    region = (
        event.get("region")
        or os.environ.get("AWS_REGION")
        or "us-east-1"
    )

    s3 = boto3.client("s3", region_name=region)

    # Idempotency: check for the bucket first. head_bucket is the
    # cheapest "does-it-exist" call and works across accounts.
    try:
        s3.head_bucket(Bucket=bucket_name)
        LOG.warning("bucket %s already exists", bucket_name)
        return {"status": "exists", "bucket": bucket_name, "region": region}
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code not in ("404", "NoSuchBucket", "NotFound"):
            raise

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
            # Race: someone else created it between our head_bucket and
            # our create_bucket. Treat as success.
            LOG.warning("bucket %s already exists", bucket_name)
            return {"status": "exists", "bucket": bucket_name, "region": region}
        raise

    LOG.info("created bucket %s in %s", bucket_name, region)
    return {"status": "created", "bucket": bucket_name, "region": region}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    sample_event = {
        "bucket_name": f"lambda-create-demo-{os.getpid()}",
        "region": "us-east-1",
    }
    print(handler(sample_event, None))
