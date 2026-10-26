"""Lambda handler: list every S3 bucket in the calling account.

Companion to L15.

Required IAM permissions:
    s3:ListAllMyBuckets
    s3:GetBucketLocation
"""

import json
import logging
import os
from datetime import timezone

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)


def _creation_date_iso(bucket: dict) -> str:
    """Return the bucket's CreationDate as an ISO-8601 string.

    Handles both real boto3 (datetime) and moto (ISO string).
    """
    dt = bucket.get("CreationDate")
    if dt is None:
        return ""
    if hasattr(dt, "isoformat"):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    return str(dt)


def _resolve_region(s3_client, bucket_name: str) -> str:
    """Resolve the bucket's region via get_bucket_location.

    us-east-1 returns an empty LocationConstraint -> we coerce to "us-east-1".
    """
    try:
        loc = s3_client.get_bucket_location(Bucket=bucket_name).get("LocationConstraint")
    except ClientError as exc:
        LOG.warning("get_bucket_location(%s) failed: %s", bucket_name, exc)
        return "unknown"
    return loc or "us-east-1"


def handler(event, context):
    """List every S3 bucket in the calling account.

    Event shape (optional):
        {} — no required keys.

    Returns:
        {"count": int, "buckets": [{"name", "region", "created_at"}]}
    """
    LOG.info("received event: %s", json.dumps(event or {}))

    region = None
    if isinstance(event, dict):
        region = event.get("region")
    region = region or os.environ.get("AWS_REGION") or "us-east-1"

    s3 = boto3.client("s3", region_name=region)

    paginator = s3.get_paginator("list_buckets")
    rows = []
    for page in paginator.paginate():
        for b in page.get("Buckets", []):
            name = b["Name"]
            rows.append({
                "name": name,
                "region": _resolve_region(s3, name),
                "created_at": _creation_date_iso(b),
            })

    LOG.info("found %d buckets", len(rows))
    return {"count": len(rows), "buckets": rows}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    print(handler({}, None))
