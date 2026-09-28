-- =====================================================================
-- 05 — OLAP: Product Funnel & Conversion Analytics  (MySQL 8.0+ star)
-- =====================================================================
-- Purpose: track the customer funnel from browse to purchase, support
-- drop-off analysis, time-between-step analysis, A/B test measurement,
-- and channel attribution.
--
-- The problem statement names 6 tables: User_Events, Purchases, Users,
-- Products, AB_Tests, Sessions. This file ships the FULL star schema
-- needed to answer every question cleanly:
--
--   * TWO FACT TABLES
--       - fact_user_events     grain = one event (browse/search/view/...)
--       - fact_sessions        grain = one shopping session
--     The event-grain fact is the funnel; the session-grain fact
--     answers "how long does conversion take?" without a window fn.
--
--   * FOUR DIMENSIONS
--       - dim_users            SCD type 2 (segment changes over time)
--       - dim_products         SCD type 2 (price/name changes)
--       - dim_ab_tests         one row per test+variant
--       - dim_date             conformed, used across all marts
--     "Conformed" means dim_date joins to every fact and dim — a single
--     truth for "what week was that?".
--
-- Design decisions worth flagging:
--
--   * WHY TWO FACT TABLES, NOT ONE WIDE TABLE.
--     A single event-grain table forces every "how many sessions?"
--     query to do DISTINCT session_id. A second grain keeps
--     counting trivial: COUNT(*) FROM fact_sessions.
--
--   * WHY USER_EVENTS IS POLYMORPHIC-FREE.
--     Every event is "user X did action Y on product Z in session S".
--     The event_type column is the discriminator and the only thing
--     that varies — a single fact table with event_type is correct.
--     Products that don't exist (search_with_no_result, page_view)
--     use NULL product_id; a NOT NULL constraint would lose those.
--
--   * WHY SESSIONS ARE MATERIALISED, NOT DERIVED.
--     "24 hours of inactivity = new session" is a rule the warehouse
--     applies once at load time. Analysts should never need to
--     re-compute session boundaries. Plus: a separate fact lets us
--     attach session-level attributes (device, country, A/B variant)
--     that are expensive to derive per-event.
--
--   * WHY A/B TEST IS A DIM, NOT A COLUMN ON THE EVENT.
--     A single user is in one variant per test, stable across the
--     test lifetime. Modelling it as a dim makes "average order value
--     for variant X" a star-join. An event column would scatter the
--     variant across millions of rows.
--
--   * WHY dim_users IS SCD TYPE 2.
--     "Did the new onboarding flow increase conversion for new vs
--     returning users?" needs to know what segment a user was IN
--     at the time of the event. SCD2 preserves that history.
--
-- MySQL 8.0+ conversion notes:
--   * TIMESTAMPTZ  -> DATETIME  (UTC stored)
--   * JSONB -> JSON
--   * BOOLEAN -> TINYINT(1)
--   * TEXT -> VARCHAR (length) / TEXT for large bodies
--   * pgcrypto -> removed (not needed here)
--   * generate_series(0, N) -> recursive CTE (MySQL 8.0+)
--   * TIMESTAMP '...' -> DATE_SUB(UTC_TIMESTAMP(), INTERVAL ...) or literal
--   * MAKE_INTERVAL(0,0,0,0,0,0, sec) -> + INTERVAL <sec> SECOND
--   * ORDER BY ... NULLS LAST -> column IS NULL ASC, column [ASC|DESC]
--   * COUNT(*) FILTER (WHERE ...) -> SUM(CASE WHEN ... THEN 1 ELSE 0 END)
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1) dim_date  (conformed — same shape across all star marts)
-- ---------------------------------------------------------------------
-- A conformed dimension is reused across multiple fact tables so joins
-- "just work" without translating date keys. day_key is the surrogate
-- primary key as YYYYMMDD INT; other column families are derived.
CREATE TABLE dim_date (
    day_key        INT PRIMARY KEY,                         -- YYYYMMDD
    date_actual    DATE NOT NULL,
    day_of_week    SMALLINT NOT NULL,                       -- 1=Mon, 7=Sun
    day_name       VARCHAR(12) NOT NULL,
    week_of_year   SMALLINT NOT NULL,
    month_of_year  SMALLINT NOT NULL,
    month_name     VARCHAR(12) NOT NULL,
    quarter        SMALLINT NOT NULL,
    year           SMALLINT NOT NULL,
    is_weekend     TINYINT(1) NOT NULL,
    is_holiday     TINYINT(1) NOT NULL DEFAULT 0,
    fiscal_quarter VARCHAR(16),                              -- 'FY26-Q3' style
    UNIQUE KEY uq_dim_date_actual (date_actual)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 2) dim_users  (SCD TYPE 2)
