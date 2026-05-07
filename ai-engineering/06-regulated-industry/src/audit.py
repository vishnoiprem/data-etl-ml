"""Tamper-evident audit log with hash chain.

Each entry includes a SHA-256 hash of its content + the previous entry's
hash. Any tampering breaks the chain at that point.

Production: write entries to S3 with Object Lock (compliance mode) for
immutability, and replicate to QLDB for cryptographic verification. CloudTrail
covers the API-call layer; this is the application-layer audit.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


GENESIS_HASH = "0" * 64


@dataclass
class AuditEntry:
    seq: int
    timestamp: str
    actor: str                    # user / role / service
    action: str                   # what happened (e.g. "rag_query", "pii_redact")
    resource: str                 # what was acted on
    outcome: str                  # "allow" | "deny" | "ok" | "error"
    controls: list[str]           # control families this satisfies
    payload_hash: str             # hash of the (sanitized) request/response
    prev_hash: str                # previous entry's hash
    entry_hash: str = ""          # hash over THIS entry (computed)

    def compute_hash(self) -> str:
        body = {
            "seq": self.seq, "timestamp": self.timestamp, "actor": self.actor,
            "action": self.action, "resource": self.resource, "outcome": self.outcome,
            "controls": self.controls, "payload_hash": self.payload_hash,
            "prev_hash": self.prev_hash,
        }
        return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


class AuditLog:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else None
        self.entries: list[AuditEntry] = []
        self._last_hash = GENESIS_HASH
        if self.path and self.path.exists():
            self._load()

    def _load(self):
        for line in self.path.read_text().splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            self.entries.append(AuditEntry(**d))
        if self.entries:
            self._last_hash = self.entries[-1].entry_hash

    def append(self, *, actor: str, action: str, resource: str, outcome: str,
               controls: list[str], payload: dict) -> AuditEntry:
        body = json.dumps(payload, sort_keys=True, default=str).encode()
        payload_hash = hashlib.sha256(body).hexdigest()
        entry = AuditEntry(
            seq=len(self.entries) + 1,
            timestamp=datetime.now(timezone.utc).isoformat(),
            actor=actor, action=action, resource=resource, outcome=outcome,
            controls=controls, payload_hash=payload_hash,
            prev_hash=self._last_hash,
        )
        entry.entry_hash = entry.compute_hash()
        self.entries.append(entry)
        self._last_hash = entry.entry_hash
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "a") as f:
                f.write(json.dumps(asdict(entry)) + "\n")
        return entry

    def verify(self) -> tuple[bool, int | None]:
        """Verify hash chain; returns (ok, broken_at_seq_or_None)."""
        prev = GENESIS_HASH
        for e in self.entries:
            if e.prev_hash != prev:
                return False, e.seq
            if e.compute_hash() != e.entry_hash:
                return False, e.seq
            prev = e.entry_hash
        return True, None
