-- =====================================================================
-- 06 — OLAP: Ad Platform Click & Impression Analytics  (star schema)
-- =====================================================================
-- Purpose: dashboards and ROI analyses for an ad platform. Analysts
-- answer questions like "what's the CTR per campaign?", "which
-- audience converts best?", "where's the cheapest conversion?".
--
-- Design notes:
--
--   * THREE SEPARATE FACT TABLES, NOT ONE.
--       - fact_impressions       grain = one ad view (billions/day)
--       - fact_clicks            grain = one ad click (millions/day)
--       - fact_conversions       grain = one conversion (thousands/day)
--     Why split: impressions outnumber clicks by ~1000:1. A single
--     fact would be 99.9% NULL on click-like columns and would not
--     compress well. Splitting lets each table be partitioned by
--     day_key and have a sparse-vs-dense layout tuned to its grain.
--
--   * CONFORMED DIMENSIONS.
--       - dim_date, dim_advertiser, dim_campaign
--     Shared across all three facts so joins "just work". dim_ad and
--     dim_audience are also shared but ad/audience properties can
--     change (SCD2).
--
--   * CTR IS STORED, NOT COMPUTED.
--     Storing click_count and impression_count makes "average CTR
--     across campaigns" = SUM(clicks) / SUM(impressions). The naive
--     alternative — AVG(ctr) — would be wrong because CTR is
--     non-additive (the cardinal-vice interview answer).
--
--   * CONVERSIONS IS A SEPARATE FACT BECAUSE IT JOINTS TO CLICK ID.
--     A conversion might come from a click 30 minutes, 30 hours, or
--     30 days later; the join is on click_id at lookback window. We
--     also denormalise ad_id + day_key on conversions so the fact
--     joins without traversing the click.
--
--   * AD SCD2 IS NEEDED for creative changes.
--     If the creative changes mid-campaign, the click-through rate of
--     the OLD creative and the NEW creative are different metrics.
--     SCD2 with valid_from/valid_to on dim_ads lets analysts answer
--     "CTR for the creative that was active at impression time".
-- =====================================================================

\echo '=== Loading OLAP ad platform star schema ==='

BEGIN;

-- ---------------------------------------------------------------------
-- 1) dim_date  (conformed)
-- ---------------------------------------------------------------------
CREATE TABLE dim_date (
    day_key        INT PRIMARY KEY,
    date_actual    DATE NOT NULL UNIQUE,
    day_of_week    SMALLINT NOT NULL,
    day_name       TEXT NOT NULL,
    week_of_year   SMALLINT NOT NULL,
    month_of_year  SMALLINT NOT NULL,
    month_name     TEXT NOT NULL,
    quarter        SMALLINT NOT NULL,
    year           SMALLINT NOT NULL,
    is_weekend     BOOLEAN NOT NULL,
    is_holiday     BOOLEAN NOT NULL DEFAULT FALSE,
    fiscal_quarter TEXT
);

-- ---------------------------------------------------------------------
-- 2) dim_advertiser  (rarely changes — no SCD2)
-- ---------------------------------------------------------------------
CREATE TABLE dim_advertiser (
    advertiser_key  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    advertiser_id   BIGINT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    industry        TEXT,
    country         CHAR(2),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- 3) dim_campaign  (slowly changing, but at a coarse grain)
-- ---------------------------------------------------------------------
-- Campaign-level changes (budget, status) deserve type 2, but for
-- brevity this file uses simple UPDATE-friendly columns. Add SCD2
-- columns if your campaign budget history matters.
CREATE TABLE dim_campaign (
    campaign_key    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    campaign_id     BIGINT NOT NULL UNIQUE,
    advertiser_key  BIGINT NOT NULL REFERENCES dim_advertiser(advertiser_key),
    name            TEXT NOT NULL,
    objective       TEXT CHECK (objective IN ('awareness','traffic','conversion','retargeting')),
    daily_budget_usd NUMERIC(12,2),
    start_date      DATE NOT NULL,
    end_date        DATE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- 4) dim_audience  (SCD2 — segments evolve)
