"""S3 -> Lambda -> DynamoDB banking transactions pipeline.

Triggered by S3 ObjectCreated:Put events on a JSON file that contains a
"transactions" array. Each record is validated and written to a DynamoDB
table named ``transactions`` with partition key ``transaction_id``.

The write is idempotent: we use ``ConditionExpression="attribute_not_exists(transaction_id)"``
so re-deliveries of the same S3 event do not create duplicate rows.

Environment variables:
    TABLE_NAME       DynamoDB table name (default: "transactions")
    LOG_LEVEL        Python log level (default: "INFO")
"""

from __future__ import annotations

import json
import logging
import os
from decimal import Decimal
from typing import Any

import boto3
from botocore.exceptions import ClientError

# ---------------------------------------------------------------------------
# Module-level clients. boto3 clients are thread-safe and Lambda re-uses the
# same container across invocations, so we create them once at import time.
# ---------------------------------------------------------------------------

TABLE_NAME = os.environ.get("TABLE_NAME", "transactions")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

_dynamodb = boto3.resource("dynamodb")
_table = _dynamodb.Table(TABLE_NAME)

# We use the low-level S3 client to download the JSON file. S3 is a
# separate service from DynamoDB, so it has its own client.
_s3 = boto3.client("s3")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log_event(level: int, event: str, **fields: Any) -> None:
    """Emit one structured JSON line to CloudWatch.

    Structured logs are easy to query with CloudWatch Logs Insights and to
    forward to a downstream SIEM. They are the recommended pattern for any
    non-trivial Lambda function.
    """
    payload = {"event": event, **fields}
    logger.log(level, json.dumps(payload, default=str))


def _coerce_for_dynamodb(record: dict[str, Any]) -> dict[str, Any]:
    """Convert a Python dict into a dict safe for DynamoDB.

    DynamoDB does not accept native Python floats; they must be ``Decimal``.
    """
    item: dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, float):
            item[key] = Decimal(str(value))
        else:
            item[key] = value
    return item


# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------

def handler(event: dict[str, Any], context: Any) -> dict[str, int]:
    """Process one or more S3 ObjectCreated events and write rows to DynamoDB.

    Parameters
    ----------
    event:
        The S3 event payload as delivered by Lambda. Shape:
        ``{"Records": [{"s3": {"bucket": {"name": ...}, "object": {"key": ...}}}]}``
    context:
        The Lambda context object (unused, but required by the runtime).

    Returns
    -------
    dict
        Summary ``{"processed": N, "skipped": M, "errors": K}`` that
        CloudWatch logs and the async invoke response will surface.
    """
    request_id = getattr(context, "aws_request_id", "local")
    _log_event(
        logging.INFO,
        "invoke.start",
        request_id=request_id,
        record_count=len(event.get("Records", [])),
    )

    processed = 0
    skipped = 0
    errors = 0

    for record in event.get("Records", []):
        try:
            bucket = record["s3"]["bucket"]["name"]
            key = record["s3"]["object"]["key"]
        except (KeyError, TypeError):
            _log_event(logging.WARNING, "record.malformed", request_id=request_id)
            errors += 1
            continue

        try:
            obj = _s3.get_object(Bucket=bucket, Key=key)
            payload = json.loads(obj["Body"].read().decode("utf-8"))
        except ClientError:
            _log_event(
                logging.ERROR,
                "s3.read_failed",
                request_id=request_id,
                bucket=bucket,
                key=key,
            )
            errors += 1
            continue
        except (json.JSONDecodeError, UnicodeDecodeError):
            _log_event(
                logging.ERROR,
                "s3.parse_failed",
                request_id=request_id,
                bucket=bucket,
                key=key,
            )
            errors += 1
            continue

        transactions = payload.get("transactions", [])
        if not isinstance(transactions, list):
            _log_event(
                logging.ERROR,
                "payload.shape_invalid",
                request_id=request_id,
                bucket=bucket,
                key=key,
            )
            errors += 1
            continue

        for tx in transactions:
            tx_id = tx.get("transaction_id")
            if not tx_id:
                _log_event(
                    logging.WARNING,
                    "record.skipped",
                    request_id=request_id,
                    reason="missing_transaction_id",
                )
                skipped += 1
                continue

            try:
                _table.put_item(
                    Item=_coerce_for_dynamodb(tx),
                    ConditionExpression="attribute_not_exists(transaction_id)",
                )
                _log_event(
                    logging.INFO,
                    "record.persisted",
                    request_id=request_id,
                    transaction_id=tx_id,
                )
                processed += 1
            except ClientError as exc:
                if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                    _log_event(
                        logging.INFO,
                        "record.duplicate",
                        request_id=request_id,
                        transaction_id=tx_id,
                    )
                    # Idempotent: duplicate is a success, not a failure.
                else:
                    _log_event(
                        logging.ERROR,
                        "dynamodb.put_failed",
                        request_id=request_id,
                        transaction_id=tx_id,
                        error=exc.response["Error"]["Code"],
                    )
                    errors += 1

    summary = {"processed": processed, "skipped": skipped, "errors": errors}
    _log_event(logging.INFO, "invoke.done", request_id=request_id, **summary)
    return summary
