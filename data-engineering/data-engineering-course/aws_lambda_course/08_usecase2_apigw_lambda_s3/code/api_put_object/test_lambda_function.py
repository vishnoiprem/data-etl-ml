"""Tests for api_put_object.

Run:
    cd code/api_put_object
    python -m pytest -v
"""
from __future__ import annotations

import base64
import importlib.util
import json
import sys
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

HERE = Path(__file__).resolve().parent
LAMBDA_PATH = HERE / "lambda_function.py"


def _load_handler():
    spec = importlib.util.spec_from_file_location("api_put_object", LAMBDA_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def handler(monkeypatch):
    monkeypatch.setenv("BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("CONTENT_TYPE", "application/octet-stream")
    if "api_put_object" in sys.modules:
        del sys.modules["api_put_object"]
    return _load_handler()


@pytest.fixture
def s3_bucket(handler):
    with mock_aws():
        boto3.client("s3", region_name="us-east-1").create_bucket(Bucket="test-bucket")
        yield


# ── tests ──────────────────────────────────────────────────────────────
def test_missing_key_returns_400(handler, s3_bucket):
    resp = handler.lambda_handler({"pathParameters": None, "body": "x"}, None)
    assert resp["statusCode"] == 400


def test_happy_path_writes_object(handler, s3_bucket):
    event = {
        "pathParameters": {"proxy": "hello.txt"},
        "body": "hello world",
        "isBase64Encoded": False,
        "headers": {"Content-Type": "text/plain"},
    }
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["key"] == "hello.txt"
    assert body["bytes"] == 11
    assert body["content_type"] == "text/plain"

    # Round-trip via raw boto3
    s3 = boto3.client("s3", region_name="us-east-1")
    obj = s3.get_object(Bucket="test-bucket", Key="hello.txt")
    assert obj["Body"].read() == b"hello world"
    assert obj["ContentType"] == "text/plain"


def test_base64_body_decoded(handler, s3_bucket):
    raw = b"\x00\x01\x02binary"
    event = {
        "pathParameters": {"proxy": "blob.bin"},
        "body": base64.b64encode(raw).decode("ascii"),
        "isBase64Encoded": True,
        "headers": {"Content-Type": "application/octet-stream"},
    }
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    s3 = boto3.client("s3", region_name="us-east-1")
    assert s3.get_object(Bucket="test-bucket", Key="blob.bin")["Body"].read() == raw


def test_empty_body_returns_400(handler, s3_bucket):
    event = {
        "pathParameters": {"proxy": "empty"},
        "body": "",
        "isBase64Encoded": False,
        "headers": {},
    }
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 400


def test_strip_slashes_in_path(handler, s3_bucket):
    event = {
        "pathParameters": {"proxy": "/nested/keys/x/"},
        "body": "ok",
        "isBase64Encoded": False,
        "headers": {"Content-Type": "text/plain"},
    }
    resp = handler.lambda_handler(event, None)
    body = json.loads(resp["body"])
    assert body["key"] == "nested/keys/x"
    assert body["bytes"] == 2
