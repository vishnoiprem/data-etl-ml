# Retention by Acquisition Channel

## Problem
D7 retention segmented by signup_channel (organic vs paid).

## How to Think
1. signup_channel lives on the user / signup event.
2. GROUP BY (signup_date, signup_channel) for cohort-level breakdown.
3. Same CASE WHEN logic as D1/D7 — just one extra dimension.

## How to Remember
- **Pattern**: "GROUP BY (cohort_date, cohort_attr) -> retention per segment."
- Compare channels side-by-side.

## SQL (Presto / Hive)
```sql
SELECT s.signup_date,
       s.signup_channel,
       COUNT(DISTINCT s.user_id) AS cohort_size,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 7) THEN s.user_id END) AS retained_d7,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 7) THEN s.user_id END) * 1.0
         / COUNT(DISTINCT s.user_id) AS d7_retention
FROM signups s
LEFT JOIN activity a USING (user_id)
GROUP BY s.signup_date, s.signup_channel
ORDER BY 1, 2;
```

## Common Mistakes
- Forgetting to segment by channel — overall retention hides channel differences.
- Comparing channels with mismatched cohort sizes — small cohorts noisy.

## AI Use Cases
- Marketing attribution + retention modeling.
- Channel ROI computation (CAC vs LTV).
- Incrementality / uplift features for bidding.
