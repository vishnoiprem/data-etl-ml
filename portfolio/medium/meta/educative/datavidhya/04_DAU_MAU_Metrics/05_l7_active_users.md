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
   2026-01-08   7          8
   2026-01-30   1          5
```
Walk-through:
- `2026-01-08`, L7 window = `2026-01-02..2026-01-08` (DATEDIFF in [0,6]): users 1,3,4,5,6,7,8 = 7 distinct.
- `2026-01-08`, L28 window = `2025-12-12..2026-01-08` (DATEDIFF in [0,27]): every user has at least one event in this window = 8 distinct.
- `2026-01-30`, L7 window = `2026-01-24..2026-01-30`: only user 6 = 1 distinct.
- `2026-01-30`, L28 window = `2026-01-03..2026-01-30`: users 1 (Jan 8), 4 (Jan 9), 6 (Jan 30), 7 (Jan 8), 8 (Jan 9) = 5 distinct.

## Common Mistakes
- Off-by-one: L7 should be 7 days, including today — that's `D-6 .. D` (6 preceding + 1 current).
- Counting events instead of users.
- Using BETWEEN D-28 AND D — gives a 29-day window.

## AI Use Cases
- Reach metric for ad campaigns.
- Power-user targeting.
- Cohort feature for ranking.
