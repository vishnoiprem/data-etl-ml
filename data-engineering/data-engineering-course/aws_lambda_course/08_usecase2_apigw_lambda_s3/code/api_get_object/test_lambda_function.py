"""Tests for api_get_object.

We use moto.mock_aws to stub S3 entirely in-memory. No AWS credentials
or network access required.

Run:
    cd code/api_get_object
    python -m pytest -v
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

HERE = Path(__file__).resolve().parent
LAMBDA_PATH = HERE / "lambda_function.py"

# ── import the handler as a module ─────────────────────────────────────
def _load_handler():
    spec = importlib.util.spec_from_file_location("api_get_object", LAMBDA_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def handler(monkeypatch):
    monkeypatch.setenv("BUCKET_NAME", "test-bucket")
    # Force a fresh import so the env var is honored.
    if "api_get_object" in sys.modules:
        del sys.modules["api_get_object"]
    return _load_handler()


@pytest.fixture
def s3_bucket(handler):
    with mock_aws():
        boto3.client("s3", region_name="us-east-1").create_bucket(Bucket="test-bucket")
        yield


# ── tests ──────────────────────────────────────────────────────────────
def test_missing_key_returns_400(handler, s3_bucket):
    resp = handler.lambda_handler({"pathParameters": None, "queryStringParameters": None}, None)
    assert resp["statusCode"] == 400
    assert "key is required" in resp["body"]


def test_happy_path_gets_object(handler, s3_bucket):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.put_object(Bucket="test-bucket", Key="orders/1", Body=b'{"id":1}')

    event = {
        "pathParameters": {"proxy": "orders/1"},
        "queryStringParameters": None,
    }
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["key"] == "orders/1"
    assert body["content"] == '{"id":1}'
    assert body["size"] == 8


def test_query_string_key_wins_over_path(handler, s3_bucket):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.put_object(Bucket="test-bucket", Key="from-qs", Body=b"qs")
    s3.put_object(Bucket="test-bucket", Key="from-path", Body=b"path")

    event = {
        "pathParameters": {"proxy": "from-path"},
        "queryStringParameters": {"key": "from-qs"},
    }
    resp = handler.lambda_handler(event, None)
    body = json.loads(resp["body"])
    assert body["key"] == "from-qs"
    assert body["content"] == "qs"


def test_missing_object_returns_404(handler, s3_bucket):
    event = {"pathParameters": {"proxy": "nope"}, "queryStringParameters": None}
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 404
    body = json.loads(resp["body"])
    assert body["error"] == "not found"


def test_metadata_round_trip(handler, s3_bucket):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.put_object(
        Bucket="test-bucket",
        Key="with-meta",
        Body=b"hello",
        Metadata={"author": "prem", "env": "dev"},
    )
    event = {"pathParameters": {"proxy": "with-meta"}, "queryStringParameters": None}
    resp = handler.lambda_handler(event, None)
    body = json.loads(resp["body"])
    assert body["metadata"] == {"author": "prem", "env": "dev"}


def test_strip_slashes_in_path(handler, s3_bucket):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.put_object(Bucket="test-bucket", Key="x", Body=b"strip me")
    event = {"pathParameters": {"proxy": "/x/"}, "queryStringParameters": None}
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["key"] == "x"
