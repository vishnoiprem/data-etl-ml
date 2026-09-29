# News Feed Engagement Analytics

## Problem
Facebook News Feed needs to analyze how stories (posts) perform: how often they were
shown, how users reacted, and how often they were shared. Each event has its own
grain and its own business meaning.

## How to Think
1. List the metrics:
   - Impressions per post, dwell time, completion-rate for video.
   - Reactions by type (like, love, haha, ...).
   - Shares by destination (timeline, group, DM, external).
2. Identify the grains:
   - `fact_post_impression`: one row per (viewer, post, render event).
   - `fact_post_reaction`: one row per (reactor, post, reaction type).
   - `fact_post_share`: one row per share event.
3. Pick fact-table type:
   - All three are transactional (event-level).
   - Optionally a `fact_post_daily` periodic snapshot for quick dashboard queries.
4. Dimensions and SCD:
   - `dim_post` SCD2 (post_type / page_or_profile can change).
   - `dim_user` SCD2 (country, locale, tenure shift over time).
   - `dim_device`, `dim_reaction_type` SCD1.

## How to Remember
- **Pattern**: "Metrics -> Grains -> Fact table types -> Dims with SCD."
- **Grain mnemonic**:
  - "One impression = one viewer saw one post once."
  - "One reaction = one user pressed one reaction type on one post."
  - "One share = one user shared one post once."
- A reaction is NOT an impression. Never collapse them.

## Schema (DDL)
```sql
CREATE TABLE fact_post_impression (
  impression_key BIGINT, post_key BIGINT, viewer_user_key BIGINT,
  author_user_key BIGINT, date_key INT, time_key INT,
  device_key INT, placement_key INT, is_video BOOLEAN, dwell_ms INT
);

CREATE TABLE fact_post_reaction (
  reaction_key BIGINT, post_key BIGINT, reactor_user_key BIGINT,
  author_user_key BIGINT, reaction_type_key INT,
  reaction_date_key INT, device_key INT
);

CREATE TABLE fact_post_share (
  share_key BIGINT, post_key BIGINT, sharer_user_key BIGINT,
  author_user_key BIGINT, share_destination_key INT, share_date_key INT
);

CREATE TABLE dim_post (
  post_key BIGINT, post_id VARCHAR(40), author_user_key BIGINT,
  post_type VARCHAR(20), page_or_profile VARCHAR(20),
  effective_from DATE, effective_to DATE, is_current BOOLEAN
);

CREATE TABLE dim_user (
  user_key BIGINT, user_id VARCHAR(40), age_bucket VARCHAR(10),
  gender VARCHAR(10), country VARCHAR(60), locale VARCHAR(20),
  tenure_days INT, effective_from DATE, effective_to DATE, is_current BOOLEAN
);

CREATE TABLE dim_reaction_type ( reaction_type_key INT, reaction_name VARCHAR(20), is_positive BOOLEAN );
CREATE TABLE dim_device ( device_key INT, device_type VARCHAR(20), os VARCHAR(20), browser VARCHAR(20) );
CREATE TABLE dim_date ( date_key INT PRIMARY KEY, full_date DATE, day_of_week VARCHAR(10), month INT, quarter INT, year INT );
```

## Common Mistakes
- Conflating reaction count and impression count in one fact -> wrong ratios.
- Using post_id (natural key) as the join key -> duplicates after edits.
- Forgetting to dimension `placement` (Top-of-feed vs inline changes dwell massively).
- Treating reactions as numeric "count" only; the type dimension is critical.

## AI Use Cases
- Predict post virality from early impression-to-share slope.
- Detect engagement-bait (high share, low dwell, low positive reaction).
- Recommend pages based on reaction co-occurrence vectors.

## Interview Questions (natural flow)

These escalate from scope to production reality. Ask in order; each answer unlocks the next.

### 1. Scope
> "Walk me through what News Feed analytics is supposed to answer. What's the daily question an ML engineer or ranking PM is asking?"

*Why it's natural:* anchors the model in a real consumer of the data, not the abstract idea of "engagement."

### 2. The split
> "You have three facts: impression, reaction, share. Why three instead of one `fact_engagement` wide table?"

*Why it's natural:* tests grain awareness. The cardinal-vice is mixing reactions with impressions and computing "engagement rate" — a non-additive ratio over a non-uniform denominator.

### 3. The metric trap
> "A junior analyst writes `AVG(reaction_count / impression_count)` to compute 'engagement rate.' What's wrong, and how would it show up in the dashboard?"

