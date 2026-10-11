"""Tests for create_table_put_items.handler.

Run with:  pytest test_script.py -v
"""

import os
from decimal import Decimal

import boto3
import pytest
from moto import mock_aws

os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

import create_table_put_items  # noqa: E402


@mock_aws
def test_handler_creates_table():
    result = create_table_put_items.handler(
        {"table_name": "orders", "items": []}, None
    )
    assert result["table"] == "orders"
    assert result["table_status"] == "created"
    assert result["items_written"] == 0

    ddb = boto3.client("dynamodb", region_name="us-east-1")
    desc = ddb.describe_table(TableName="orders")["Table"]
    assert desc["TableStatus"] == "ACTIVE"
    assert desc["BillingModeSummary"]["BillingMode"] == "PAY_PER_REQUEST"


@mock_aws
def test_handler_puts_items_into_new_table():
    result = create_table_put_items.handler(
        {
            "table_name": "orders",
            "items": [
                {"id": "o-1", "customer": "alice", "total": 19.99},
                {"id": "o-2", "customer": "bob",   "total": 42.00},
                {"id": "o-3", "customer": "carol", "total": 7.50},
            ],
        },
        None,
    )
    assert result["table_status"] == "created"
    assert result["items_written"] == 3

    ddb = boto3.client("dynamodb", region_name="us-east-1")
    items = ddb.scan(TableName="orders")["Items"]
    assert len(items) == 3

    # The low-level *client* API returns AttributeValue shapes
    # ({'S': '...'}, {'N': '...'}, ...). Floats were coerced to Decimal
    # strings on the way in.
    by_id = {item["id"]["S"]: item for item in items}
    assert by_id["o-1"]["total"] == {"N": "19.99"}
    assert by_id["o-2"]["customer"] == {"S": "bob"}


@mock_aws
def test_handler_is_idempotent_on_existing_table():
    # First call creates.
    first = create_table_put_items.handler(
        {"table_name": "orders", "items": [{"id": "o-1"}]}, None
    )
    assert first["table_status"] == "created"
    assert first["items_written"] == 1

    # Second call sees the existing table and *still* writes items.
    second = create_table_put_items.handler(
        {"table_name": "orders", "items": [{"id": "o-2"}]}, None
    )
    assert second["table_status"] == "exists"
    assert second["items_written"] == 1

    ddb = boto3.client("dynamodb", region_name="us-east-1")
    assert len(ddb.scan(TableName="orders")["Items"]) == 2


@mock_aws
def test_handler_coerces_floats_to_decimal():
    # The Decimal coercion is what makes this work: `str(0.1 + 0.2)`
    # produces "0.30000000000000004" (the exact representation of the
    # binary float), and that string is what gets stored as a 'N'
    # AttributeValue. If the handler passed a native float to
    # put_item, boto3 would raise TypeError before we even reach DDB.
    create_table_put_items.handler({"table_name": "orders", "items": []}, None)
    create_table_put_items.handler(
        {"table_name": "orders", "items": [{"id": "o-1", "total": 0.1 + 0.2}]}, None,
    )

    ddb = boto3.client("dynamodb", region_name="us-east-1")
    resp = ddb.get_item(TableName="orders", Key={"id": {"S": "o-1"}})
    # The number was stored as an 'N' AttributeValue (not rejected as a float).
    assert "N" in resp["Item"]["total"]
    # And the value round-trips through Decimal.
    assert Decimal(resp["Item"]["total"]["N"]) == Decimal(str(0.1 + 0.2))