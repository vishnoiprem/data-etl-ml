"""api_get_object — read an S3 object whose key is the URL path or ?key=.

API Gateway proxy event shape (relevant keys):
    {
      "pathParameters": {"proxy": "orders/123"},
      "queryStringParameters": {"key": "orders/123", "version": "v1"},
      "headers": {...},
      ...
    }

Response shape (proxy integration):
    {"statusCode": 200, "headers": {...}, "body": "<json string>"}

Environment:
    BUCKET_NAME  — required, name of the S3 bucket to read from.

Notes:
    * The handler is intentionally tiny so it can be reasoned about
      end-to-end in a single screen.
    * No top-level side effects: the boto3 client is created once at
      module import time, which is the standard pattern in Lambda
      (containers are reused across invocations).
    * All errors are mapped to JSON responses with the appropriate
      statusCode. We re-raise unexpected ClientErrors so API Gateway
      returns a 500 and CloudWatch gets the full traceback.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

BUCKET: str = os.environ["BUCKET_NAME"]
_s3 = boto3.client("s3")


def _resolve_key(event: dict[str, Any]) -> str:
    """Prefer ?key=... over the {proxy+} path. Returns "" if neither."""
    q = event.get("queryStringParameters") or {}
    if q.get("key"):
        return q["key"]
    path = event.get("pathParameters") or {}
    return (path.get("proxy") or "").strip("/")


def _json(status: int, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    key = _resolve_key(event)
    if not key:
        return _json(400, {"error": "key is required (?key=... or /<key>)"})

    q = event.get("queryStringParameters") or {}
    version_id = q.get("version")  # optional S3 VersionId

    kwargs: dict[str, Any] = {"Bucket": BUCKET, "Key": key}
    if version_id:
        kwargs["VersionId"] = version_id

    try:
        resp = _s3.get_object(**kwargs)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        if code in ("NoSuchKey", "404"):
            return _json(404, {"error": "not found", "key": key})
        LOG.exception("S3 GetObject failed for key=%s", key)
        raise

    body = resp["Body"].read().decode("utf-8")
    return _json(
        200,
        {
            "key": key,
            "content": body,
            "last_modified": resp["LastModified"].isoformat(),
            "size": resp.get("ContentLength"),
            "metadata": dict(resp.get("Metadata", {})),
        },
    )
