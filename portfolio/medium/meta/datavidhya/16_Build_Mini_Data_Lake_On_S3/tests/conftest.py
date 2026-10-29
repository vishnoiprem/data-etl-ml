"""Pytest fixtures shared across the data lake tests.

Uses moto's @mock_aws decorator to simulate the S3 service entirely
in-process. The lab's six stages all run against this simulated bucket.
"""
from __future__ import annotations

import os
import sys

import boto3
import pytest

# Make sample_data importable for `open()`.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
SAMPLES = os.path.join(_ROOT, "sample_data")
sys.path.insert(0, _ROOT)


@pytest.fixture
def bucket_name() -> str:
    """Stable name across the test session; matches the lab's prefix."""
    return "s3-intro-data-lake-bucket-test"


@pytest.fixture
def seeded_bucket(bucket_name: str):
    """Create a fresh moto-mocked bucket pre-seeded with the lab's raw/ files.

    Yields the boto3 S3 client. The bucket is deleted at teardown.
    """
    from moto import mock_aws

    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=bucket_name)

        # Seed raw/ files (the lab does this).
        with open(os.path.join(SAMPLES, "january-sales.csv"),
                  encoding="utf-8") as fh:
            s3.put_object(Bucket=bucket_name,
                          Key="raw/sales/january-sales.csv",
                          Body=fh.read().encode("utf-8"))
        with open(os.path.join(SAMPLES, "customers.json"),
                  encoding="utf-8") as fh:
            s3.put_object(Bucket=bucket_name,
                          Key="raw/customers/customers.json",
                          Body=fh.read().encode("utf-8"))
        yield s3