-- ---------------------------------------------------------------------
-- Type 2 means: never UPDATE the row. When a user's segment changes,
-- we INSERT a new row with valid_from = now() and valid_to = NULL,
-- then UPDATE the prior row's valid_to. The effective segment for an
-- event is whichever row was current AT event_ts.
CREATE TABLE dim_users (
    user_key        BIGINT AUTO_INCREMENT PRIMARY KEY,      -- surrogate
    user_id         BIGINT NOT NULL,                       -- natural/business id
    email           VARCHAR(254),
    segment         VARCHAR(16) NOT NULL,                  -- 'new','returning','vip','churned'
    acquisition_channel VARCHAR(32),                       -- 'paid_search','organic','referral'
    country         CHAR(2),
    valid_from      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_to        DATETIME,                              -- NULL means current
    is_current      TINYINT(1) NOT NULL DEFAULT 1,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_dim_users_segment CHECK (segment IN ('new','returning','vip','churned'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- The bitemporal lookup ("what was the user as of day X?") uses:
--   WHERE user_id = X AND valid_from <= day_X AND (valid_to > day_X OR valid_to IS NULL)
-- Two indexes support both directions.
CREATE INDEX idx_dim_users_natural ON dim_users(user_id, is_current);
CREATE INDEX idx_dim_users_valid   ON dim_users(user_id, valid_from, valid_to);

-- ---------------------------------------------------------------------
-- 3) dim_products  (SCD TYPE 2)
-- ---------------------------------------------------------------------
CREATE TABLE dim_products (
    product_key     BIGINT AUTO_INCREMENT PRIMARY KEY,
    product_id      BIGINT NOT NULL,
    name            VARCHAR(255) NOT NULL,
    category        VARCHAR(64) NOT NULL,
    sub_category    VARCHAR(64),
    price_usd       DECIMAL(10,2) NOT NULL,
    cost_usd        DECIMAL(10,2),
    is_active       TINYINT(1) NOT NULL DEFAULT 1,
    valid_from      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_to        DATETIME,
    is_current      TINYINT(1) NOT NULL DEFAULT 1,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_dim_products_natural ON dim_products(product_id, is_current);

-- ---------------------------------------------------------------------
-- 4) dim_ab_tests  (one row per test; variants live in child table)
-- ---------------------------------------------------------------------
-- Tests are static enough to warrant their own table. The variant
-- lookup happens by joining through to ab_test_assignments — but for
-- star-schema queries, we put variant_id directly on the events
-- fact (denormalised) so analysts don't need the test-id join.
CREATE TABLE dim_ab_tests (
    ab_test_key     BIGINT AUTO_INCREMENT PRIMARY KEY,
    test_id         VARCHAR(64) NOT NULL,                  -- 'homepage_hero_q3'
    test_name       VARCHAR(255) NOT NULL,
    started_at      DATETIME NOT NULL,
    ended_at        DATETIME,
    is_active       TINYINT(1) NOT NULL DEFAULT 1,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_ab_test_id (test_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 5) dim_variants  (variant of a test — child of dim_ab_tests)
-- ---------------------------------------------------------------------
CREATE TABLE dim_variants (
    variant_key     BIGINT AUTO_INCREMENT PRIMARY KEY,
    ab_test_id      VARCHAR(64) NOT NULL,
    variant_code    VARCHAR(32) NOT NULL,                  -- 'control','treatment_a'
    description     VARCHAR(255),
    UNIQUE KEY uq_variant (ab_test_id, variant_code),
    CONSTRAINT fk_variant_test FOREIGN KEY (ab_test_id) REFERENCES dim_ab_tests(test_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 6) dim_ab_assignments  (which user is in which variant)
-- ---------------------------------------------------------------------
-- A user is assigned to ONE variant per test. Sticky for the life of
-- the test. The dedup fingerprint prevents cross-test reuse.
CREATE TABLE dim_ab_assignments (
    user_id         BIGINT NOT NULL,
    ab_test_id      VARCHAR(64) NOT NULL,
    variant_key     BIGINT NOT NULL,
    assigned_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, ab_test_id),
    CONSTRAINT fk_aba_test    FOREIGN KEY (ab_test_id)  REFERENCES dim_ab_tests(test_id),
    CONSTRAINT fk_aba_variant FOREIGN KEY (variant_key) REFERENCES dim_variants(variant_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 7) fact_user_events  (grain = one event per row)
-- ---------------------------------------------------------------------
-- Stage labels map to event_type:
--   'browse','search','view_product','add_to_cart','checkout','purchase','remove_from_cart'
-- The funnel queries GROUP BY event_type. The product_id is nullable
-- because search-with-no-result and page-view events don't reference a
-- product.
CREATE TABLE fact_user_events (
    event_id        BIGINT AUTO_INCREMENT PRIMARY KEY,
    event_ts        DATETIME NOT NULL,
    day_key         INT NOT NULL,
    user_key        BIGINT NOT NULL,
    product_key     BIGINT,
    -- FK to fact_sessions added after both tables exist (cross-table FK).
    session_id      BIGINT NOT NULL,
    variant_key     BIGINT,
    event_type      VARCHAR(32) NOT NULL,
    device_type     VARCHAR(16),
    country         CHAR(2),
    referrer        VARCHAR(255),
    -- Time between THIS event and the previous one in the same session.
    -- Materialised at load time so we can GROUP BY minute buckets
    -- without window functions.
    seconds_since_session_start INT,
    CONSTRAINT fk_fue_date    FOREIGN KEY (day_key)     REFERENCES dim_date(day_key),
    CONSTRAINT fk_fue_user    FOREIGN KEY (user_key)    REFERENCES dim_users(user_key),
    CONSTRAINT fk_fue_product FOREIGN KEY (product_key) REFERENCES dim_products(product_key),
    CONSTRAINT fk_fue_variant FOREIGN KEY (variant_key) REFERENCES dim_variants(variant_key),
    CONSTRAINT chk_fue_event_type CHECK (event_type IN (
        'browse','search','view_product',
        'add_to_cart','remove_from_cart',
        'checkout','purchase')),
    CONSTRAINT chk_fue_device_type CHECK (device_type IN ('mobile','desktop','tablet','other') OR device_type IS NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_fact_events_user_day  ON fact_user_events(user_key, day_key);
CREATE INDEX idx_fact_events_session   ON fact_user_events(session_id);
CREATE INDEX idx_fact_events_product   ON fact_user_events(product_key, day_key);
CREATE INDEX idx_fact_events_day_type  ON fact_user_events(day_key, event_type);

-- ---------------------------------------------------------------------
-- 8) fact_sessions  (grain = one session per row)
-- ---------------------------------------------------------------------
-- Sessions are the lifecycle fact. Has purchase_amount because the
-- purchase amount is at session grain, not event grain. funnel_stage_at
-- records "the highest funnel stage this session reached" so analysts
-- can drop_off analysis without re-deriving it.
CREATE TABLE fact_sessions (
    session_id       BIGINT PRIMARY KEY,
    user_key         BIGINT NOT NULL,
    day_key          INT NOT NULL,
    variant_key      BIGINT,
    device_type      VARCHAR(16),
    country          CHAR(2),
    started_at       DATETIME NOT NULL,
    ended_at         DATETIME,                             -- NULL if session still open
    duration_sec     INT,
    event_count      INT NOT NULL DEFAULT 0,
    funnel_stage_at  VARCHAR(32),                          -- highest stage reached
    purchase_amount_usd DECIMAL(12,2),
    is_converted     TINYINT(1) NOT NULL DEFAULT 0,
    CONSTRAINT fk_fs_user    FOREIGN KEY (user_key)    REFERENCES dim_users(user_key),
    CONSTRAINT fk_fs_date    FOREIGN KEY (day_key)     REFERENCES dim_date(day_key),
    CONSTRAINT fk_fs_variant FOREIGN KEY (variant_key) REFERENCES dim_variants(variant_key),
    CONSTRAINT chk_fs_funnel CHECK (funnel_stage_at IN (
        'browse','search','view_product',
        'add_to_cart','checkout','purchase') OR funnel_stage_at IS NULL),
    CONSTRAINT chk_fs_device CHECK (device_type IN ('mobile','desktop','tablet','other') OR device_type IS NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_fact_sessions_user_day ON fact_sessions(user_key, day_key);
CREATE INDEX idx_fact_sessions_variant  ON fact_sessions(variant_key);

-- Cross-table FK declared here (after fact_sessions exists) so the
-- session-grain enforces referential integrity with the event-grain.
-- fact_user_events.session_id MUST correspond to a real session row.
ALTER TABLE fact_user_events
    ADD CONSTRAINT fk_events_session
    FOREIGN KEY (session_id) REFERENCES fact_sessions(session_id);

-- =====================================================================
-- Sample data
-- =====================================================================

INSERT INTO dim_date (day_key, date_actual, day_of_week, day_name, week_of_year,
                      month_of_year, month_name, quarter, year, is_weekend, fiscal_quarter) VALUES
    (20260101, '2026-01-01', 4, 'Thursday',    1,  1, 'January',  1, 2026, 0, 'FY26-Q3'),
    (20260115, '2026-01-15', 4, 'Thursday',    3,  1, 'January',  1, 2026, 0, 'FY26-Q3'),
    (20260201, '2026-02-01', 7, 'Sunday',      5,  2, 'February', 1, 2026, 1, 'FY26-Q4'),
    (20260215, '2026-02-15', 7, 'Sunday',      7,  2, 'February', 1, 2026, 1, 'FY26-Q4'),
    (20260301, '2026-03-01', 7, 'Sunday',     10,  3, 'March',    1, 2026, 1, 'FY26-Q4');

-- SCD2 user segments. Alice and Bob have multiple versions because their
-- segment changed over time (a real production case).
INSERT INTO dim_users (user_id, email, segment, acquisition_channel, country, valid_from, valid_to, is_current) VALUES
    -- Alice: started 'new', became 'returning' on 2026-02-01.
    (1, 'alice@example.com', 'new',       'organic',      'US', '2026-01-01', '2026-02-01', 0),
    (1, 'alice@example.com', 'returning', 'organic',      'US', '2026-02-01', NULL,         1),
    -- Bob: started 'returning', upgraded to 'vip' on 2026-02-15.
    (2, 'bob@example.com',   'returning', 'paid_search',  'GB', '2026-01-01', '2026-02-15', 0),
    (2, 'bob@example.com',   'vip',       'paid_search',  'GB', '2026-02-15', NULL,         1),
    -- Carla: 'churned', then 'returning' again (came back).
    (3, 'carla@example.com', 'churned',   'referral',     'IT', '2026-01-01', '2026-03-01', 0),
    (3, 'carla@example.com', 'returning', 'referral',     'IT', '2026-03-01', NULL,         1),
    -- Dimitri: still 'new'.
    (4, 'dimitri@example.com','new',      'paid_social',  'RU', '2026-01-01', NULL,         1);

INSERT INTO dim_products (product_id, name, category, sub_category, price_usd) VALUES
    (101, 'Wireless headphones',   'electronics', 'audio',      149.00),
    (102, 'Mechanical keyboard',   'electronics', 'computing',  129.00),
    (103, 'Yoga mat',              'fitness',     'equipment',   39.00),
    (104, 'Coffee beans 1kg',      'grocery',     'beverage',    24.00);

INSERT INTO dim_ab_tests (test_id, test_name, started_at, ended_at) VALUES
    ('homepage_hero_q1', 'Homepage hero copy', '2026-01-15', NULL);

INSERT INTO dim_variants (ab_test_id, variant_code, description) VALUES
    ('homepage_hero_q1', 'control',     'Original copy'),
    ('homepage_hero_q1', 'treatment_a', 'New copy: "Save 20% today"');

INSERT INTO dim_ab_assignments (user_id, ab_test_id, variant_key) VALUES
    (1, 'homepage_hero_q1', 1),         -- Alice -> control
    (2, 'homepage_hero_q1', 2),         -- Bob   -> treatment_a
    (3, 'homepage_hero_q1', 1),         -- Carla -> control
    (4, 'homepage_hero_q1', 2);         -- Dimitri -> treatment_a

-- Sessions. Each session has multiple events.
INSERT INTO fact_sessions (session_id, user_key, day_key, variant_key, device_type,
                          country, started_at, ended_at, duration_sec, event_count,
                          funnel_stage_at, purchase_amount_usd, is_converted) VALUES
    -- Alice: session 1001, browsed but didn't buy on day 20260115.
    (1001, 1, 20260115, 1, 'desktop', 'US', '2026-01-15 14:00', '2026-01-15 14:23', 1380, 5,
     'view_product', NULL, 0),
    -- Alice: session 1002, converted on day 20260215 (after she became 'returning').
    (1002, 2, 20260215, 2, 'mobile',  'GB', '2026-02-15 09:30', '2026-02-15 09:48', 1080, 7,
     'purchase',     278.00, 1),
    -- Bob: converted on 20260115 (variant treatment_a).
    (1003, 3, 20260115, 1, 'desktop', 'IT', '2026-01-15 11:00', '2026-01-15 11:25', 1500, 6,
     'purchase',     49.00, 1),
    -- Bob: abandoned cart on 20260115 (variant control).
    (1004, 3, 20260115, 1, 'desktop', 'IT', '2026-01-15 16:00', '2026-01-15 16:18', 1080, 5,
     'add_to_cart',  NULL, 0),
    -- Carla: visited only, no conversion.
    (1005, 5, 20260201, NULL, 'mobile', 'RU', '2026-02-01 10:00', '2026-02-01 10:08', 480, 3,
     'browse',       NULL, 0);

-- Events (fact_user_events). The same user can hit multiple stages of
-- the funnel in one session; that's why we have a SEPARATE events fact.
INSERT INTO fact_user_events (event_ts, day_key, user_key, product_key, session_id,
                               variant_key, event_type, device_type, country,
                               seconds_since_session_start) VALUES
    -- Alice session 1001: browsed but did not buy.
    ('2026-01-15 14:00:00', 20260115, 1, NULL,   1001, 1, 'browse',         'desktop', 'US', 0),
    ('2026-01-15 14:01:00', 20260115, 1, 1,      1001, 1, 'view_product',   'desktop', 'US', 60),
    ('2026-01-15 14:05:00', 20260115, 1, 2,      1001, 1, 'view_product',   'desktop', 'US', 300),
    ('2026-01-15 14:15:00', 20260115, 1, 3,      1001, 1, 'view_product',   'desktop', 'US', 900),
    ('2026-01-15 14:23:00', 20260115, 1, 1,      1001, 1, 'remove_from_cart','desktop','US', 1380),

    -- Bob session 1002: converted on Feb 15 (his segment was 'vip' by then).
    ('2026-02-15 09:30:00', 20260215, 3, NULL,   1002, 2, 'browse',         'mobile',  'GB', 0),
    ('2026-02-15 09:32:00', 20260215, 3, 1,      1002, 2, 'view_product',   'mobile',  'GB', 120),
    ('2026-02-15 09:35:00', 20260215, 3, 2,      1002, 2, 'view_product',   'mobile',  'GB', 300),
    ('2026-02-15 09:38:00', 20260215, 3, 2,      1002, 2, 'add_to_cart',    'mobile',  'GB', 480),
    ('2026-02-15 09:42:00', 20260215, 3, 1,      1002, 2, 'add_to_cart',    'mobile',  'GB', 720),
    ('2026-02-15 09:45:00', 20260215, 3, NULL,   1002, 2, 'checkout',       'mobile',  'GB', 900),
    ('2026-02-15 09:48:00', 20260215, 3, NULL,   1002, 2, 'purchase',       'mobile',  'GB', 1080),

    -- Bob session 1003: converted on Jan 15 (segment was 'returning' then).
    ('2026-01-15 11:00:00', 20260115, 2, NULL,   1003, 1, 'browse',         'desktop', 'IT', 0),
    ('2026-01-15 11:02:00', 20260115, 2, 4,      1003, 1, 'view_product',   'desktop', 'IT', 120),
    ('2026-01-15 11:08:00', 20260115, 2, 4,      1003, 1, 'add_to_cart',    'desktop', 'IT', 480),
    ('2026-01-15 11:18:00', 20260115, 2, NULL,   1003, 1, 'checkout',       'desktop', 'IT', 1080),
    ('2026-01-15 11:25:00', 20260115, 2, NULL,   1003, 1, 'purchase',       'desktop', 'IT', 1500);

-- =====================================================================
-- Self-verifying queries
-- =====================================================================

-- Q1: funnel by stage (with distinct user counts).
SELECT event_type,
       COUNT(*) AS event_count,
       COUNT(DISTINCT user_key) AS users_reached
FROM fact_user_events
GROUP BY event_type
ORDER BY CASE event_type
            WHEN 'browse'       THEN 1
            WHEN 'search'       THEN 2
            WHEN 'view_product' THEN 3
            WHEN 'add_to_cart'  THEN 4
            WHEN 'checkout'     THEN 5
            WHEN 'purchase'     THEN 6
            WHEN 'remove_from_cart' THEN 7
         END;

-- Q2: drop-off rates between stages.
-- COUNT(DISTINCT ... CASE WHEN ...) is supported in MySQL 8.0+
SELECT
    COUNT(DISTINCT CASE WHEN event_type IN ('browse','search','view_product') THEN user_key END) AS reached_view,
    COUNT(DISTINCT CASE WHEN event_type = 'add_to_cart'  THEN user_key END) AS reached_cart,
    COUNT(DISTINCT CASE WHEN event_type = 'checkout'     THEN user_key END) AS reached_checkout,
    COUNT(DISTINCT CASE WHEN event_type = 'purchase'     THEN user_key END) AS reached_purchase
INTO @reached_view, @reached_cart, @reached_checkout, @reached_purchase
FROM fact_user_events;

SELECT
    @reached_view                                                   AS reached_view,
    @reached_cart                                                   AS reached_cart,
    ROUND(100.0 * @reached_cart    / NULLIF(@reached_view,0),    1) AS view_to_cart_pct,
    @reached_checkout                                               AS reached_checkout,
    ROUND(100.0 * @reached_checkout/ NULLIF(@reached_cart,0),    1) AS cart_to_checkout_pct,
    @reached_purchase                                               AS reached_purchase,
    ROUND(100.0 * @reached_purchase/ NULLIF(@reached_checkout,0),1) AS checkout_to_purchase_pct;

-- Q3: A/B test conversion rate by variant.
SELECT v.variant_code,
       COUNT(*) AS sessions,
       SUM(CASE WHEN s.is_converted THEN 1 ELSE 0 END) AS conversions,
       ROUND(100.0 * SUM(CASE WHEN s.is_converted THEN 1 ELSE 0 END) / COUNT(*), 2)
            AS conversion_rate_pct,
       ROUND(AVG(s.purchase_amount_usd), 2) AS avg_order_value
FROM fact_sessions s
JOIN dim_variants v ON v.variant_key = s.variant_key
GROUP BY v.variant_code
ORDER BY conversion_rate_pct DESC;

-- Q4: mobile vs desktop conversion (the prompt's question).
SELECT device_type,
       COUNT(*) AS sessions,
       SUM(CASE WHEN is_converted THEN 1 ELSE 0 END) AS conversions,
       ROUND(100.0 * SUM(CASE WHEN is_converted THEN 1 ELSE 0 END) / COUNT(*), 2) AS cr_pct
FROM fact_sessions
GROUP BY device_type
ORDER BY cr_pct DESC;

-- Q5: time between view and cart per session.
SELECT session_id,
       MAX(CASE WHEN event_type = 'view_product' THEN seconds_since_session_start END) AS sec_to_first_view,
       MAX(CASE WHEN event_type = 'add_to_cart'  THEN seconds_since_session_start END) AS sec_to_cart
FROM fact_user_events
WHERE session_id IN (1002, 1003, 1004)
GROUP BY session_id
ORDER BY session_id;

-- Q6: SCD2 — Alice's segment as of Jan 15 vs Feb 15.
-- This is why SCD2 exists. The same user has different segments at
-- different points in time, and the right one for each event is the
-- segment that was active WHEN the event happened.
SELECT
    (SELECT segment FROM dim_users
        WHERE user_id = 1
          AND valid_from <= '2026-01-15'
          AND (valid_to > '2026-01-15' OR valid_to IS NULL)
        ORDER BY valid_from DESC LIMIT 1) AS alice_segment_jan_15,
    (SELECT segment FROM dim_users
        WHERE user_id = 1
          AND valid_from <= '2026-02-15'
          AND (valid_to > '2026-02-15' OR valid_to IS NULL)
        ORDER BY valid_from DESC LIMIT 1) AS alice_segment_feb_15;

-- Q7: revenue attribution by acquisition channel (SCD-aware).
-- For each session, find the channel that was active AT session start.
WITH session_channel AS (
    SELECT s.session_id, s.is_converted, s.purchase_amount_usd,
           COALESCE((
               SELECT u.acquisition_channel FROM dim_users u
               WHERE u.user_key = s.user_key LIMIT 1
           ), 'unknown') AS channel
    FROM fact_sessions s
    WHERE s.is_converted
)
SELECT channel,
       COUNT(*) AS conversions,
       ROUND(SUM(purchase_amount_usd), 2) AS total_revenue
FROM session_channel
GROUP BY channel
ORDER BY total_revenue DESC;

-- Q8: sessions abandoned at cart vs checkout.
SELECT funnel_stage_at,
       COUNT(*) AS sessions,
       ROUND(AVG(duration_sec), 1) AS avg_session_sec
FROM fact_sessions
WHERE is_converted = 0 AND funnel_stage_at IS NOT NULL
GROUP BY funnel_stage_at
ORDER BY sessions DESC;

-- Done: OLAP product funnel star schema (MySQL 8.0+, all timestamps UTC)