*Why it's natural:* classic interview answer. AVG-of-ratios is biased by post-level impression volume. The right metric is `SUM(reactions) / SUM(impressions)`.

### 4. Reaction ≠ impression
> "A user likes a post they've never seen in their feed (e.g. via a profile visit). Does that row land in `fact_post_impression`, `fact_post_reaction`, or both? Why?"

*Why it's natural:* tests understanding that impressions and reactions are different business events with different grains — the schema must allow them to exist independently.

### 5. The placement dimension
> "You have `placement_key`. PM asks why dwell time differs between 'Top of feed' and 'inline.' Walk me through the analysis."

*Why it's natural:* placement is the strongest confounder. Tests whether the candidate knows to *slice* a non-additive metric by placement before drawing conclusions.

### 6. SCD2 on dim_post
> "A post changes from 'photo' to 'video' (because the user swapped the media). For events from January, does it show up as photo or video in last-quarter's engagement analysis?"

*Why it's natural:* SCD2 application. Tests if the candidate understands that `effective_from/effective_to` on dim_post must align with the event timestamp.

### 7. Scale
> "10B impressions per day. What's the first thing to break, and what's the cheapest fix you'd ship?"

*Why it's natural:* signals production reality. Hot partitions on (post_key, date_key) are the usual answer; the fix is composite partitioning or pre-aggregation.

### 8. Edge case
> "A user reports 'I never saw this post in my feed, but I got 50 reactions on it.' Walk me through what the data model says vs what the UI says."

*Why it's natural:* tests whether the candidate can map between data semantics and user-facing reality. The data model may be right while the UI is broken — and vice versa.

## 30-Day Sample Data (January 2026)

Volume budget for a mid-size News Feed test cohort:

| Table | Rows |
|-------|------|
| `dim_date` | 31 |
| `dim_post` | 25 |
| `dim_user` | 31 (30 users, 1 SCD2 split for u-005 on Jan 18) |
| `dim_reaction_type` | 6 |
| `dim_device` | 5 |
| `dim_placement` | 4 |
| `fact_post_impression` | ~750 |
| `fact_post_reaction` | ~225 |
| `fact_post_share` | ~50 |

### Funnel ratios (sanity-check on the load)

```
reach rate (impressions / viewers):
  ~25 impressions per viewer over 31 days

reaction rate:
  ~30% of impressions yield a reaction (225 / 750)

share rate (of reacted):
  ~22% of reactors share (50 / 225)
```

### Sample queries that work against the 30-day load

```sql
-- The cardinal-vice ratio: engagement rate (CORRECT way).
SELECT p.post_type,
       COUNT(DISTINCT i.impression_key)                AS impressions,
       COUNT(DISTINCT r.reaction_key)                  AS reactions,
       COUNT(DISTINCT s.share_key)                     AS shares,
       ROUND(100.0 * COUNT(DISTINCT r.reaction_key)
                  / NULLIF(COUNT(DISTINCT i.impression_key), 0), 2)
                                                       AS reaction_rate_pct,
       ROUND(100.0 * COUNT(DISTINCT s.share_key)
                  / NULLIF(COUNT(DISTINCT r.reaction_key), 0), 2)
                                                       AS share_of_reaction_pct
FROM dim_post p
LEFT JOIN fact_post_impression i ON i.post_key = p.post_key
LEFT JOIN fact_post_reaction  r ON r.post_key = p.post_key
LEFT JOIN fact_post_share     s ON s.post_key = p.post_key
WHERE i.date_key BETWEEN 20260101 AND 20260131
GROUP BY p.post_type
ORDER BY impressions DESC;

-- Hour-of-day reach (uses time_key HHMM).
SELECT FLOOR(i.time_key / 100) AS hour_utc,
       COUNT(*)                AS impressions,
       ROUND(AVG(i.dwell_ms))  AS avg_dwell_ms
FROM fact_post_impression i
WHERE i.date_key BETWEEN 20260101 AND 20260131
GROUP BY FLOOR(i.time_key / 100)
ORDER BY hour_utc;

-- SCD2 demo: reactions from u-005 before and after RU->DE relocation.
-- He moved on Jan 18. Before that his country='RU'; after, country='DE'.
SELECT u.country,
       COUNT(*) AS reactions
FROM fact_post_reaction r
JOIN dim_user u
  ON u.user_key = r.reactor_user_key
 AND r.reaction_date_key >= u.effective_from
 AND (r.reaction_date_key < u.effective_to OR u.effective_to = '9999-12-31')
WHERE r.reactor_user_key = 5
GROUP BY u.country;
```

