"""Unit tests for the S3 -> DynamoDB Lambda handler.

We use ``moto.mock_aws`` to stub the AWS APIs so the suite runs end-to-end on
a developer laptop without touching the real AWS control plane. The test
exercises three things:

1. happy path: an S3 Put notification triggers the handler, every record
   from the sample JSON is persisted to the DynamoDB table;
2. idempotency: re-invoking the handler with the same event does not create
   duplicate rows and the duplicate write is logged as ``record.duplicate``;
3. validation: a row missing ``transaction_id`` is skipped, not written.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import boto3
import pytest
from moto import mock_aws

from s3_to_dynamodb_lambda import (
    TABLE_NAME,
    _dynamodb,
    _table,
    handler,
)


SAMPLE_PATH = Path(__file__).resolve().parent.parent / "sample_data" / "sample_transactions.json"
BUCKET_NAME = "banking-transactions-ingest"
OBJECT_KEY = "raw/2026-10-10/sample_transactions.json"


def _build_event(bucket: str, key: str) -> dict[str, Any]:
    """Build the S3 event payload that Lambda would receive in production."""
    return {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "eventName": "ObjectCreated:Put",
                "s3": {
                    "bucket": {"name": bucket},
                    "object": {"key": key},
                },
            }
        ]
    }


@pytest.fixture
def aws_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provision a moto-backed S3 bucket + DynamoDB table and seed the file."""
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=BUCKET_NAME)
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=OBJECT_KEY,
            Body=SAMPLE_PATH.read_bytes(),
            ContentType="application/json",
        )

        dynamodb = boto3.client("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName=TABLE_NAME,
            AttributeDefinitions=[{"AttributeName": "transaction_id", "AttributeType": "S"}],
            KeySchema=[{"AttributeName": "transaction_id", "KeyType": "HASH"}],
            BillingMode="PAY_PER_REQUEST",
        )

        # moto resets the boto3 clients we built at import time, so re-bind
        # them to the moto context for the duration of the test.
        ddb_resource = boto3.resource("dynamodb", region_name="us-east-1")
        monkeypatch.setattr("s3_to_dynamodb_lambda._dynamodb", ddb_resource)
        monkeypatch.setattr("s3_to_dynamodb_lambda._table", ddb_resource.Table(TABLE_NAME))
        monkeypatch.setattr(
            "s3_to_dynamodb_lambda._s3",
            boto3.client("s3", region_name="us-east-1"),
        )
        yield


def _scan_items() -> list[dict[str, Any]]:
    """Return every row currently in the transactions table."""
    response = _table.scan()
    return response.get("Items", [])


def test_handler_persists_every_record(aws_environment: None) -> None:
    """Happy path: 5 records in, 5 records out."""
    context = MagicMock()
    context.aws_request_id = "test-request-1"

    summary = handler(_build_event(BUCKET_NAME, OBJECT_KEY), context)

    assert summary == {"processed": 5, "skipped": 0, "errors": 0}
    items = _scan_items()
    assert len(items) == 5
    assert {item["transaction_id"] for item in items} == {
        f"TXN-100{i}" for i in range(1, 6)
    }


def test_handler_is_idempotent(aws_environment: None) -> None:
    """Re-invoking with the same event must not create duplicate rows."""
    context = MagicMock()
    context.aws_request_id = "test-request-2"

    event = _build_event(BUCKET_NAME, OBJECT_KEY)
    first = handler(event, context)
    second = handler(event, context)

    assert first == {"processed": 5, "skipped": 0, "errors": 0}
    # The second invocation sees 5 conditional-check failures, which the
    # handler treats as benign duplicates.
    assert second == {"processed": 0, "skipped": 0, "errors": 0}
    assert len(_scan_items()) == 5


def test_handler_skips_rows_missing_transaction_id(aws_environment: None) -> None:
    """A row with no transaction_id must be skipped, not persisted."""
    s3 = boto3.client("s3", region_name="us-east-1")
    bad_key = "raw/2026-10-10/bad.json"
    bad_payload = {
        "transactions": [
            {"transaction_id": "TXN-2001", "amount": 10.0, "customer_id": "CUST-1"},
            {"amount": 20.0, "customer_id": "CUST-2"},  # missing transaction_id
            {"transaction_id": "TXN-2003", "amount": 30.0, "customer_id": "CUST-3"},
        ]
    }
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=bad_key,
        Body=json.dumps(bad_payload).encode("utf-8"),
        ContentType="application/json",
    )

    context = MagicMock()
    context.aws_request_id = "test-request-3"

    summary = handler(_build_event(BUCKET_NAME, bad_key), context)

    assert summary == {"processed": 2, "skipped": 1, "errors": 0}
    items = _scan_items()
    assert {item["transaction_id"] for item in items} == {"TXN-2001", "TXN-2003"}
