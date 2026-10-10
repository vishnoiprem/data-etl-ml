-- The 6 onsite-flavored SQL problems for the 2026 Meta DE loop.
-- Schema: code/meta_schema.sql
-- Tests:  tests/test_meta_onsite_sql.py

-- Problem 1: Messenger yesterday-active -> video-call %.
WITH yesterday_active AS (
    SELECT DISTINCT user_id
    FROM   messenger_event
    WHERE  DATE(event_ts) = DATE('now', '-1 day')
),
video_callers AS (
    SELECT DISTINCT caller_id AS user_id
    FROM   messenger_call
    WHERE  is_video = 1
      AND  DATE(started_ts) = DATE('now', '-1 day')
    UNION
    SELECT DISTINCT callee_id AS user_id
    FROM   messenger_call
    WHERE  is_video = 1
      AND  DATE(started_ts) = DATE('now', '-1 day')
)
SELECT CAST(COUNT(DISTINCT v.user_id) AS REAL) /
       NULLIF(COUNT(DISTINCT y.user_id), 0) AS video_pct
FROM   yesterday_active y
LEFT JOIN video_callers v ON v.user_id = y.user_id;

-- Problem 2: 7-day rolling retention by *first* country.
WITH events_with_rank AS (
    SELECT user_id, country, event_ts,
           FIRST_VALUE(country) OVER (
               PARTITION BY user_id ORDER BY event_ts
           ) AS first_country
    FROM   instagram_story_events
),
first_seen AS (
    SELECT user_id, first_country,
           MIN(DATE(event_ts)) AS first_day
    FROM   events_with_rank
    GROUP BY user_id, first_country
),
window_activity AS (
    SELECT f.user_id, f.first_country, f.first_day,
           MAX(CASE WHEN DATE(e.event_ts) BETWEEN f.first_day
                                            AND DATE(f.first_day, '+7 days')
                    THEN 1 ELSE 0 END) AS returned
    FROM   first_seen f
    JOIN   instagram_story_events e ON e.user_id = f.user_id
    GROUP BY f.user_id, f.first_country, f.first_day
)
SELECT first_country AS country,
       COUNT(*) AS total,
       CAST(SUM(returned) AS REAL) / COUNT(*) AS retention_7d
FROM   window_activity
GROUP BY first_country
ORDER BY retention_7d DESC;

-- Problem 3: WhatsApp Q1 cohort, monthly volume through Q3, power-user rate.
WITH first_msg AS (
    SELECT sender_id, MIN(DATE(sent_ts)) AS first_day
    FROM   whatsapp_message
    GROUP BY sender_id
),
q1_cohort AS (
    SELECT sender_id, first_day
    FROM   first_msg
    WHERE  first_day BETWEEN '2024-01-01' AND '2024-03-31'
),
monthly AS (
    SELECT q.sender_id, q.first_day,
           STRFTIME('%Y-%m', m.sent_ts) AS month,
           COUNT(*) AS n_msg
    FROM   q1_cohort q
    JOIN   whatsapp_message m ON m.sender_id = q.sender_id
    WHERE  STRFTIME('%Y-%m', m.sent_ts) <= '2024-09'
    GROUP BY q.sender_id, q.first_day, month
),
power_user_by_6 AS (
    SELECT sender_id, MAX(n_msg) AS peak
    FROM   monthly
    WHERE  month <= STRFTIME('%Y-%m', DATE(first_day, '+6 months'))
    GROUP BY sender_id
),
cohort_size AS (
    SELECT COUNT(*) AS n FROM q1_cohort
)
SELECT
    (SELECT n FROM cohort_size) AS cohort_size,
    SUM(CASE WHEN peak >= 100 THEN 1 ELSE 0 END) AS power_users,
    CAST(SUM(CASE WHEN peak >= 100 THEN 1 ELSE 0 END) AS REAL) /
        (SELECT n FROM cohort_size) AS power_user_rate
FROM   power_user_by_6;

-- Problem 4: top-3 ad-sets per advertiser (with 5-set threshold).
WITH ad_set_perf AS (
    SELECT advertiser_id, ad_set_id,
           SUM(revenue) AS rev,
           SUM(spend)   AS sp,
           SUM(revenue) * 1.0 / NULLIF(SUM(spend), 0) AS roas
    FROM   ad_event
    WHERE  event_ts >= DATE('now', '-7 days')
    GROUP BY advertiser_id, ad_set_id
),
qualified AS (
    SELECT advertiser_id
    FROM   ad_set_perf
    GROUP BY advertiser_id
    HAVING COUNT(*) >= 5
),
ranked AS (
    SELECT a.*,
           ROW_NUMBER() OVER (PARTITION BY advertiser_id
                              ORDER BY roas DESC) AS rk
    FROM   ad_set_perf a
    WHERE  a.advertiser_id IN (SELECT advertiser_id FROM qualified)
)
SELECT advertiser_id, ad_set_id, roas
FROM   ranked
WHERE  rk <= 3
ORDER BY advertiser_id, rk;

-- Problem 5: engagement by hour-of-day (across all posts).
WITH eng AS (
    SELECT post_id, COUNT(*) AS n_eng
    FROM   engagement_event
    GROUP BY post_id
)
SELECT CAST(STRFTIME('%H', p.post_ts) AS INTEGER) AS hour,
       COUNT(DISTINCT p.post_id) AS n_posts,
       SUM(COALESCE(e.n_eng, 0)) AS total_eng,
       CAST(SUM(COALESCE(e.n_eng, 0)) AS REAL) /
           NULLIF(COUNT(DISTINCT p.post_id), 0) AS avg_eng
FROM   facebook_post p
LEFT JOIN eng e ON e.post_id = p.post_id
GROUP BY hour
ORDER BY hour;

-- Problem 6: ads auction time-travel.
SELECT bid_amount
FROM   ad_auction_event
WHERE  ad_id = :ad_id
  AND  won_flag = 1
  AND  auction_ts <= :as_of_ts
ORDER BY auction_ts DESC
LIMIT 1;
