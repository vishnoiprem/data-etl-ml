# Funnel by User Segment (New vs Returning)

## Problem
Compute funnel counts split by user segment.

## How to Think
1. Derive the segment attribute once (CTE with first_event_date + DATEDIFF).
2. Join events with the segments table.
3. GROUP BY segment, pivot the same as a regular funnel.

## How to Remember
- **Pattern**: "Add segment to GROUP BY -> funnel per segment."
- Segments must be derived per user first; don't compute them inline per event.

## SQL (Presto / Hive)
```sql
WITH user_first AS (
  SELECT user_id, MIN(event_date) AS first_event_date FROM events GROUP BY user_id
),
segments AS (
  SELECT user_id, first_event_date,
         CASE WHEN DATEDIFF(CAST('2026-01-02' AS DATE), first_event_date) <= 30
              THEN 'returning' ELSE 'lapsed' END AS user_segment
  FROM user_first
)
SELECT s.user_segment,
       COUNT(DISTINCT CASE WHEN e.event_name = 'impression' THEN e.user_id END) AS impressions,
       COUNT(DISTINCT CASE WHEN e.event_name = 'click'      THEN e.user_id END) AS clicks
FROM events e
JOIN segments s USING (user_id)
GROUP BY s.user_segment;
```

## Common Mistakes
- Computing segment inside COUNT(DISTINCT CASE WHEN …) — performance disaster (per-row lookup).
- Hardcoding "now" — use a parameter so backfills match.

## AI Use Cases
- Comparing new vs power-user conversion.
- Personalization opportunity sizing.
- Segment-targeted feature rollout evaluation.
