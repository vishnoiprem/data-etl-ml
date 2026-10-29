# Replay / Streaming Sessionization

## Problem
Process an unbounded Kafka stream of user events and emit sessionized output in real time. The system must handle late-arriving events, out-of-order timestamps, and replays from a specific offset.

## How to Think
1. Define a watermark on `event_ts` to bound how long the engine waits for late data.
2. Use `session_window(event_ts, "30 minutes")` to group events dynamically — Presto's `SESSION` and Spark Structured Streaming's `session_window` do this natively.
3. Aggregate per `(user_id, session_window)` for metrics.
4. Persist state via `update` output mode so already-emitted sessions can be updated when late events arrive.
5. For replay, reset the checkpoint directory and the source offset; the engine rebuilds session state from scratch.

## How to Remember
- **Pattern**: "watermark + session_window + stateful aggregation."
- `session_window` collapses events separated by less than the gap; it's the streaming equivalent of the cumsum flag.
- Without a watermark, state grows unbounded — always set one.
- Replay tip: copy the checkpoint to a new path so you don't trample production.

## SQL (Presto)
```sql
-- Flink-style in Presto via session window TVF
SELECT user_id,
       window_start,
       window_end,
       COUNT(*) AS event_count
FROM TABLE(
    SESSION(
        TABLE events,
        DESCRIPTOR(event_ts),
        INTERVAL '30' MINUTE
    )
)
GROUP BY user_id, window_start, window_end
ORDER BY window_start;
```

## Common Mistakes
- Forgetting `withWatermark` — state grows until OOM.
- Setting the watermark equal to the gap — late events inside the gap window are silently lost.
- Treating a session window as a tumbling window — it has variable length by definition.
- Mixing output modes (`append` vs `update`) without checking if late updates are acceptable.

## AI Use Cases
- Real-time recommender: feed the active session into a transformer that re-ranks every second.
- Live fraud detection: spike in session creation rate triggers an alert.
- Streaming dashboards: active sessions per second, session length histogram updated live.
