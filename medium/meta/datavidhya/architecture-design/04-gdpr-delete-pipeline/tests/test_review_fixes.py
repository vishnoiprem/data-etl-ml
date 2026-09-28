"""Regression tests for review findings (Problem 4)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

import pytest

from verification import verify_and_certify
from delete_coordinator import Receipt
from crypto_shred import CryptoKeyRegistry


# --------------------------------------------------------------------- #
# Merkle root — must handle odd leaf count without dropping
# --------------------------------------------------------------------- #

def test_merkle_root_with_three_receipts():
    """3 receipts is the minimum case that triggered the old odd-leaf bug."""
    receipts = [
        Receipt("iceberg", "t1", 100, 0, "direct", 1.0, 2.0, "OK"),
        Receipt("redis",   "k1",   1, 0, "direct", 1.0, 2.0, "OK"),
        Receipt("s3",      "p1",   0, 5, "direct", 1.0, 2.0, "OK"),
    ]
    cert = verify_and_certify("req-001", "user_42", receipts)
    assert cert.systems_covered == 3
    assert cert.total_rows_deleted == 101
    assert cert.total_objects_deleted == 5
    assert len(cert.merkle_root) == 64     # SHA-256 hex

    # Same input must produce same root (deterministic)
    cert2 = verify_and_certify("req-001", "user_42", receipts)
    assert cert.merkle_root == cert2.merkle_root


def test_merkle_root_with_single_receipt():
    cert = verify_and_certify("req-001", "user_42",
                              [Receipt("iceberg", "t1", 1, 0, "direct", 1.0, 2.0, "OK")])
    assert len(cert.merkle_root) == 64


# --------------------------------------------------------------------- #
# Crypto-shred — pending window + cancel
# --------------------------------------------------------------------- #

def test_crypto_shred_pending_window_then_delete():
    reg = CryptoKeyRegistry()
    reg.create_key("user_42")
    reg.schedule_deletion("user_42", pending_window_days=7)
    assert reg._keys["user_42"].status == "SCHEDULED_DELETION"
    assert not reg.pending_window_expired("user_42")

    # simulate elapsed time — patch the timestamp
    import time
    key = reg._keys["user_42"]
    key.deletion_scheduled_at = time.time() - 8 * 86_400   # 8 days ago
    assert reg.pending_window_expired("user_42")

    reg.force_delete("user_42")
    assert reg._keys["user_42"].status == "DELETED"


def test_crypto_shred_cancel_during_pending():
    reg = CryptoKeyRegistry()
    reg.create_key("user_42")
    reg.schedule_deletion("user_42")
    reg.cancel_deletion("user_42")
    assert reg._keys["user_42"].status == "ACTIVE"


# --------------------------------------------------------------------- #
# Dedup multi-user guard — covered by Problem 5's test_dedup.py.
# --------------------------------------------------------------------- #