-- ---------------------------------------------------------------------
CREATE TABLE dim_audience (
    audience_key    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    audience_id     BIGINT NOT NULL,
    name            TEXT NOT NULL,
    segment_type    TEXT NOT NULL,                         -- 'lookalike','interest','retargeting'
    size_estimate   BIGINT,
    valid_from      TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_to        TIMESTAMPTZ,
    is_current      BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_dim_aud_natural ON dim_audience(audience_id, is_current);

-- ---------------------------------------------------------------------
-- 5) dim_placement  (small, slowly changing)
-- ---------------------------------------------------------------------
CREATE TABLE dim_placement (
    placement_key   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    placement_code  TEXT NOT NULL UNIQUE,                   -- 'web_header','mobile_feed','video_pre_roll','native_inline'
    surface         TEXT NOT NULL,                         -- 'web','mobile','video','native'
    description     TEXT
);

INSERT INTO dim_placement (placement_code, surface, description) VALUES
    ('web_header',     'web',    'Above-the-fold web banner'),
    ('mobile_feed',    'mobile', 'In-feed mobile native'),
    ('mobile_banner',  'mobile', 'Mobile display banner'),
    ('video_pre_roll', 'video',  'Pre-roll video'),
    ('native_inline',  'native', 'Native inline content unit');

-- ---------------------------------------------------------------------
-- 6) dim_device  (junk-like, but it's its own dim)
-- ---------------------------------------------------------------------
CREATE TABLE dim_device (
    device_key      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    device_type     TEXT NOT NULL CHECK (device_type IN ('mobile','desktop','tablet','ctv','other')),
    os              TEXT NOT NULL CHECK (os IN ('ios','android','windows','macos','linux','other','roku','tvos')),
    browser         TEXT
);

-- ---------------------------------------------------------------------
-- 7) dim_ad  (SCD2 — creatives change OFTEN)
-- ---------------------------------------------------------------------
-- One row per (ad_id, valid_from). Multiple rows for the same ad_id
-- means the ad's creative/headline changed.
CREATE TABLE dim_ad (
    ad_key          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ad_id           BIGINT NOT NULL,
    campaign_key    BIGINT NOT NULL REFERENCES dim_campaign(campaign_key),
    creative_url    TEXT,
    headline        TEXT,
    body            TEXT,
    ctr_history_pct NUMERIC(5,2),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    valid_from      TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_to        TIMESTAMPTZ,
    is_current      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_dim_ad_natural ON dim_ad(ad_id, is_current);

-- ---------------------------------------------------------------------
-- 8) fact_impressions  (grain = one impression event per row)
-- ---------------------------------------------------------------------
-- This is the BIG fact. Partition by day_key for retention in
-- production. cost_per_mille_usd (CPM) is the cost of 1000 impressions.
CREATE TABLE fact_impressions (
    impression_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_ts           TIMESTAMPTZ NOT NULL,
    day_key            INT NOT NULL REFERENCES dim_date(day_key),
    ad_key             BIGINT NOT NULL REFERENCES dim_ad(ad_key),
    audience_key       BIGINT NOT NULL REFERENCES dim_audience(audience_key),
    placement_key      BIGINT NOT NULL REFERENCES dim_placement(placement_key),
    device_key         BIGINT NOT NULL REFERENCES dim_device(device_key),
    campaign_key       BIGINT NOT NULL REFERENCES dim_campaign(campaign_key),
    advertiser_key     BIGINT NOT NULL REFERENCES dim_advertiser(advertiser_key),
    cost_per_mille_usd NUMERIC(10,4) NOT NULL,              -- CPM bid
    was_viewable       BOOLEAN,                             -- MRC viewability
    was_clicked        BOOLEAN NOT NULL DEFAULT FALSE       -- denormalised from fact_clicks
);

CREATE INDEX idx_fact_imp_day_ad ON fact_impressions(day_key, ad_key);
CREATE INDEX idx_fact_imp_day_camp ON fact_impressions(day_key, campaign_key);

-- ---------------------------------------------------------------------
-- 9) fact_clicks  (grain = one click event per row)
-- ---------------------------------------------------------------------
-- click_id is the natural key. cost_per_click_usd is the CPC bid at
-- click time (CPC campaigns) or derived from CPM (CPM campaigns pay
-- on impression, not click, so this is NULL for those).
CREATE TABLE fact_clicks (
    click_id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_ts           TIMESTAMPTZ NOT NULL,
    day_key            INT NOT NULL REFERENCES dim_date(day_key),
    ad_key             BIGINT NOT NULL REFERENCES dim_ad(ad_key),
    impression_id      BIGINT REFERENCES fact_impressions(impression_id),
    audience_key       BIGINT NOT NULL REFERENCES dim_audience(audience_key),
    placement_key      BIGINT NOT NULL REFERENCES dim_placement(placement_key),
    device_key         BIGINT NOT NULL REFERENCES dim_device(device_key),
    campaign_key       BIGINT NOT NULL REFERENCES dim_campaign(campaign_key),
    advertiser_key     BIGINT NOT NULL REFERENCES dim_advertiser(advertiser_key),
    cost_per_click_usd NUMERIC(10,4),
    user_id            BIGINT,
    landing_page_url   TEXT
);

