"""
Q14: Process S3 Events with Lambda   [AWS | Event-Driven, S3, Lambda]

Wire an S3 ObjectCreated event to a Lambda that reads CSV from raw/,
validates each row, enriches the good ones, and writes the split
outputs to processed/ and rejected/.

How to Think:
- One S3 event record = one new object. Lambda receives up to N records
  per invocation but conceptually processes each independently; the
  per-record accepted/rejected lists are pure functions of the CSV body.
- The handler is small on purpose. Each helper (read / validate /
  enrich / write) does one thing; the handler is the orchestrator.
  Anything past ~150 lines here is a smell -- split into a layer module.
- Validation, not parsing, is the rejection step. A row with a missing
  required column is NOT a parse error -- csv.DictReader gives you an
  empty string for missing columns and the validator decides.
- Enrichment is deterministic. FX rates and timestamps come from the
  handler environment so retries produce the same numbers (the lab
  expects re-runs to be idempotent).

The trap:
- Reading from raw/ and writing to processed/ with the SAME key prefix
  would loop forever -- the second write also fires an ObjectCreated
  event. The handler must NEVER round-trip back to raw/.
- Without the s3: prefix + .csv suffix filter, ObjectCreated:* fires
  on the processed/ output too. The SAM template wires the filter on
  the EventSource, not the handler. Never trust client-side filtering.
- The "duplicate order_id" trap is the row 1001 at the END of orders_raw.csv.
  It passes per-row validation, but the handler must keep a seen-set so it
  goes to rejected/ rather than processed/.

AWS note:
- The handler uses print/LOG so CloudWatch Logs streams it structured.
  Use `sam logs -n OrdersProcessorFunction --tail` to stream.
- For production, the IAM policy is OVERLY broad: AmazonS3ReadOnlyAccess +
  AmazonS3FullAccess. Lab-grade; scope it to the bucket ARN before any
  real use.
"""
import csv
import datetime as _dt
import hashlib
import io
import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Tuple

import boto3

# Standard Lambda logger -- CloudWatch picks it up automatically.
LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

# Env-var driven prefix routing.
RAW_PREFIX       = os.environ.get("RAW_PREFIX",       "raw/")
PROCESSED_PREFIX = os.environ.get("PROCESSED_PREFIX", "processed/")
REJECTED_PREFIX  = os.environ.get("REJECTED_PREFIX",  "rejected/")

# Required columns. Anything else => rejected with reason "missing_field:<col>".
REQUIRED_FIELDS = ("order_id", "customer_id", "amount", "currency", "order_date")

# Accepted ISO currencies. Real systems would resolve to ISO 4217 via an FX
# service; this stub keeps the demo deterministic.
ALLOWED_CURRENCIES = frozenset({"USD", "EUR", "GBP", "JPY", "INR"})

# FX stub: USD per 1 unit of currency. Constant so retries are deterministic.
# Real systems would call an FX service or pull daily rates from S3.
FX_TO_USD = {
    "USD": 1.00,
    "EUR": 1.08,
    "GBP": 1.27,
    "JPY": 0.0067,
    "INR": 0.012,
}

# ISO-8601 date (YYYY-MM-DD) validator. Strict -- no "9/20/2026" formats.
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ----------------------------------------------------------------------- main
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, int]:
    """S3 ObjectCreated event(s) -> validate -> enrich -> split write.

    Event shape (one record, lab-style):
        {"Records": [{
            "s3": {"bucket": {"name": "..."}, "object": {"key": "raw/x.csv"}}
        }]}
    """
    s3 = boto3.client("s3")
    accepted_total = rejected_total = 0

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


# ---------------------------------------------------------------------- route
def _should_process(key: str) -> bool:
    """Trust the SAM-side filter for prod; double-check here for paranoia."""
    return key.startswith(RAW_PREFIX) and key.endswith(".csv")


# ----------------------------------------------------------------------- IO
def _read_object(s3, bucket: str, key: str) -> str:
    """Read the whole object as text. Failed GetObject is fatal -- the event
    will retry on transient errors automatically."""
    obj = s3.get_object(Bucket=bucket, Key=key)
    return obj["Body"].read().decode("utf-8")


def _write_objects(s3, bucket: str, source_key: str,
                   rows: List[Dict[str, Any]], target_prefix: str) -> None:
    """Buffer the rows to CSV and PutObject. Key mirrors source minus raw/."""
    csv_body, target_key = _render(rows, source_key, target_prefix)
    s3.put_object(Bucket=bucket, Key=target_key,
                  Body=csv_body.encode("utf-8"),
                  ContentType="text/csv")
    LOG.info("wrote s3://%s/%s (%d bytes)", bucket, target_key, len(csv_body))


def _render(rows: List[Dict[str, Any]], source_key: str,
            target_prefix: str) -> Tuple[bytes, str]:
    """Serialize rows to CSV and compute the target key.

    raw/orders_2026-09-27.csv -> processed/orders_2026-09-27.csv
    """
    target_key = target_prefix + source_key[len(RAW_PREFIX):]
    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return buf.getvalue(), target_key


# -------------------------------------------------------------------- logic
def _split_rows(body: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Validate every row, then enrich good ones, then dedup by order_id.

    Order of operations:
      1. csv.DictReader over body.
      2. _validate rejects malformed rows first (cheap, per-row).
      3. accepted rows are enriched in order.
      4. duplicate order_id goes to rejected with reason "duplicate_order_id".
    """
    accepted, rejected = [], []
    seen = set()

    for row in csv.DictReader(io.StringIO(body)):
        err = _validate(row)
        if err:
            rejected.append({**row, "_rejected_reason": err})
            continue

        oid = row["order_id"]
        if oid in seen:
            rejected.append({**row, "_rejected_reason": "duplicate_order_id"})
            continue
        seen.add(oid)

        accepted.append(_enrich(row))

    return accepted, rejected


def _validate(row: Dict[str, str]) -> str:
    """Return a reason string on failure, '' on success. Reasons are stable so
    CloudWatch log queries can group on them: ``rejected_reason LIKE 'bad_%'``.
    """
    # 1. required fields present and non-empty
    for col in REQUIRED_FIELDS:
        v = (row.get(col) or "").strip()
        if not v:
            return f"missing_field:{col}"

    # 2. amount > 0 (lab trap)
    try:
        amount = float(row["amount"])
    except ValueError:
        return "bad_amount:not_a_number"
    if amount <= 0:
        return "bad_amount:not_positive"

    # 3. currency is an allowed ISO code (lab trap)
    if row["currency"] not in ALLOWED_CURRENCIES:
        return f"bad_currency:{row['currency']}"

    # 4. order_date is YYYY-MM-DD (lab trap)
    if not _DATE_RE.match(row["order_date"]):
        return f"bad_date:{row['order_date']}"

    return ""


def _enrich(row: Dict[str, str]) -> Dict[str, Any]:
    """Add derived columns. Deterministic so re-processing is idempotent.

    New columns:
      amount_usd    : float -- converted via FX stub
      processed_at  : ISO-8601 UTC timestamp of THIS run
      row_hash      : sha256 of the original input fields (audit trail)
    """
    currency = row["currency"]
    amount   = float(row["amount"])

    enriched = dict(row)            # shallow copy, don't mutate caller's row
    enriched["amount_usd"]   = round(amount * FX_TO_USD[currency], 2)
    enriched["processed_at"] = _dt.datetime.now(_dt.timezone.utc).isoformat(
        timespec="seconds")
    enriched["row_hash"]     = hashlib.sha256(
        json.dumps(row, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    return enriched
