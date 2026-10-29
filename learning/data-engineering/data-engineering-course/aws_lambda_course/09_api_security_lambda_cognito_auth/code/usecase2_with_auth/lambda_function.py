"""usecase2_with_auth — same S3-backed CRUD as L31/L32, but with two routes.

The integration Lambda for the secured Use Case 2 REST API. The API has:

* /public/{proxy+}   — protected by a Cognito User Pool Authorizer (L36c)
* /internal/{proxy+} — protected by a Lambda Authorizer (L36b)

Both routes run through the same function. The function discriminates
between routes by reading event["requestContext"]["resourcePath"] (the
matched resource definition, *not* the URL), and reads the caller
identity from event["requestContext"]["authorizer"] in whichever shape
the active authorizer populated it.

Event shapes we handle:

* Lambda Authorizer (TOKEN) — populates a flat authorizer dict with the
  `context` map from AuthResponse hoisted to the top level:
      requestContext.authorizer = {"principalId": "...", "tenant": "...",
                                     "scope": "...", "sub": "..."}

* Cognito User Pool Authorizer — populates:
      requestContext.authorizer = {"claims": {"sub": "...", "client_id": "...",
                                              "scope": "...", "iss": "..."}}

* No authorizer / open method — requestContext.authorizer is None or
  empty. We refuse those requests with a 401 because every method in
  production has an authorizer.

Environment:
    BUCKET_NAME  — required, name of the S3 bucket to read/write.

Response shape (proxy integration):
    {"statusCode": int, "headers": {...}, "body": "<json string>"}
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

BUCKET: str = os.environ["BUCKET_NAME"]
_s3 = boto3.client("s3")


# ── caller identity ────────────────────────────────────────────────────
def _caller_for_internal(event: Dict[str, Any]) -> Dict[str, str]:
    """Read the authorizer context produced by the Lambda Authorizer."""
    auth = event.get("requestContext", {}).get("authorizer") or {}
    return {
        "principal_id": str(auth.get("principalId", "anonymous")),
        "tenant": str(auth.get("tenant", "")),
        "scope": str(auth.get("scope", "")),
        "sub": str(auth.get("sub", "")),
    }


def _caller_for_public(event: Dict[str, Any]) -> Dict[str, str]:
    """Read the claims produced by the Cognito User Pool Authorizer.

    API Gateway flattens all JWT claims into a string->string map under
    `requestContext.authorizer.claims`. We never see a nested dict here.
    """
    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("claims", {})
    ) or {}
    return {
        "principal_id": str(claims.get("sub", "anonymous")),
        "client_id": str(claims.get("client_id", "")),
        "scope": str(claims.get("scope", "")),
        "iss": str(claims.get("iss", "")),
    }


# ── request helpers ────────────────────────────────────────────────────
def _route_of(event: Dict[str, Any]) -> str:
    """Return 'public', 'internal', or 'unknown' based on the matched resource."""
    path = event.get("requestContext", {}).get("resourcePath", "")
    if path.startswith("/public"):
        return "public"
    if path.startswith("/internal"):
        return "internal"
    return "unknown"


def _resolve_key(event: Dict[str, Any]) -> str:
    """Pull the S3 key from the {proxy+} path parameter."""
    path = event.get("pathParameters") or {}
    return (path.get("proxy") or "").strip("/")


def _json(status: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


def _is_authorized(event: Dict[str, Any]) -> bool:
    """Verify that the authorizer actually populated the block we expect.

    We never trust an empty / missing authorizer block, even if API
    Gateway would have sent the request through. That is the
    "default deny" posture from L36a.
    """
    auth = event.get("requestContext", {}).get("authorizer") or {}
    if not auth:
        return False
    route = _route_of(event)
    if route == "internal":
        # Lambda Authorizer: principalId is required.
        return bool(auth.get("principalId"))
    if route == "public":
        # Cognito Authorizer: claims block must have at least a `sub`.
        return bool((auth.get("claims") or {}).get("sub"))
    return False


# ── handler ────────────────────────────────────────────────────────────
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    route = _route_of(event)
    if route not in ("public", "internal"):
        return _json(404, {"error": f"unknown route: {route}"})

    if not _is_authorized(event):
        # Belt-and-braces: if the authorizer did not populate the block,
        # reject even if API Gateway let it through.
        return _json(401, {"error": "missing or invalid authorizer context"})

    key = _resolve_key(event)
    if not key:
        return _json(400, {"error": "key is required in the URL path"})

    # The internal route enforces a prefix on the S3 key — internal
    # callers may not read or write under /public/ in the bucket.
    # Production-quality versions of this rule live in the authorizer,
    # but we keep an integration-side check as defense in depth.
    if route == "internal" and not key.startswith("internal/"):
        return _json(
            403,
            {"error": "internal callers may only touch internal/ keys", "key": key},
        )

    caller = (
        _caller_for_internal(event)
        if route == "internal"
        else _caller_for_public(event)
    )
    method = event.get("httpMethod", "GET").upper()

    if method == "GET":
        try:
            resp = _s3.get_object(Bucket=BUCKET, Key=key)
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
                "route": route,
                "caller": caller,
                "content": body,
                "size": resp.get("ContentLength"),
            },
        )

    if method == "PUT":
        raw_body = event.get("body") or b""
        if isinstance(raw_body, str):
            body_bytes = raw_body.encode("utf-8")
        else:
            body_bytes = raw_body
        if not body_bytes:
            return _json(400, {"error": "body is empty"})

        _s3.put_object(Bucket=BUCKET, Key=key, Body=body_bytes)
        LOG.info(
            "wrote s3://%s/%s by route=%s principal=%s",
            BUCKET, key, route, caller["principal_id"],
        )
        return _json(
            200,
            {
                "key": key,
                "route": route,
                "caller": caller,
                "bytes": len(body_bytes),
            },
        )

    return _json(405, {"error": f"method {method} not allowed"})
