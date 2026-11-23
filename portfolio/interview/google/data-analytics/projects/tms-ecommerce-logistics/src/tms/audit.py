"""The audit ledger: a durable record of every decision the system made.

**Why a JSONL ledger.** A TMS makes decisions that a merchant will
eventually dispute: why was this parcel held, why was this route ordered
that way, why was this order blocked. When the dispute comes, the answer
has to be reconstructable — and reconstructing it from live state is
impossible, because the state has moved on.

JSONL specifically, rather than JSON, because it is append-only and
streamable: a ledger that can be tailed, grepped, and shipped to a log
aggregator without a database. Each line is one self-contained decision.

Sub-parts
---------
- :class:`AuditLedger` — the append-only store.
- :func:`write_ledger` — flush to a JSONL file.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class Decision:
    """One recorded decision."""

    decision_id: str
    decided_at: datetime
    kind: str
    subject_id: str
    outcome: str
    rationale: str
    detail: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """A JSON-friendly view."""
        return {
            "decision_id": self.decision_id,
            "decided_at": self.decided_at.isoformat(),
            "kind": self.kind,
            "subject_id": self.subject_id,
            "outcome": self.outcome,
            "rationale": self.rationale,
            "detail": self.detail,
        }


@dataclass(slots=True)
class AuditLedger:
    """An append-only ledger of decisions."""

    decisions: list[Decision] = field(default_factory=list)
    _seq: int = 0

    def record(
        self,
        kind: str,
        subject_id: str,
        outcome: str,
        rationale: str,
        decided_at: datetime | None = None,
        detail: dict[str, Any] | None = None,
    ) -> Decision:
        """Append one decision and return it."""
        self._seq += 1
        decision = Decision(
            decision_id=f"dec-{self._seq:06d}",
            decided_at=decided_at or datetime.now(timezone.utc),
            kind=kind,
            subject_id=subject_id,
            outcome=outcome,
            rationale=rationale,
            detail=detail or {},
        )
        self.decisions.append(decision)
        return decision

    def by_kind(self, kind: str) -> list[Decision]:
        """All decisions of one kind."""
        return [d for d in self.decisions if d.kind == kind]

    def summary(self) -> dict[str, Any]:
        """Aggregate counts by kind and outcome."""
        by_kind: dict[str, int] = {}
        by_outcome: dict[str, int] = {}
        for decision in self.decisions:
            by_kind[decision.kind] = by_kind.get(decision.kind, 0) + 1
            by_outcome[decision.outcome] = by_outcome.get(decision.outcome, 0) + 1
        return {
            "total": len(self.decisions),
            "by_kind": by_kind,
            "by_outcome": by_outcome,
        }


def write_ledger(ledger: AuditLedger, path: Path) -> Path:
    """Flush the ledger to a JSONL file.

    One decision per line, so the file can be appended to, tailed, or
    streamed into an aggregator without parsing the whole thing.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for decision in ledger.decisions:
            handle.write(json.dumps(decision.as_dict(), sort_keys=True) + "\n")
    return path


def read_ledger(path: Path) -> list[dict[str, Any]]:
    """Read a JSONL ledger back into a list of dicts."""
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows
