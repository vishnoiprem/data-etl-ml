# Resurrection Cohorts

## Problem
Identify "resurrected" users — those who churned for >= 30 days and came back.

## How to Think
1. Compute gap between consecutive active days per user (LAG + DATEDIFF).
2. MAX(gap) per user is the longest absence.
3. Resurrected = max_gap >= 30 AND user has activity after the gap.

## How to Remember
- **Pattern**: "Resurrected = max gap >= N days AND active after the gap."
- Define N explicitly (Meta usually uses 30 or 60).

## SQL (Presto / Hive)
```sql
WITH gaps AS (
  SELECT user_id, event_date,
         LAG(event_date) OVER (PARTITION BY user_id ORDER BY event_date) AS prev_event,
         DATEDIFF(event_date, LAG(event_date) OVER (PARTITION BY user_id ORDER BY event_date)) AS gap
  FROM activity
)
SELECT user_id,
       MAX(gap) AS max_gap,
       MAX(gap) >= 30 AS resurrected
FROM gaps
GROUP BY user_id;
```

## Common Mistakes
- Calling single-event users "resurrected" — they have no gap, so max_gap is NULL.
- Using >= vs > — pick one and stick to it.

## AI Use Cases
- Win-back campaign triggers.
- Churn-revival prediction model target.
- LTV recovery modeling.
