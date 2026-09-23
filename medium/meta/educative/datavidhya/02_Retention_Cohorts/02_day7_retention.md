# Day-7 Retention (D7)

## Problem
Of users who signed up, what % were active exactly 7 days after signup?

## How to Think
1. Same skeleton as D1; the day offset is 7.
2. Alternative: `DATEDIFF(event_date, signup_date) = 7` — same result for calendar-day math.
3. For a "week-wide" window use BETWEEN 7 AND 13.

## How to Remember
- **Pattern**: "D7 = activity on signup_date + 7."
- Use DATE_ADD or DATEDIFF consistently.

## SQL (Presto / Hive)
```sql
SELECT s.signup_date,
       COUNT(DISTINCT s.user_id) AS cohort_size,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 7)
                           THEN s.user_id END) AS retained_d7,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 7)
                           THEN s.user_id END) * 1.0 / COUNT(DISTINCT s.user_id) AS d7_retention
FROM signups s
LEFT JOIN activity a USING (user_id)
GROUP BY s.signup_date;
```

## Common Mistakes
- Off-by-one: DATE_ADD adds 7 days; the new date is signup + 7, not signup + 6.
- Using timestamp math with calendar dates — TZ shifts change the result.

## AI Use Cases
- Cohort performance tracking.
- New product feature ramp-up monitoring.
- Lifecycle stage classification (new / active / dormant).
