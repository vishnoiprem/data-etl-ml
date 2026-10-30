"""
Problem 01: Dedup events by (user_id, event_id) preserving first occurrence
Meta flavor: "Events from Facebook Pixel, Pixel CAPI, and Conversions API arrive
out-of-order. We must dedupe so re-running the job on the same window yields
the same row count and revenue."

How to Think:
- Idempotent dedup hinges on choosing a stable key. Two events are "the same" if
  they share (user_id, event_id). Order of arrival must not affect output.
- Use a dict keyed by (user_id, event_id). On insert, only set if absent. The
  first occurrence wins; later duplicates are silently dropped.
- This is O(n) time, O(n) space, and re-runs are safe by construction.

How to Remember:
- A seen-set keyed by business identity yields deterministic output regardless
  of source ordering or replay.

AI Use Cases
- Dedup of recommendation impressions, ad clicks, and conversions from
  overlapping tracking pixels.
"""
from __future__ import annotations
from typing import Iterable, Iterator
import json


def transform(events: Iterable[dict]) -> list[dict]:
    seen: dict[tuple, dict] = {}
    for ev in events:
        key = (ev.get("user_id"), ev.get("event_id"))
        if key not in seen:
            seen[key] = ev
    return list(seen.values())


if __name__ == "__main__":
    raw = [
        {"user_id": 1, "event_id": "e1", "amount": 10.0},
        {"user_id": 1, "event_id": "e1", "amount": 99.0},  # dup
        {"user_id": 2, "event_id": "e2", "amount": 5.0},
        {"user_id": 1, "event_id": "e3", "amount": 7.0},
        {"user_id": 2, "event_id": "e2", "amount": 5.0},  # dup
    ]
    out = transform(raw)
    print(json.dumps(out, indent=2))
    assert len(out) == 3
    print("DEDUP_OK")
