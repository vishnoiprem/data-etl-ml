"""Tests for usecase2_with_auth.lambda_function.

We use moto.mock_aws to stub S3 entirely in-memory. There is no
network access and no AWS credentials required.

Run:
    cd code/usecase2_with_auth
    python -m pytest -v
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict

import boto3
import pytest
from moto import mock_aws


HERE = Path(__file__).resolve().parent
LAMBDA_PATH = HERE / "lambda_function.py"


# ── import the handler as a module ─────────────────────────────────────
def _load_handler():
    spec = importlib.util.spec_from_file_location("usecase2_with_auth", LAMBDA_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def handler(monkeypatch):
    monkeypatch.setenv("BUCKET_NAME", "test-bucket")
    if "usecase2_with_auth" in sys.modules:
        del sys.modules["usecase2_with_auth"]
    return _load_handler()


@pytest.fixture
def s3_bucket(handler):
    with mock_aws():
        boto3.client("s3", region_name="us-east-1").create_bucket(Bucket="test-bucket")
        yield boto3.client("s3", region_name="us-east-1")


def _event(
    method: str,
    path: str,
    *,
    resource_path: str,
    path_param: str,
    body: str = "",
    authorizer: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build a minimal API Gateway proxy event for tests."""
    return {
        "resource": resource_path,
        "path": path,
        "httpMethod": method,
        "pathParameters": {"proxy": path_param},
        "queryStringParameters": None,
        "headers": {},
        "body": body,
        "isBase64Encoded": False,
        "requestContext": {
            "resourcePath": resource_path,
            "resourceId": "rid",
            "apiId": "abcd",
            "httpMethod": method,
            "authorizer": authorizer,
        },
    }


# ── internal route — Lambda Authorizer context shape ──────────────────
def test_internal_get_happy_path(handler, s3_bucket):
    s3_bucket.put_object(Bucket="test-bucket", Key="internal/audit/2026-10-10", Body=b'{"ok":true}')
    event = _event(
        "GET", "/internal/audit/2026-10-10",
        resource_path="/internal/{proxy+}", path_param="internal/audit/2026-10-10",
        authorizer={
            "principalId": "svc-1",
            "tenant": "acme",
            "scope": "read",
            "sub": "svc-1",
        },
    )
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["key"] == "internal/audit/2026-10-10"
    assert body["route"] == "internal"
    assert body["caller"]["tenant"] == "acme"
    assert body["caller"]["principal_id"] == "svc-1"


def test_internal_put_happy_path(handler, s3_bucket):
    event = _event(
        "PUT", "/internal/batch/2026-10-10",
        resource_path="/internal/{proxy+}", path_param="internal/batch/2026-10-10",
        body='{"items":1}',
        authorizer={
            "principalId": "svc-2",
            "tenant": "acme",
            "scope": "write",
            "sub": "svc-2",
        },
    )
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["bytes"] == len('{"items":1}')
    assert body["caller"]["scope"] == "write"

    # Confirm the object actually landed in S3.
    obj = s3_bucket.get_object(Bucket="test-bucket", Key="internal/batch/2026-10-10")
    assert obj["Body"].read() == b'{"items":1}'


# ── public route — Cognito claims shape ────────────────────────────────
def test_public_get_happy_path(handler, s3_bucket):
    s3_bucket.put_object(Bucket="test-bucket", Key="public/orders/123", Body=b'{"id":123}')
    event = _event(
        "GET", "/public/orders/123",
        resource_path="/public/{proxy+}", path_param="public/orders/123",
        authorizer={
            "claims": {
                "sub": "service-uuid-1",
                "client_id": "abc123",
                "scope": "demo-pool/read:items",
                "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_xyz",
            }
        },
    )
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["key"] == "public/orders/123"
    assert body["route"] == "public"
    assert body["caller"]["client_id"] == "abc123"
    assert body["caller"]["scope"] == "demo-pool/read:items"


def test_public_put_happy_path(handler, s3_bucket):
    event = _event(
        "PUT", "/public/orders/124",
        resource_path="/public/{proxy+}", path_param="public/orders/124",
        body=b'{"id":124}',
        authorizer={
            "claims": {
                "sub": "service-uuid-2",
                "client_id": "abc123",
                "scope": "demo-pool/read:items demo-pool/write:items",
                "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_xyz",
            }
        },
    )
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["caller"]["scope"].endswith("write:items")


# ── failure modes ──────────────────────────────────────────────────────
def test_missing_key_returns_400(handler):
    event = _event(
        "GET", "/public/",
        resource_path="/public/{proxy+}", path_param="/",
        authorizer={"claims": {"sub": "user-1"}},
    )
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 400
    assert "key is required" in resp["body"]


def test_internal_caller_may_not_touch_public_prefix(handler, s3_bucket):
    """Defense-in-depth: an internal caller cannot read a public-prefix key."""
    s3_bucket.put_object(Bucket="test-bucket", Key="public/orders/123", Body=b"secret")
    event = _event(
        "GET", "/internal/orders/123",
        resource_path="/internal/{proxy+}", path_param="public/orders/123",
        authorizer={"principalId": "svc-1", "tenant": "acme", "scope": "read"},
    )
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 403
    body = json.loads(resp["body"])
    assert "internal callers may only touch" in body["error"]


def test_no_authorizer_returns_401(handler):
    """Empty / missing authorizer block must always 401."""
    event = _event(
        "GET", "/internal/audit/x",
        resource_path="/internal/{proxy+}", path_param="internal/audit/x",
        authorizer=None,
    )
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 401


def test_unknown_route_returns_404(handler):
    """If resourcePath does not start with /public or /internal, 404."""
    event = _event(
        "GET", "/something/else",
        resource_path="/something/else", path_param="else",
        authorizer={"claims": {"sub": "x"}},
    )
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 404


def test_internal_get_404_when_object_missing(handler, s3_bucket):
    event = _event(
        "GET", "/internal/audit/missing",
        resource_path="/internal/{proxy+}", path_param="internal/audit/missing",
        authorizer={"principalId": "svc-1", "tenant": "acme"},
    )
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 404
    body = json.loads(resp["body"])
    assert body["error"] == "not found"


def test_put_with_empty_body_returns_400(handler):
    event = _event(
        "PUT", "/public/orders/x",
        resource_path="/public/{proxy+}", path_param="public/orders/x",
        body="",
        authorizer={"claims": {"sub": "x"}},
    )
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 400
    assert "body is empty" in resp["body"]
