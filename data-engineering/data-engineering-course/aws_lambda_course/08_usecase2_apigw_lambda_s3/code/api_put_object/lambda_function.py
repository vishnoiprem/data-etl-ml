"""api_put_object — write the request body to S3 at a key derived from
the URL path.

API Gateway proxy event shape (relevant keys):
    {
      "pathParameters": {"proxy": "orders/123"},
      "body": "<raw body, may be base64 if isBase64Encoded=true>",
      "isBase64Encoded": false,
      "headers": {"Content-Type": "application/json", ...},
      ...
    }

Environment:
    BUCKET_NAME  — required, name of the S3 bucket to write to.
    CONTENT_TYPE — optional, default "application/octet-stream".

Notes:
    * For binary uploads the client must set isBase64Encoded=true
      (API Gateway does this automatically when the Content-Type is
      not text/* and the body contains non-printable bytes).
    * We copy the user-supplied Content-Type into the S3 object's
      metadata so a later GET can reproduce the original mime type.
"""
from __future__ import annotations

import base64
import json
import logging
import os
from typing import Any

import boto3

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

BUCKET: str = os.environ["BUCKET_NAME"]
CONTENT_TYPE: str = os.environ.get("CONTENT_TYPE", "application/octet-stream")
_s3 = boto3.client("s3")


def _decode_body(event: dict[str, Any]) -> bytes:
    body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        return base64.b64decode(body)
    return body.encode("utf-8")


def _resolve_key(event: dict[str, Any]) -> str:
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
        return _json(400, {"error": "key is required in the URL path"})

    body_bytes = _decode_body(event)
    if not body_bytes:
        return _json(400, {"error": "body is empty"})

    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    user_ct = headers.get("content-type", CONTENT_TYPE)

    _s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=body_bytes,
        ContentType=user_ct,
    )

    LOG.info("wrote s3://%s/%s (%d bytes, ct=%s)", BUCKET, key, len(body_bytes), user_ct)
    return _json(200, {"key": key, "bytes": len(body_bytes), "content_type": user_ct})
