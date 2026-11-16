"""Snapshots: a recorded pull of AWS data, on disk.

A snapshot is what makes an AWS analysis reproducible and reviewable.
It is a JSON file holding the normalised records plus the metadata
needed to interpret them — which region, which window, which group
definitions, which periods were estimated, and which errors the
normalizer recorded.

Two kinds of snapshot live here:

``cost_records``
    The normalised Cost Explorer output. This is what the detectors
    read.

``raw_payload``
    The untouched AWS response, kept so a normalizer change can be
    re-run against the same source without another AWS call.

Snapshots are written to ``data/snapshots/``, which is git-ignored by
default — a snapshot can contain account identifiers. The *fixtures*
under ``tests/fixtures/`` are the ones meant to be tracked: they are
recorded AWS responses, not live account data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .models import CostRecord

#: The default snapshot directory, relative to the project root.
DEFAULT_SNAPSHOT_DIR = Path("data/snapshots")

#: The snapshot kinds this module knows about.
KIND_COST_RECORDS = "cost_records"
KIND_RAW_PAYLOAD = "raw_payload"

SNAPSHOT_VERSION = 1


@dataclass(slots=True)
class Snapshot:
    """One recorded pull."""

    kind: str
    region: str
    start: str
    end: str
    granularity: str
    group_definitions: list[dict[str, str]] = field(default_factory=list)
    records: list[CostRecord] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    periods_seen: list[str] = field(default_factory=list)
    estimated_periods: list[str] = field(default_factory=list)
    raw: dict[str, Any] | None = None
    taken_at: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "snapshot_version": SNAPSHOT_VERSION,
            "kind": self.kind,
            "region": self.region,
            "start": self.start,
            "end": self.end,
            "granularity": self.granularity,
            "group_definitions": self.group_definitions,
            "records": [r.to_dict() for r in self.records],
            "errors": list(self.errors),
            "periods_seen": list(self.periods_seen),
            "estimated_periods": list(self.estimated_periods),
            "taken_at": self.taken_at or _now(),
        }
        if self.notes:
            payload["notes"] = self.notes
        if self.raw is not None:
            payload["raw"] = self.raw
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Snapshot:
        return cls(
            kind=data.get("kind", KIND_COST_RECORDS),
            region=data.get("region", ""),
            start=data.get("start", ""),
            end=data.get("end", ""),
            granularity=data.get("granularity", "MONTHLY"),
            group_definitions=list(data.get("group_definitions", [])),
            records=[CostRecord.from_dict(r) for r in data.get("records", [])],
            errors=list(data.get("errors", [])),
            periods_seen=list(data.get("periods_seen", [])),
            estimated_periods=list(data.get("estimated_periods", [])),
            raw=data.get("raw"),
            taken_at=data.get("taken_at", ""),
            notes=data.get("notes", ""),
        )

    @property
    def complete_records(self) -> list[CostRecord]:
        """Only the records covering a whole, non-estimated month.

        An incomplete or estimated period is excluded *entirely* —
        never divided, never compared. Comparing a projected month
        against a settled one manufactures a growth finding that does
        not exist.
        """
        return [
            r
            for r in self.records
            if r.is_complete_month and not r.estimated and r.period_label not in self.estimated_periods
        ]

    @property
    def excluded_periods(self) -> list[str]:
        """The periods that were excluded, so the report can name them."""
        excluded: list[str] = []
        for label in self.periods_seen:
            if label in self.estimated_periods:
                excluded.append(label)
                continue
            records = [r for r in self.records if r.period_label == label]
            if records and not all(r.is_complete_month for r in records):
                excluded.append(label)
        return excluded


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_snapshot(snapshot: Snapshot, directory: Path | str = DEFAULT_SNAPSHOT_DIR) -> Path:
    """Write a snapshot to disk and return its path."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    stamp = snapshot.taken_at or _now()
    safe_stamp = stamp.replace(":", "").replace("-", "")
    name = f"{snapshot.kind}_{snapshot.region}_{snapshot.start}_{snapshot.end}_{safe_stamp}.json"
    path = directory / name

    path.write_text(json.dumps(snapshot.to_dict(), indent=2, sort_keys=True))
    return path


def read_snapshot(path: Path | str) -> Snapshot:
    """Read a snapshot back."""
    data = json.loads(Path(path).read_text())
    return Snapshot.from_dict(data)


def list_snapshots(directory: Path | str = DEFAULT_SNAPSHOT_DIR) -> list[Path]:
    """Every snapshot in a directory, newest first."""
    directory = Path(directory)
    if not directory.exists():
        return []
    return sorted(directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


def latest_snapshot(
    directory: Path | str = DEFAULT_SNAPSHOT_DIR,
    kind: str | None = None,
) -> Snapshot | None:
    """The most recent snapshot, optionally of one kind."""
    for path in list_snapshots(directory):
        snapshot = read_snapshot(path)
        if kind is None or snapshot.kind == kind:
            return snapshot
    return None


def snapshot_from_result(
    result,
    *,
    kind: str = KIND_COST_RECORDS,
    region: str = "",
    start: str = "",
    end: str = "",
    granularity: str = "MONTHLY",
    group_definitions: list[dict[str, str]] | None = None,
    raw: dict[str, Any] | None = None,
    notes: str = "",
) -> Snapshot:
    """Build a snapshot from a normalizer result."""
    return Snapshot(
        kind=kind,
        region=region,
        start=start,
        end=end,
        granularity=granularity,
        group_definitions=list(group_definitions or []),
        records=list(result.records),
        errors=list(result.errors),
        periods_seen=list(result.periods_seen),
        estimated_periods=list(result.estimated_periods),
        raw=raw,
        notes=notes,
    )


def snapshot_label(snapshot: Snapshot) -> str:
    """A one-line label for a snapshot."""
    return (
        f"{snapshot.region} {snapshot.start}..{snapshot.end} "
        f"({snapshot.granularity}, {len(snapshot.records)} records, "
        f"taken {snapshot.taken_at or 'unknown'})"
    )


def period_range(start: str, end: str) -> list[str]:
    """The month labels between two dates, inclusive of both.

    Used to report which months a window was *supposed* to cover, so a
    missing month is visible as a gap rather than as silence.
    """
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    labels: list[str] = []
    year, month = start_date.year, start_date.month
    while (year, month) <= (end_date.year, end_date.month):
        labels.append(f"{year:04d}-{month:02d}")
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1
    return labels
