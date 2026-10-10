"""api_objects — unified GET + DELETE handler for Use Case 2.

This handler unifies the L31 `api_get_object` and L32 query-string
refactor into a single Lambda that also handles `DELETE`, so a single
function can sit behind two methods (GET, DELETE) on the same
`/{proxy+}` resource. POST / PUT are intentionally not handled here;
they remain the responsibility of `api_put_object` from L31.

API Gateway proxy event shape (relevant keys):
    {
      "httpMethod": "GET" | "DELETE" | "OPTIONS" | ...,
      "path": "/objects/orders/123",
      "pathParameters": {"proxy": "objects/orders/123"},
      "queryStringParameters": {"key": "orders/123", ...},
      "headers": {...},
      "requestContext": {...},
      ...
    }

Response shape (proxy integration):
    {"statusCode": int, "headers": {...}, "body": "<json string>"}

Environment:
    BUCKET_NAME — required, name of the S3 bucket.

Notes:
    * NoSuchKey from S3 becomes 404. Any other ClientError is
      re-raised so API Gateway returns 5xx (the *server's* fault,
      not the client's).
    * CORS headers are baked into the response so the browser can
      read the body even though the *preflight* is served by API
      Gateway itself (mock OPTIONS integration).
    * No top-level side effects: the boto3 client is created once at
      module import time, which is the standard pattern in Lambda
      (containers are reused across invocations).
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

CORS_HEADERS: dict[str, str] = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
}


# ── helpers ──────────────────────────────────────────────────────────
def _resolve_key(event: dict[str, Any]) -> str:
    """Prefer ?key=... over the {proxy+} path. Returns "" if neither."""
    q = event.get("queryStringParameters") or {}
    if q.get("key"):
        return q["key"]
    path = event.get("pathParameters") or {}
    return (path.get("proxy") or "").strip("/")


def _resp(status: int, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


# ── verbs ─────────────────────────────────────────────────────────────
def _get(event: dict[str, Any]) -> dict[str, Any]:
    key = _resolve_key(event)
    if not key:
        return _resp(400, {"error": "key is required (?key=... or /<key>)"})

    try:
        obj = _s3.get_object(Bucket=BUCKET, Key=key)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
            return _resp(404, {"error": "not found", "key": key})
        LOG.exception("S3 GetObject failed for key=%s", key)
        raise

    body = obj["Body"].read().decode("utf-8")
    return _resp(
        200,
        {
            "key": key,
            "content": body,
            "size": obj.get("ContentLength"),
            "content_type": obj.get("ContentType"),
            "last_modified": obj["LastModified"].isoformat(),
            "metadata": dict(obj.get("Metadata", {})),
        },
    )


def _delete(event: dict[str, Any]) -> dict[str, Any]:
    key = _resolve_key(event)
    if not key:
        return _resp(400, {"error": "key is required (?key=... or /<key>)"})

    # Pre-check existence so we can return a friendly 404 to the caller.
    # (S3 itself is idempotent on DELETE — DeleteObject of a missing key
    # succeeds silently. We prefer the more useful "404 not found".)
    try:
        _s3.head_object(Bucket=BUCKET, Key=key)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in ("NoSuchKey", "404", "NotFound"):
            return _resp(404, {"error": "not found", "key": key})
        LOG.exception("S3 HeadObject failed for key=%s", key)
        raise

    _s3.delete_object(Bucket=BUCKET, Key=key)
    return _resp(204, {"key": key, "deleted": True})


# ── entry point ───────────────────────────────────────────────────────
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    method = (event.get("httpMethod") or "").upper()
    LOG.info("method=%s path=%s", method, event.get("path"))

    if method == "GET":
        return _get(event)
    if method == "DELETE":
        return _delete(event)
    return _resp(405, {"error": f"method {method} not allowed"})