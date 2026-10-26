"""Tests for the unified api_objects handler (GET + DELETE).

We use moto.mock_aws to stub S3 entirely in-memory. No AWS credentials
or network access required.

Run:
    cd code/api_pt3_handlers
    python -m pytest -v
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

HERE = Path(__file__).resolve().parent
LAMBDA_PATH = HERE / "lambda_function.py"


# ── import the handler as a module ────────────────────────────────────
def _load_handler():
    spec = importlib.util.spec_from_file_location("api_objects", LAMBDA_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def handler(monkeypatch):
    monkeypatch.setenv("BUCKET_NAME", "test-bucket")
    # Force a fresh import so the env var is honored.
    if "api_objects" in sys.modules:
        del sys.modules["api_objects"]
    return _load_handler()


@pytest.fixture
def s3_bucket(handler):
    with mock_aws():
        boto3.client("s3", region_name="us-east-1").create_bucket(Bucket="test-bucket")
        yield


# ── tests ─────────────────────────────────────────────────────────────
def test_get_returns_200_when_object_exists(handler, s3_bucket):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.put_object(
        Bucket="test-bucket",
        Key="orders/1",
        Body=b'{"id":1,"total":99.95}',
        ContentType="application/json",
    )

    event = {
        "httpMethod": "GET",
        "path": "/orders/1",
        "pathParameters": {"proxy": "orders/1"},
        "queryStringParameters": None,
    }
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["key"] == "orders/1"
    assert body["content"] == '{"id":1,"total":99.95}'
    # S3 may have added/stripped a trailing byte during storage, so just
    # assert the size matches what we get back from a direct S3 read.
    assert body["size"] == len(b'{"id":1,"total":99.95}')
    assert body["content_type"] == "application/json"


def test_get_returns_404_when_object_missing(handler, s3_bucket):
    event = {
        "httpMethod": "GET",
        "path": "/orders/missing",
        "pathParameters": {"proxy": "orders/missing"},
        "queryStringParameters": None,
    }
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 404
    body = json.loads(resp["body"])
    assert body["error"] == "not found"
    assert body["key"] == "orders/missing"


def test_delete_returns_204_when_object_exists(handler, s3_bucket):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.put_object(Bucket="test-bucket", Key="orders/2", Body=b"delete-me")

    event = {
        "httpMethod": "DELETE",
        "path": "/orders/2",
        "pathParameters": {"proxy": "orders/2"},
        "queryStringParameters": None,
    }
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 204
    body = json.loads(resp["body"])
    assert body == {"key": "orders/2", "deleted": True}

    # Confirm the object really is gone.
    with pytest.raises(s3.exceptions.NoSuchKey):
        s3.get_object(Bucket="test-bucket", Key="orders/2")


def test_delete_returns_404_when_object_missing(handler, s3_bucket):
    event = {
        "httpMethod": "DELETE",
        "path": "/orders/ghost",
        "pathParameters": {"proxy": "orders/ghost"},
        "queryStringParameters": None,
    }
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 404
    body = json.loads(resp["body"])
    assert body["error"] == "not found"
    assert body["key"] == "orders/ghost"


def test_method_not_allowed_returns_405(handler, s3_bucket):
    event = {
        "httpMethod": "PATCH",
        "path": "/x",
        "pathParameters": {"proxy": "x"},
        "queryStringParameters": None,
    }
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 405
    body = json.loads(resp["body"])
    assert "not allowed" in body["error"]


def test_get_query_string_key_wins_over_path(handler, s3_bucket):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.put_object(Bucket="test-bucket", Key="from-qs", Body=b"qs")
    s3.put_object(Bucket="test-bucket", Key="from-path", Body=b"path")

    event = {
        "httpMethod": "GET",
        "path": "/from-path",
        "pathParameters": {"proxy": "from-path"},
        "queryStringParameters": {"key": "from-qs"},
    }
    resp = handler.lambda_handler(event, None)
    body = json.loads(resp["body"])
    assert body["key"] == "from-qs"
    assert body["content"] == "qs"


def test_missing_key_returns_400(handler, s3_bucket):
    event = {
        "httpMethod": "GET",
        "path": "/",
        "pathParameters": None,
        "queryStringParameters": None,
    }
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 400
    assert "key is required" in resp["body"]


def test_cors_headers_present_on_every_response(handler, s3_bucket):
    event = {
        "httpMethod": "GET",
        "path": "/nope",
        "pathParameters": {"proxy": "nope"},
        "queryStringParameters": None,
    }
    resp = handler.lambda_handler(event, None)
    headers = resp["headers"]
    assert headers["Access-Control-Allow-Origin"] == "*"
    assert "GET" in headers["Access-Control-Allow-Methods"]
    assert "DELETE" in headers["Access-Control-Allow-Methods"]
    assert headers["Content-Type"] == "application/json"