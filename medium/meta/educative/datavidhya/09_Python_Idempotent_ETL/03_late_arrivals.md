# Late-arriving events handled within a 7-day grace window

## Problem
Pixel events record `event_date` and arrive later than they occurred (mobile
offline buffers, CAPI retries). Your daily partitions must accept events for
the past 7 days based on `ingest_date` and reject anything older. The job must
remain idempotent: re-processing the same late deliveries produces the same
output.

## How to Think
1. Two timestamps matter: `event_date` (when it happened) and `ingest_date`
   (when we are processing). They are usually different.
2. Define the grace window: `[ingest_date - 7, ingest_date]`. Outside -> reject.
3. Route each accepted event into the partition keyed by `event_date`, not
   `ingest_date`. This makes late events naturally co-located with the rest of
   that day's data.
4. Future-dated events (`event_date > ingest_date`) are suspicious and should
   land in a quarantine bucket or be rejected outright.

## How to Remember
- **Pattern**: "partition by event_date, gate by ingest_date window"
- Idempotency = same input -> same output, regardless of run count.
- The grace window is a property of the runtime, never a property of the row.

## Code (Python)
```python
from datetime import date, timedelta

def in_window(event_date, ingest_date, grace_days=7):
    floor = ingest_date - timedelta(days=grace_days)
    return floor <= event_date <= ingest_date
```

## Common Mistakes
- Partitioning by `ingest_date` -- late events end up in the wrong day.
- Hard-coding "7 days" inside the row, so each run computes its own window.
- Accepting future-dated events (clock skew, malicious clients).
- Mutating `event_date` for "normalization", losing debugging info.

## AI Use Cases
- Backfilling Meta Pixel/CAPI conversions while reconciling with daily revenue
  reports.
- Reconciliation of late-arriving training labels for ranking models.
- Adjusting anomaly detection windows so noisy late data does not trigger
  alerts.
