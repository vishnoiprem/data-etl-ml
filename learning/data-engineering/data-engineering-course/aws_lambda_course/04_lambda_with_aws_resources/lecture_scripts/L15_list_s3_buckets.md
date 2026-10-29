---
l_id: L15
title: List S3 Bucket with AWS Lambda and Boto3
duration_min: 8.39
prereqs: [L13, L14]
---

# L15 — List S3 Buckets with AWS Lambda and Boto3

> **Author:** Prem Vishnoi &lt;prem.vishnoi.example.com&gt;
> **Section:** 4 — AWS Lambda with S3, EC2, DynamoDB
> **Duration target:** 8:39

## Prereqs

- L13 / L14 — you should be comfortable with `boto3.client("s3", ...)`
  and the canonical Lambda template.

## Key terms

- **`list_buckets`** — the single API call that returns *all*
  buckets in the calling AWS account. Includes owner, region hint,
  and creation date.
- **Bucket creation date** — returned as a `datetime` object by boto3
  (in real AWS) or as an ISO-8601 string (in `moto`). We normalize
  both to ISO-8601.
- **Pagination** — `list_buckets` is paginated, but accounts rarely
  exceed one page. Still, we use the paginator to be safe.

## Lecture

> "This is the shortest of the three S3 lectures because
> `list_buckets` is a single API call. The handler is 15 lines. The
> interesting part is the post-processing: we want the bucket name,
> the region, *and* the creation date. The first comes from the
> `list_buckets` response; the second requires a `get_bucket_location`
> call per bucket; the third comes from `list_buckets` directly."

### The handler

```python
import json
import logging
import os
from datetime import timezone

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)


def _creation_date_iso(bucket: dict) -> str:
    """Return the bucket's CreationDate as an ISO-8601 string."""
    dt = bucket.get("CreationDate")
    if dt is None:
        return ""
    # `moto` returns ISO-8601 strings; real boto3 returns datetime.
    if hasattr(dt, "isoformat"):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    return str(dt)


def handler(event, context):
    """List every S3 bucket in the calling account.

    Expected event (optional):
        {} — no required keys.

    Returns:
        {"count": N, "buckets": [{"name", "region", "created_at"}]}
    """
    LOG.info("received event: %s", json.dumps(event or {}))

    region = event.get("region") if isinstance(event, dict) else None
    region = region or os.environ.get("AWS_REGION", "us-east-1")

    s3 = boto3.client("s3", region_name=region)

    paginator = s3.get_paginator("list_buckets")
    rows = []
    for page in paginator.paginate():
        for b in page.get("Buckets", []):
            name = b["Name"]
            created_at = _creation_date_iso(b)
            try:
                bucket_region = s3.get_bucket_location(Bucket=name)
            except ClientError as exc:
                LOG.warning("get_bucket_location(%s) failed: %s", name, exc)
                bucket_region = "unknown"
            rows.append({
                "name": name,
                "region": bucket_region or "us-east-1",
                "created_at": created_at,
            })

    LOG.info("found %d buckets", len(rows))
    return {"count": len(rows), "buckets": rows}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(handler({}, None))
```

### Walkthrough

1. **No required keys.** `list_buckets` doesn't take any parameters,
   so the event is optional. We accept `{}` to keep the test
   signature uniform with L13/L14.

2. **Pagination.** Almost every account has fewer than 1000 buckets,
   so one page is enough. We use the paginator anyway because it
   future-proofs the handler.

3. **`get_bucket_location`.** The `list_buckets` response *does not*
   include the bucket's region. To find it, you call
   `get_bucket_location(Bucket=name)`. For `us-east-1` it returns an
   empty `LocationConstraint`; we coerce that to `"us-east-1"`. The
   default boto3 `s3.us-east-1` *endpoint* always works for the
   `get_bucket_location` call — the request doesn't actually go to
   the bucket's region, it goes to the *control plane*, which is
   global.

4. **`_creation_date_iso`.** Two quirks here. First, `moto` returns
   `CreationDate` as an ISO-8601 string; real boto3 returns a
   `datetime` object. We handle both. Second, naive datetimes in
   Python are a constant foot-gun; we tag the result as UTC before
   formatting.

5. **Error handling.** If `get_bucket_location` fails for one bucket,
   we log a warning and continue with `"unknown"`. We do *not* abort
   the whole listing — one bad bucket should not poison the result.

### IAM permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowList",
      "Effect": "Allow",
      "Action": ["s3:ListAllMyBuckets", "s3:GetBucketLocation"],
      "Resource": "*"
    }
  ]
}
```

`s3:ListAllMyBuckets` is the IAM action that maps to `list_buckets`.
Note that it is **account-wide** (`Resource: "*"`) — there is no
way to scope it to a single bucket because the call itself is
account-wide.

### What the response looks like

```json
{
  "count": 3,
  "buckets": [
    {
      "name": "lambda-create-demo-prem-2026",
      "region": "us-east-1",
      "created_at": "2026-10-04T12:31:08+00:00"
    },
    {
      "name": "glue-course-target",
      "region": "eu-west-1",
      "created_at": "2026-09-18T09:02:44+00:00"
    },
    {
      "name": "bedrock-manufacturing-logs",
      "region": "us-east-1",
      "created_at": "2026-08-22T17:45:11+00:00"
    }
  ]
}
```

This is exactly the kind of thing you'd feed into a CloudWatch
dashboard or a Slack notification.

## Hands-on

```bash
cd 04_lambda_with_aws_resources/code/list_s3
pytest test_script.py -v
```

You should see at least 2 tests:
- `test_handler_lists_no_buckets` — empty account
- `test_handler_lists_multiple_buckets` — bucket created via L13's
  handler + a couple more fixtures, with creation dates asserted

## Quiz prep

- `list_buckets` does *not* return the bucket's region. You must
  call `get_bucket_location` per bucket.
- `get_bucket_location` returns an empty `LocationConstraint` for
  buckets in `us-east-1`.
- The IAM action that maps to `list_buckets` is `s3:ListAllMyBuckets`.
- The `CreationDate` field is a `datetime` in real boto3 and a
  string in `moto`. Handle both.

## Further reading

- AWS docs: [ListBuckets API](https://docs.aws.amazon.com/AmazonS3/latest/API/API_ListBuckets.html)
- AWS docs: [GetBucketLocation API](https://docs.aws.amazon.com/AmazonS3/latest/API/API_GetBucketLocation.html)
- `code/list_s3/README.md`
- `code/list_s3/list_s3_buckets.py` — the full module