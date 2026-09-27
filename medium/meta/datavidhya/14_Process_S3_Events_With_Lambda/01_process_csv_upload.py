"""
Q14: Process S3 Events with Lambda   [AWS | Event-Driven, S3, Lambda]

Offline driver: simulate an S3 ObjectCreated event, run the Lambda handler
against a stub bucket, and assert the split output matches the expected
processed/ and rejected/ CSVs.

How to Think:
- The handler is a pure function of (event, bucket contents). Stub boto3
  with an in-memory dict and you can re-run the whole pipeline on a laptop
  with no AWS creds -- which is exactly what this script does.
- The expected CSVs are hand-computed by reading data/orders_raw.csv and
  walking the same rules the handler does. If a test fails, the bug is in
  the handler or in this file -- never in the AWS service.

The trap:
- The processed CSV has one non-deterministic column (processed_at =
  wall-clock time). We strip it before comparing.
- The handler writes to BOTH processed/ and rejected/ prefixes. Forgetting
  to assert rejected output is the #1 silent failure: the function
  "succeeds" but bad rows disappear.
- The duplicate-order_id row (the second 1001) is accepted by per-row
  validation but caught by the seen-set. If the seen-set logic is broken,
  the assertion fails with a specific mismatch count.

AWS note:
- For real Lambda runs the handler is invoked by the S3 event source. Here
  we synthesize the event JSON ourselves; that's the same payload shape the
  AWS notification service delivers.
"""
from __future__ import annotations

import os
import sys
from typing import Dict, List

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "lambda_function"))

import app                              # noqa: E402  -- import after sys.path
from _stubs import StubBucket, install, load_csv,  \
                   load_raw_csv, parse_csv, put_event  # noqa: E402

PROCESSED_KEEP = ("order_id", "customer_id", "amount", "currency",
                  "order_date", "amount_usd")
REJECTED_KEEP  = ("order_id", "customer_id", "amount", "currency",
                  "order_date", "_rejected_reason", "_rejected_detail")


def expect_csv(title: str, got: List[Dict[str, str]],
               expected: List[Dict[str, str]],
               normaliser) -> None:
    g = normaliser(got)
    e = normaliser(expected)
    if g != e:
        print(f"[FAIL] {title}")
        print(f"   expected: {e}")
        print(f"   got:      {g}")
        raise AssertionError(title)
    print(f"[PASS] {title}  ({len(g)} rows)")


def _norm_processed(rows):
    return [tuple(r[k] for k in PROCESSED_KEEP) for r in rows]


def _norm_rejected(rows):
    return [tuple(r[k] for k in REJECTED_KEEP) for r in rows]


def main() -> None:
    stub = StubBucket()
    install(stub)

    raw_key = "raw/orders_2026-09-27.csv"
    bucket = "orders-lab-test-bucket"
    stub.put(raw_key, load_raw_csv())
    event = put_event(bucket, raw_key)

    print("\n=== Q14 Process S3 Events with Lambda ===\n")

    # Stage 1: handler returns accepted/rejected counts.
    result = app.lambda_handler(event, context=None)
    assert result == {"accepted": 7, "rejected": 5}, result
    print(f"[PASS] Q14 handler returned {result}")

    # Stage 2: stub received BOTH processed/ and rejected/ writes.
    proc_key = "processed/orders_2026-09-27.csv"
    rej_key  = "rejected/orders_2026-09-27.csv"
    assert stub.has(proc_key) and stub.has(rej_key), list(stub.objects)
    print("[PASS] Q14 stub bucket has processed/ AND rejected/ keys")

    # Stage 3: processed CSV row-by-row matches expected.
    got_proc_rows = parse_csv(stub.get(proc_key))
    expect_csv("Q14 processed CSV matches expected",
               got_proc_rows,
               load_csv(os.path.join(_HERE, "data", "orders_processed_expected.csv")),
               _norm_processed)

    # Stage 4: rejected CSV row-by-row matches expected.
    got_rej_rows = parse_csv(stub.get(rej_key))
    expect_csv("Q14 rejected CSV matches expected",
               got_rej_rows,
               load_csv(os.path.join(_HERE, "data", "orders_rejected_expected.csv")),
               _norm_rejected)

    # Stage 5: per-row breakdown -- the lab's named trap rows.
    reasons = sorted({r["_rejected_reason"] for r in got_rej_rows})
    assert reasons == ["bad_amount", "bad_currency", "bad_date",
                       "duplicate_order_id", "missing_field"], reasons
    print(f"[PASS] Q14 rejection reasons covered: {reasons}")

    # Stage 6: enrichment -- every accepted row has the three derived fields.
    for row in got_proc_rows:
        assert row["amount_usd"] and row["processed_at"] \
               and len(row["row_hash"]) == 16, row
    print(f"[PASS] Q14 every accepted row has amount_usd, processed_at, row_hash")

    # Stage 7: idempotency NOTE -- counts are stable, but processed_at is
    # wall-clock so the second run's CSV differs byte-for-byte. Counts match.
    result2 = app.lambda_handler(event, context=None)
    assert result2 == result, f"non-idempotent counts: {result} vs {result2}"
    print("[PASS] Q14 re-running the handler returns identical counts")

    # Stage 8: non-matching key skip -- a key under processed/ is ignored.
    proc_event = put_event(bucket, proc_key)
    assert app.lambda_handler(proc_event, context=None) == {"accepted": 0, "rejected": 0}
    print("[PASS] Q14 handler ignores processed/ keys (no S3-event loop)")

    print("\n=== All Q14 stages pass ===\n")


if __name__ == "__main__":
    main()
