# Classic 4-Step Funnel

## Problem
Count distinct users at each funnel step on a single date.

## How to Think
1. Each step is an event_name in the events table.
2. COUNT(DISTINCT user_id) per step, pivoted via CASE WHEN.
3. No ordering constraints here — each step is independent.

## How to Remember
- **Pattern**: "One row, COUNT(DISTINCT) pivoted by step."
- Use COUNT(DISTINCT) — same user, multiple events must not inflate counts.

## SQL (Presto / Hive)
```sql
SELECT
  COUNT(DISTINCT CASE WHEN event_name = 'impression'   THEN user_id END) AS step1_impression,
  COUNT(DISTINCT CASE WHEN event_name = 'click'        THEN user_id END) AS step2_click,
  COUNT(DISTINCT CASE WHEN event_name = 'add_to_cart'  THEN user_id END) AS step3_add_to_cart,
  COUNT(DISTINCT CASE WHEN event_name = 'purchase'     THEN user_id END) AS step4_purchase
FROM events;
```

## Common Mistakes
- Counting event rows instead of distinct users — over-counts active users.
- Forgetting the date filter when computing a daily funnel.

## AI Use Cases
- Conversion optimization at each funnel step.
- Drop-off point identification for product teams.
- Funnel features for downstream ML models.
