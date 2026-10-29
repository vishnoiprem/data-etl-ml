# Dedup events by (user_id, event_id) preserving first occurrence

## Problem
You receive a stream of events from upstream sources (Facebook Pixel, CAPI, etc.).
The same logical event may arrive more than once (retries, partial failures,
parallel writers). Your ETL must drop duplicates while keeping the first
occurrence, and re-running the job on the same input must produce the same
output.

## How to Think
1. Pick a stable business identity. Here: `(user_id, event_id)`.
2. Iterate once. For each event, compute the key.
3. If the key is unseen, store it; otherwise skip.
4. Returning the dict's values preserves insertion order, i.e. first occurrence.

## How to Remember
- **Pattern**: "dict by key wins" -- `seen[key] = seen.get(key) or ev`
- Idempotency = same input -> same output, regardless of run count.
- Order of arrival must not affect output: rely on a deterministic key set.

## Code (Python)
```python
def transform(events):
    seen = {}
    for ev in events:
        key = (ev.get("user_id"), ev.get("event_id"))
        if key not in seen:
            seen[key] = ev
    return list(seen.values())
```

## Common Mistakes
- Hashing on `ts` or other mutable attributes that change across retries.
- Using a list and scanning on each insert -> O(n^2).
- Dropping by index without a stable key -- re-runs behave differently.
- Forgetting that None values in `user_id` collide on the same missing slot.

## AI Use Cases
- Dedup of recommendation impressions, ad clicks, and conversions from
  overlapping tracking pixels at Meta.
- Building training datasets from multi-source event logs without label leakage.
- Joining click streams with action streams where the same row may show up
  twice on retry.
