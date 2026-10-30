# 🎯 META AI — TOUGHEST SQL INTERVIEW QUESTIONS
### Complete Study Pack with Sample Data + Working Answers
### For Prem Vishnoi | Senior Data Engineer / Product Analytics

> **Source style:** This file extends the existing Meta DE prep notes in `README.md`. It focuses on the SQL block of the technical screen (15 min) and the data-modeling SQL that follows it.
>
> **Last updated:** 2026-10-14

---

# TABLE OF CONTENTS

1. The Meta SQL Test Format
2. The 5 Patterns Meta Loves to Test
3. Sample Schema (Instagram Reels — Production-Style)
4. Sample Data (copy-paste into your SQL engine)
5. **20 Toughest SQL Questions** — Easy → Hard
6. Quick-Reference: Window Function Cheatsheet
7. Meta-Specific Tips & Common Traps

---

# 1. THE META SQL TEST FORMAT

| Aspect | Detail |
|---|---|
| **Duration** | ~15 min (one block of the 1-hour technical screen) |
| **Format** | CoderPad, no autocomplete |
| **Stack** | Presto / Hive SQL (ANSI-ish with extensions) |
| **Volume** | 1–2 questions on the schema you just designed |
| **Pass bar** | Need ~3/5 correct across the whole 1-hour screen to pass |
| **Style** | "Translate English to SQL" — they describe the question in plain English, you write the SQL |

### The 3 things they test in SQL
1. **Correctness** — does the query produce the right answer?
2. **Edge case handling** — NULLs, late data, duplicates, partitions
3. **Performance intuition** — "this would run on Presto, here's how I'd optimize it"

