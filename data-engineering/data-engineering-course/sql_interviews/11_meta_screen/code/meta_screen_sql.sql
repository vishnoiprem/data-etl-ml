-- The 5 SQL screen problems for the 2026 Meta DE CoderPad.
-- Schema: code/meta_schema.sql
-- Tests:  tests/test_meta_screen_sql.py

-- Problem 1: 7-day rolling retention by country.
WITH first_seen AS (
    SELECT user_id, country,
           MIN(DATE(event_ts)) AS first_day
    FROM   instagram_story_events
    GROUP BY user_id, country
),
window_activity AS (
    SELECT f.user_id, f.country, f.first_day,
           MAX(CASE WHEN DATE(e.event_ts) BETWEEN f.first_day
                                            AND DATE(f.first_day, '+7 days')
                    THEN 1 ELSE 0 END) AS returned
    FROM   first_seen f
    JOIN   instagram_story_events e
      ON   e.user_id = f.user_id
    GROUP BY f.user_id, f.country, f.first_day
),
country_stats AS (
    SELECT country,
           COUNT(*)         AS total,
           SUM(returned)    AS returned_count
    FROM   window_activity
    GROUP BY country
)
SELECT country,
       CAST(returned_count AS REAL) / total AS retention_7d
FROM   country_stats
WHERE  total >= 1000
ORDER BY retention_7d DESC;

-- Problem 2: peak engagement in first hour.
WITH hour1 AS (
    SELECT p.post_id, p.page_id, p.post_ts,
           COUNT(e.event_id) AS hour1_eng
    FROM   facebook_post p
    LEFT JOIN engagement_event e
      ON  e.post_id = p.post_id
     AND  e.event_ts BETWEEN p.post_ts
                        AND DATETIME(p.post_ts, '+1 hour')
    GROUP BY p.post_id, p.page_id, p.post_ts
),
peak AS (
    SELECT page_id, MAX(hour1_eng) AS peak_hour1
    FROM   hour1
    GROUP BY page_id
)
SELECT h.post_id, h.page_id, h.hour1_eng, p.peak_hour1
FROM   hour1 h
JOIN   peak p ON p.page_id = h.page_id
WHERE  h.hour1_eng >= 0.10 * p.peak_hour1
ORDER BY h.hour1_eng DESC;

-- Problem 3: top-3 posts per page (with threshold).
WITH page_stats AS (
    SELECT page_id, impressions
    FROM   facebook_post
),
qualified_pages AS (
    SELECT page_id
    FROM   page_stats
    GROUP BY page_id
    HAVING MIN(impressions) >= 100
),
ranked AS (
    SELECT post_id, page_id, impressions,
           ROW_NUMBER() OVER (PARTITION BY page_id
                              ORDER BY impressions DESC) AS rk
    FROM   facebook_post
    WHERE  page_id IN (SELECT page_id FROM qualified_pages)
)
SELECT post_id, page_id, impressions
FROM   ranked
WHERE  rk <= 3
ORDER BY page_id, rk;

-- Problem 4: sessionize events (30-min gap).
WITH events AS (
    SELECT user_id, event_ts,
           LAG(event_ts) OVER (PARTITION BY user_id
                               ORDER BY event_ts) AS prev_ts
    FROM   instagram_story_events
),
gaps AS (
    SELECT user_id, event_ts, prev_ts,
           CASE WHEN prev_ts IS NULL
                 OR (JULIANDAY(event_ts) - JULIANDAY(prev_ts)) * 24 * 60 > 30
                THEN 1 ELSE 0
           END AS new_session
    FROM   events
),
session_ids AS (
    SELECT user_id, event_ts,
           SUM(new_session) OVER (PARTITION BY user_id
                                  ORDER BY event_ts) AS session_id
    FROM   gaps
)
SELECT user_id,
       session_id,
       MIN(event_ts) AS session_start,
       MAX(event_ts) AS session_end,
       COUNT(*)      AS event_count
FROM   session_ids
GROUP BY user_id, session_id
ORDER BY user_id, session_id;

-- Problem 5: gaps-and-islands (3+ consecutive days).
WITH user_days AS (
    SELECT DISTINCT user_id, DATE(event_ts) AS d
    FROM   instagram_story_events
),
grp AS (
    SELECT user_id, d,
           DATE(d, '-' || (ROW_NUMBER() OVER (PARTITION BY user_id
                                              ORDER BY d)) || ' days') AS grp_key
    FROM   user_days
),
streaks AS (
    SELECT user_id, grp_key,
           COUNT(*) AS streak_len,
           MIN(d)   AS streak_start,
           MAX(d)   AS streak_end
    FROM   grp
    GROUP BY user_id, grp_key
)
SELECT user_id, MAX(streak_len) AS longest_streak
FROM   streaks
WHERE  streak_len >= 3
GROUP BY user_id
ORDER BY longest_streak DESC;
