"""Tests for create_s3_bucket.handler.

Run with:  pytest test_script.py -v
"""

import os

import boto3
import pytest
from moto import mock_aws

# Set fake AWS creds before any boto3 client is created.
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

import create_s3_bucket  # noqa: E402  (import after env setup)


@mock_aws
def test_handler_creates_bucket_us_east_1():
    event = {"bucket_name": "demo-bucket-us-east-1", "region": "us-east-1"}
    result = create_s3_bucket.handler(event, None)

    assert result["status"] == "created"
    assert result["bucket"] == "demo-bucket-us-east-1"
    assert result["region"] == "us-east-1"

    # Confirm the bucket really exists in the (mocked) AWS API.
    s3 = boto3.client("s3", region_name="us-east-1")
    resp = s3.list_buckets()
    names = {b["Name"] for b in resp["Buckets"]}
    assert "demo-bucket-us-east-1" in names


@mock_aws
def test_handler_creates_bucket_in_explicit_region():
    event = {"bucket_name": "demo-bucket-eu-west-1", "region": "eu-west-1"}
    result = create_s3_bucket.handler(event, None)

    assert result["status"] == "created"
    assert result["region"] == "eu-west-1"

    s3 = boto3.client("s3", region_name="eu-west-1")
    resp = s3.list_buckets()
    names = {b["Name"] for b in resp["Buckets"]}
    assert "demo-bucket-eu-west-1" in names


@mock_aws
def test_handler_returns_exists_when_bucket_already_owned():
    # Pre-create the bucket.
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="preexisting-bucket")

    result = create_s3_bucket.handler(
        {"bucket_name": "preexisting-bucket", "region": "us-east-1"}, None
    )
    assert result["status"] == "exists"
    assert result["bucket"] == "preexisting-bucket"
