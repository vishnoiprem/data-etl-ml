# Schema-evolution-safe parsing (extra keys ignored, missing keys -> None)

## Problem
Upstream payloads change shape over time: new keys are added, old keys are
removed. The ETL must produce a fixed-shape downstream table so that
re-running the job on any payload version yields rows with the same columns.
Unknown keys are dropped; missing keys become NULL.

## How to Think
1. Define the output schema explicitly (a dataclass, a TypedDict, or a list of
   column names).
2. For each input row, project ONLY the known fields. Ignore anything else.
3. Coerce types defensively (numbers, dates). On failure, treat as None and
   log; do not crash.
4. The transform becomes `input row x known schema -> output row`. Pure
   function. Replays are safe.

## How to Remember
- **Pattern**: "project to a known field set; treat source as untrusted"
- Idempotency = same input -> same output, regardless of run count.
- Output schema lives in YOUR code, not in the source payload.

## Code (Python)
```python
from dataclasses import dataclass, asdict, fields

@dataclass(frozen=True)
class EventRow:
    user_id: str | None = None
    event_id: str | None = None
    event_type: str | None = None

def transform(events):
    out = []
    for ev in events:
        kwargs = {f.name: ev.get(f.name) for f in fields(EventRow)}
        out.append(asdict(EventRow(**kwargs)))
    return out
```

## Common Mistakes
- Iterating the source dict's keys into the output -- schema follows upstream.
- Letting `KeyError` propagate on missing fields.
- Hard-coercing values (`int(x)`) instead of failing soft to None.
- Embedding version logic inside the transform -- it will silently leak.

## AI Use Cases
- Stable ingestion of evolving Meta Pixel and CAPI payloads.
- Forward-compatible feature-store pipelines for ranking/recommendation models.
- A/B experiment pipelines where treatment metadata shifts across tests.