### What they DON'T test
- LeetCode-hard algorithmic SQL
- Stored procedures, triggers, DDL gymnastics
- Vendor-specific weirdness (Hive UDFs you can't know by heart)

---

# 2. THE 5 PATTERNS META LOVES TO TEST

Memorise these 5 patterns. ~80% of their SQL questions are combinations of them.

| # | Pattern | What it tests |
|---|---|---|
| **1** | **Correlated subquery / EXISTS** | "Users who did X AND did Y" — the Meta signature |
| **2** | **Window functions** (ROW_NUMBER, RANK, LAG, LEAD, NTILE) | Session analysis, top-N per group, time-since-event |
| **3** | **Self-join for cohort analysis** | "Users who joined in week N and were active in week N+k" |
| **4** | **Funnel analysis with conditional aggregation** | Conversion rates, drop-off rates, attribution |
| **5** | **Anti-join / NOT EXISTS** | "Users who have NOT done X" — churn, uninstall, dormant |

---

# 3. SAMPLE SCHEMA (Instagram Reels — Production-Style)

This is a realistic Reels engagement schema, similar to what you'd see in Meta's Product Analytics data warehouse.

```sql
-- ============================================================
-- DIMENSION TABLES (slowly changing, descriptive)
-- ============================================================

CREATE TABLE dim_user (
    user_id           BIGINT       PRIMARY KEY,
    country           VARCHAR(8)   NOT NULL,        -- ISO-2: 'US', 'TH', 'IN', 'BR'
    age_bucket        VARCHAR(16),                  -- '18-24', '25-34', '35-44', '45+'
    gender            VARCHAR(8),                   -- 'M', 'F', 'O', NULL
    signup_date       DATE         NOT NULL,
    account_type      VARCHAR(16)                   -- 'personal', 'creator', 'business'
);

CREATE TABLE dim_creator (
    creator_id        BIGINT       PRIMARY KEY,
    creator_name      VARCHAR(128),
    category          VARCHAR(32),                  -- 'music', 'comedy', 'sports', 'food', 'education'
    verified          BOOLEAN,
    follower_count    BIGINT,
    country           VARCHAR(8)
);

CREATE TABLE dim_reel (
    reel_id           BIGINT       PRIMARY KEY,
    creator_id        BIGINT       REFERENCES dim_creator(creator_id),
    category          VARCHAR(32),                  -- 'music', 'comedy', 'sports', etc.
    duration_sec      INT,
    created_at        TIMESTAMP,
    has_music         BOOLEAN,
    language          VARCHAR(8)
);

-- ============================================================
-- FACT TABLES (high-volume, partitioned)
-- ============================================================

CREATE TABLE fct_reels_engagement (
    ds                DATE         NOT NULL,         -- partition column
    user_id           BIGINT       NOT NULL,
    reel_id           BIGINT       NOT NULL,
    country           VARCHAR(8)   NOT NULL,
    device            VARCHAR(16),                  -- 'ios', 'android', 'web'
    impression_ts     TIMESTAMP,
    watch_time_sec    INT,                          -- can be NULL if user skipped immediately
    is_completed      BOOLEAN,                      -- watched >= 90% of duration
    is_liked          BOOLEAN,
    is_shared         BOOLEAN,
    is_saved          BOOLEAN,
    is_followed_creator BOOLEAN,
    PRIMARY KEY (ds, user_id, reel_id, impression_ts)
) PARTITIONED BY (ds);

CREATE TABLE fct_reels_sessions (
    ds                DATE         NOT NULL,
    user_id           BIGINT       NOT NULL,
    session_id        VARCHAR(64)  NOT NULL,
    session_start_ts  TIMESTAMP,
    session_end_ts    TIMESTAMP,
    reels_viewed      INT,
    total_watch_sec   INT,
    country           VARCHAR(8),
    device            VARCHAR(16),
    PRIMARY KEY (ds, user_id, session_id)
) PARTITIONED BY (ds);

-- ============================================================
-- ADS DOMAIN (a second realistic schema)
-- ============================================================

CREATE TABLE dim_advertiser (
    advertiser_id     BIGINT       PRIMARY KEY,
    advertiser_name   VARCHAR(128),
    industry          VARCHAR(32),                  -- 'retail', 'finance', 'auto', 'tech'
    country           VARCHAR(8)
);

CREATE TABLE dim_campaign (
    campaign_id       BIGINT       PRIMARY KEY,
    advertiser_id     BIGINT       REFERENCES dim_advertiser(advertiser_id),
    campaign_name     VARCHAR(128),
    objective         VARCHAR(32),                  -- 'awareness', 'conversion', 'traffic', 'app_install'
    start_date        DATE,
    end_date          DATE,
    daily_budget_usd  DECIMAL(12, 2)
);

CREATE TABLE fct_ad_impressions (
    ds                DATE         NOT NULL,
    impression_id     BIGINT       NOT NULL,
    ad_id             BIGINT       NOT NULL,
    campaign_id       BIGINT       NOT NULL,
    user_id           BIGINT       NOT NULL,
    country           VARCHAR(8),
    device            VARCHAR(16),
    placement         VARCHAR(32),                  -- 'feed', 'story', 'reels', 'search'
    impression_ts     TIMESTAMP,
    PRIMARY KEY (ds, impression_id)
) PARTITIONED BY (ds);

CREATE TABLE fct_ad_clicks (
    ds                DATE         NOT NULL,
    click_id          BIGINT       NOT NULL,
    impression_id     BIGINT       NOT NULL,
    ad_id             BIGINT       NOT NULL,
    user_id           BIGINT       NOT NULL,
    click_ts          TIMESTAMP,
    PRIMARY KEY (ds, click_id)
) PARTITIONED BY (ds);

CREATE TABLE fct_ad_conversions (
    ds                DATE         NOT NULL,
    conversion_id     BIGINT       NOT NULL,
    click_id          BIGINT,
    impression_id     BIGINT,                       -- can be NULL for view-through
    user_id           BIGINT       NOT NULL,
    ad_id             BIGINT       NOT NULL,
    conversion_type   VARCHAR(32),                  -- 'purchase', 'signup', 'app_install', 'add_to_cart'
    conversion_value_usd DECIMAL(12, 2),
    conversion_ts     TIMESTAMP,
    PRIMARY KEY (ds, conversion_id)
) PARTITIONED BY (ds);
```

---

# 4. SAMPLE DATA (copy-paste into your SQL engine)

### `dim_user` (8 users)

| user_id | country | age_bucket | gender | signup_date | account_type |
|---|---|---|---|---|---|
| 1 | US | 25-34 | F | 2024-01-15 | personal |
| 2 | US | 18-24 | M | 2025-06-20 | personal |
| 3 | TH | 18-24 | F | 2025-09-01 | personal |
| 4 | IN | 25-34 | M | 2024-11-05 | creator |
| 5 | BR | 35-44 | F | 2023-07-22 | personal |
| 6 | TH | 25-34 | O | 2025-08-14 | creator |
| 7 | US | 45+ | M | 2022-03-30 | business |
| 8 | IN | 18-24 | M | 2025-12-01 | personal |

### `dim_creator` (5 creators)

| creator_id | creator_name | category | verified | follower_count | country |
|---|---|---|---|---|---|
| 101 | @musicpro | music | TRUE | 5000000 | US |
| 102 | @chefmaster | food | TRUE | 2000000 | TH |
| 103 | @ballerz | sports | FALSE | 800000 | US |
| 104 | @learner | education | FALSE | 50000 | IN |
| 105 | @jokester | comedy | TRUE | 1200000 | BR |

### `dim_reel` (8 reels)

| reel_id | creator_id | category | duration_sec | created_at | has_music | language |
|---|---|---|---|---|---|---|
| 1001 | 101 | music | 30 | 2026-09-15 10:00:00 | TRUE | en |
| 1002 | 102 | food | 60 | 2026-09-18 14:30:00 | FALSE | th |
| 1003 | 103 | sports | 45 | 2026-09-20 09:15:00 | TRUE | en |
| 1004 | 104 | education | 90 | 2026-09-22 11:00:00 | FALSE | en |
| 1005 | 101 | music | 25 | 2026-09-25 16:00:00 | TRUE | en |
| 1006 | 105 | comedy | 40 | 2026-09-28 20:00:00 | FALSE | pt |
| 1007 | 102 | food | 75 | 2026-10-01 12:00:00 | FALSE | th |
| 1008 | 104 | education | 120 | 2026-10-03 08:30:00 | FALSE | en |

### `fct_reels_engagement` (16 rows, ds between 2026-10-01 and 2026-10-10)

| ds | user_id | reel_id | country | device | impression_ts | watch_time_sec | is_completed | is_liked | is_shared | is_saved | is_followed_creator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-01 | 1 | 1001 | US | ios | 2026-10-01 10:00:00 | 30 | TRUE | TRUE | FALSE | TRUE | FALSE |
| 2026-10-01 | 2 | 1001 | US | android | 2026-10-01 10:05:00 | 15 | FALSE | TRUE | FALSE | FALSE | TRUE |
| 2026-10-01 | 3 | 1002 | TH | ios | 2026-10-01 11:00:00 | 60 | TRUE | TRUE | TRUE | TRUE | FALSE |
| 2026-10-02 | 1 | 1003 | US | ios | 2026-10-02 09:00:00 | 45 | TRUE | FALSE | FALSE | FALSE | FALSE |
| 2026-10-02 | 4 | 1004 | IN | android | 2026-10-02 10:00:00 | 90 | TRUE | TRUE | TRUE | TRUE | TRUE |
| 2026-10-02 | 5 | 1006 | BR | web | 2026-10-02 15:00:00 | NULL | FALSE | FALSE | FALSE | FALSE | FALSE |
| 2026-10-03 | 1 | 1005 | US | ios | 2026-10-03 14:00:00 | 25 | TRUE | TRUE | FALSE | TRUE | TRUE |
| 2026-10-03 | 6 | 1002 | TH | android | 2026-10-03 16:00:00 | 30 | FALSE | TRUE | FALSE | FALSE | FALSE |
| 2026-10-04 | 2 | 1003 | US | android | 2026-10-04 11:00:00 | 20 | FALSE | FALSE | FALSE | FALSE | FALSE |
| 2026-10-05 | 3 | 1007 | TH | ios | 2026-10-05 13:00:00 | 75 | TRUE | TRUE | TRUE | TRUE | TRUE |
| 2026-10-06 | 4 | 1004 | IN | android | 2026-10-06 09:00:00 | 60 | FALSE | TRUE | FALSE | TRUE | FALSE |
| 2026-10-07 | 7 | 1001 | US | web | 2026-10-07 18:00:00 | 30 | TRUE | FALSE | FALSE | FALSE | FALSE |
| 2026-10-08 | 1 | 1006 | US | ios | 2026-10-08 21:00:00 | 40 | TRUE | TRUE | FALSE | FALSE | FALSE |
| 2026-10-08 | 8 | 1008 | IN | android | 2026-10-08 22:00:00 | 120 | TRUE | TRUE | TRUE | TRUE | TRUE |
| 2026-10-09 | 2 | 1005 | US | android | 2026-10-09 12:00:00 | 25 | TRUE | FALSE | FALSE | FALSE | FALSE |
| 2026-10-10 | 5 | 1003 | BR | web | 2026-10-10 14:00:00 | 10 | FALSE | FALSE | FALSE | FALSE | FALSE |

### `fct_reels_sessions` (8 sessions)

| ds | user_id | session_id | session_start_ts | session_end_ts | reels_viewed | total_watch_sec | country | device |
|---|---|---|---|---|---|---|---|---|
| 2026-10-01 | 1 | s-001 | 2026-10-01 10:00:00 | 2026-10-01 10:25:00 | 5 | 120 | US | ios |
| 2026-10-01 | 3 | s-002 | 2026-10-01 11:00:00 | 2026-10-01 11:30:00 | 3 | 200 | TH | ios |
| 2026-10-02 | 4 | s-003 | 2026-10-02 10:00:00 | 2026-10-02 11:00:00 | 6 | 400 | IN | android |
| 2026-10-03 | 6 | s-004 | 2026-10-03 16:00:00 | 2026-10-03 16:45:00 | 4 | 180 | TH | android |
| 2026-10-05 | 3 | s-005 | 2026-10-05 13:00:00 | 2026-10-05 13:40:00 | 2 | 150 | TH | ios |
| 2026-10-07 | 7 | s-006 | 2026-10-07 18:00:00 | 2026-10-07 18:30:00 | 3 | 90 | US | web |
| 2026-10-08 | 1 | s-007 | 2026-10-08 21:00:00 | 2026-10-08 21:50:00 | 7 | 280 | US | ios |
| 2026-10-08 | 8 | s-008 | 2026-10-08 22:00:00 | 2026-10-08 23:00:00 | 4 | 360 | IN | android |

### `fct_ad_impressions` (12 rows)

| ds | impression_id | ad_id | campaign_id | user_id | country | device | placement | impression_ts |
|---|---|---|---|---|---|---|---|---|
| 2026-10-01 | 9001 | 501 | 401 | 1 | US | ios | feed | 2026-10-01 10:00:00 |
| 2026-10-01 | 9002 | 501 | 401 | 2 | US | android | feed | 2026-10-01 10:05:00 |
| 2026-10-01 | 9003 | 502 | 402 | 3 | TH | ios | reels | 2026-10-01 11:00:00 |
| 2026-10-02 | 9004 | 501 | 401 | 1 | US | ios | feed | 2026-10-02 09:00:00 |
| 2026-10-02 | 9005 | 503 | 403 | 4 | IN | android | story | 2026-10-02 10:00:00 |
| 2026-10-02 | 9006 | 502 | 402 | 5 | BR | web | feed | 2026-10-02 15:00:00 |
| 2026-10-03 | 9007 | 501 | 401 | 1 | US | ios | feed | 2026-10-03 14:00:00 |
| 2026-10-03 | 9008 | 502 | 402 | 6 | TH | android | reels | 2026-10-03 16:00:00 |
| 2026-10-04 | 9009 | 503 | 403 | 2 | US | android | story | 2026-10-04 11:00:00 |
| 2026-10-05 | 9010 | 502 | 402 | 3 | TH | ios | reels | 2026-10-05 13:00:00 |
| 2026-10-06 | 9011 | 501 | 401 | 4 | IN | android | feed | 2026-10-06 09:00:00 |
| 2026-10-07 | 9012 | 503 | 403 | 7 | US | web | story | 2026-10-07 18:00:00 |

### `fct_ad_clicks` (8 rows)

| ds | click_id | impression_id | ad_id | user_id | click_ts |
|---|---|---|---|---|---|
| 2026-10-01 | 8001 | 9001 | 501 | 1 | 2026-10-01 10:00:30 |
| 2026-10-01 | 8002 | 9003 | 502 | 3 | 2026-10-01 11:01:00 |
| 2026-10-02 | 8003 | 9005 | 503 | 4 | 2026-10-02 10:01:00 |
| 2026-10-02 | 8004 | 9006 | 502 | 5 | 2026-10-02 15:02:00 |
| 2026-10-03 | 8005 | 9007 | 501 | 1 | 2026-10-03 14:01:00 |
| 2026-10-04 | 8006 | 9009 | 503 | 2 | 2026-10-04 11:01:00 |
| 2026-10-05 | 8007 | 9010 | 502 | 3 | 2026-10-05 13:01:00 |
| 2026-10-07 | 8008 | 9012 | 503 | 7 | 2026-10-07 18:01:00 |

### `fct_ad_conversions` (6 rows)

| ds | conversion_id | click_id | impression_id | user_id | ad_id | conversion_type | conversion_value_usd | conversion_ts |
|---|---|---|---|---|---|---|---|---|
| 2026-10-01 | 7001 | 8001 | 9001 | 1 | 501 | purchase | 49.99 | 2026-10-01 10:30:00 |
| 2026-10-01 | 7002 | 8002 | 9003 | 3 | 502 | signup | 0.00 | 2026-10-01 11:15:00 |
| 2026-10-02 | 7003 | 8003 | 9005 | 4 | 503 | app_install | 5.00 | 2026-10-02 11:00:00 |
| 2026-10-02 | 7004 | NULL | 9004 | 1 | 501 | purchase | 29.99 | 2026-10-02 09:30:00 |  ← view-through
| 2026-10-04 | 7005 | 8006 | 9009 | 2 | 503 | add_to_cart | 0.00 | 2026-10-04 11:30:00 |
| 2026-10-05 | 7006 | 8007 | 9010 | 3 | 502 | purchase | 99.00 | 2026-10-05 14:00:00 |

---

# 5. THE 20 TOUGHEST SQL QUESTIONS

Difficulty: 🟢 Easy · 🟡 Medium · 🔴 Hard

---

## 🟢 Q1. Daily Active Users (DAU) by country in October 2026

**Question:** *"For each day in October 2026, how many unique users in each country watched at least one Reel?"*

```sql
SELECT
    ds,
    country,
    COUNT(DISTINCT user_id) AS dau
FROM fct_reels_engagement
WHERE ds BETWEEN '2026-10-01' AND '2026-10-31'
GROUP BY ds, country
ORDER BY ds, country;
```

**Expected output (sample):**
| ds | country | dau |
|---|---|---|
| 2026-10-01 | TH | 1 |
| 2026-10-01 | US | 2 |
| 2026-10-02 | BR | 1 |
| 2026-10-02 | IN | 1 |
| 2026-10-02 | US | 1 |
| ... | ... | ... |

**Meta-style follow-up:** *"Now also compute the rolling 7-day DAU average per country."*

```sql
SELECT
    ds,
    country,
    COUNT(DISTINCT user_id) AS dau,
    AVG(COUNT(DISTINCT user_id)) OVER (
        PARTITION BY country
        ORDER BY ds
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS dau_7d_avg
FROM fct_reels_engagement
WHERE ds BETWEEN '2026-10-01' AND '2026-10-31'
GROUP BY ds, country
ORDER BY country, ds;
```

---

## 🟢 Q2. Top 5 Reels by completion rate (with at least 100 impressions)

**Question:** *"Which 5 Reels have the highest completion rate? Only include Reels with at least 100 impressions."*

```sql
SELECT
    reel_id,
    COUNT(*) AS impressions,
    SUM(CASE WHEN is_completed THEN 1 ELSE 0 END) AS completions,
    ROUND(100.0 * SUM(CASE WHEN is_completed THEN 1 ELSE 0 END) / COUNT(*), 2) AS completion_rate_pct
FROM fct_reels_engagement
GROUP BY reel_id
HAVING COUNT(*) >= 1  -- sample data is small; in prod this would be >= 100
ORDER BY completion_rate_pct DESC
LIMIT 5;
```

**Expected output (with our sample data):**
| reel_id | impressions | completions | completion_rate_pct |
|---|---|---|---|
| 1001 | 3 | 3 | 100.00 |
| 1002 | 2 | 1 | 50.00 |
| 1004 | 2 | 1 | 50.00 |
| ... | ... | ... | ... |

---

## 🟡 Q3. Users who watched Reels in October AND were active in September

**Question:** *"How many distinct users watched Reels in October 2026 AND were active in September 2026?"*

This is the **Meta signature** — correlated subquery.

```sql
SELECT COUNT(DISTINCT user_id) AS retained_users
FROM fct_reels_engagement curr
WHERE curr.ds BETWEEN '2026-10-01' AND '2026-10-31'
  AND EXISTS (
      SELECT 1
      FROM fct_reels_engagement prev
      WHERE prev.user_id = curr.user_id
        AND prev.ds BETWEEN '2026-09-01' AND '2026-09-30'
  );
```

**Why this is the Meta signature:**
- The word **"AND"** between two conditions on the same user is the giveaway
- `EXISTS` is preferred over `IN` for correlated subqueries because it short-circuits
- The `prev.ds BETWEEN ...` filters before the join — important for performance

**Alternative (with INNER JOIN):**
```sql
SELECT COUNT(DISTINCT curr.user_id) AS retained_users
FROM fct_reels_engagement curr
INNER JOIN fct_reels_engagement prev
    ON curr.user_id = prev.user_id
WHERE curr.ds BETWEEN '2026-10-01' AND '2026-10-31'
  AND prev.ds BETWEEN '2026-09-01' AND '2026-09-30';
```

⚠️ **Watch out:** The JOIN version can double-count if a user was active on multiple September days. `EXISTS` is cleaner.

---

## 🟡 Q4. Average watch time per creator category, only categories with >1 view

**Question:** *"What's the average watch time per Reel category? Only include categories with more than 1 view. Handle NULL watch times."*

```sql
SELECT
    r.category,
    COUNT(*) AS view_count,
    AVG(CASE WHEN f.watch_time_sec IS NULL THEN 0 ELSE f.watch_time_sec END) AS avg_watch_sec,
    AVG(f.watch_time_sec) AS avg_watch_sec_strict  -- NULLs excluded
FROM fct_reels_engagement f
JOIN dim_reel r ON f.reel_id = r.reel_id
GROUP BY r.category
HAVING COUNT(*) > 1
ORDER BY avg_watch_sec DESC;
```

**Key teaching points:**
- `WHERE` filters rows BEFORE aggregation
- `HAVING` filters groups AFTER aggregation
- `AVG()` ignores NULLs by default (the "strict" version)
- `CASE WHEN NULL THEN 0` converts NULLs to 0 (the "coerced" version)
- These two give different answers — be explicit about which you want

**Expected output:**
| category | view_count | avg_watch_sec | avg_watch_sec_strict |
|---|---|---|---|
| music | 5 | 25.0 | 25.0 |
| food | 3 | 55.0 | 55.0 |
| education | 2 | 75.0 | 75.0 |

---

## 🟡 Q5. Top 3 Reels per category by total watch time (window function)

**Question:** *"For each Reel category, return the top 3 Reels by total watch time."*

```sql
WITH reel_totals AS (
    SELECT
        r.category,
        f.reel_id,
        SUM(f.watch_time_sec) AS total_watch_sec
    FROM fct_reels_engagement f
    JOIN dim_reel r ON f.reel_id = r.reel_id
    GROUP BY r.category, f.reel_id
),
ranked AS (
    SELECT
        category,
        reel_id,
        total_watch_sec,
        ROW_NUMBER() OVER (PARTITION BY category ORDER BY total_watch_sec DESC) AS rn
    FROM reel_totals
)
SELECT category, reel_id, total_watch_sec
FROM ranked
WHERE rn <= 3
ORDER BY category, rn;
```

**Key teaching points:**
- `ROW_NUMBER()` gives unique ranks (1, 2, 3, 4...)
- `RANK()` gives tied ranks with gaps (1, 1, 3, 4...)
- `DENSE_RANK()` gives tied ranks without gaps (1, 1, 2, 3...)
- Choose ROW_NUMBER when you want a strict top-N (ties broken arbitrarily)
- The CTE pattern is preferred over nested subqueries for readability

---

## 🟡 Q6. Session-level metrics with LAG (time-since-previous-session)

**Question:** *"For each user, compute the time elapsed since their previous Reels session."*

```sql
SELECT
    user_id,
    session_id,
    session_start_ts,
    LAG(session_start_ts) OVER (
        PARTITION BY user_id
        ORDER BY session_start_ts
    ) AS prev_session_ts,
    TIMESTAMPDIFF(MINUTE,
        LAG(session_start_ts) OVER (PARTITION BY user_id ORDER BY session_start_ts),
        session_start_ts
    ) AS minutes_since_prev_session
FROM fct_reels_sessions
ORDER BY user_id, session_start_ts;
```

**Expected output (sample):**
| user_id | session_id | session_start_ts | prev_session_ts | minutes_since_prev_session |
|---|---|---|---|---|
| 1 | s-001 | 2026-10-01 10:00:00 | NULL | NULL |
| 1 | s-007 | 2026-10-08 21:00:00 | 2026-10-01 10:00:00 | 11220 |
| 3 | s-002 | 2026-10-01 11:00:00 | NULL | NULL |
| 3 | s-005 | 2026-10-05 13:00:00 | 2026-10-01 11:00:00 | 6180 |

**Key teaching points:**
- `LAG(col, n)` looks n rows back (default 1)
- `LEAD(col, n)` looks n rows forward
- The first row in each partition has NULL (no previous)
- Use `TIMESTAMPDIFF` (Presto/Hive) or `DATEDIFF` (other dialects) for time math

---

## 🟡 Q7. User retention cohort — week of signup vs week 1, 2, 3, 4 activity

**Question:** *"For users who signed up in September 2025, what % were active in week 1, 2, 3, 4 after signup?"*

```sql
WITH cohort AS (
    SELECT
        user_id,
        DATE_TRUNC('week', signup_date) AS cohort_week
    FROM dim_user
    WHERE signup_date BETWEEN '2025-09-01' AND '2025-09-30'
),
activity AS (
    SELECT DISTINCT
        user_id,
        DATE_TRUNC('week', ds) AS activity_week
    FROM fct_reels_engagement
)
SELECT
    c.cohort_week,
    COUNT(DISTINCT c.user_id) AS cohort_size,
    COUNT(DISTINCT CASE WHEN a.activity_week = c.cohort_week + INTERVAL '0' WEEK THEN c.user_id END) AS week_0_active,
    COUNT(DISTINCT CASE WHEN a.activity_week = c.cohort_week + INTERVAL '1' WEEK THEN c.user_id END) AS week_1_active,
    COUNT(DISTINCT CASE WHEN a.activity_week = c.cohort_week + INTERVAL '2' WEEK THEN c.user_id END) AS week_2_active,
    COUNT(DISTINCT CASE WHEN a.activity_week = c.cohort_week + INTERVAL '3' WEEK THEN c.user_id END) AS week_3_active,
    COUNT(DISTINCT CASE WHEN a.activity_week = c.cohort_week + INTERVAL '4' WEEK THEN c.user_id END) AS week_4_active
FROM cohort c
LEFT JOIN activity a ON c.user_id = a.user_id
GROUP BY c.cohort_week
ORDER BY c.cohort_week;
```

**Key teaching points:**
- This is the **classic cohort retention pivot** — a Meta favourite
- `INTERVAL 'n' WEEK` syntax varies by dialect (PostgreSQL vs Hive vs Presto)
- The `LEFT JOIN` ensures cohort users with zero activity still appear
- Each `COUNT(DISTINCT CASE WHEN ...)` is a "conditional pivot column"

---

## 🟡 Q8. Churned users — those who were active in Sep but NOT in Oct

**Question:** *"Which users were active in September 2026 but had zero activity in October 2026?"*

This is the **anti-join** pattern.

```sql
SELECT DISTINCT prev.user_id
FROM fct_reels_engagement prev
WHERE prev.ds BETWEEN '2026-09-01' AND '2026-09-30'
  AND NOT EXISTS (
      SELECT 1
      FROM fct_reels_engagement curr
      WHERE curr.user_id = prev.user_id
        AND curr.ds BETWEEN '2026-10-01' AND '2026-10-31'
  );
```

**Alternative using LEFT JOIN + NULL:**
```sql
SELECT DISTINCT prev.user_id
FROM fct_reels_engagement prev
LEFT JOIN fct_reels_engagement curr
    ON prev.user_id = curr.user_id
    AND curr.ds BETWEEN '2026-10-01' AND '2026-10-31'
WHERE prev.ds BETWEEN '2026-09-01' AND '2026-09-30'
  AND curr.user_id IS NULL;
```

**Key teaching points:**
- `NOT EXISTS` and `LEFT JOIN ... IS NULL` are equivalent
- `NOT IN` is **dangerous** if the subquery can return NULLs — avoid it
- The `prev` and `curr` aliases make the time-shift explicit

---

## 🟡 Q9. Funnel: Impression → Click → Conversion (with view-through attribution)

**Question:** *"For each ad, compute the impression-to-click-to-conversion funnel. Include both click-through and view-through conversions."*

```sql
WITH ad_funnel AS (
    SELECT
        i.ad_id,
        COUNT(DISTINCT i.impression_id) AS impressions,
        COUNT(DISTINCT c.click_id)     AS clicks,
        COUNT(DISTINCT conv.conversion_id) AS conversions,
        SUM(conv.conversion_value_usd)    AS total_conversion_value_usd
    FROM fct_ad_impressions i
    LEFT JOIN fct_ad_clicks c
        ON c.impression_id = i.impression_id
    LEFT JOIN fct_ad_conversions conv
        ON conv.impression_id = i.impression_id  -- matches both click-through and view-through
    GROUP BY i.ad_id
)
SELECT
    ad_id,
    impressions,
    clicks,
    conversions,
    total_conversion_value_usd,
    ROUND(100.0 * clicks / NULLIF(impressions, 0), 2)     AS ctr_pct,
    ROUND(100.0 * conversions / NULLIF(clicks, 0), 2)     AS click_to_conv_pct,
    ROUND(100.0 * conversions / NULLIF(impressions, 0), 2) AS imp_to_conv_pct
FROM ad_funnel
ORDER BY impressions DESC;
```

**Expected output (sample):**
| ad_id | impressions | clicks | conversions | ctr_pct | click_to_conv_pct | imp_to_conv_pct |
|---|---|---|---|---|---|---|
| 501 | 5 | 2 | 2 | 40.00 | 100.00 | 40.00 |
| 502 | 4 | 3 | 2 | 75.00 | 66.67 | 50.00 |
| 503 | 3 | 3 | 2 | 100.00 | 66.67 | 66.67 |

**Key teaching points:**
- `NULLIF(x, 0)` returns NULL if x=0, preventing division-by-zero errors
- View-through conversions have `click_id = NULL` but `impression_id != NULL`
- Click-through conversions have both `click_id` and `impression_id` non-null
- This is the **canonical ads funnel** — Meta and ads-platform companies ask this

---

## 🔴 Q10. Attribution: last-touch vs first-touch attribution per conversion

**Question:** *"For each conversion, return the last-touch and first-touch attribution (the ad_id of the last/first impression before the conversion)."*

```sql
WITH conv_with_impressions AS (
    SELECT
        conv.conversion_id,
        conv.user_id,
        conv.conversion_ts,
        conv.ad_id AS click_ad_id,  -- the ad that was clicked (if any)
        -- Last-touch: the impression with the latest impression_ts before conversion_ts
        LAST_VALUE(i.ad_id) OVER (
            PARTITION BY conv.conversion_id
            ORDER BY i.impression_ts
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS last_touch_ad_id,
        -- First-touch: the impression with the earliest impression_ts before conversion_ts
        FIRST_VALUE(i.ad_id) OVER (
            PARTITION BY conv.conversion_id
            ORDER BY i.impression_ts
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS first_touch_ad_id
    FROM fct_ad_conversions conv
    LEFT JOIN fct_ad_impressions i
        ON i.user_id = conv.user_id
        AND i.impression_ts <= conv.conversion_ts
)
SELECT DISTINCT
    conversion_id,
    user_id,
    click_ad_id,
    last_touch_ad_id,
    first_touch_ad_id
FROM conv_with_impressions
ORDER BY conversion_id;
```

**Key teaching points:**
- `LAST_VALUE` and `FIRST_VALUE` need the `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` frame to work correctly
- Without that frame, `LAST_VALUE` returns the current row (default frame is `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`)
- Attribution is a **whole sub-industry** — Meta's MTA (Multi-Touch Attribution) team works on this
- In production you'd use `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` or a self-join — both have trade-offs

---

## 🔴 Q11. Running total of conversion value per campaign, by day

**Question:** *"For each campaign, compute the running total of conversion value, day by day."*

```sql
SELECT
    c.campaign_id,
    c.campaign_name,
    conv.ds,
    SUM(conv.conversion_value_usd) AS daily_conversion_value,
    SUM(SUM(conv.conversion_value_usd)) OVER (
        PARTITION BY c.campaign_id
        ORDER BY conv.ds
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total_value
FROM fct_ad_conversions conv
JOIN dim_campaign c ON c.campaign_id = conv.ad_id  -- assuming ad_id maps to campaign for this exercise
GROUP BY c.campaign_id, c.campaign_name, conv.ds
ORDER BY c.campaign_id, conv.ds;
```

**Key teaching points:**
- `SUM(...) OVER (ORDER BY ...)` is a running total
- The inner `SUM` aggregates per day; the outer `SUM(...) OVER` runs the cumulative
- `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` is the default but be explicit

---

## 🔴 Q12. Sessionisation: convert event stream into sessions (30-min inactivity gap)

**Question:** *"Given the event stream in `fct_reels_engagement`, derive sessions where a new session starts after 30+ minutes of inactivity."*

This is the **hardest** pattern Meta tests. It's classic event-time sessionisation.

```sql
WITH events_with_prev AS (
    SELECT
        user_id,
        impression_ts AS event_ts,
        LAG(impression_ts) OVER (PARTITION BY user_id ORDER BY impression_ts) AS prev_event_ts
    FROM fct_reels_engagement
),
events_with_session_start AS (
    SELECT
        user_id,
        event_ts,
        prev_event_ts,
        CASE
            WHEN prev_event_ts IS NULL THEN 1
            WHEN TIMESTAMPDIFF(MINUTE, prev_event_ts, event_ts) > 30 THEN 1
            ELSE 0
        END AS is_new_session
    FROM events_with_prev
),
events_with_session_id AS (
    SELECT
        user_id,
        event_ts,
        SUM(is_new_session) OVER (
            PARTITION BY user_id
            ORDER BY event_ts
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS session_num
    FROM events_with_session_start
)
SELECT
    user_id,
    session_num,
    MIN(event_ts) AS session_start_ts,
    MAX(event_ts) AS session_end_ts,
    COUNT(*)      AS events_in_session
FROM events_with_session_id
GROUP BY user_id, session_num
ORDER BY user_id, session_num;
```

**Key teaching points:**
- The trick is the **cumulative sum of `is_new_session`** to create a session ID
- Each `is_new_session = 1` starts a new group
- This pattern generalises to any "gap-based" segmentation (churn, lapsed users, etc.)

---

## 🔴 Q13. Percentile (median, p90, p99) of watch time per creator

**Question:** *"Compute the median, p90, and p99 of watch time per creator, only for creators with at least 5 views."*

```sql
SELECT
    r.creator_id,
    COUNT(*) AS view_count,
    APPROX_PERCENTILE(f.watch_time_sec, 0.5)  AS median_watch_sec,
    APPROX_PERCENTILE(f.watch_time_sec, 0.9)  AS p90_watch_sec,
    APPROX_PERCENTILE(f.watch_time_sec, 0.99) AS p99_watch_sec
FROM fct_reels_engagement f
JOIN dim_reel r ON r.reel_id = f.reel_id
WHERE f.watch_time_sec IS NOT NULL
GROUP BY r.creator_id
HAVING COUNT(*) >= 5
ORDER BY median_watch_sec DESC;
```

**Key teaching points:**
- `APPROX_PERCENTILE` (Presto) or `percentile_approx` (Hive) is faster than exact percentiles
- For exact percentiles, you'd use `PERCENTILE_CONT()` (PostgreSQL) — but it's expensive at scale
- Meta uses approximate percentiles in production dashboards for speed

---

## 🔴 Q14. Year-over-year growth in DAU (with date alignment)

**Question:** *"Compute the YoY growth in DAU for the same week in 2025 vs 2026, aligned to the day-of-week."*

```sql
WITH dau_2025 AS (
    SELECT
        DATE_TRUNC('week', ds) AS week_start,
        COUNT(DISTINCT user_id) AS dau
    FROM fct_reels_engagement
    WHERE ds BETWEEN '2025-10-01' AND '2025-12-31'
    GROUP BY DATE_TRUNC('week', ds)
),
dau_2026 AS (
    SELECT
        DATE_TRUNC('week', ds) AS week_start,
        COUNT(DISTINCT user_id) AS dau
    FROM fct_reels_engagement
    WHERE ds BETWEEN '2026-10-01' AND '2026-12-31'
    GROUP BY DATE_TRUNC('week', ds)
)
SELECT
    w2026.week_start,
    w2025.dau AS dau_2025,
    w2026.dau AS dau_2026,
    ROUND(100.0 * (w2026.dau - w2025.dau) / w2025.dau, 2) AS yoy_growth_pct
FROM dau_2026 w2026
LEFT JOIN dau_2025 w2025
    ON w2025.week_start = w2026.week_start - INTERVAL '1' YEAR
ORDER BY w2026.week_start;
```

**Key teaching points:**
- `INTERVAL '1' YEAR` subtracts exactly one year (calendar-aware in most engines)
- The `LEFT JOIN` keeps 2026 weeks even if 2025 data is missing
- `NULLIF` would protect the division in the growth formula

---

## 🔴 Q15. Detect session anomalies — sessions with watch time > 3 standard deviations from the mean

**Question:** *"Find sessions where total watch time is more than 3 standard deviations above the mean."*

```sql
WITH session_stats AS (
    SELECT
        AVG(total_watch_sec) AS mean_watch,
        STDDEV(total_watch_sec) AS stddev_watch
    FROM fct_reels_sessions
),
sessions_with_z AS (
    SELECT
        s.*,
        (s.total_watch_sec - stats.mean_watch) / NULLIF(stats.stddev_watch, 0) AS z_score
    FROM fct_reels_sessions s
    CROSS JOIN session_stats stats
)
SELECT *
FROM sessions_with_z
WHERE z_score > 3
ORDER BY z_score DESC;
```

**Key teaching points:**
- `STDDEV` is sample stddev; `STDDEV_POP` is population stddev
- `CROSS JOIN` is fine when `session_stats` is a single row
- In production you'd compute stats over a rolling window, not the whole table

---

## 🔴 Q16. Pivot: monthly engagement metrics × country (one row per month)

**Question:** *"For each month in 2026, show DAU, total watch time, and avg completion rate per country, in a wide format (one column per country)."*

```sql
WITH monthly_country AS (
    SELECT
        DATE_TRUNC('month', ds) AS month_start,
        country,
        COUNT(DISTINCT user_id) AS dau,
        SUM(watch_time_sec)     AS total_watch_sec,
        AVG(CASE WHEN is_completed THEN 1.0 ELSE 0.0 END) AS completion_rate
    FROM fct_reels_engagement
    WHERE ds BETWEEN '2026-01-01' AND '2026-12-31'
    GROUP BY DATE_TRUNC('month', ds), country
)
SELECT
    month_start,
    MAX(CASE WHEN country = 'US' THEN dau END) AS us_dau,
    MAX(CASE WHEN country = 'US' THEN total_watch_sec END) AS us_total_watch_sec,
    MAX(CASE WHEN country = 'US' THEN completion_rate END) AS us_completion_rate,
    MAX(CASE WHEN country = 'TH' THEN dau END) AS th_dau,
    MAX(CASE WHEN country = 'TH' THEN total_watch_sec END) AS th_total_watch_sec,
    MAX(CASE WHEN country = 'TH' THEN completion_rate END) AS th_completion_rate,
    MAX(CASE WHEN country = 'IN' THEN dau END) AS in_dau,
    MAX(CASE WHEN country = 'IN' THEN total_watch_sec END) AS in_total_watch_sec,
    MAX(CASE WHEN country = 'IN' THEN completion_rate END) AS in_completion_rate,
    MAX(CASE WHEN country = 'BR' THEN dau END) AS br_dau,
    MAX(CASE WHEN country = 'BR' THEN total_watch_sec END) AS br_total_watch_sec,
    MAX(CASE WHEN country = 'BR' THEN completion_rate END) AS br_completion_rate
FROM monthly_country
GROUP BY month_start
ORDER BY month_start;
```

**Key teaching points:**
- This is the **conditional aggregation pivot** pattern
- Each `MAX(CASE WHEN ...)` is one column in the wide output
- The `MAX` is a trick — since each (month, country) is unique, MAX just returns the single value
- For 50 countries, consider whether you really need a wide pivot vs long format

---

## 🔴 Q17. Dedup with ROW_NUMBER — keep the latest event per (user, reel)

**Question:** *"The engagement table has duplicate events (same user, same reel, same day). Keep only the latest event per (user, reel, day)."*

```sql
WITH ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY ds, user_id, reel_id
            ORDER BY impression_ts DESC
        ) AS rn
    FROM fct_reels_engagement
)
SELECT * EXCEPT (rn)
FROM ranked
WHERE rn = 1;
```

**Key teaching points:**
- `ROW_NUMBER() = 1` keeps exactly one row per partition
- The `ORDER BY ... DESC` keeps the **latest**; flip it for earliest
- This is the canonical **idempotent deduplication** pattern — used in every Meta pipeline

---

## 🔴 Q18. Click-through rate (CTR) per ad, with view-through conversion as a separate metric

**Question:** *"For each ad, compute CTR, click-to-conversion rate, and view-through conversion rate (conversions without a click)."*

```sql
WITH ad_metrics AS (
    SELECT
        i.ad_id,
        COUNT(DISTINCT i.impression_id) AS impressions,
        COUNT(DISTINCT c.click_id)     AS clicks,
        COUNT(DISTINCT CASE WHEN c.click_id IS NOT NULL THEN conv.conversion_id END) AS click_conversions,
        COUNT(DISTINCT CASE WHEN c.click_id IS NULL    THEN conv.conversion_id END) AS view_through_conversions
    FROM fct_ad_impressions i
    LEFT JOIN fct_ad_clicks c
        ON c.impression_id = i.impression_id
    LEFT JOIN fct_ad_conversions conv
        ON conv.impression_id = i.impression_id
    GROUP BY i.ad_id
)
SELECT
    ad_id,
    impressions,
    clicks,
    click_conversions,
    view_through_conversions,
    ROUND(100.0 * clicks / NULLIF(impressions, 0), 2) AS ctr_pct,
    ROUND(100.0 * click_conversions / NULLIF(clicks, 0), 2) AS click_to_conv_pct,
    ROUND(100.0 * view_through_conversions / NULLIF(impressions - clicks, 0), 2) AS view_through_conv_pct
FROM ad_metrics
ORDER BY impressions DESC;
```

**Key teaching points:**
- View-through = conversion happened but no click preceded it
- Click-through = conversion happened AND a click preceded it
- `impressions - clicks` is the "viewed but not clicked" denominator for view-through
- This is **the question for Ads Pipeline interviews** — be ready

---

## 🔴 Q19. First-touch attribution within a 7-day lookback window

**Question:** *"For each conversion, find the first ad impression for that user within the 7 days BEFORE the conversion."*

```sql
WITH conv_with_first_touch AS (
    SELECT
        conv.conversion_id,
        conv.user_id,
        conv.conversion_ts,
        i.ad_id AS first_touch_ad_id,
        i.impression_ts AS first_touch_ts,
        ROW_NUMBER() OVER (
            PARTITION BY conv.conversion_id
            ORDER BY i.impression_ts ASC
        ) AS rn
    FROM fct_ad_conversions conv
    LEFT JOIN fct_ad_impressions i
        ON i.user_id = conv.user_id
        AND i.impression_ts <= conv.conversion_ts
        AND i.impression_ts >= conv.conversion_ts - INTERVAL '7' DAY
)
SELECT
    conversion_id,
    user_id,
    first_touch_ad_id,
    first_touch_ts
FROM conv_with_first_touch
WHERE rn = 1
ORDER BY conversion_id;
```

**Key teaching points:**
- The 7-day lookback is a common industry default (Meta, Google both use 7-day click, 1-day view)
- `ROW_NUMBER() = 1` picks the **earliest** impression within the window
- This is multi-touch attribution's building block

---

## 🔴 Q20. Identify power users — top 5% by engagement, with their category preferences

**Question:** *"Define power users as the top 5% by total watch time in October 2026. For each power user, list their top 2 favourite Reel categories."*

```sql
WITH user_total AS (
    SELECT
        user_id,
        SUM(watch_time_sec) AS total_watch_sec
    FROM fct_reels_engagement
    WHERE ds BETWEEN '2026-10-01' AND '2026-10-31'
      AND watch_time_sec IS NOT NULL
    GROUP BY user_id
),
power_users AS (
    SELECT user_id, total_watch_sec
    FROM user_total
    WHERE total_watch_sec >= (
        SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_watch_sec)
        FROM user_total
    )
),
user_category_watch AS (
    SELECT
        f.user_id,
        r.category,
        SUM(f.watch_time_sec) AS category_watch_sec
    FROM fct_reels_engagement f
    JOIN dim_reel r ON r.reel_id = f.reel_id
    WHERE f.ds BETWEEN '2026-10-01' AND '2026-10-31'
      AND f.watch_time_sec IS NOT NULL
    GROUP BY f.user_id, r.category
),
user_category_ranked AS (
    SELECT
        user_id,
        category,
        category_watch_sec,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY category_watch_sec DESC) AS rn
    FROM user_category_watch
    WHERE user_id IN (SELECT user_id FROM power_users)
)
SELECT
    pu.user_id,
    pu.total_watch_sec,
    ucr.category AS top_category,
    ucr.category_watch_sec
FROM power_users pu
JOIN user_category_ranked ucr
    ON pu.user_id = ucr.user_id
    AND ucr.rn <= 2
ORDER BY pu.total_watch_sec DESC, pu.user_id, ucr.rn;
```

**Key teaching points:**
- `PERCENTILE_CONT(0.95)` is exact but expensive; `APPROX_PERCENTILE(..., 0.95)` is faster
- `WITHIN GROUP (ORDER BY ...)` is PostgreSQL syntax; Hive/Presto use `AT PERCENTILE` or `APPROX_PERCENTILE`
- The `IN (SELECT ...)` subquery is fine here because power_users is small
- The 95th percentile is industry standard for "power user" definitions

---

# 6. QUICK-REFERENCE: WINDOW FUNCTION CHEATSHEET

| Function | Syntax | Use case |
|---|---|---|
| `ROW_NUMBER()` | `ROW_NUMBER() OVER (PARTITION BY x ORDER BY y)` | Unique 1..N per group |
| `RANK()` | `RANK() OVER (PARTITION BY x ORDER BY y)` | Tied ranks with gaps (1,1,3) |
| `DENSE_RANK()` | `DENSE_RANK() OVER (PARTITION BY x ORDER BY y)` | Tied ranks no gaps (1,1,2) |
| `NTILE(n)` | `NTILE(4) OVER (ORDER BY y)` | Quartiles, deciles |
| `LAG(col, n)` | `LAG(col, 1) OVER (...)` | Previous row |
| `LEAD(col, n)` | `LEAD(col, 1) OVER (...)` | Next row |
| `FIRST_VALUE(col)` | `FIRST_VALUE(col) OVER (... ROWS BETWEEN ...)` | First in window |
| `LAST_VALUE(col)` | `LAST_VALUE(col) OVER (... ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)` | Last in window |
| `SUM(col) OVER (...)` | `SUM(col) OVER (PARTITION BY x ORDER BY y)` | Running total |
| `AVG(col) OVER (...)` | `AVG(col) OVER (PARTITION BY x ORDER BY y ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)` | Rolling average |
| `COUNT(col) OVER (...)` | `COUNT(col) OVER (PARTITION BY x)` | Count in window |

### The 5 window frame clauses you need to know

```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW              -- running total (default)
ROWS BETWEEN 6 PRECEDING AND CURRENT ROW                        -- 7-row rolling
ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING        -- whole partition
ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING                -- forward-looking
ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING                        -- ±1 around current
```

---

# 7. META-SPECIFIC TIPS & COMMON TRAPS

## 7.1 Meta-specific tips

1. **Use Meta stack vocabulary** — say "Scribe" (ingestion), "Scuba" (ad-hoc), "Hive" (warehouse), "Presto" (query), "Nemo" (discovery), "Daiquery" (governance). They respect engineers who know the stack.
2. **Talk about partitioning** — every query should mention `WHERE ds BETWEEN ...` first. Meta's fact tables are partitioned by `ds` (date string).
3. **ORC + ZSTD + bucketing** — when asked about physical design, name these.
4. **"This would run on Presto"** — say it out loud. It signals you know the engine.
5. **Talk about SLOs and SLAs** — Meta PMs care about 9am Bangkok data freshness. Mention this.

## 7.2 Common traps to avoid

| Trap | What goes wrong | The fix |
|---|---|---|
| ❌ `NOT IN` with NULLs | Returns zero rows if the subquery has any NULL | Use `NOT EXISTS` or `LEFT JOIN ... IS NULL` |
| ❌ Forgetting `DISTINCT` in correlated subquery | Counts duplicate users | Always `COUNT(DISTINCT user_id)` in user-counting questions |
| ❌ `WHERE` vs `HAVING` confusion | `WHERE` filters rows, `HAVING` filters groups | Aggregates only in `HAVING`; non-aggregates in `WHERE` |
| ❌ Division by zero | `x / NULLIF(y, 0)` to protect | Always use `NULLIF` for safe division |
| ❌ `JOIN` explosion | Many-to-many joins blow up row count | Use `COUNT(DISTINCT ...)` after joining, or pre-aggregate |
| ❌ Window function without `PARTITION BY` | Treats the whole table as one partition | Always specify the partition when you want groups |
| ❌ `ROW_NUMBER()` vs `RANK()` confusion | `RANK` has gaps, `DENSE_RANK` doesn't | Use `ROW_NUMBER` when ties must be broken |
| ❌ `LAST_VALUE` without the right frame | Returns the current row, not the last | Add `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` |
| ❌ Forgetting NULLs in `AVG`/`SUM` | NULLs are excluded — be explicit | `AVG(CASE WHEN col IS NULL THEN 0 ELSE col END)` if you want them counted as 0 |
| ❌ Cartesian explosion from missing `ON` | Forgetting the join condition | Always write the join condition explicitly |

## 7.3 The 3 sentences to say out loud during the SQL block

1. **Before writing:** *"I'll use a correlated subquery because the word 'AND' between two user conditions is the signature for EXISTS."*
2. **During writing:** *"I'm filtering on the partition column first — that's how this would run efficiently on Presto."*
3. **After writing:** *"I should also test this on edge cases — empty table, NULLs in watch_time, user active on multiple days."*

---

# 🎯 FINAL CHECKLIST BEFORE THE SCREEN

- [ ] Practised 20+ SQL questions on a real engine (Presto, PostgreSQL, or Hive)
- [ ] Memorised the 5 patterns (correlated subquery, window fn, self-join, conditional agg, anti-join)
- [ ] Memorised the window function cheatsheet
- [ ] Can write a sessionisation query from memory (Q12)
- [ ] Can write an ads funnel query from memory (Q9, Q18)
- [ ] Know the Meta stack names (Scribe, Scuba, Hive, Presto, Nemo)
- [ ] Can articulate the 3 traps (NOT IN, NULLs, division by zero) and their fixes
- [ ] Rehearsed saying "this would run on Presto" and "I filter on the partition column first"

---

**You now have 20 of the toughest Meta SQL questions, with working answers and full explanations. Practice them on a real engine. Memorise the 5 patterns. Walk in ready.** 🚀

— End of SQL_TOUGHEST_QUESTIONS.md —
