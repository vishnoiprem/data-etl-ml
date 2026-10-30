"""Pytest fixtures shared across the S3 lifecycle + logging tests.

Uses moto's @mock_aws to simulate the data + log bucket pair in-process.
"""
from __future__ import annotations

import json
import os
import sys

import boto3
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

DATA_BUCKET = "s3-lifecycle-data-bucket-test"
LOG_BUCKET  = "s3-lifecycle-logs-bucket-test"

# Policy the lab applies to the log bucket so the S3 log delivery service
# can PutObject into it. moto requires this before put_bucket_logging().
LOG_BUCKET_POLICY = {
    "Version": "2012-10-17",
    "Statement": [{
        "Sid": "AllowS3LogDelivery",
        "Effect": "Allow",
        "Principal": {"Service": "logging.s3.amazonaws.com"},
        "Action": "s3:PutObject",
        "Resource": f"arn:aws:s3:::{LOG_BUCKET}/*",
        "Condition": {"StringEquals": {"aws:SourceAccount": "123456789012"}},
    }],
}


@pytest.fixture
def seeded_buckets():
    """Create the data + log bucket pair, attach the log policy, and seed the
    log bucket with an example access log file. Yields the boto3 S3 client.
    """
    from moto import mock_aws

    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=DATA_BUCKET)
        s3.create_bucket(Bucket=LOG_BUCKET)

        # Log bucket policy -- moto enforces it like the real service.
        s3.put_bucket_policy(Bucket=LOG_BUCKET,
                             Policy=json.dumps(LOG_BUCKET_POLICY))

        # Seed the example access log file in the log bucket.
        log_path = os.path.join(_ROOT, "sample_data", "example-access-log.txt")
        with open(log_path, encoding="utf-8") as fh:
            s3.put_object(Bucket=LOG_BUCKET,
                          Key="example-access-log.txt",
                          Body=fh.read().encode("utf-8"))

        yield s3
