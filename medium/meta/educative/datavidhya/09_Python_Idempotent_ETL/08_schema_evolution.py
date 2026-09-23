"""
Problem 08: Schema-evolution-safe parsing (extra keys ignored, missing keys -> None)
Meta flavor: "Schema for a Pixel payload changes every few weeks: new fields
appear, deprecated fields disappear. The same ETL must keep producing the
same downstream table shape regardless of payload version."

How to Think:
- The pipeline's contract is the set of known fields. Anything beyond is
  ignored; anything missing becomes None. Output schema is fixed.
- This makes the transform a pure function of `(row, known_fields)`.
- Document the field set explicitly; never iterate raw dict keys into the
  output.
- The transform is then a projection, not a passthrough.

How to Remember:
- Project to a known field set; treat the source as untrusted.

AI Use Cases
- Stable ingestion of evolving event payloads from Meta Pixel and Conversions
  API.
- Forward-compatible ETL for AI feature stores.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, fields
from typing import Iterable


@dataclass(frozen=True)
class EventRow:
    user_id: str | None = None
    event_id: str | None = None
    event_type: str | None = None
    event_date: str | None = None
    value: float | None = None


def _coerce(field_name: str, value):
    if value is None:
        return None
    if field_name == "value":
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    if field_name in ("user_id", "event_id", "event_type", "event_date"):
        return str(value)
    return value


def transform(events: Iterable[dict]) -> list[dict]:
    out = []
    for ev in events:
        kwargs = {}
        for f in fields(EventRow):
            kwargs[f.name] = _coerce(f.name, ev.get(f.name))
        out.append(asdict(EventRow(**kwargs)))
    return out


if __name__ == "__main__":
    rows = [
        {"user_id": "u1", "event_id": "e1", "event_type": "click",
         "event_date": "2026-01-05", "value": "9.99",
         "extra_brand_new_field": "ignored"},
        {"user_id": "u2", "event_id": "e2"},  # missing most fields
        {"user_id": "u3", "event_id": "e3", "value": "NaN-bad"},
    ]
    for r in transform(rows):
        print(r)
