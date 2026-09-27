"""
Q23: Product Funnel & Conversion Analytics   [Medium | Dim Model — star schema]
Tags: Star Schema

Star schema for the shopping journey: browse -> add to cart -> checkout -> buy.

THE GRAIN DECISION IS THE ANSWER, and this question has a specific right one:

  fact_session_funnel = ACCUMULATING SNAPSHOT, one row per session,
                        with one TIMESTAMP COLUMN PER MILESTONE.

Why accumulating snapshot and not transactional:
  A funnel is a process with a known, fixed set of stages. An accumulating
  snapshot holds one row per process instance and UPDATES it as the instance
  advances. That makes every funnel question trivial:
    - "how many reached checkout?"  -> COUNT(checkout_ts IS NOT NULL)
    - "time from cart to purchase?" -> a column subtraction, no self-join
  A transactional fact (one row per step event) forces a self-join or a pivot
  for every single one of those questions.

  This is the fact type candidates forget exists. Naming it is the signal.

When you would ALSO keep a transactional fact:
  When steps can repeat or arrive out of order, or you need the full event
  stream for sessionization/debugging. Real warehouses keep both: the raw
  transactional fact, and the accumulating snapshot built from it. Say that.

Grain trap — session vs user:
  One row per SESSION, not per user. A user with three shopping sessions has
  three funnel instances. Choosing user-grain silently collapses them and
  conversion rates become meaningless.

Additivity warning:
  The timestamp columns are NOT additive. You cannot SUM them. Durations
  derived from them are additive only as averages over a consistent denominator
  — and the denominator must be "sessions that reached both milestones", never
  all sessions.
"""
from _seeds import spark, expect

DDL = """
-- ACCUMULATING SNAPSHOT. Grain: one row per shopping session.
-- Row is INSERTed at session start and UPDATEd as milestones are hit.
CREATE TABLE fact_session_funnel (
  session_key       BIGINT,     -- PK (degenerate dimension: the session id)
  user_key          BIGINT,     -- FK dim_user
  start_date_key    INT,        -- FK dim_date
  device_key        INT,        -- FK dim_device
  channel_key       INT,        -- FK dim_channel (paid/organic/referral)
  -- one nullable timestamp per milestone = the accumulating snapshot pattern
  view_ts           TIMESTAMP,
  add_to_cart_ts    TIMESTAMP,
  checkout_ts       TIMESTAMP,
  purchase_ts       TIMESTAMP,
  -- additive measures, safe to SUM
  items_in_cart     INT,
  order_amount      DECIMAL(12,2)
);

-- TRANSACTIONAL companion, kept for the raw stream. Grain: one row per event.
CREATE TABLE fact_funnel_event (
  event_key    BIGINT,
  session_key  BIGINT,
  user_key     BIGINT,
  step_key     INT,             -- FK dim_funnel_step (gives step ORDER)
  event_ts     TIMESTAMP,
  date_key     INT
);

-- dim_funnel_step exists so step ORDER lives in the model, not in every query.
CREATE TABLE dim_funnel_step (
  step_key   INT,               -- PK
  step_name  VARCHAR(30),       -- view / add_to_cart / checkout / purchase
  step_order INT                -- 1..4
);

CREATE TABLE dim_user (
  user_key    BIGINT,           -- PK (surrogate)
  user_id     VARCHAR(40),      -- natural key
  country     VARCHAR(60),
  signup_date DATE,
  -- SCD2: attribute sessions to the user's state AT SESSION TIME
  effective_from DATE, effective_to DATE, is_current BOOLEAN
);

CREATE TABLE dim_device  ( device_key INT, device_type VARCHAR(20), os VARCHAR(20) );
CREATE TABLE dim_channel ( channel_key INT, channel_name VARCHAR(30) );
CREATE TABLE dim_date    ( date_key INT, full_date DATE, day_of_week VARCHAR(10),
                           week_of_year INT, month INT, quarter INT, year INT );
"""