### Expected output (sanity check)

```
reaction_rate by post_type:
  video  ~31%
  photo  ~28%
  text   ~25%
  link   ~22%

share-of-reaction by post_type:
  video  ~24%
  photo  ~21%
  text   ~18%
  link   ~12%
  
  
  
```

Full row-by-row SQL is in `02_news_feed_engagement.py` (`DIM_DATE_30D_FEED`, `DIM_POST_30D`, `DIM_USER_30D`, `FACT_POST_IMPRESSION_30D`, `FACT_POST_REACTION_30D`, `FACT_POST_SHARE_30D`).


```
-- =========================================================
-- 1. TOTAL IMPRESSIONS
-- =========================================================

SELECT COUNT(*) AS total_impressions
FROM fact_post_impression;


-- =========================================================
-- 2. TOTAL REACTIONS
-- =========================================================

SELECT COUNT(*) AS total_reactions
FROM fact_post_reaction;


-- =========================================================
-- 3. TOTAL SHARES
-- =========================================================

SELECT COUNT(*) AS total_shares
FROM fact_post_share;


-- =========================================================
-- 4. TOP POSTS BY IMPRESSIONS
-- =========================================================

SELECT
    p.post_id,
    COUNT(*) AS impressions
FROM fact_post_impression i
JOIN dim_post p
    ON i.post_key = p.post_key
GROUP BY p.post_id
ORDER BY impressions DESC;


-- =========================================================
-- 5. TOP POSTS BY REACTIONS
-- =========================================================

SELECT
    p.post_id,
    COUNT(*) AS reactions
FROM fact_post_reaction r
JOIN dim_post p
    ON r.post_key = p.post_key
GROUP BY p.post_id
ORDER BY reactions DESC;


-- =========================================================
-- 6. TOP POSTS BY SHARES
-- =========================================================

SELECT
    p.post_id,
    COUNT(*) AS shares
FROM fact_post_share s
JOIN dim_post p
    ON s.post_key = p.post_key
GROUP BY p.post_id
ORDER BY shares DESC;


-- =========================================================
-- 7. REACTION RATE
-- =========================================================

SELECT
    p.post_id,
    COUNT(DISTINCT i.impression_key) AS impressions,
    COUNT(DISTINCT r.reaction_key) AS reactions,
    ROUND(
        100.0 *
        COUNT(DISTINCT r.reaction_key)
        / NULLIF(COUNT(DISTINCT i.impression_key),0),
        2
    ) AS reaction_rate_pct
FROM dim_post p
LEFT JOIN fact_post_impression i
    ON p.post_key=i.post_key
LEFT JOIN fact_post_reaction r
    ON p.post_key=r.post_key
GROUP BY p.post_id
ORDER BY reaction_rate_pct DESC;


-- =========================================================
-- 8. SHARE RATE
-- =========================================================

SELECT
    p.post_id,
    COUNT(DISTINCT r.reaction_key) AS reactions,
    COUNT(DISTINCT s.share_key) AS shares,
    ROUND(
        100.0 *
        COUNT(DISTINCT s.share_key)
        / NULLIF(COUNT(DISTINCT r.reaction_key),0),
        2
    ) AS share_rate_pct
FROM dim_post p
LEFT JOIN fact_post_reaction r
    ON p.post_key=r.post_key
LEFT JOIN fact_post_share s
    ON p.post_key=s.post_key
GROUP BY p.post_id
ORDER BY share_rate_pct DESC;


-- =========================================================
-- 9. VIRALITY SCORE
-- =========================================================

SELECT
    p.post_id,
    COUNT(DISTINCT s.share_key) AS shares,
    COUNT(DISTINCT i.impression_key) AS impressions,
    ROUND(
        COUNT(DISTINCT s.share_key)*100.0
        / NULLIF(COUNT(DISTINCT i.impression_key),0),
        2
    ) AS virality_score
FROM dim_post p
LEFT JOIN fact_post_impression i
    ON p.post_key=i.post_key
LEFT JOIN fact_post_share s
    ON p.post_key=s.post_key
GROUP BY p.post_id
ORDER BY virality_score DESC;


-- =========================================================
-- 10. CONTENT TYPE PERFORMANCE
-- =========================================================

SELECT
    p.post_type,
    COUNT(DISTINCT i.impression_key) AS impressions,
    COUNT(DISTINCT r.reaction_key) AS reactions,
    ROUND(
        COUNT(DISTINCT r.reaction_key)*100.0
        / NULLIF(COUNT(DISTINCT i.impression_key),0),
        2
    ) AS engagement_rate
FROM dim_post p
LEFT JOIN fact_post_impression i
    ON p.post_key=i.post_key
LEFT JOIN fact_post_reaction r
    ON p.post_key=r.post_key
GROUP BY p.post_type
ORDER BY engagement_rate DESC;


-- =========================================================
-- 11. REACTION BREAKDOWN
-- =========================================================

SELECT
    rt.reaction_name,
    COUNT(*) AS reactions
FROM fact_post_reaction r
JOIN dim_reaction_type rt
    ON r.reaction_type_key=rt.reaction_type_key
GROUP BY rt.reaction_name
ORDER BY reactions DESC;


-- =========================================================
-- 12. POSITIVE VS NEGATIVE REACTIONS
-- =========================================================

SELECT
    rt.is_positive,
    COUNT(*) AS reactions
FROM fact_post_reaction r
JOIN dim_reaction_type rt
ON r.reaction_type_key=rt.reaction_type_key
GROUP BY rt.is_positive;


-- =========================================================
-- 13. AVG DWELL TIME
-- =========================================================

SELECT
    ROUND(AVG(dwell_ms),0) AS avg_dwell_ms
FROM fact_post_impression;


-- =========================================================
-- 14. DWELL TIME BY POST TYPE
-- =========================================================

SELECT
    p.post_type,
    ROUND(AVG(i.dwell_ms),0) AS avg_dwell_ms
FROM fact_post_impression i
JOIN dim_post p
    ON i.post_key=p.post_key
GROUP BY p.post_type
ORDER BY avg_dwell_ms DESC;


-- =========================================================
-- 15. PLACEMENT ANALYSIS
-- =========================================================

SELECT
    placement_key,
    COUNT(*) AS impressions,
    ROUND(AVG(dwell_ms),0) AS avg_dwell
FROM fact_post_impression
GROUP BY placement_key;


-- =========================================================
-- 16. DEVICE ANALYSIS
-- =========================================================

SELECT
    d.device_type,
    COUNT(*) AS impressions
FROM fact_post_impression i
JOIN dim_device d
    ON i.device_key=d.device_key
GROUP BY d.device_type;


-- =========================================================
-- 17. MOBILE VS DESKTOP REACTIONS
-- =========================================================

SELECT
    d.device_type,
    COUNT(*) AS reactions
FROM fact_post_reaction r
JOIN dim_device d
    ON r.device_key=d.device_key
GROUP BY d.device_type;


-- =========================================================
-- 18. DAILY IMPRESSION TREND
-- =========================================================

SELECT
    date_key,
    COUNT(*) AS impressions
FROM fact_post_impression
GROUP BY date_key
ORDER BY date_key;


-- =========================================================
-- 19. DAILY REACTION TREND
-- =========================================================

SELECT
    reaction_date_key,
    COUNT(*) AS reactions
FROM fact_post_reaction
GROUP BY reaction_date_key
ORDER BY reaction_date_key;


-- =========================================================
-- 20. DAILY SHARE TREND
-- =========================================================

SELECT
    share_date_key,
    COUNT(*) AS shares
FROM fact_post_share
GROUP BY share_date_key
ORDER BY share_date_key;


-- =========================================================
-- 21. HOUR OF DAY ANALYSIS
-- =========================================================

SELECT
    FLOOR(time_key/100) AS hour,
    COUNT(*) AS impressions,
    ROUND(AVG(dwell_ms),0) AS avg_dwell
FROM fact_post_impression
GROUP BY FLOOR(time_key/100)
ORDER BY hour;


-- =========================================================
-- 22. TOP AUTHORS BY REACTIONS
-- =========================================================

SELECT
    author_user_key,
    COUNT(*) AS reactions
FROM fact_post_reaction
GROUP BY author_user_key
ORDER BY reactions DESC;


-- =========================================================
-- 23. TOP AUTHORS BY SHARES
-- =========================================================

SELECT
    author_user_key,
    COUNT(*) AS shares
FROM fact_post_share
GROUP BY author_user_key
ORDER BY shares DESC;


-- =========================================================
-- 24. SHARE DESTINATION ANALYSIS
-- =======================
```