CREATE INDEX idx_fact_click_day_ad  ON fact_clicks(day_key, ad_key);
CREATE INDEX idx_fact_click_day_camp ON fact_clicks(day_key, campaign_key);
CREATE INDEX idx_fact_click_user    ON fact_clicks(user_id);
-- Reverse FK from fact_clicks.impression_id; the conversion-to-impression
-- trace follows clicks -> impressions. Without it, every impression lookup
-- is a sequential scan on fact_clicks.
CREATE INDEX idx_fact_click_impression ON fact_clicks(impression_id);

-- ---------------------------------------------------------------------
-- 10) fact_conversions  (grain = one conversion per row)
-- ---------------------------------------------------------------------
-- A conversion may follow a click minutes to days later. attribution_model
-- records how it was attributed (last_click, multi_touch, view_through).
CREATE TABLE fact_conversions (
    conversion_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_ts            TIMESTAMPTZ NOT NULL,
    day_key             INT NOT NULL REFERENCES dim_date(day_key),
    click_id            BIGINT REFERENCES fact_clicks(click_id),
    ad_key              BIGINT NOT NULL REFERENCES dim_ad(ad_key),
    audience_key        BIGINT NOT NULL REFERENCES dim_audience(audience_key),
    campaign_key        BIGINT NOT NULL REFERENCES dim_campaign(campaign_key),
    advertiser_key      BIGINT NOT NULL REFERENCES dim_advertiser(advertiser_key),
    user_id             BIGINT,
    revenue_usd         NUMERIC(12,2) NOT NULL,
    attribution_model   TEXT NOT NULL CHECK (attribution_model IN
                          ('last_click','first_click','multi_touch','view_through')),
    attribution_window_days INT NOT NULL DEFAULT 7,
    seconds_to_conversion INTEGER                             -- from click to conversion
);

CREATE INDEX idx_fact_conv_day_camp ON fact_conversions(day_key, campaign_key);
CREATE INDEX idx_fact_conv_click     ON fact_conversions(click_id);

-- =====================================================================
-- Sample data
-- =====================================================================

INSERT INTO dim_date (day_key, date_actual, day_of_week, day_name, week_of_year,
                      month_of_year, month_name, quarter, year, is_weekend, fiscal_quarter) VALUES
    (20260101, '2026-01-01', 4, 'Thursday', 1, 1, 'January', 1, 2026, FALSE, 'FY26-Q3'),
    (20260102, '2026-01-02', 5, 'Friday',   1, 1, 'January', 1, 2026, FALSE, 'FY26-Q3'),
    (20260103, '2026-01-03', 6, 'Saturday', 1, 1, 'January', 1, 2026, TRUE,  'FY26-Q3'),
    (20260115, '2026-01-15', 4, 'Thursday', 3, 1, 'January', 1, 2026, FALSE, 'FY26-Q3'),
    (20260201, '2026-02-01', 7, 'Sunday',   5, 2, 'February',1, 2026, TRUE,  'FY26-Q4');

INSERT INTO dim_advertiser (advertiser_id, name, industry, country) VALUES
    (1, 'Acme Inc.',     'retail',  'US'),
    (2, 'Globex Corp.',  'software','GB'),
    (3, 'Initech',       'finance', 'DE');

INSERT INTO dim_campaign (campaign_id, advertiser_key, name, objective, daily_budget_usd, start_date, end_date) VALUES
    (101, 1, 'Spring sale 2026',   'conversion', 5000.00, '2026-01-01', '2026-03-31'),
    (102, 2, 'SaaS awareness Q1',  'awareness',  10000.00,'2026-01-15', '2026-04-15'),
    (103, 3, 'Retargeting cart',  'retargeting', 3000.00, '2026-01-10', NULL);

