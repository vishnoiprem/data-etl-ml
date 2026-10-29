# L28 Active Users

## Problem
For each day, how many distinct users were active in the preceding 28 days (inclusive)?

## How to Think
1. For each day D, count distinct users with event_date in [D-27, D].
2. Self-join via a day-listing CTE.

## How to Remember
- **Pattern**: "L28(D) = COUNT(DISTINCT) WHERE event_date BETWEEN D-27 AND D."
- 28 = D-27 + current.

## SQL (Presto / Hive)
```sql
WITH days AS (SELECT DISTINCT event_date AS dt FROM events)
SELECT d.dt,
       COUNT(DISTINCT e.user_id) AS l28_active_users
FROM days d
LEFT JOIN events e ON e.event_date BETWEEN DATE_SUB(d.dt, 27) AND d.dt
GROUP BY d.dt
ORDER BY d.dt;
```

## SQL (MySQL 8.0+) — no window functions
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

-- L28 + L7 in one pass. The `as_of` CTE is a literal date list (one row
-- per evaluation date). The CROSS JOIN + WHERE prunes the scan via the
-- (event_date) index — only the L28 window is read per as_of date.
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
WHERE e.event_date >= DATE_SUB(a.d, INTERVAL 27 DAY)
GROUP BY a.d
ORDER BY a.d;
```

### Expected output
```
   as_of_date   l7_users   l28_users
   2026-01-08   7          8
   2026-01-30   1          5
```

## Common Mistakes
- Using BETWEEN D-28 AND D — gives a 29-day window.
- Counting events instead of distinct users.

## AI Use Cases
- Habit-formation metric.
- Engagement features for ranking.
- Lifecycle-stage classification.
