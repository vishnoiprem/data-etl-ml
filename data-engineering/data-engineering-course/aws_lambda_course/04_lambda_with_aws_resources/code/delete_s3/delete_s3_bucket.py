"""Lambda handler: delete an S3 bucket (force-emptied first).

Companion to L14.

Required IAM permissions:
    s3:ListBucket
    s3:ListBucketVersions
    s3:DeleteObject
    s3:DeleteObjectVersion
    s3:DeleteBucket
    s3:HeadBucket
"""

import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)


def _force_empty(s3_client, bucket_name: str) -> int:
    """Delete every object and every version from the bucket.

    Returns the number of objects deleted.
    """
    deleted = 0

    # 1. Current (unversioned) objects.
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket_name):
        contents = page.get("Contents", [])
        if not contents:
            continue
        s3_client.delete_objects(
            Bucket=bucket_name,
            Delete={
                "Objects": [{"Key": obj["Key"]} for obj in contents],
                "Quiet": True,
            },
        )
        deleted += len(contents)

    # 2. Versioned objects + delete markers (no-op for unversioned buckets).
    try:
        version_paginator = s3_client.get_paginator("list_object_versions")
        for page in version_paginator.paginate(Bucket=bucket_name):
            objects = page.get("Versions", []) + page.get("DeleteMarkers", [])
            if not objects:
                continue
            s3_client.delete_objects(
                Bucket=bucket_name,
                Delete={
                    "Objects": [
                        {"Key": v["Key"], "VersionId": v["VersionId"]}
                        for v in objects
                    ],
                    "Quiet": True,
                },
            )
            deleted += len(objects)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") != "NoSuchBucket":
            raise

    return deleted


def handler(event, context):
    """Delete an S3 bucket (force-emptied first).

    Event shape:
        {
          "bucket_name": "my-bucket",
          "region": "us-east-1"        # optional
        }

    Returns:
        {"status": "deleted"|"absent", "bucket": str,
         "deleted_objects": int, "region": str}
    """
    LOG.info("received event: %s", json.dumps(event))

    bucket_name = event["bucket_name"]
    region = (
        event.get("region")
        or os.environ.get("AWS_REGION")
        or "us-east-1"
    )

    s3 = boto3.client("s3", region_name=region)

    try:
        s3.head_bucket(Bucket=bucket_name)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in ("404", "NoSuchBucket", "NotFound"):
            LOG.warning("bucket %s does not exist; nothing to do", bucket_name)
            return {
                "status": "absent",
                "bucket": bucket_name,
                "deleted_objects": 0,
                "region": region,
            }
        raise

    deleted = _force_empty(s3, bucket_name)
    s3.delete_bucket(Bucket=bucket_name)
    LOG.info("deleted bucket %s (force-emptied %d objects)", bucket_name, deleted)
    return {
        "status": "deleted",
        "bucket": bucket_name,
        "deleted_objects": deleted,
        "region": region,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    sample_event = {"bucket_name": "demo-bucket-to-delete", "region": "us-east-1"}
    print(handler(sample_event, None))
