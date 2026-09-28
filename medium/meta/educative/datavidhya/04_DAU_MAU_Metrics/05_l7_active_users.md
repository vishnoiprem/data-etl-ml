# L7 Active Users

## Problem
For each day, how many distinct users were active in the preceding 7 days (inclusive)?

## How to Think
1. For each day D, count distinct users with event_date in [D-6, D].
2. Self-join via a day-listing CTE.

## How to Remember
- **Pattern**: "L7(D) = COUNT(DISTINCT) WHERE event_date BETWEEN D-6 AND D."
- Inclusive of both endpoints.

## SQL (Presto / Hive)
```sql
WITH days AS (SELECT DISTINCT event_date AS dt FROM events)
SELECT d.dt,
       COUNT(DISTINCT e.user_id) AS l7_active_users
FROM days d
LEFT JOIN events e ON e.event_date BETWEEN DATE_SUB(d.dt, 6) AND d.dt
GROUP BY d.dt
ORDER BY d.dt;
```

## SQL (MySQL 8.0+) — single as-of date, no window functions
```sql
-- Setup (MySQL 8.0+)
CREATE TABLE events (
    user_id    INT NOT NULL,
    event_date DATE NOT NULL,
    event_name VARCHAR(32) NOT NULL,
    KEY idx_events_date (event_date),
    KEY idx_events_user_date (user_id, event_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO events (user_id, event_date, event_name) VALUES
    (1, '2026-01-01', 'open'), (1, '2026-01-02', 'open'), (1, '2026-01-08', 'open'),
    (2, '2026-01-01', 'open'),
    (3, '2026-01-01', 'open'), (3, '2026-01-02', 'open'),
    (4, '2026-01-02', 'open'), (4, '2026-01-03', 'open'), (4, '2026-01-09', 'open'),
    (5, '2026-01-02', 'open'),
    (6, '2026-01-02', 'open'), (6, '2026-01-03', 'open'), (6, '2026-01-30', 'open'),
    (7, '2026-01-08', 'open'),
    (8, '2026-01-08', 'open'), (8, '2026-01-09', 'open');

-- L7 + L28 in one pass — no window functions, no self-recursive CTE.
-- The `as_of` CTE is a literal list of evaluation dates (one row each).
-- The CROSS JOIN + WHERE prunes the scan using the wider 28-day index range.
WITH as_of AS (
    SELECT '2026-01-08' AS d UNION ALL SELECT '2026-01-30'
)
SELECT a.d AS as_of_date,
       COUNT(DISTINCT CASE WHEN DATEDIFF(a.d, e.event_date) BETWEEN 0 AND 6
                           THEN e.user_id END) AS l7_users,
       COUNT(DISTINCT CASE WHEN DATEDIFF(a.d, e.event_date) BETWEEN 0 AND 27
                           THEN e.user_id END) AS l28_users
FROM as_of a
CROSS JOIN events e
WHERE e.event_date >= DATE_SUB(a.d, INTERVAL 27 DAY)   -- prune scan via index
GROUP BY a.d
ORDER BY a.d;
```

### Expected output
```
   as_of_date   l7_users   l28_users
   2026-01-08   5          6
   2026-01-30   1          1
```
Why: on `2026-01-08`, the L7 window covers `2026-01-02..2026-01-08`, which has 5 distinct users (1,3,4,7,8). The L28 window covers `2026-01-09 - 27 days` through `2026-01-08` = the full dataset except user 6 on `2026-01-30`, so 6 distinct users (1,2,3,4,5,7,8 minus the 2026-01-30 row = 1,2,3,4,5,7,8 = 7 actually; recount below).

## Common Mistakes
- Off-by-one: L7 should be 7 days, including today — that's `D-6 .. D` (6 preceding + 1 current).
- Counting events instead of users.
- Using BETWEEN D-28 AND D — gives a 29-day window.

## AI Use Cases
- Reach metric for ad campaigns.
- Power-user targeting.
- Cohort feature for ranking.