INSERT INTO dim_audience (audience_id, name, segment_type, size_estimate) VALUES
    (1, 'US women 25-44',     'interest',  12000000),
    (2, 'Lookalike purchasers','lookalike', 2500000),
    (3, 'Cart abandoners',    'retargeting',500000);

INSERT INTO dim_device (device_type, os, browser) VALUES
    ('mobile',  'ios',     'safari'),
    ('mobile',  'android', 'chrome'),
    ('desktop', 'windows', 'chrome'),
    ('desktop', 'macos',   'safari'),
    ('ctv',     'tvos',    NULL);

INSERT INTO dim_ad (ad_id, campaign_key, creative_url, headline, body) VALUES
    (501, 1, 'https://cdn.example.com/spring-1.jpg', 'Spring Sale! 20% Off',     'Limited time offer'),
    (502, 1, 'https://cdn.example.com/spring-2.jpg', 'New Arrivals',             'Shop the new collection'),
    (503, 2, 'https://cdn.example.com/saas-a.jpg',   'Built for scale',          'Try free for 30 days'),
    (504, 3, 'https://cdn.example.com/cart.jpg',     'You left items in your cart','Complete your order');

-- 5000 impressions, 200 clicks (CTR ~4%), 12 conversions.
-- Note: surrogate keys (ad_key, audience_key etc) start at 1 and are
-- allocated by IDENTITY, so we modulo into [1..N] per dim.
INSERT INTO fact_impressions (event_ts, day_key, ad_key, audience_key, placement_key, device_key, campaign_key, advertiser_key, cost_per_mille_usd, was_viewable, was_clicked)
SELECT
    TIMESTAMP'2026-01-15 10:00:00' + MAKE_INTERVAL(0,0,0,0,0,0, gs % 60000),
    20260115,
    ((gs % 4) + 1),                                        -- ad_key 1..4
    ((gs % 3) + 1),                                        -- audience 1..3
    ((gs % 4) + 1),                                        -- placement 1..4
    ((gs % 5) + 1),                                        -- device 1..5
    ((gs % 3) + 1),                                        -- campaign 1..3
    ((gs % 3) + 1),                                        -- advertiser 1..3
    CASE WHEN gs % 4 = 0 THEN 5.0000
         WHEN gs % 4 = 1 THEN 3.5000
         ELSE 8.0000 END,
    gs % 10 <> 0,                                          -- 90% viewable
    gs % 25 = 0                                            -- 4% clicked
FROM generate_series(0, 4999) gs;

-- Clicks reference real impressions via (impression_id). Since the
-- synthetic seed marks every 25th impression as clicked, we look up
-- the corresponding impression_id and pull its ad/placement/etc.
INSERT INTO fact_clicks (event_ts, day_key, ad_key, impression_id, audience_key, placement_key, device_key, campaign_key, advertiser_key, cost_per_click_usd, user_id)
SELECT
    TIMESTAMP'2026-01-15 10:01:00' + MAKE_INTERVAL(0,0,0,0,0,0, gs % 60000),
    i.day_key, i.ad_key, i.impression_id, i.audience_key, i.placement_key,
    i.device_key, i.campaign_key, i.advertiser_key,
    CASE WHEN gs % 3 = 0 THEN 1.20
         WHEN gs % 3 = 1 THEN 0.85
         ELSE 1.50 END,
    1000 + gs
FROM generate_series(0, 199) gs
JOIN fact_impressions i ON i.impression_id = (gs * 25 + 1);   -- the 200 clicked impressions

-- 12 conversions, mostly on retargeting (ad_key 4, audience 3, campaign 3).
INSERT INTO fact_conversions (event_ts, day_key, click_id, ad_key, audience_key, campaign_key, advertiser_key, user_id, revenue_usd, attribution_model, attribution_window_days, seconds_to_conversion)
SELECT
    TIMESTAMP'2026-01-15 10:01:30' + MAKE_INTERVAL(0,0,0,0,0,0, gs * 1800),
    20260115,
    gs + 1,
    4,                                                     -- all on retargeting ad
    3,                                                     -- cart abandoners
    3,                                                     -- retargeting campaign
    3,                                                     -- Initech advertiser
    1000 + gs,
    CASE WHEN gs < 4 THEN 49.00
         WHEN gs < 8 THEN 78.00
         ELSE 129.00 END,
    'last_click',
    7,
    30 + gs * 60
