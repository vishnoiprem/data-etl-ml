"""
Crypto-shredding — per-user encryption keys; delete the key to "delete" the data.

Used for:
  - Immutable backup stores
  - ML training datasets (re-generate without user_id)
  - Any system where direct row deletion is impractical

Workflow (matches AWS KMS / GCP KMS semantics):
  1. Wrap KMS per-user key around PII columns at write time
  2. To "delete", call schedule_deletion(user, pending_window_days)
     → status transitions ACTIVE → SCHEDULED_DELETION
     → after pending_window expires, call force_delete to mark DELETED
  3. cancel_deletion(user) can roll back SCHEDULED_DELETION → ACTIVE
     (e.g. admin realizes the deletion was an error)
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
        """Schedule key for deletion. Status flips to SCHEDULED_DELETION.
        Must call force_delete() after pending_window_days have elapsed to
        finalize — mirrors AWS KMS mandatory waiting period."""
        if user_id not in self._keys:
            raise KeyError(f"no key for user {user_id}")
        key = self._keys[user_id]
        if key.status != "ACTIVE":
            return key
        key.status = "SCHEDULED_DELETION"
        key.deletion_scheduled_at = time.time()
        key._pending_window_days = pending_window_days
        return key

    def force_delete(self, user_id: str, pending_window_days: int = 7):
        """Immediately delete the key. In production, callers should first
        verify that pending_window_days have elapsed since schedule_deletion()."""
        if user_id not in self._keys:
            return
        key = self._keys[user_id]
        if key.status == "ACTIVE":
            # Implicitly schedule + delete
            self.schedule_deletion(user_id, pending_window_days)
        key = self._keys[user_id]
        key.status = "DELETED"
        key.deleted_at = time.time()

    def cancel_deletion(self, user_id: str):
        """Roll back a SCHEDULED_DELETION. Only allowed before force_delete."""
        if user_id not in self._keys:
            return
        key = self._keys[user_id]
        if key.status != "SCHEDULED_DELETION":
            return
        key.status = "ACTIVE"
        key.deletion_scheduled_at = None
        return key

    def pending_window_expired(self, user_id: str) -> bool:
        """True if pending window has elapsed (eligible for force_delete)."""
        if user_id not in self._keys:
            return False
        key = self._keys[user_id]
        if key.status != "SCHEDULED_DELETION" or key.deletion_scheduled_at is None:
            return False
        elapsed_days = (time.time() - key.deletion_scheduled_at) / 86_400
        return elapsed_days >= getattr(key, "_pending_window_days", 7)


def encrypt_value(plaintext: str, key_id: str) -> bytes:
    """Mock encrypt: real prod uses KMS GenerateDataKey + AES-GCM."""
    return f"ENC[{key_id}]:{plaintext}".encode()


def is_readable(key: CryptoKey) -> bool:
    return key.status == "ACTIVE"
