"""Tests for delete_s3_bucket.handler.

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

import delete_s3_bucket  # noqa: E402


@mock_aws
def test_handler_deletes_empty_bucket():
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="empty-bucket")

    result = delete_s3_bucket.handler(
        {"bucket_name": "empty-bucket", "region": "us-east-1"}, None
    )

    assert result["status"] == "deleted"
    assert result["bucket"] == "empty-bucket"
    assert result["deleted_objects"] == 0

    # Confirm the bucket is gone.
    names = {b["Name"] for b in s3.list_buckets()["Buckets"]}
    assert "empty-bucket" not in names


@mock_aws
def test_handler_force_empties_then_deletes_bucket():
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="full-bucket")
    s3.put_object(Bucket="full-bucket", Key="a.txt", Body=b"a")
    s3.put_object(Bucket="full-bucket", Key="b/c.txt", Body=b"c")

    result = delete_s3_bucket.handler(
        {"bucket_name": "full-bucket", "region": "us-east-1"}, None
    )

    assert result["status"] == "deleted"
    assert result["deleted_objects"] == 2
    names = {b["Name"] for b in s3.list_buckets()["Buckets"]}
    assert "full-bucket" not in names


@mock_aws
def test_handler_is_idempotent_for_missing_bucket():
    result = delete_s3_bucket.handler(
        {"bucket_name": "never-existed", "region": "us-east-1"}, None
    )
    assert result["status"] == "absent"
    assert result["deleted_objects"] == 0