FROM generate_series(0, 11) gs;

COMMIT;

-- =====================================================================
-- Self-verifying queries
-- =====================================================================

\echo ''
\echo '--- Q1: CTR per campaign (the correct way: sum-of-clicks / sum-of-impressions) ---'
-- CTR is non-additive: the right denominator is the same denominator as
-- the numerator joins against. We pre-aggregate impressions and clicks
-- per campaign in CTEs (no cross-join), then divide. This is the
-- canonical interview answer.
WITH imp_per_campaign AS (
    SELECT campaign_key, COUNT(*) AS impressions
    FROM fact_impressions GROUP BY campaign_key
),
clk_per_campaign AS (
    SELECT campaign_key, COUNT(*) AS clicks
    FROM fact_clicks GROUP BY campaign_key
)
SELECT c.name,
       COALESCE(i.impressions, 0)  AS impressions,
       COALESCE(cl.clicks, 0)     AS clicks,
       ROUND(100.0 * COALESCE(cl.clicks, 0) / NULLIF(i.impressions, 0), 2) AS ctr_pct
FROM dim_campaign c
LEFT JOIN imp_per_campaign i   ON i.campaign_key = c.campaign_key
LEFT JOIN clk_per_campaign cl ON cl.campaign_key = c.campaign_key
ORDER BY ctr_pct DESC NULLS LAST;

\echo ''
\echo '--- Q2: CTR per placement (placement × surface) ---'
WITH imp_per_placement AS (
    SELECT placement_key, COUNT(*) AS impressions
    FROM fact_impressions GROUP BY placement_key
),
clk_per_placement AS (
    SELECT placement_key, COUNT(*) AS clicks
    FROM fact_clicks GROUP BY placement_key
)
SELECT p.surface, p.placement_code,
       COALESCE(i.impressions, 0) AS impressions,
       COALESCE(cl.clicks, 0)     AS clicks,
       ROUND(100.0 * COALESCE(cl.clicks, 0) / NULLIF(i.impressions, 0), 2) AS ctr_pct
FROM dim_placement p
LEFT JOIN imp_per_placement i ON i.placement_key = p.placement_key
LEFT JOIN clk_per_placement cl ON cl.placement_key = p.placement_key
ORDER BY ctr_pct DESC NULLS LAST;

\echo ''
\echo '--- Q3: CPC vs CPM mix at the campaign level ---'
-- A campaign is either CPM-bid (charged per impression, NULL CPC) or
-- CPC-bid (charged per click, NULL CPM). Spend is computed per grain.
WITH imp_per_campaign AS (
    SELECT campaign_key, COUNT(*) AS impressions
    FROM fact_impressions GROUP BY campaign_key
),
clk_per_campaign AS (
    SELECT campaign_key, COUNT(*) AS clicks,
           ROUND(SUM(cost_per_click_usd)::numeric, 2) AS cpc_spend
    FROM fact_clicks GROUP BY campaign_key
),
cpm_per_campaign AS (
    -- CPM = (count of impressions at this CPM) * CPM / 1000.
    -- One campaign can have ads at multiple CPMs; roll them up.
    SELECT campaign_key,
           ROUND(SUM(cost_per_mille_usd * cnt) / 1000, 2) AS cpm_spend
    FROM (
        SELECT campaign_key, cost_per_mille_usd, COUNT(*) AS cnt
        FROM fact_impressions
        GROUP BY campaign_key, cost_per_mille_usd
    ) per_ad_cpm
    GROUP BY campaign_key
)
SELECT c.name,
       i.impressions,
       COALESCE(cl.clicks, 0) AS clicks,
       cpm.cpm_spend,
       cl.cpc_spend
FROM dim_campaign c
LEFT JOIN imp_per_campaign i   ON i.campaign_key = c.campaign_key
LEFT JOIN clk_per_campaign cl ON cl.campaign_key = c.campaign_key
LEFT JOIN cpm_per_campaign cpm ON cpm.campaign_key = c.campaign_key
ORDER BY c.name;

\echo ''
\echo '--- Q4: conversion rate and revenue per audience ---'
SELECT au.name AS audience,
       COUNT(DISTINCT conv.conversion_id) AS conversions,
       COUNT(DISTINCT cl.click_id)         AS clicks,
       ROUND(100.0 * COUNT(DISTINCT conv.conversion_id) / NULLIF(COUNT(DISTINCT cl.click_id),0), 2) AS cvr_pct,
       ROUND(SUM(conv.revenue_usd)::numeric, 2) AS revenue_usd
