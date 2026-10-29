# Funnel With Array of Events (Presto `array_agg` Approach)

## Problem
Compute a multi-step funnel where each user's events are represented as a
single sorted array, then check for ordered step presence using array
positions. This is faster than N self-joins on Presto/Hive at scale.

## How to Think
1. Reduce to one row per user via `array_agg(event_name ORDER BY event_ts)`.
2. Use `array_position(arr, step)` to get the (first) index of each step.
3. For strict ordering, verify `pos(step_N) > pos(step_(N-1))`.
4. This avoids N self-joins and works on columnar engines with vectorized
   array ops -- order-of-magnitude faster on large fact tables.
5. Be careful with ties on `event_ts` -- add a tie-breaker column to keep order deterministic.

## How to Remember
- **Pattern**: "array_agg -> array_position -> ordered comparison."
- **Anti-pattern**: nested self-joins for 4+ steps -- exponential join fan-out.
- **Watch out**: `array_position` returns 1-based index; NULL means missing.

## SQL (Presto / Hive)
```sql
WITH user_arr AS (
  SELECT user_id,
         array_agg(event_name ORDER BY event_ts) AS events
  FROM events
  WHERE event_date = CURRENT_DATE
  GROUP BY user_id
)
SELECT COUNT(DISTINCT user_id) AS users
FROM user_arr
WHERE array_position(events,'impression')  IS NOT NULL
  AND array_position(events,'click')       > array_position(events,'impression')
  AND array_position(events,'add_to_cart') > array_position(events,'click')
  AND array_position(events,'purchase')    > array_position(events,'add_to_cart');
```

## Common Mistakes
- Forgetting to break ties on timestamp -- arrays with duplicate ts are non-deterministic.
- Confusing `array_position` (returns 1-based) with array index (0-based).
- Using `IN` instead of `array_position` -- cannot enforce ordering.

## AI Use Cases
- **Sequence models**: arrays are direct training tokens for RNNs / Transformers.
- **User-journey embeddings**: skip-gram over event arrays learns step analogies.
- **RAG over user history**: array of events becomes retrieval context.
- **Streaming features**: arrays are emitted as a single Avro/Parquet column for downstream joins.
