"""Append-only event log with hash chain."""
from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Event:
    seq: int
    ts: float
    actor: str
    action: str           # "read" | "edit" | "delete" | "create"
    target: str
    prev_hash: str
    payload: dict = field(default_factory=dict)

    def digest(self) -> str:
        body = json.dumps({
            "seq": self.seq, "ts": self.ts, "actor": self.actor,
            "action": self.action, "target": self.target,
            "prev_hash": self.prev_hash, "payload": self.payload,
        }, sort_keys=True)
        return hashlib.sha256(body.encode()).hexdigest()


class AuditLog:
    def __init__(self):
        self.events: list[Event] = []

    def append(self, actor: str, action: str, target: str, payload: Optional[dict] = None) -> Event:
        prev = self.events[-1].digest() if self.events else "0" * 64
        e = Event(
            seq=len(self.events), ts=time.time(),
            actor=actor, action=action, target=target,
            prev_hash=prev, payload=payload or {},
        )
        self.events.append(e)
        return e

    def verify(self) -> tuple[bool, int]:
        """Returns (ok, first_bad_seq)."""
        prev = "0" * 64
        for e in self.events:
            if e.prev_hash != prev:
                return False, e.seq
            prev = e.digest()
        return True, -1


if __name__ == "__main__":
    log = AuditLog()
    log.append("alice", "read", "row:42")
    log.append("alice", "edit", "row:42", {"field": "status"})
    log.append("bob",   "read", "row:42")
    ok, bad = log.verify()
    print(f"verify: ok={ok}, bad_seq={bad}, total={len(log.events)}")