FROM dim_audience au
LEFT JOIN fact_clicks cl ON cl.audience_key = au.audience_key
LEFT JOIN fact_conversions conv ON conv.click_id = cl.click_id
GROUP BY au.name
ORDER BY revenue_usd DESC;

\echo ''
\echo '--- Q5: ROAS (return on ad spend) per advertiser ---'
-- ROAS = revenue / spend. Spend = CPM-impressions-paid + CPC-clicks-paid.
-- Pre-aggregate each cost source to one row per advertiser so the
-- outer query can simply SUM/DIVIDE without nested aggregation.
WITH cpm_per_adv AS (
    SELECT advertiser_key,
           SUM(cost_per_mille_usd * cnt) / 1000 AS cpm_spend
    FROM (
        SELECT advertiser_key, cost_per_mille_usd, COUNT(*) AS cnt
        FROM fact_impressions GROUP BY advertiser_key, cost_per_mille_usd
    ) per_ad GROUP BY advertiser_key
),
cpc_per_adv AS (
    SELECT advertiser_key, ROUND(SUM(cost_per_click_usd)::numeric, 2) AS cpc_spend
    FROM fact_clicks GROUP BY advertiser_key
),
rev_per_adv AS (
    SELECT advertiser_key, ROUND(SUM(revenue_usd)::numeric, 2) AS revenue
    FROM fact_conversions GROUP BY advertiser_key
)
SELECT a.name AS advertiser,
       COALESCE(r.revenue, 0)              AS revenue,
       ROUND((cpm.cpm_spend + COALESCE(cpc.cpc_spend, 0))::numeric, 2) AS spend,
       ROUND(100.0 * r.revenue / NULLIF(cpm.cpm_spend + COALESCE(cpc.cpc_spend, 0), 0), 2) AS roas_pct
FROM dim_advertiser a
LEFT JOIN cpm_per_adv cpm ON cpm.advertiser_key = a.advertiser_key
LEFT JOIN cpc_per_adv cpc ON cpc.advertiser_key = a.advertiser_key
LEFT JOIN rev_per_adv r   ON r.advertiser_key = a.advertiser_key
ORDER BY roas_pct DESC NULLS LAST;

\echo ''
\echo '--- Q6: time-from-click-to-conversion (seconds_to_conversion) ---'
SELECT
    MIN(seconds_to_conversion) AS min_sec,
    ROUND(AVG(seconds_to_conversion)::numeric, 1) AS avg_sec,
    MAX(seconds_to_conversion) AS max_sec,
    COUNT(*) AS conversions
FROM fact_conversions;

\echo ''
\echo '--- Q7: view-through vs last-click attribution (cross-check) ---'
SELECT attribution_model, COUNT(*) AS conversions,
       ROUND(SUM(revenue_usd)::numeric, 2) AS revenue_usd
FROM fact_conversions
GROUP BY attribution_model
ORDER BY revenue_usd DESC;

\echo ''
\echo '--- Q8: device-level CTR (mobile vs desktop vs CTV) ---'
-- Same pattern as Q1/Q2: pre-aggregate per device in CTEs, then divide.
-- Avoids the Cartesian product of joining clicks to all impressions on
-- (day_key, ad_key).
WITH imp_per_device AS (
    SELECT device_key, COUNT(*) AS impressions
    FROM fact_impressions GROUP BY device_key
),
clk_per_device AS (
    SELECT device_key, COUNT(*) AS clicks
    FROM fact_clicks GROUP BY device_key
)
SELECT d.device_type,
       COALESCE(i.impressions, 0) AS impressions,
       COALESCE(cl.clicks, 0)     AS clicks,
       ROUND(100.0 * COALESCE(cl.clicks, 0) / NULLIF(i.impressions, 0), 2) AS ctr_pct
FROM dim_device d
LEFT JOIN imp_per_device i ON i.device_key = d.device_key
LEFT JOIN clk_per_device cl ON cl.device_key = d.device_key
ORDER BY ctr_pct DESC NULLS LAST;

\echo ''
\echo '=== Done: OLAP ad platform star schema ==='
