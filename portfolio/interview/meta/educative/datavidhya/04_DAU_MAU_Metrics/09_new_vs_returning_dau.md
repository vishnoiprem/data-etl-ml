# New vs Returning DAU

## Problem
For each day, separate DAU into new users (first event ever) and returning users.

## How to Think
1. Compute first_event_date per user (CTE).
2. Join events back; new = first_event_date = event_date, returning = first < event_date.

## How to Remember
- **Pattern**: "first_event_date = D -> new. first_event_date < D -> returning."
- Use MIN(event_date) to derive first_seen.

## SQL (Presto / Hive)
```sql
WITH first_seen AS (
  SELECT user_id, MIN(event_date) AS first_event_date FROM events GROUP BY user_id
)
SELECT e.event_date,
       COUNT(DISTINCT CASE WHEN f.first_event_date = e.event_date THEN e.user_id END) AS new_dau,
       COUNT(DISTINCT CASE WHEN f.first_event_date < e.event_date THEN e.user_id END) AS returning_dau
FROM events e JOIN first_seen f USING (user_id)
GROUP BY e.event_date ORDER BY e.event_date;
```

## Common Mistakes
- Using <= instead of < — counts the first day as both new and returning.
- Recomputing first_seen per event — performance disaster.

## AI Use Cases
- Acquisition-vs-retention dashboards.
- Marketing efficiency analysis.
- Feature onboarding targeting.
