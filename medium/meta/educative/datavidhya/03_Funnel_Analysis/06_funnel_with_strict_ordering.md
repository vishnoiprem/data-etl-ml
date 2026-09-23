# Funnel With Strict Ordering (Step1 -> Step2 -> Step3 in Order)

## Problem
Count distinct users who performed step 1, step 2, and step 3 in **strict
temporal order**. Out-of-order events (e.g., verify before signup due to clock
skew) must not count.

## How to Think
1. First reduce to the **first** occurrence of each step per user using
   `ROW_NUMBER() OVER (PARTITION BY user_id, event_name ORDER BY event_ts)`.
2. Self-join steps 1 -> 2 -> 3 with `b.ts > a.ts` constraints.
3. Be explicit about which side is the "earliest" timestamp.
4. Prefer server-side timestamps (`event_received_ts`) for production; client
   clocks get skewed on mobile.
5. Document the ordering assumption -- it changes the funnel number materially.

## How to Remember
- **Pattern**: "ROW_NUMBER -> self-join with > conditions."
- **Anti-pattern**: `INNER JOIN` without timestamp guards.
- **Watch out**: clock skew produces "ghost users" without strict ordering.

## SQL (Presto / Hive)
```sql
WITH first_ts AS (
  SELECT user_id, event_name, event_ts,
         ROW_NUMBER() OVER (PARTITION BY user_id, event_name
                            ORDER BY event_ts) AS rn
  FROM events
  WHERE event_date = CURRENT_DATE
)
SELECT COUNT(DISTINCT t1.user_id) AS strict_funnel_users
FROM (SELECT user_id, event_ts FROM first_ts
      WHERE rn = 1 AND event_name = 'step1') t1
JOIN (SELECT user_id, event_ts FROM first_ts
      WHERE rn = 1 AND event_name = 'step2') t2
  ON t1.user_id = t2.user_id AND t2.event_ts > t1.event_ts
JOIN (SELECT user_id, event_ts FROM first_ts
      WHERE rn = 1 AND event_name = 'step3') t3
  ON t1.user_id = t3.user_id AND t3.event_ts > t2.event_ts;
```

## Common Mistakes
- Skipping `ROW_NUMBER` -- joining raw events double-counts.
- Using `ts1 < ts2 < ts3` in WHERE on joined columns can produce wrong rows in
  engines without short-circuit semantics.
- Confusing "first event" with "any event" -- strict ordering needs first.

## AI Use Cases
- **Causal inference**: ordered transitions are valid counterfactual samples.
- **Sequential recommenders**: causal attention masks rely on strict order.
- **Graph neural networks over user journeys**: edges are timestamped for valid propagation.
- **Marketing-ML uplift modeling**: strict ordering restricts the eligible treated population.
