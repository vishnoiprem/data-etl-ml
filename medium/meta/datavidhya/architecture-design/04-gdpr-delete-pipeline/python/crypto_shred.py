"""
Crypto-shredding — per-user encryption keys; delete the key to "delete" the data.

Used for:
  - Immutable backup stores
  - ML training datasets (re-generate without user_id)
  - Any system where direct row deletion is impractical

Workflow:
  1. Wrap KMS per-user key around PII columns at write time
  2. To "delete", call kms:ScheduleKeyDeletion → after waiting period,
     ciphertext becomes undecryptable
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class CryptoKey:
    key_id: str
    user_id: str
    alias: str
    status: str                # ACTIVE | SCHEDULED_DELETION | DELETED
    created_at: float
    deletion_scheduled_at: Optional[float] = None
    deleted_at: Optional[float] = None


class CryptoKeyRegistry:
    """Mock of AWS KMS / GCP KMS per-user key management."""
    def __init__(self):
        self._keys: Dict[str, CryptoKey] = {}

    def create_key(self, user_id: str) -> CryptoKey:
        key = CryptoKey(
            key_id=f"kms-{hashlib.sha256(user_id.encode()).hexdigest()[:16]}",
            user_id=user_id,
            alias=f"alias/user/{user_id}",
            status="ACTIVE",
            created_at=time.time(),
        )
        self._keys[user_id] = key
        return key

    def schedule_deletion(self, user_id: str, pending_window_days: int = 7):
        if user_id not in self._keys:
            raise KeyError(f"no key for user {user_id}")
        key = self._keys[user_id]
        if key.status != "ACTIVE":
            return key
        key.status = "SCHEDULED_DELETION"
        key.deletion_scheduled_at = time.time()
        return key

    def force_delete(self, user_id: str):
        if user_id not in self._keys:
            return
        key = self._keys[user_id]
        key.status = "DELETED"
        key.deleted_at = time.time()


def encrypt_value(plaintext: str, key_id: str) -> bytes:
    """Mock encrypt: real prod uses KMS GenerateDataKey + AES-GCM."""
    return f"ENC[{key_id}]:{plaintext}".encode()


def is_readable(key: CryptoKey) -> bool:
    return key.status == "ACTIVE"
