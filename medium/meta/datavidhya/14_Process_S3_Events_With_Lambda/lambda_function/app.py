"""Q14: Process S3 Events with Lambda.

S3 ObjectCreated event -> read raw/ CSV -> validate each row -> enrich the
good ones -> write the split to processed/ and rejected/. Deterministic
except for the wall-clock `processed_at` (intentional -- audit trail).

The handler NEVER round-trips back to raw/; the SAM event filter is the
primary defense and this handler's `_should_process` is the secondary one
to break the S3-event loop if a key slips through.
"""
from __future__ import annotations

import csv
import datetime as _dt
import hashlib
import io
import json
import logging
import os
import re
from typing import Any, Dict, List, NamedTuple, Tuple

import boto3

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

RAW_PREFIX       = os.environ.get("RAW_PREFIX",       "raw/")
PROCESSED_PREFIX = os.environ.get("PROCESSED_PREFIX", "processed/")
REJECTED_PREFIX  = os.environ.get("REJECTED_PREFIX",  "rejected/")
CSV_CONTENT_TYPE = "text/csv"

REQUIRED_FIELDS = ("order_id", "customer_id", "amount", "currency", "order_date")
ALLOWED_CURRENCIES = frozenset({"USD", "EUR", "GBP", "JPY", "INR"})

# FX rates (USD per 1 unit). Constant so retries are deterministic on this
# axis; production would call an FX service and write the snapshot.
FX_TO_USD = {"USD": 1.00, "EUR": 1.08, "GBP": 1.27, "JPY": 0.0067, "INR": 0.012}

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class Reason:
    """Stable rejection categories. Detail is in a separate column.

    Keeping reason as a bare category (no embedded detail) lets CloudWatch
    log queries and BI dashboards group by category without parsing.
    """
    MISSING_FIELD       = "missing_field"
    BAD_AMOUNT          = "bad_amount"
    BAD_CURRENCY        = "bad_currency"
    BAD_DATE            = "bad_date"
    DUPLICATE_ORDER_ID  = "duplicate_order_id"


class Reject(NamedTuple):
    reason:  str
    detail:  str = ""


class _Valid(NamedTuple):
    """Per-row validation result on success: re-emit ``order_id`` and the
    already-parsed ``amount`` so the enricher doesn't reparse."""
    order_id: str
    amount:   float


def _reject(row: Dict[str, Any], rej: Reject) -> Dict[str, Any]:
    """Annotate a rejected row with the ``_rejected_reason`` / ``_rejected_detail``
    columns. Centralising this keeps the two rejection paths (validator and
    duplicate-order_id) in lockstep.
    """
    return {**row,
            "_rejected_reason": rej.reason,
            "_rejected_detail": rej.detail}


# ----------------------------------------------------------------------- main
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, int]:
    """S3 ObjectCreated event(s) -> validate -> enrich -> split write."""
    s3 = boto3.client("s3")
    accepted_total, rejected_total = 0, 0

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key    = record["s3"]["object"]["key"]

        if not _should_process(key):
            LOG.info("skip non-matching key: %s", key)
            continue

        LOG.info("processing s3://%s/%s", bucket, key)
        body = _read_object(s3, bucket, key)

        accepted, rejected = _split_rows(body)
        accepted_total += len(accepted)
        rejected_total += len(rejected)

        if accepted:
            _write_objects(s3, bucket, key, accepted, PROCESSED_PREFIX)
        if rejected:
            _write_objects(s3, bucket, key, rejected, REJECTED_PREFIX)

        LOG.info("key=%s accepted=%d rejected=%d",
                 key, len(accepted), len(rejected))

    return {"accepted": accepted_total, "rejected": rejected_total}


def _should_process(key: str) -> bool:
    return key.startswith(RAW_PREFIX) and key.endswith(".csv")


def _read_object(s3, bucket: str, key: str) -> str:
    obj = s3.get_object(Bucket=bucket, Key=key)
    return obj["Body"].read().decode("utf-8")


def _write_objects(s3, bucket: str, source_key: str,
                   rows: List[Dict[str, Any]], target_prefix: str) -> None:
    csv_body, target_key = _render(rows, source_key, target_prefix)
    s3.put_object(Bucket=bucket, Key=target_key,
                  Body=csv_body.encode("utf-8"),
                  ContentType=CSV_CONTENT_TYPE)
    LOG.info("wrote s3://%s/%s (%d bytes)", bucket, target_key, len(csv_body))


def _render(rows: List[Dict[str, Any]], source_key: str,
            target_prefix: str) -> Tuple[bytes, str]:
    """Strip the raw/ prefix and prepend the target prefix."""
    target_key = target_prefix + source_key[len(RAW_PREFIX):]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue(), target_key


def _split_rows(body: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Validate, dedup, enrich. Bad rows go to ``rejected`` with a reason."""
    accepted, rejected = [], []
    seen = set()
    processed_at = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")

    for row in csv.DictReader(io.StringIO(body)):
        result = _validate(row)
        if isinstance(result, Reject):
            rejected.append(_reject(row, result))
            continue

        oid = result.order_id
        if oid in seen:
            rejected.append(_reject(row, Reject(Reason.DUPLICATE_ORDER_ID, "")))
            continue
        seen.add(oid)

        accepted.append(_enrich(row, result.amount, processed_at))

    return accepted, rejected


def _validate(row: Dict[str, str]) -> "Reject | _Valid":
    """Return a ``Reject`` on failure or a ``_Valid`` on success."""
    for col in REQUIRED_FIELDS:
        if not (row.get(col) or "").strip():
            return Reject(Reason.MISSING_FIELD, col)

    try:
        amount = float(row["amount"])
    except ValueError:
        return Reject(Reason.BAD_AMOUNT, "not_a_number")
    if amount <= 0:
        return Reject(Reason.BAD_AMOUNT, "not_positive")

    if row["currency"] not in ALLOWED_CURRENCIES:
        return Reject(Reason.BAD_CURRENCY, row["currency"])

    if not _DATE_RE.match(row["order_date"]):
        return Reject(Reason.BAD_DATE, row["order_date"])

    return _Valid(order_id=row["order_id"], amount=amount)


def _enrich(row: Dict[str, str], amount: float, processed_at: str) -> Dict[str, Any]:
    """Add ``amount_usd`` (FX), ``processed_at`` (snapshot from caller), and
    ``row_hash`` (audit). The first two columns are derived; ``processed_at``
    is non-deterministic so consumers needing byte-stable re-runs should sort
    by ``row_hash``.
    """
    enriched = dict(row)
    enriched["amount_usd"]   = f"{amount * FX_TO_USD[row['currency']]:.2f}"
    enriched["processed_at"] = processed_at
    enriched["row_hash"]     = hashlib.sha256(
        json.dumps(row, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    return enriched
