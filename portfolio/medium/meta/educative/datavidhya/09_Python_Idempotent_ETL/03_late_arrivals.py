"""
Problem 03: Late-arriving events handled within a 7-day grace window
Meta flavor: "Pixel events can be delayed up to 7 days (mobile offline queues).
Our daily partitions must accept late events for `event_date` in the past 7
days and silently ignore anything older -- otherwise counts get inflated and
backfilled counts cannot be reconciled."

How to Think:
- Two dates matter: `event_date` (when it happened) and `ingest_date` (when we
  saw it). Late events have `event_date < ingest_date`.
- The grace window is `[ingest_date - 7 days, ingest_date]`. Anything earlier
  is rejected and reported.
- Use a daily partition directory per `event_date`. Replays, retries, and
  late deliveries all coalesce into the correct partition.

How to Remember:
- Logic lives in the window check, not in the row identity. The same row may
  arrive tomorrow, and must land in the same partition.

AI Use Cases
- Backfilling Meta Pixel and CAPI conversions while keeping daily revenue in
  sync with what we reported earlier.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Iterable


@dataclass
class LateStats:
    accepted: list[dict] = field(default_factory=list)
    rejected: list[dict] = field(default_factory=list)


def _to_date(s: str) -> date:
    return datetime.strptime(s[:10], "%Y-%m-%d").date()


def transform(events: Iterable[dict], ingest_date: str,
              grace_days: int = 7) -> LateStats:
    in_day = _to_date(ingest_date)
    floor = in_day - timedelta(days=grace_days)
    stats = LateStats()
    for ev in events:
        edate = _to_date(ev["event_date"])
        if edate > in_day:
            stats.rejected.append(ev)  # future-dated, suspicious
        elif edate < floor:
            stats.rejected.append(ev)  # too late
        else:
            stats.accepted.append({
                "event_id": ev["event_id"],
                "event_date": edate.isoformat(),
                "user_id": ev.get("user_id"),
            })
    stats.accepted.sort(key=lambda r: (r["event_date"], r["event_id"]))
    return stats


if __name__ == "__main__":
    raw = [
        {"event_id": "a", "event_date": "2026-01-09", "user_id": 1},  # inside
        {"event_id": "b", "event_date": "2026-01-05", "user_id": 2},  # inside
        {"event_id": "c", "event_date": "2026-01-01", "user_id": 3},  # too old
        {"event_id": "d", "event_date": "2026-01-15", "user_id": 4},  # future
    ]
    out = transform(raw, ingest_date="2026-01-10")
    print("accepted:", out.accepted)
    print("rejected:", len(out.rejected), "rows")
