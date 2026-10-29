# DAU by Surface

## Problem
For each day and surface (News Feed, Reels, Stories, Marketplace), count distinct active users.

## How to Think
1. Each event carries a surface attribute.
2. GROUP BY (event_date, surface).
3. COUNT(DISTINCT user_id) per group.

## How to Remember
- **Pattern**: "GROUP BY (dt, surface), COUNT(DISTINCT user_id)."
- A user active in two surfaces counts in BOTH.

## SQL (Presto / Hive)
```sql
SELECT event_date, surface, COUNT(DISTINCT user_id) AS dau
FROM events
GROUP BY event_date, surface
ORDER BY event_date, surface;
```

## Common Mistakes
- Treating surface as nullable — events without surface get dropped or aggregated weirdly.
- Forgetting that DAU per surface != overall DAU.

## AI Use Cases
- Product-area engagement comparison.
- Surface-level growth attribution.
- Re-allocation of dev effort.
