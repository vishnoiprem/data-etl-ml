# Flatten nested JSON properties dict, count per event_type per user per day

## Problem
Events arrive with a nested `properties` blob (e.g. `properties.meta.placement`).
You want a daily aggregate: count per `(user_id, event_type, day)`. Properties
have no schema guarantees -- new keys appear often. Output must be the same on
re-runs.

## How to Think
1. Decide the group-by identity BEFORE looking at properties.
   Here: `(user_id, event_type, day)` from the top-level fields only.
2. Flatten properties recursively into dotted keys for downstream debugging but
   do not include them in counts.
3. Use a `defaultdict` keyed by the group tuple; sort by the same tuple at the
   end so the output is byte-stable.
4. First-write-wins for any "sample" field you carry alongside counts to keep
   output deterministic.

## How to Remember
- **Pattern**: "key by stable fields, ignore the rest"
- Idempotency = same input -> same output, regardless of run count.
- Sort the final list so reruns produce identical bytes for diffing.

## Code (Python)
```python
def transform(events):
    counts = {}
    for ev in events:
        day = (ev.get("ts") or "")[:10]
        key = (ev.get("user_id"), ev.get("event_type"), day)
        counts[key] = counts.get(key, 0) + 1
    out = [
        {"user_id": u, "event_type": et, "day": d, "count": c}
        for (u, et, d), c in counts.items()
    ]
    out.sort(key=lambda r: (r["day"], r["user_id"], r["event_type"]))
    return out
```

## Common Mistakes
- Including any property field in the group-by key (e.g. `properties.value`).
  Counts will diverge across runs as properties vary.
- Forgetting to coerce `ts` -- a missing timestamp makes two rows collide.
- Producing output as a dict whose insertion order depends on input order;
  always sort or use OrderedDict.
- Recursing on a deeply nested value without a depth guard (stack overflows).

## AI Use Cases
- Daily per-user engagement metrics for ad attribution at Meta.
- Funnel analytics and creative A/B evaluation.
- Aggregating MAI (Meta AI) conversation logs into per-user, per-intent counts.
