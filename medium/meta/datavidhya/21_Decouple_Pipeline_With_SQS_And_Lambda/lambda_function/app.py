"""Q21: Decouple a Pipeline with SQS and Lambda.

The Lambda consumer the lab's event source mapping invokes. The same
handler runs in production (via AWS Lambda) and offline (via the
in-memory SQS simulator in ``sqs_stub.py``).

Batch event shape (one Records list per invocation):
    {"Records": [
        {"messageId":       "...",
         "receiptHandle":   "...",
         "body":            "<json payload>",
         "attributes":      {"ApproximateReceiveCount": "1", ...},
         "messageAttributes": {...},
         "eventSource":     "aws:sqs",
         "eventSourceARN":  "arn:aws:sqs:...:main-queue",
         "awsRegion":       "us-east-1"
        },
        ...
    ]}

Behaviour:
    - Validate every payload. Bad/missing fields => raise, SQS will retry.
    - Successful rows are logged and counted; the function returns the
      batch size, which is what AWS Lambda uses for the event source
      mapping's "Successful messages deleted" metric.
    - Poison messages keep failing until SQS's maxReceiveCount fires; the
      redrive policy then moves them to the DLQ. This file just keeps
      raising on bad input; the queue + redrive do the routing.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

REQUIRED_FIELDS = ("order_id", "customer_id", "amount", "currency")

# ISO currencies -- mirroring slot 14's lab for consistency.
ALLOWED_CURRENCIES = frozenset({"USD", "EUR", "GBP", "JPY", "INR"})
_AMOUNT_RE = re.compile(r"^\d+(\.\d{1,2})?$")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, int]:
    """SQS batch event -> process each record -> return counts.

    If ANY record fails validation the whole batch raises. AWS Lambda's
    event source mapping treats a raised exception as "leave all messages
    in the queue" -- they get retried on the next poll. This is the
    "poison message" behaviour the lab demos.
    """
    records = event.get("Records", [])
    LOG.info("processing batch of %d message(s)", len(records))

    processed: List[Dict[str, Any]] = []
    for record in records:
        body = json.loads(record["body"])
        _validate_payload(body)
        processed.append(body)
        LOG.info("order_id=%s customer_id=%s amount=%s %s -- OK",
                 body["order_id"], body["customer_id"],
                 body["amount"], body["currency"])

    return {"batch_size": len(records), "processed": len(processed)}


def _validate_payload(payload: Dict[str, Any]) -> None:
    """Raise on the first bad field. The redrive policy + DLQ catch the
    message after ``maxReceiveCount`` retries."""
    for col in REQUIRED_FIELDS:
        if col not in payload or payload[col] in (None, "", []):
            raise ValueError(f"missing required field: {col}")

    if not _AMOUNT_RE.match(str(payload["amount"])):
        raise ValueError(f"bad amount: {payload['amount']!r}")

    if payload["currency"] not in ALLOWED_CURRENCIES:
        raise ValueError(f"bad currency: {payload['currency']!r}")
