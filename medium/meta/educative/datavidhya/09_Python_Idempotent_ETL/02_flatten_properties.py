"""
Problem 02: Flatten nested JSON properties dict, count per event_type per user per day
Meta flavor: "Aggregate raw Pixel + CAPI events into a daily per-user, per-action
counter for funnel analytics. Properties vary by event -- strip them out, but
keep the count per (user, event_type, day) stable across reruns."

How to Think:
- The nested `properties` dict contains pixel-level details. We must NOT use any
  of its keys in the group-by, or counts will drift between runs if upstream
  adds a new property.
- Group purely on (user_id, event_type, day). Flattening is a side effect to
  capture the raw payload if needed, not part of the dedup key.
- Sort outputs deterministically so diffing two reruns is trivial.

How to Remember:
- Derive counts from a key that does NOT depend on free-form JSON fields.

AI Use Cases
- Daily engagement metrics per user for ad attribution at Meta.
- Funnel stages for ad-creative A/B tests.
"""
from __future__ import annotations
from collections import defaultdict
from typing import Iterable


def _flatten(props: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in (props or {}).items():
        path = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(_flatten(v, path))
        else:
            out[path] = v
    return out


def transform(events: Iterable[dict]) -> list[dict]:
    counts: dict[tuple, dict] = defaultdict(lambda: {"count": 0, "sample_props": {}})
    for ev in events:
        day = (ev.get("ts") or "")[:10]
        key = (ev.get("user_id"), ev.get("event_type"), day)
        bucket = counts[key]
        bucket["count"] += 1
        flat = _flatten(ev.get("properties") or {})
        # keep the first flat props as a stable sample
        bucket.setdefault("sample_props", flat)
    out = []
    for (user_id, event_type, day), val in counts.items():
        out.append({
            "user_id": user_id,
            "event_type": event_type,
            "day": day,
            "count": val["count"],
        })
    out.sort(key=lambda r: (r["day"], r["user_id"], r["event_type"]))
    return out


if __name__ == "__main__":
    events = [
        {"user_id": 1, "event_type": "click", "ts": "2026-01-01T10:00",
         "properties": {"ad_id": "a1", "meta": {"placement": "feed"}}},
        {"user_id": 1, "event_type": "click", "ts": "2026-01-01T18:30",
         "properties": {"ad_id": "a2"}},
        {"user_id": 1, "event_type": "purchase", "ts": "2026-01-01T20:00",
         "properties": {"value": 9.99}},
        {"user_id": 2, "event_type": "click", "ts": "2026-01-02T09:00",
         "properties": {"ad_id": "a1"}},
    ]
    for row in transform(events):
        print(row)
