"""Offline tests for lambda_function.app -- no AWS credentials required.

The S3 stub is shared with the self-asserting driver via
lambda_function._stubs.
"""
from __future__ import annotations

import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "lambda_function"))

import app                                # noqa: E402
from _stubs import StubBucket, install, load_raw_csv, parse_csv, put_event  # noqa: E402


@pytest.fixture
def stub_bucket() -> StubBucket:
    return StubBucket()


@pytest.fixture
def patched_s3(monkeypatch: pytest.MonkeyPatch,
               stub_bucket: StubBucket) -> StubBucket:
    install(stub_bucket, monkeypatch=monkeypatch)
    return stub_bucket


# ============================================================== tests
def test_accepts_valid_rows_and_splits_rejects(patched_s3: StubBucket) -> None:
    """Happy path: 12 raw rows -> 7 accepted, 5 rejected."""
    key = "raw/orders_2026-09-27.csv"
    patched_s3.put(key, load_raw_csv())

    result = app.lambda_handler(put_event("orders-lab-test-bucket", key),
                                context=None)

    assert result == {"accepted": 7, "rejected": 5}
    assert patched_s3.has("processed/orders_2026-09-27.csv")
    assert patched_s3.has("rejected/orders_2026-09-27.csv")


def test_duplicate_order_id_goes_to_rejected(patched_s3: StubBucket) -> None:
    """Row 1001 repeated -- caught by the seen-set, not the validator."""
    key = "raw/dup.csv"
    patched_s3.put(key,
                   "order_id,customer_id,amount,currency,order_date\n"
                   "1001,42,99.50,USD,2026-09-20\n"
                   "1001,42,99.50,USD,2026-09-20\n")

    result = app.lambda_handler(put_event("orders-lab-test-bucket", key),
                                context=None)

    assert result == {"accepted": 1, "rejected": 1}, result
    rej = parse_csv(patched_s3.get("rejected/dup.csv"))
    assert rej[0]["_rejected_reason"] == app.Reason.DUPLICATE_ORDER_ID


def test_rejection_reasons_are_stable(patched_s3: StubBucket) -> None:
    """The five named trap categories are produced by the validator."""
    key = "raw/traps.csv"
    patched_s3.put(
        key,
        "order_id,customer_id,amount,currency,order_date\n"
        "1,,5.00,USD,2026-01-01\n"                # missing_field:customer_id
        "2,1,-1.00,USD,2026-01-01\n"              # bad_amount:not_positive
        "3,1,5.00,XYZ,2026-01-01\n"               # bad_currency:XYZ
        "4,1,5.00,USD,2026/01/01\n"               # bad_date:2026/01/01
        "5,1,5.00,USD,2026-01-01\n"               # accepted -- sanity row
    )

    app.lambda_handler(put_event("orders-lab-test-bucket", key), context=None)
    rej = parse_csv(patched_s3.get("rejected/traps.csv"))
    reasons = {r["_rejected_reason"] for r in rej}

    expected = {app.Reason.MISSING_FIELD, app.Reason.BAD_AMOUNT,
                app.Reason.BAD_CURRENCY, app.Reason.BAD_DATE}
    assert expected <= reasons
    assert app.Reason.DUPLICATE_ORDER_ID not in reasons


def test_non_matching_keys_are_skipped(patched_s3: StubBucket) -> None:
    """processed/ keys are filtered out so S3 events on the writes don't loop."""
    event = put_event("b", "processed/orders.csv")

    result = app.lambda_handler(event, context=None)

    assert result == {"accepted": 0, "rejected": 0}
    assert patched_s3.objects == {}


def test_validator_rejects_blank_required_fields() -> None:
    """Whitespace-only customer_id is rejected; the .strip() handles it."""
    err = app._validate({"order_id": "1", "customer_id": "   ",
                         "amount": "5.00", "currency": "USD",
                         "order_date": "2026-01-01"})
    assert err.reason == app.Reason.MISSING_FIELD
    assert err.detail == "customer_id"


def test_enrichment_is_deterministic_given_same_inputs() -> None:
    """row_hash depends only on the input row -- two calls match."""
    row = {"order_id": "1", "customer_id": "42",
           "amount": "99.50", "currency": "USD", "order_date": "2026-09-20"}
    a = app._enrich(dict(row), amount=99.50, processed_at="2026-09-27T00:00:00+00:00")
    b = app._enrich(dict(row), amount=99.50, processed_at="2026-09-27T00:00:01+00:00")
    assert a["row_hash"] == b["row_hash"]
    assert a["amount_usd"] == b["amount_usd"] == "99.50"
    assert float(a["amount_usd"]) == 99.50