# s1,s5 convert fully. s2 stalls at cart. s3 bounces after view. s4 abandons
# at checkout — the most valuable segment in the whole table.
spark.createDataFrame([
    (1, 10, "2026-03-01 10:00:00", "2026-03-01 10:05:00",
     "2026-03-01 10:10:00", "2026-03-01 10:15:00"),
    (2, 11, "2026-03-01 10:00:00", "2026-03-01 10:20:00", None, None),
    (3, 12, "2026-03-01 11:00:00", None, None, None),
    (4, 13, "2026-03-01 12:00:00", "2026-03-01 12:05:00",
     "2026-03-01 12:30:00", None),
    (5, 10, "2026-03-02 09:00:00", "2026-03-02 09:05:00",
     "2026-03-02 09:20:00", "2026-03-02 09:30:00"),
], ["session_key", "user_key", "view_ts", "add_to_cart_ts",
    "checkout_ts", "purchase_ts"]).createOrReplaceTempView("fact_session_funnel")

# The payoff: the whole funnel from ONE table scan, no self-joins.
expect("Q23 funnel from the accumulating snapshot", """
WITH counts AS (
    SELECT COUNT(view_ts)        AS viewed,
           COUNT(add_to_cart_ts) AS carted,
           COUNT(checkout_ts)    AS checked_out,
           COUNT(purchase_ts)    AS purchased
    FROM fact_session_funnel
)
SELECT 'view' AS step, viewed AS sessions, 1 AS o FROM counts
UNION ALL SELECT 'add_to_cart', carted,      2 FROM counts
UNION ALL SELECT 'checkout',    checked_out, 3 FROM counts
UNION ALL SELECT 'purchase',    purchased,   4 FROM counts
ORDER BY o
""", [("view", 5, 1), ("add_to_cart", 4, 2), ("checkout", 3, 3), ("purchase", 2, 4)])

expect("Q23 step-to-step conversion and drop-off", """
WITH counts AS (
    SELECT COUNT(view_ts) AS viewed, COUNT(add_to_cart_ts) AS carted,
           COUNT(checkout_ts) AS checked_out, COUNT(purchase_ts) AS purchased
    FROM fact_session_funnel
),
steps AS (
    SELECT 'view' AS step, viewed AS s, 1 AS o FROM counts
    UNION ALL SELECT 'add_to_cart', carted, 2 FROM counts
    UNION ALL SELECT 'checkout', checked_out, 3 FROM counts
    UNION ALL SELECT 'purchase', purchased, 4 FROM counts
)
SELECT step, s AS sessions,
       ROUND(100.0 * s / LAG(s) OVER (ORDER BY o), 2) AS conv_from_prev_pct,
       ROUND(100.0 - 100.0 * s / LAG(s) OVER (ORDER BY o), 2) AS drop_off_pct
FROM steps ORDER BY o
""", [
    ("view", 5, None, None),
    ("add_to_cart", 4, 80.00, 20.00),
    ("checkout", 3, 75.00, 25.00),
    ("purchase", 2, 66.67, 33.33),
])

# Latency between milestones: a subtraction, because of the grain choice.
# Denominator is sessions that reached BOTH ends — never all sessions.
expect("Q23 avg minutes view -> purchase (converters only)", """
SELECT COUNT(*) AS converters,
       ROUND(AVG((UNIX_TIMESTAMP(purchase_ts) - UNIX_TIMESTAMP(view_ts)) / 60.0), 2)
           AS avg_min_to_purchase
FROM fact_session_funnel
WHERE purchase_ts IS NOT NULL
""", [(2, 22.50)])

# Checkout abandoners — the segment the business actually wants to retarget.
expect("Q23 checkout abandoners", """
SELECT session_key FROM fact_session_funnel
WHERE checkout_ts IS NOT NULL AND purchase_ts IS NULL
ORDER BY session_key
""", [(4,)])
