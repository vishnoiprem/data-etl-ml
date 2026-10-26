"""Lambda handler: create a DynamoDB table (idempotent) and put items.

Companion to L18.

Required IAM permissions:
    dynamodb:CreateTable
    dynamodb:DescribeTable
    dynamodb:PutItem
    dynamodb:ListTables
"""

import json
import logging
import os
from decimal import Decimal

import boto3
from boto3.dynamodb.types import TypeSerializer
from botocore.exceptions import ClientError

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)


def _table_exists(ddb_client, table_name: str) -> bool:
    try:
        ddb_client.describe_table(TableName=table_name)
        return True
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "ResourceNotFoundException":
            return False
        raise


def _create_table(ddb_client, table_name: str, partition_key: str = "id") -> str:
    """Create the table (or no-op if it exists).

    Returns "created" if a new table was made, "exists" otherwise.
    """
    if _table_exists(ddb_client, table_name):
        return "exists"

    try:
        ddb_client.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": partition_key, "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": partition_key, "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "ResourceInUseException":
            return "exists"  # race with another invoker
        raise

    ddb_client.get_waiter("table_exists").wait(TableName=table_name)
    return "created"


def _coerce_floats(item: dict) -> dict:
    """DynamoDB rejects native Python floats; convert to Decimal."""
    out = {}
    for k, v in item.items():
        if isinstance(v, float):
            out[k] = Decimal(str(v))
        else:
            out[k] = v
    return out


def _serialize_item(item: dict) -> dict:
    """Convert a native-Python item to the low-level DynamoDB format.

    The boto3 *client* API for put_item/update_item expects the
    AttributeValue shape ({'S': '...'}, {'N': '...'}, ...). The
    *resource* API accepts native types and does this conversion for
    you. We use the client + a TypeSerializer to keep the API
    uniform with the rest of section 4.
    """
    serializer = TypeSerializer()
    return {k: serializer.serialize(v) for k, v in item.items()}


def _put_items(ddb_client, table_name: str, items: list[dict]) -> int:
    """Put each item, returning the number of writes performed."""
    written = 0
    for item in items:
        ddb_client.put_item(
            TableName=table_name,
            Item=_serialize_item(_coerce_floats(item)),
        )
        written += 1
    return written


def handler(event, context):
    """Create a DynamoDB table (idempotent) and put items into it.

    Event shape:
        {
          "table_name":     "orders",
          "partition_key":  "id",                  # optional, default "id"
          "region":         "us-east-1",           # optional
          "items": [
            {"id": "o-1", "customer": "alice", "total": 19.99},
            {"id": "o-2", "customer": "bob",   "total": 42.00}
          ]
        }

    Returns:
        {"table": str, "table_status": "created"|"exists",
         "items_written": int, "region": str}
    """
    LOG.info("received event: %s", json.dumps(event, default=str))

    table_name = event["table_name"]
    partition_key = event.get("partition_key", "id")
    items = event.get("items", []) or []
    region = (
        event.get("region")
        or os.environ.get("AWS_REGION")
        or "us-east-1"
    )

    ddb = boto3.client("dynamodb", region_name=region)
    table_status = _create_table(ddb, table_name, partition_key)
    written = _put_items(ddb, table_name, items) if items else 0

    LOG.info("table=%s status=%s items_written=%d", table_name, table_status, written)
    return {
        "table": table_name,
        "table_status": table_status,
        "items_written": written,
        "region": region,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    sample = {
        "table_name": "demo-orders",
        "partition_key": "id",
        "items": [
            {"id": "o-1", "customer": "alice", "total": 19.99},
            {"id": "o-2", "customer": "bob",   "total": 42.00},
            {"id": "o-3", "customer": "carol", "total": 7.50},
        ],
    }
    print(handler(sample, None))