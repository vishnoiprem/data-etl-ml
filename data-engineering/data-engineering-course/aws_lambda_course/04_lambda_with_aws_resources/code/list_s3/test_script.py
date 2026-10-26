"""Tests for list_s3_buckets.handler.

Run with:  pytest test_script.py -v
"""

import os

import boto3
import pytest
from moto import mock_aws

os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

import list_s3_buckets  # noqa: E402


@mock_aws
def test_handler_lists_no_buckets():
    result = list_s3_buckets.handler({}, None)
    assert result == {"count": 0, "buckets": []}


@mock_aws
def test_handler_lists_multiple_buckets():
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="alpha-bucket")
    s3.create_bucket(Bucket="beta-bucket")
    s3.create_bucket(Bucket="gamma-bucket")

    result = list_s3_buckets.handler({}, None)

    assert result["count"] == 3
    names = {row["name"] for row in result["buckets"]}
    assert names == {"alpha-bucket", "beta-bucket", "gamma-bucket"}

    # Every row must include region + created_at.
    for row in result["buckets"]:
        assert row["region"] == "us-east-1"
        assert row["created_at"]  # non-empty string


@mock_aws
def test_handler_resolves_region_for_explicit_region_bucket():
    s3_us = boto3.client("s3", region_name="us-east-1")
    s3_eu = boto3.client("s3", region_name="eu-west-1")
    s3_us.create_bucket(Bucket="us-bucket")
    s3_eu.create_bucket(
        Bucket="eu-bucket",
        CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
    )

    result = list_s3_buckets.handler({}, None)
    by_name = {row["name"]: row["region"] for row in result["buckets"]}
    assert by_name["us-bucket"] == "us-east-1"
    assert by_name["eu-bucket"] == "eu-west-1"
