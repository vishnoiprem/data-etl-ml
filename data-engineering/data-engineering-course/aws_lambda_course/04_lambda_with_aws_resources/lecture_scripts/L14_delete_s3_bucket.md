---
l_id: L14
title: Delete S3 Bucket with AWS Lambda and Boto3
duration_min: 6.07
prereqs: [L13]
---

# L14 — Delete S3 Bucket with AWS Lambda and Boto3

> **Author:** Prem Vishnoi &lt;prem.vishnoi.example.com&gt;
> **Section:** 4 — AWS Lambda with S3, EC2, DynamoDB
> **Duration target:** 6:07

## Prereqs

- L13 — you should have a working `create_bucket` handler. Delete is
  its symmetric counterpart.

## Key terms

- **Force-empty** — recursively delete every object and every object
  version in a bucket before deleting the bucket itself. Required
  because S3 will not delete a non-empty bucket.
- **Object versions** — if versioning is enabled, every `put_object`
  creates a new version. To fully empty a versioned bucket you must
  delete *all* versions *and* all delete markers.
- **`NoSuchBucket`** — the `ClientError` code for "bucket does not
  exist". Treat as success for idempotency.

## Lecture

> "Last lecture we created a bucket. This lecture we delete it. The
> trap is that AWS won't delete a bucket that has objects in it. So
> our handler has two steps: first, force-empty the bucket by listing
> and deleting every object; second, delete the bucket itself. For a
> versioned bucket we also have to delete the object versions and the
> delete markers. That makes the body 25 lines instead of 3. But the
> shape is identical to the create handler from L13."

### The handler

```python
import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)


def _force_empty(s3_client, bucket_name: str) -> int:
    """Delete every object (and every version) from the bucket.

    Returns the number of objects deleted.
    """
    deleted = 0

    # 1. Current (unversioned) objects
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

    # 2. Versioned objects + delete markers (no-op for unversioned buckets)
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

    Expected event:
        {"bucket_name": "my-bucket", "region": "us-east-1" (optional)}
    """
    LOG.info("received event: %s", json.dumps(event))

    bucket_name = event["bucket_name"]
    region = event.get("region") or os.environ.get("AWS_REGION", "us-east-1")

    s3 = boto3.client("s3", region_name=region)

    try:
        s3.head_bucket(Bucket=bucket_name)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in ("404", "NoSuchBucket", "NotFound"):
            LOG.warning("bucket %s does not exist; nothing to do", bucket_name)
            return {"status": "absent", "bucket": bucket_name, "deleted_objects": 0}
        raise

    deleted = _force_empty(s3, bucket_name)
    s3.delete_bucket(Bucket=bucket_name)
    LOG.info("deleted bucket %s (force-emptied %d objects)", bucket_name, deleted)
    return {"status": "deleted", "bucket": bucket_name, "deleted_objects": deleted}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(handler({"bucket_name": "demo-bucket", "region": "us-east-1"}, None))
```

### Walkthrough

1. **Idempotency.** The first thing we do is `head_bucket`. If the
   bucket does not exist, we return a structured `absent` response
   instead of raising. Same pattern as L13: idempotency-friendly
   handlers are easier to wire up to EventBridge schedules (L17).

2. **`_force_empty`.** This is the new code compared to L13. We use
   the `list_objects_v2` paginator because S3 returns at most 1000
   objects per page. For each non-empty page we issue a single
   `delete_objects` call with up to 1000 keys. That is a *batch*
   delete; it is dramatically faster than one `delete_object` per
   key.

3. **Versioned buckets.** If the bucket has versioning enabled, the
   *current* object list does not show old versions. We call
   `list_object_versions` and delete every `Version` and every
   `DeleteMarker`. For an unversioned bucket this returns no pages
   and the loop is a no-op.

4. **Final `delete_bucket`.** After the bucket is empty, the delete
   call is a one-liner. AWS returns 204 No Content on success.

5. **Return value.** `status` is one of `deleted` or `absent`.
   `deleted_objects` is the count — useful for logging and for
   alarms.

### IAM permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
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
    }
  ]
}
```

The `Resource` is the bucket *and* `bucket/*` because list/delete
operations act on the objects (which are sub-resources), not the
bucket itself.

## Hands-on

```bash
cd 04_lambda_with_aws_resources/code/delete_s3
pytest test_script.py -v
```

You should see at least 2 tests pass:
- `test_handler_deletes_empty_bucket` — happy path
- `test_handler_force_empties_then_deletes_bucket` — bucket with
  objects inside

## Quiz prep

- A non-empty bucket cannot be deleted until it is empty.
- Versioned buckets require deleting every version and every delete
  marker before the bucket itself can be deleted.
- The idempotent error code for "bucket does not exist" is
  `NoSuchBucket` (or `404` / `NotFound`).
- `delete_objects` accepts up to 1000 keys per call.

## Further reading

- AWS docs: [DeleteBucket API](https://docs.aws.amazon.com/AmazonS3/latest/API/API_DeleteBucket.html)
- AWS docs: [DeleteObjects API](https://docs.aws.amazon.com/AmazonS3/latest/API/API_DeleteObjects.html)
- `code/delete_s3/README.md`
- `code/delete_s3/delete_s3_bucket.py` — the full module
