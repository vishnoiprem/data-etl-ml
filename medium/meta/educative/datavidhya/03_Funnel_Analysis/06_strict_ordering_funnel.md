# Strict Ordering Funnel

## Problem
Count users who reached each step in strict chronological order.

## How to Think
1. For each user, MIN(timestamp) per step.
2. Reached step k in order: previous_step_ts IS NOT NULL AND current_step_ts > previous_step_ts.
3. Aggregate COUNT over per-user table.

## How to Remember
- **Pattern**: "MIN(step_ts) > MIN(prev_step_ts) -> ordered."
- Per-user MIN forces a single decision per user.

## SQL (Presto / Hive)
```sql
WITH per_user AS (
  SELECT user_id,
         MIN(CASE WHEN event_name = 'impression' THEN ts END) AS impression_ts,
         MIN(CASE WHEN event_name = 'click'      THEN ts END) AS click_ts,
         MIN(CASE WHEN event_name = 'purchase'   THEN ts END) AS purchase_ts
  FROM events GROUP BY user_id
)
SELECT
  COUNT(CASE WHEN impression_ts IS NOT NULL THEN 1 END) AS reached_impression,
  COUNT(CASE WHEN click_ts > impression_ts THEN 1 END) AS reached_click_in_order,
  COUNT(CASE WHEN purchase_ts > click_ts AND click_ts > impression_ts THEN 1 END) AS reached_purchase_in_order
FROM per_user;
```

## Common Mistakes
- Counting strict-order as "any user with all events" — ignores ordering.
- Using MAX instead of MIN — captures the LAST occurrence, not the first.

## AI Use Cases
- Attribution modeling (last-click vs first-click).
- Path-aware conversion analysis.
- Sequential recommender evaluation.
