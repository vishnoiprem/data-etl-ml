# Time-to-Convert Between Steps

## Problem
Compute average minutes between consecutive funnel events per user.

## How to Think
1. Pivot events so each row is a user with one column per step's timestamp.
2. Subtract timestamps, divide by 60.0 for minutes.
3. AVG() across users per pair.

## How to Remember
- **Pattern**: "Pivot -> subtract -> AVG."
- Pivot via MAX(CASE WHEN event_name = step THEN ts END) for SQL.

## SQL (Presto / Hive)
```sql
WITH pivoted AS (
  SELECT user_id,
         MAX(CASE WHEN event_name = 'impression'  THEN ts END) AS impression_ts,
         MAX(CASE WHEN event_name = 'click'       THEN ts END) AS click_ts,
         MAX(CASE WHEN event_name = 'add_to_cart' THEN ts END) AS cart_ts,
         MAX(CASE WHEN event_name = 'purchase'    THEN ts END) AS purchase_ts
  FROM events GROUP BY user_id
)
SELECT
  AVG(UNIX_TIMESTAMP(click_ts)    - UNIX_TIMESTAMP(impression_ts)) / 60.0 AS avg_min_impression_to_click,
  AVG(UNIX_TIMESTAMP(cart_ts)     - UNIX_TIMESTAMP(click_ts))      / 60.0 AS avg_min_click_to_cart,
  AVG(UNIX_TIMESTAMP(purchase_ts) - UNIX_TIMESTAMP(cart_ts))       / 60.0 AS avg_min_cart_to_purchase
FROM pivoted;
```

## Common Mistakes
- Computing deltas on raw events without pivoting — same user's multiple events cause duplicates.
- Casting strings without UNIX_TIMESTAMP — text math doesn't work.

## AI Use Cases
- Friction detection (slow steps).
- Real-time abandonment triggers.
- Latency features for ranking models.
