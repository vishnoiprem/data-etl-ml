"""
Product Funnel & Conversion Analytics   [Medium | Star schema design]
DataVidhya: "design a star schema that tracks the customer funnel"

Source: 6 OLTP tables -> User_Events(8), Purchases(6), Users(4), Products(5),
AB_Tests(5), Sessions(6). Deliverable: a dimensional model that answers the
product team's six questions and makes drop-off cheap to compute.

NOTE: `12_DataVidhya_Meta_Set/23_model_product_funnel_star.py` argues the grain
decision for this question in the abstract. THIS file builds the whole thing
against the 6 named source tables and satisfies all 7 stated requirements,
including the two the abstract version skips: SCD2 on user segment, and A/B
variant attribution.

================================================================================
THE MODEL
================================================================================

  fact_funnel_event        TRANSACTIONAL      one row per stage occurrence
  fact_session_funnel      ACCUMULATING SNAP  one row per session

  dim_user       SCD2 (segment changes over time)
  dim_product    SCD1
  dim_stage      the funnel spine -- pins stage ORDER, which the source lacks
  dim_ab_variant the test/variant a user was assigned
  session_id     DEGENERATE dimension, stored on both facts, no dim table

WHY TWO FACTS (requirement 7) -- this is the core of the answer:
  The transactional fact is the SOURCE OF TRUTH. Stages repeat ("view product ->
  leave -> view again"), so it must be event-grain or you lose that.
  The accumulating snapshot is the SERVING LAYER. A funnel is a process with a
  fixed set of stages, so one row per session with one timestamp column per
  milestone makes every funnel question a column comparison instead of a
  self-join:
      "how many reached checkout?"   -> COUNT(checkout_ts IS NOT NULL)
      "time from view to purchase?"  -> a subtraction, no join
  Naming "accumulating snapshot" is the signal. It is the fact type candidates
  forget exists, and it is the one this question is actually about.

GRAIN, stated as sentences (say these out loud):
  fact_funnel_event   -> "one row per user per session per stage OCCURRENCE"
  fact_session_funnel -> "one row per session"

  Session grain, NOT user grain. A user with three shopping sessions has three
  funnel instances; collapsing to user-grain makes conversion meaningless.

================================================================================
THE TRAPS
================================================================================
- DISTINCT USERS, NOT EVENTS (constraint 4). Stages repeat, so COUNT(*) per
  stage inflates the top of the funnel and understates drop-off. Asserted.
- LOOSE vs STRICT funnel. Loose counts each stage independently; strict requires
  monotonically increasing timestamps. A user who purchases without an
  add_to_cart row counts in `purchase` under loose but not strict. The two give
  DIFFERENT drop-off curves -- ask which the team means. Asserted.
- purchase_amount is NULL for every non-purchase session (constraint 3). AVG
  skips NULLs, so "average order value" over all sessions and over purchasing
  sessions differ by the conversion rate. The denominator must be stated.
- SCD2 point-in-time segment. A user who was 'new' in January and is 'vip' now
  must have January sessions attributed to 'new'. Joining on is_current
  relabels history and makes the vip cohort look artificially good -- the
  classic survivorship bug in cohort reporting. Asserted.
- The 24h session rule (constraint 2) is a SESSIONIZATION decision that happens
  UPSTREAM of the model. If the source `session_id` was cut on a different rule
  than 24h-of-inactivity, the model faithfully reports the wrong sessions.
  Asserted with a gap-and-island recomputation.
- A/B assignment is per USER and stable (constraint 5), not per session. Model
  it as a user-scoped dimension; deriving it per session invites a user showing
  two variants, which invalidates the test.
- Time between stages must be stored, not computed at read time (requirement 6)
  -- otherwise every consumer re-derives it and they disagree on which
  occurrence of a repeated stage to measure from.

Spark note:
- Dimensions all broadcast. fact_funnel_event is partitioned by event_date;
  fact_session_funnel is small enough to be a daily full rebuild from it.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("13-product-funnel-star-schema")
         .master("local[2]")
         .config("spark.sql.shuffle.partitions", "2")
         .config("spark.ui.showConsoleProgress", "false")
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")


def expect(title, sql, expected_rows):
    """Run a query and assert its exact rows, in order. Decimal/float safe."""
    import decimal

    def norm(v):
        if isinstance(v, decimal.Decimal):
            return float(v)
        if isinstance(v, float):
            return round(v, 6)
        return v

    got = [tuple(norm(c) for c in r) for r in spark.sql(sql).collect()]
    exp = [tuple(norm(c) for c in r) for r in expected_rows]
    if got != exp:
        print(f"[FAIL] {title}")
        print(f"   expected: {exp}")
        print(f"   got:      {got}")
        raise AssertionError(title)
    print(f"[PASS] {title}")
    return got


from pyspark.sql import functions as F, Window as W

OPEN_END = "9999-12-31"
STAGES = ["browse", "search", "view_product", "add_to_cart", "checkout", "purchase"]

# ==============================================================================
# SOURCE (OLTP) -- the 6 tables as given
# ==============================================================================

# Users(4). `segment` is the CURRENT value only -- OLTP overwrites it.
spark.sql("""
CREATE OR REPLACE TEMP VIEW Users AS
SELECT * FROM VALUES
    (1, DATE'2025-11-01', 'vip',       'US'),
    (2, DATE'2026-01-05', 'returning', 'IN'),
    (3, DATE'2026-02-20', 'new',       'BR')
AS t(user_id, signup_date, segment, country)
""")

# Products(5)
spark.sql("""
CREATE OR REPLACE TEMP VIEW Products AS
SELECT * FROM VALUES
    (900, 'Noise Cancelling Headphones', 'audio',  CAST(299.00 AS DECIMAL(10,2)), TRUE),
    (901, 'Laptop Stand',                'desk',   CAST( 49.00 AS DECIMAL(10,2)), TRUE),
    (902, 'Mechanical Keyboard',         'desk',   CAST(129.00 AS DECIMAL(10,2)), TRUE)
AS t(product_id, product_name, category, price, is_active)
""")

# AB_Tests(5). Assignment is per USER and stable (constraint 5).
spark.sql("""
CREATE OR REPLACE TEMP VIEW AB_Tests AS
SELECT * FROM VALUES
    ('T1', 1, 'checkout_redesign', 'treatment', DATE'2026-01-01'),
    ('T1', 2, 'checkout_redesign', 'control',   DATE'2026-01-01'),
    ('T1', 3, 'checkout_redesign', 'treatment', DATE'2026-02-20')
AS t(test_id, user_id, test_name, variant, assigned_date)
""")

# Sessions(6). device_type and marketing_channel live here -- they are
# session-scoped, which is why questions 4 and 6 are answerable at all.
spark.sql("""
CREATE OR REPLACE TEMP VIEW Sessions AS
SELECT * FROM VALUES
    ('S1', 1, TIMESTAMP'2026-01-10 09:00:00', TIMESTAMP'2026-01-10 09:40:00',
        'mobile',  'paid_search'),
    ('S2', 1, TIMESTAMP'2026-03-02 14:00:00', TIMESTAMP'2026-03-02 14:25:00',
        'desktop', 'organic'),
    ('S3', 2, TIMESTAMP'2026-03-03 11:00:00', TIMESTAMP'2026-03-03 11:12:00',
        'mobile',  'email'),
    ('S4', 3, TIMESTAMP'2026-03-04 20:00:00', TIMESTAMP'2026-03-04 20:30:00',
        'desktop', 'paid_social'),
    ('S5', 2, TIMESTAMP'2026-03-05 08:00:00', TIMESTAMP'2026-03-05 08:05:00',
        'mobile',  'organic')
AS t(session_id, user_id, session_start, session_end, device_type, marketing_channel)
""")

# User_Events(8). Note S1 has view_product TWICE (constraint 1: stages repeat),
# and S4 reaches purchase with NO add_to_cart row -- the loose/strict divider.
spark.sql("""
CREATE OR REPLACE TEMP VIEW User_Events AS
SELECT * FROM VALUES
    (1,  1, 'S1', 'browse',       CAST(NULL AS INT), TIMESTAMP'2026-01-10 09:00:00', 'mobile',  '/home'),
    (2,  1, 'S1', 'search',       CAST(NULL AS INT), TIMESTAMP'2026-01-10 09:03:00', 'mobile',  '/search'),
    (3,  1, 'S1', 'view_product', 900,               TIMESTAMP'2026-01-10 09:05:00', 'mobile',  '/p/900'),
    (4,  1, 'S1', 'view_product', 900,               TIMESTAMP'2026-01-10 09:20:00', 'mobile',  '/p/900'),
    (5,  1, 'S1', 'add_to_cart',  900,               TIMESTAMP'2026-01-10 09:25:00', 'mobile',  '/cart'),
    (6,  1, 'S1', 'checkout',     900,               TIMESTAMP'2026-01-10 09:35:00', 'mobile',  '/checkout'),
    (7,  1, 'S1', 'purchase',     900,               TIMESTAMP'2026-01-10 09:40:00', 'mobile',  '/confirm'),
    (8,  1, 'S2', 'browse',       CAST(NULL AS INT), TIMESTAMP'2026-03-02 14:00:00', 'desktop', '/home'),
    (9,  1, 'S2', 'view_product', 901,               TIMESTAMP'2026-03-02 14:10:00', 'desktop', '/p/901'),
    (10, 1, 'S2', 'add_to_cart',  901,               TIMESTAMP'2026-03-02 14:20:00', 'desktop', '/cart'),
    (11, 2, 'S3', 'browse',       CAST(NULL AS INT), TIMESTAMP'2026-03-03 11:00:00', 'mobile',  '/home'),
    (12, 2, 'S3', 'search',       CAST(NULL AS INT), TIMESTAMP'2026-03-03 11:04:00', 'mobile',  '/search'),
    (13, 2, 'S3', 'view_product', 902,               TIMESTAMP'2026-03-03 11:08:00', 'mobile',  '/p/902'),
    (14, 3, 'S4', 'browse',       CAST(NULL AS INT), TIMESTAMP'2026-03-04 20:00:00', 'desktop', '/home'),
    (15, 3, 'S4', 'view_product', 900,               TIMESTAMP'2026-03-04 20:05:00', 'desktop', '/p/900'),
    (16, 3, 'S4', 'checkout',     900,               TIMESTAMP'2026-03-04 20:25:00', 'desktop', '/checkout'),
    (17, 3, 'S4', 'purchase',     900,               TIMESTAMP'2026-03-04 20:30:00', 'desktop', '/confirm'),
    (18, 2, 'S5', 'browse',       CAST(NULL AS INT), TIMESTAMP'2026-03-05 08:00:00', 'mobile',  '/home')
AS t(event_id, user_id, session_id, event_type, product_id, event_timestamp,
     device_type, page_url)
""")

# Purchases(6). Amount exists ONLY for completed purchases (constraint 3).
spark.sql("""
CREATE OR REPLACE TEMP VIEW Purchases AS
SELECT * FROM VALUES
    (5001, 1, 'S1', 900, TIMESTAMP'2026-01-10 09:40:00', CAST(299.00 AS DECIMAL(10,2))),
    (5002, 3, 'S4', 900, TIMESTAMP'2026-03-04 20:30:00', CAST(299.00 AS DECIMAL(10,2)))
AS t(purchase_id, user_id, session_id, product_id, purchase_timestamp, amount)
""")

print("[PASS] source: 6 OLTP tables loaded (User_Events, Purchases, Users, "
      "Products, AB_Tests, Sessions)")

# ==============================================================================
# DIMENSIONS
# ==============================================================================

# dim_stage -- the funnel SPINE. The source has no stage ORDER; this pins it.
# Without an integer step_num, ORDER BY sorts alphabetically and 'purchase'
# comes before 'view_product'.
spark.sql("""
CREATE OR REPLACE TEMP VIEW dim_stage AS
SELECT * FROM VALUES
    (1, 'browse'),       (2, 'search'),   (3, 'view_product'),
    (4, 'add_to_cart'),  (5, 'checkout'), (6, 'purchase')
AS t(stage_key, stage_name)
""")

alpha = [r[0] for r in spark.sql(
    "SELECT stage_name FROM dim_stage ORDER BY stage_name").collect()]
ordered = [r[0] for r in spark.sql(
    "SELECT stage_name FROM dim_stage ORDER BY stage_key").collect()]
assert alpha[0] == "add_to_cart" and ordered == STAGES, (alpha, ordered)
print("[PASS] dim_stage pins funnel order -- alphabetical would start at "
      f"'{alpha[0]}' and put purchase before view_product")

# dim_user -- SCD TYPE 2 (requirement 3). The OLTP `segment` is overwritten, so
# history comes from a change log. User 1 went new -> returning -> vip.
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW user_segment_changes AS
SELECT * FROM VALUES
    (1, 'new',       DATE'2025-11-01'),
    (1, 'returning', DATE'2026-02-01'),
    (1, 'vip',       DATE'2026-03-01'),
    (2, 'new',       DATE'2026-01-05'),
    (2, 'returning', DATE'2026-02-15'),
    (3, 'new',       DATE'2026-02-20')
AS t(user_id, segment, changed_on)
""")
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW dim_user AS
SELECT ROW_NUMBER() OVER (ORDER BY c.user_id, c.changed_on) AS user_sk,
       c.user_id,
       u.country,
       u.signup_date,
       c.segment,
       c.changed_on                                            AS effective_from,
       COALESCE(LEAD(c.changed_on) OVER w, DATE'{OPEN_END}')    AS effective_to,
       LEAD(c.changed_on) OVER w IS NULL                        AS is_current
FROM user_segment_changes c
JOIN Users u ON u.user_id = c.user_id
WINDOW w AS (PARTITION BY c.user_id ORDER BY c.changed_on)
""")
spark.table("dim_user").orderBy("user_sk").show(truncate=False)

open_rows = spark.sql("""
SELECT user_id, SUM(CASE WHEN is_current THEN 1 ELSE 0 END) AS n
FROM dim_user GROUP BY user_id ORDER BY user_id
""").collect()
assert all(r[1] == 1 for r in open_rows), open_rows
print("[PASS] dim_user is SCD2 with exactly one is_current row per user_id")

# dim_product -- SCD1 (price changes are not funnel-relevant history here).
spark.sql("""
CREATE OR REPLACE TEMP VIEW dim_product AS
SELECT product_id AS product_sk, product_id, product_name, category, price
FROM Products
UNION ALL
SELECT -1, CAST(NULL AS INT), '(not applicable)', '(not applicable)',
       CAST(NULL AS DECIMAL(10,2))
""")
print("[PASS] dim_product includes a -1 'not applicable' member for "
      "product-less stages (browse/search)")

# dim_ab_variant -- scoped to USER, because assignment is stable per user.
spark.sql("""
CREATE OR REPLACE TEMP VIEW dim_ab_variant AS
SELECT ROW_NUMBER() OVER (ORDER BY test_id, user_id) AS ab_variant_sk,
       test_id, user_id, test_name, variant, assigned_date
FROM AB_Tests
""")
stability = spark.sql("""
SELECT user_id, COUNT(DISTINCT variant) AS variants
FROM dim_ab_variant GROUP BY test_id, user_id HAVING COUNT(DISTINCT variant) > 1
""").count()
assert stability == 0
print("[PASS] dim_ab_variant: no user has two variants for one test "
      "-- assignment stability holds (constraint 5)")

# ==============================================================================
# FACT 1 -- fact_funnel_event  (TRANSACTIONAL)
# grain: one row per user per session per stage OCCURRENCE
# session_id is a DEGENERATE dimension: stored inline, no dim table (req 2)
# seconds_since_prev_stage is STORED, not derived at read time (req 6)
# ==============================================================================
spark.sql("""
CREATE OR REPLACE TEMP VIEW fact_funnel_event AS
SELECT e.event_id                                  AS funnel_event_sk,
       e.session_id,                               -- DEGENERATE dimension
       du.user_sk,
       COALESCE(e.product_id, -1)                  AS product_sk,
       ds.stage_key,
       ab.ab_variant_sk,
       s.device_type,
       s.marketing_channel,
       e.event_timestamp,
       CAST(e.event_timestamp AS DATE)             AS event_date,
       -- stored duration between consecutive stage events in the session
       CAST(UNIX_TIMESTAMP(e.event_timestamp) - UNIX_TIMESTAMP(
            LAG(e.event_timestamp) OVER (PARTITION BY e.session_id
                                         ORDER BY e.event_timestamp, e.event_id)
       ) AS INT)                                   AS seconds_since_prev_stage
FROM User_Events e
JOIN dim_stage ds ON ds.stage_name = e.event_type
JOIN Sessions  s  ON s.session_id  = e.session_id
#   POINT-IN-TIME SCD2 join: the segment held when the event happened
JOIN dim_user du ON du.user_id = e.user_id
                AND CAST(e.event_timestamp AS DATE) >= du.effective_from
                AND CAST(e.event_timestamp AS DATE) <  du.effective_to
LEFT JOIN dim_ab_variant ab ON ab.user_id = e.user_id AND ab.test_id = 'T1'
""")

assert spark.table("fact_funnel_event").count() == spark.table("User_Events").count() == 18
print("[PASS] fact_funnel_event: 18 events in, 18 rows out -- no fan-out from "
      "the SCD2 or A/B joins")

spark.sql("""
SELECT session_id, stage_key, event_timestamp, seconds_since_prev_stage
FROM fact_funnel_event WHERE session_id = 'S1' ORDER BY event_timestamp
""").show(truncate=False)

# Repeated stage survives as two rows (constraint 1).
repeats = spark.sql("""
SELECT COUNT(*) FROM fact_funnel_event f JOIN dim_stage d USING (stage_key)
WHERE f.session_id = 'S1' AND d.stage_name = 'view_product'
""").collect()[0][0]
assert repeats == 2
print("[PASS] S1's two view_product events are two rows -- repeated stages preserved")

# ==============================================================================
# FACT 2 -- fact_session_funnel  (ACCUMULATING SNAPSHOT)
# grain: one row per session, one timestamp column per milestone
# ==============================================================================
spark.sql("""
CREATE OR REPLACE TEMP VIEW fact_session_funnel AS
WITH milestones AS (
    SELECT f.session_id,
           MIN(f.user_sk)             AS user_sk,
           MIN(f.ab_variant_sk)       AS ab_variant_sk,
           MIN(f.device_type)         AS device_type,
           MIN(f.marketing_channel)   AS marketing_channel,
           CAST(MIN(f.event_timestamp) AS DATE) AS session_date,
           -- FIRST occurrence of each stage: a repeated stage must not
           -- move the milestone later
           MIN(CASE WHEN d.stage_name = 'browse'       THEN f.event_timestamp END) AS browse_ts,
           MIN(CASE WHEN d.stage_name = 'search'       THEN f.event_timestamp END) AS search_ts,
           MIN(CASE WHEN d.stage_name = 'view_product' THEN f.event_timestamp END) AS view_ts,
           MIN(CASE WHEN d.stage_name = 'add_to_cart'  THEN f.event_timestamp END) AS cart_ts,
           MIN(CASE WHEN d.stage_name = 'checkout'     THEN f.event_timestamp END) AS checkout_ts,
           MIN(CASE WHEN d.stage_name = 'purchase'     THEN f.event_timestamp END) AS purchase_ts
    FROM fact_funnel_event f
    JOIN dim_stage d USING (stage_key)
    GROUP BY f.session_id
)
SELECT m.*,
       p.amount AS purchase_amount,            -- NULL unless purchased (c3)
       -- stored durations; NULL when either milestone was never reached
       CAST(UNIX_TIMESTAMP(m.purchase_ts) - UNIX_TIMESTAMP(m.view_ts) AS INT)
           AS seconds_view_to_purchase,
       CAST(UNIX_TIMESTAMP(m.cart_ts) - UNIX_TIMESTAMP(m.view_ts) AS INT)
           AS seconds_view_to_cart,
       -- the deepest stage reached, for a one-column abandonment report
       CASE WHEN m.purchase_ts IS NOT NULL THEN 6
            WHEN m.checkout_ts IS NOT NULL THEN 5
            WHEN m.cart_ts     IS NOT NULL THEN 4
            WHEN m.view_ts     IS NOT NULL THEN 3
            WHEN m.search_ts   IS NOT NULL THEN 2
            ELSE 1 END AS max_stage_key
FROM milestones m
LEFT JOIN Purchases p ON p.session_id = m.session_id
""")

spark.table("fact_session_funnel").select(
    "session_id", "view_ts", "cart_ts", "checkout_ts", "purchase_ts",
    "purchase_amount", "max_stage_key").orderBy("session_id").show(truncate=False)

assert spark.table("fact_session_funnel").count() == 5
print("[PASS] fact_session_funnel: one row per session (5), accumulating snapshot")

# A repeated stage must not push the milestone later -- MIN, not MAX.
s1_view = spark.sql(
    "SELECT view_ts FROM fact_session_funnel WHERE session_id='S1'").collect()[0][0]
assert str(s1_view) == "2026-01-10 09:05:00", s1_view
print("[PASS] S1's view milestone is the FIRST view (09:05), not the repeat (09:20)")

# ==============================================================================
# THE SIX BUSINESS QUESTIONS
# ==============================================================================

# Q1: What % of users who view a product actually buy it?
Q1 = """
SELECT COUNT(DISTINCT CASE WHEN view_ts     IS NOT NULL THEN user_sk END) AS viewers,
       COUNT(DISTINCT CASE WHEN purchase_ts IS NOT NULL THEN user_sk END) AS buyers,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN purchase_ts IS NOT NULL THEN user_sk END)
                   / COUNT(DISTINCT CASE WHEN view_ts IS NOT NULL THEN user_sk END), 2)
           AS view_to_purchase_pct
FROM fact_session_funnel
"""
expect("Q1 view -> purchase conversion (distinct users)", Q1, [(4, 2, 50.00)])
print("      note: user_sk is SCD2, so a user counted in two segments counts "
      "twice here -- use user_id if the question is about PEOPLE")

# The same question at PERSON grain, which is usually what's meant.
Q1B = """
SELECT COUNT(DISTINCT CASE WHEN f.view_ts IS NOT NULL THEN u.user_id END)     AS viewers,
       COUNT(DISTINCT CASE WHEN f.purchase_ts IS NOT NULL THEN u.user_id END) AS buyers
FROM fact_session_funnel f JOIN dim_user u ON u.user_sk = f.user_sk
"""
expect("Q1b same question at person grain", Q1B, [(3, 2)])
print("      3 people viewed, 2 bought = 66.67% -- vs 50% at user_sk grain. "
      "State which grain the metric uses.")

# Q2: Where do most users abandon? -- DISTINCT users per stage (constraint 4)
Q2 = """
WITH reached AS (
    SELECT d.stage_key, d.stage_name, COUNT(DISTINCT u.user_id) AS users
    FROM fact_funnel_event f
    JOIN dim_stage d USING (stage_key)
    JOIN dim_user  u ON u.user_sk = f.user_sk
    GROUP BY d.stage_key, d.stage_name
)
SELECT stage_name,
       users,
       LAG(users) OVER (ORDER BY stage_key) AS prev_users,
       ROUND(100.0 * (LAG(users) OVER (ORDER BY stage_key) - users)
                   / LAG(users) OVER (ORDER BY stage_key), 2) AS drop_off_pct
FROM reached ORDER BY stage_key
"""
spark.sql(Q2).show(truncate=False)
expect("Q2 drop-off by stage, LOOSE definition", Q2, [
    ("browse",       3, None, None),
    ("search",       2, 3,    33.33),
    ("view_product", 3, 2,   -50.00),   # negative: loose counting artefact
    ("add_to_cart",  1, 3,    66.67),
    ("checkout",     2, 1,  -100.00),
    ("purchase",     2, 2,     0.00),
])
print("      NEGATIVE drop-off at view_product and checkout is the tell: loose "
      "counting lets a stage exceed its predecessor. Real funnels need strict.")

# Q2-strict: each stage requires the FULL prior chain in timestamp order.
# The chain must be CUMULATIVE -- checking only the immediate predecessor lets a
# session that skipped a middle stage rejoin the funnel later, which is exactly
# the bug strict counting exists to prevent.
Q2_STRICT = """
WITH per_session AS (
    SELECT f.user_sk,
           f.view_ts IS NOT NULL                                     AS r_view,
           f.view_ts IS NOT NULL
             AND f.cart_ts     >= f.view_ts                          AS r_cart,
           f.view_ts IS NOT NULL
             AND f.cart_ts     >= f.view_ts
             AND f.checkout_ts >= f.cart_ts                          AS r_checkout,
           f.view_ts IS NOT NULL
             AND f.cart_ts     >= f.view_ts
             AND f.checkout_ts >= f.cart_ts
             AND f.purchase_ts >= f.checkout_ts                      AS r_purchase
    FROM fact_session_funnel f
),
reached AS (
    SELECT u.user_id,
           MAX(CASE WHEN p.r_view     THEN 1 ELSE 0 END) AS s_view,
           MAX(CASE WHEN p.r_cart     THEN 1 ELSE 0 END) AS s_cart,
           MAX(CASE WHEN p.r_checkout THEN 1 ELSE 0 END) AS s_checkout,
           MAX(CASE WHEN p.r_purchase THEN 1 ELSE 0 END) AS s_purchase
    FROM per_session p JOIN dim_user u ON u.user_sk = p.user_sk
    GROUP BY u.user_id
)
SELECT 'view_product' AS stage_name, SUM(s_view)     AS users FROM reached
UNION ALL SELECT 'add_to_cart',      SUM(s_cart)     FROM reached
UNION ALL SELECT 'checkout',         SUM(s_checkout) FROM reached
UNION ALL SELECT 'purchase',         SUM(s_purchase) FROM reached
"""
strict = expect("Q2-strict requires the full ordered chain, so the curve only falls",
                Q2_STRICT, [
                    ("view_product", 3),
                    ("add_to_cart",  1),
                    ("checkout",     1),
                    ("purchase",     1),
                ])
counts = [r[1] for r in strict]
assert counts == sorted(counts, reverse=True), counts
print("      monotonically non-increasing, unlike the loose curve above")
print("      user 3 (S4) purchased with NO add_to_cart -- counted under loose, "
      "excluded under strict. Two different answers; ask which is wanted.")

# Proof that the chain has to be cumulative: checking only the immediate
# predecessor readmits S4's purchase and the curve rises again at the end.
non_cumulative = spark.sql("""
WITH reached AS (
    SELECT u.user_id,
           MAX(CASE WHEN f.cart_ts     >= f.view_ts     THEN 1 ELSE 0 END) AS s_cart,
           MAX(CASE WHEN f.purchase_ts >= f.checkout_ts THEN 1 ELSE 0 END) AS s_purchase
    FROM fact_session_funnel f JOIN dim_user u ON u.user_sk = f.user_sk
    GROUP BY u.user_id
)
SELECT SUM(s_cart) AS cart_users, SUM(s_purchase) AS purchase_users FROM reached
""").collect()[0]
assert (non_cumulative[0], non_cumulative[1]) == (1, 2), non_cumulative
print("      per-predecessor-only checks give cart=1 but purchase=2 -- S4 rejoins "
      "the funnel after skipping cart, so the chain must be cumulative")

# Q3: How long from view to purchase? -- a subtraction, no self-join
Q3 = """
SELECT ROUND(AVG(seconds_view_to_purchase) / 60.0, 2) AS avg_minutes_view_to_purchase,
       COUNT(seconds_view_to_purchase)                AS sessions_measured
FROM fact_session_funnel
"""
# S1: 09:05 -> 09:40 = 35 min.  S4: 20:05 -> 20:30 = 25 min.  Mean = 30.
expect("Q3 time view -> purchase (accumulating snapshot makes this trivial)",
       Q3, [(30.0, 2)])
print("      denominator is 2 (sessions that reached BOTH milestones), not 5. "
      "AVG over all sessions would be meaningless.")

# Q4: Do mobile users convert differently than desktop?
Q4 = """
SELECT device_type,
       COUNT(*) AS sessions,
       COUNT(purchase_ts) AS purchases,
       ROUND(100.0 * COUNT(purchase_ts) / COUNT(*), 2) AS session_cvr_pct
FROM fact_session_funnel
GROUP BY device_type ORDER BY session_cvr_pct DESC, device_type
"""
expect("Q4 conversion by device", Q4, [
    ("desktop", 2, 1, 50.00),
    ("mobile",  3, 1, 33.33),
])

# Q5: Which A/B variant leads to more purchases?
Q5 = """
SELECT ab.variant,
       COUNT(*)                                        AS sessions,
       COUNT(f.purchase_ts)                            AS purchases,
       ROUND(100.0 * COUNT(f.purchase_ts) / COUNT(*), 2) AS cvr_pct
FROM fact_session_funnel f
JOIN dim_ab_variant ab ON ab.ab_variant_sk = f.ab_variant_sk
GROUP BY ab.variant ORDER BY cvr_pct DESC, ab.variant
"""
expect("Q5 conversion by A/B variant", Q5, [
    ("treatment", 3, 2, 66.67),
    ("control",   2, 0,  0.00),
])

# Q6: For purchasers, which marketing channel brought them in?
Q6 = """
SELECT marketing_channel,
       COUNT(*)                        AS purchase_sessions,
       ROUND(SUM(purchase_amount), 2)  AS revenue
FROM fact_session_funnel
WHERE purchase_ts IS NOT NULL
GROUP BY marketing_channel ORDER BY revenue DESC, marketing_channel
"""
expect("Q6 purchase attribution by channel", Q6, [
    ("paid_search", 1, 299.00),
    ("paid_social", 1, 299.00),
])

# ==============================================================================
# THE TRAPS, ASSERTED
# ==============================================================================

# --- events vs distinct users (constraint 4)
both = spark.sql("""
SELECT d.stage_name, COUNT(*) AS events, COUNT(DISTINCT u.user_id) AS users
FROM fact_funnel_event f JOIN dim_stage d USING (stage_key)
JOIN dim_user u ON u.user_sk = f.user_sk
WHERE d.stage_name = 'view_product' GROUP BY d.stage_name
""").collect()[0]
assert (both[1], both[2]) == (5, 3), both   # S1 x2, S2, S3, S4 -> 3 people
print(f"[PASS] view_product has {both[1]} events but {both[2]} distinct users "
      "-- counting events inflates the funnel")

# --- purchase_amount NULL for non-purchases (constraint 3)
aov = spark.sql("""
SELECT ROUND(AVG(purchase_amount), 2)                                AS avg_over_purchasers,
       ROUND(SUM(purchase_amount) / COUNT(*), 2)                     AS avg_over_all_sessions,
       COUNT(*)                                                      AS sessions,
       COUNT(purchase_amount)                                        AS with_amount
FROM fact_session_funnel
""").collect()[0]
assert (float(aov[0]), float(aov[1]), aov[2], aov[3]) == (299.00, 119.60, 5, 2), aov
print(f"[PASS] AVG(purchase_amount) = {aov[0]} over purchasers vs {aov[1]} spread "
      "over all sessions -- AVG skips NULLs, so the denominator must be stated")

# --- SCD2 point-in-time vs is_current
pit = spark.sql("""
SELECT du.segment, COUNT(*) AS purchase_sessions
FROM fact_session_funnel f
JOIN dim_user du ON du.user_sk = f.user_sk
WHERE f.purchase_ts IS NOT NULL
GROUP BY du.segment ORDER BY du.segment
""").collect()
assert [(r[0], r[1]) for r in pit] == [("new", 2)], pit
print("[PASS] point-in-time: both purchases attributed to segment 'new' "
      "-- the segment held when they bought")

as_is = spark.sql("""
SELECT du.segment, COUNT(*) AS purchase_sessions
FROM fact_session_funnel f
JOIN dim_user u_pit ON u_pit.user_sk = f.user_sk
JOIN dim_user du ON du.user_id = u_pit.user_id AND du.is_current
WHERE f.purchase_ts IS NOT NULL
GROUP BY du.segment ORDER BY du.segment
""").collect()
assert [(r[0], r[1]) for r in as_is] == [("new", 1), ("vip", 1)], as_is
print("[PASS] joining on is_current instead relabels user 1's January purchase "
      "as 'vip' -- the vip cohort looks better than it earned (survivorship)")

# --- the 24h sessionization rule (constraint 2) happens UPSTREAM
# Recompute sessions with gap-and-island and compare to the source session_id.
recomputed = spark.sql("""
WITH flagged AS (
    SELECT user_id, event_timestamp, session_id,
           CASE WHEN UNIX_TIMESTAMP(event_timestamp) - UNIX_TIMESTAMP(
                    LAG(event_timestamp) OVER (PARTITION BY user_id
                                               ORDER BY event_timestamp)
                ) > 86400 OR LAG(event_timestamp) OVER (PARTITION BY user_id
                                               ORDER BY event_timestamp) IS NULL
                THEN 1 ELSE 0 END AS is_new_session
    FROM User_Events
),
islands AS (
    SELECT user_id, session_id,
           SUM(is_new_session) OVER (PARTITION BY user_id ORDER BY event_timestamp
                                     ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
               AS derived_session_num
    FROM flagged
)
SELECT COUNT(DISTINCT user_id || '-' || CAST(derived_session_num AS STRING)) AS derived,
       COUNT(DISTINCT session_id) AS from_source
FROM islands
""").collect()[0]
assert (recomputed[0], recomputed[1]) == (5, 5), recomputed
print(f"[PASS] 24h gap-and-island rederives {recomputed[0]} sessions, matching the "
      f"source's {recomputed[1]} -- the rule is validated, not assumed")

# --- A/B assignment is per USER, not per session
per_user = spark.sql("""
SELECT u.user_id, COUNT(DISTINCT ab.variant) AS variants, COUNT(*) AS sessions
FROM fact_session_funnel f
JOIN dim_user u ON u.user_sk = f.user_sk
JOIN dim_ab_variant ab ON ab.ab_variant_sk = f.ab_variant_sk
GROUP BY u.user_id ORDER BY u.user_id
""").collect()
assert all(r[1] == 1 for r in per_user), per_user
multi = [r[0] for r in per_user if r[2] > 1]
assert multi == [1, 2], multi
print(f"[PASS] users {multi} have multiple sessions but one variant each "
      "-- a session-derived variant would have broken the test")

# --- session_id is degenerate: on both facts, no dim table
tables = {r.tableName for r in spark.sql("SHOW TABLES").collect()}
assert "dim_session" not in tables
assert "session_id" in spark.table("fact_funnel_event").columns
assert "session_id" in spark.table("fact_session_funnel").columns
print("[PASS] session_id is a degenerate dimension on both facts -- no dim_session "
      "(requirement 2)")

# --- the two facts reconcile
recon = spark.sql("""
SELECT (SELECT COUNT(DISTINCT session_id) FROM fact_funnel_event)   AS from_events,
       (SELECT COUNT(*)                   FROM fact_session_funnel) AS snapshot_rows
""").collect()[0]
assert recon[0] == recon[1] == 5, recon
print("[PASS] both facts reconcile: 5 distinct sessions in the event fact = "
      "5 rows in the snapshot")

print("\n[PASS] all 7 requirements satisfied: per-stage rows, degenerate session_id, "
      "SCD2 segments, A/B variant, distinct-user drop-off, stored durations, two facts")

# ---- MySQL way ----------------------------------------------------------
# CREATE TABLE + sample data:
#   CREATE TABLE Users (
#       user_id      INT          NOT NULL,
#       signup_date  DATE         NOT NULL,
#       segment      VARCHAR(16)  NOT NULL,
#       country      VARCHAR(8)   NOT NULL,
#       PRIMARY KEY (user_id)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO Users (user_id, signup_date, segment, country) VALUES
#       (1, '2025-11-01', 'vip',       'US'),
#       (2, '2026-01-05', 'returning', 'IN'),
#       (3, '2026-02-20', 'new',       'BR');
#
#   CREATE TABLE Products (
#       product_id   INT             NOT NULL,
#       product_name VARCHAR(64)     NOT NULL,
#       category     VARCHAR(16)     NOT NULL,
#       price        DECIMAL(10,2)   NOT NULL,
#       is_active    TINYINT(1)      NOT NULL,
#       PRIMARY KEY (product_id)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO Products (product_id, product_name, category, price, is_active) VALUES
#       (900, 'Noise Cancelling Headphones', 'audio', 299.00, 1),
#       (901, 'Laptop Stand',                'desk',   49.00, 1),
#       (902, 'Mechanical Keyboard',         'desk',  129.00, 1);
#
#   CREATE TABLE AB_Tests (
#       test_id        VARCHAR(16) NOT NULL,
#       user_id        INT         NOT NULL,
#       test_name      VARCHAR(32) NOT NULL,
#       variant        VARCHAR(16) NOT NULL,
#       assigned_date  DATE        NOT NULL,
#       PRIMARY KEY (test_id, user_id)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO AB_Tests (test_id, user_id, test_name, variant, assigned_date) VALUES
#       ('T1', 1, 'checkout_redesign', 'treatment', '2026-01-01'),
#       ('T1', 2, 'checkout_redesign', 'control',   '2026-01-01'),
#       ('T1', 3, 'checkout_redesign', 'treatment', '2026-02-20');
#
#   CREATE TABLE Sessions (
#       session_id         VARCHAR(8)  NOT NULL,
#       user_id            INT         NOT NULL,
#       session_start      DATETIME    NOT NULL,
#       session_end        DATETIME    NOT NULL,
#       device_type        VARCHAR(16) NOT NULL,
#       marketing_channel  VARCHAR(16) NOT NULL,
#       PRIMARY KEY (session_id),
#       KEY idx_sess_user (user_id)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO Sessions VALUES
#       ('S1', 1, '2026-01-10 09:00:00', '2026-01-10 09:40:00', 'mobile',  'paid_search'),
#       ('S2', 1, '2026-03-02 14:00:00', '2026-03-02 14:25:00', 'desktop', 'organic'),
#       ('S3', 2, '2026-03-03 11:00:00', '2026-03-03 11:12:00', 'mobile',  'email'),
#       ('S4', 3, '2026-03-04 20:00:00', '2026-03-04 20:30:00', 'desktop', 'paid_social'),
#       ('S5', 2, '2026-03-05 08:00:00', '2026-03-05 08:05:00', 'mobile',  'organic');
#
#   CREATE TABLE User_Events (
#       event_id        INT           NOT NULL,
#       user_id         INT           NOT NULL,
#       session_id      VARCHAR(8)    NOT NULL,
#       event_type      VARCHAR(16)   NOT NULL,
#       product_id      INT               NULL,
#       event_timestamp DATETIME      NOT NULL,
#       device_type     VARCHAR(16)   NOT NULL,
#       page_url        VARCHAR(64)   NOT NULL,
#       PRIMARY KEY (event_id),
#       KEY idx_ue_session (session_id),
#       KEY idx_ue_user_ts (user_id, event_timestamp)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO User_Events VALUES
#       (1,  1, 'S1', 'browse',       NULL, '2026-01-10 09:00:00', 'mobile',  '/home'),
#       (2,  1, 'S1', 'search',       NULL, '2026-01-10 09:03:00', 'mobile',  '/search'),
#       (3,  1, 'S1', 'view_product', 900,  '2026-01-10 09:05:00', 'mobile',  '/p/900'),
#       (4,  1, 'S1', 'view_product', 900,  '2026-01-10 09:20:00', 'mobile',  '/p/900'),
#       (5,  1, 'S1', 'add_to_cart',  900,  '2026-01-10 09:25:00', 'mobile',  '/cart'),
#       (6,  1, 'S1', 'checkout',     900,  '2026-01-10 09:35:00', 'mobile',  '/checkout'),
#       (7,  1, 'S1', 'purchase',     900,  '2026-01-10 09:40:00', 'mobile',  '/confirm'),
#       (8,  1, 'S2', 'browse',       NULL, '2026-03-02 14:00:00', 'desktop', '/home'),
#       (9,  1, 'S2', 'view_product', 901,  '2026-03-02 14:10:00', 'desktop', '/p/901'),
#       (10, 1, 'S2', 'add_to_cart',  901,  '2026-03-02 14:20:00', 'desktop', '/cart'),
#       (11, 2, 'S3', 'browse',       NULL, '2026-03-03 11:00:00', 'mobile',  '/home'),
#       (12, 2, 'S3', 'search',       NULL, '2026-03-03 11:04:00', 'mobile',  '/search'),
#       (13, 2, 'S3', 'view_product', 902,  '2026-03-03 11:08:00', 'mobile',  '/p/902'),
#       (14, 3, 'S4', 'browse',       NULL, '2026-03-04 20:00:00', 'desktop', '/home'),
#       (15, 3, 'S4', 'view_product', 900,  '2026-03-04 20:05:00', 'desktop', '/p/900'),
#       (16, 3, 'S4', 'checkout',     900,  '2026-03-04 20:25:00', 'desktop', '/checkout'),
#       (17, 3, 'S4', 'purchase',     900,  '2026-03-04 20:30:00', 'desktop', '/confirm'),
#       (18, 2, 'S5', 'browse',       NULL, '2026-03-05 08:00:00', 'mobile',  '/home');
#
#   CREATE TABLE Purchases (
#       purchase_id       INT           NOT NULL,
#       user_id           INT           NOT NULL,
#       session_id        VARCHAR(8)    NOT NULL,
#       product_id        INT           NOT NULL,
#       purchase_timestamp DATETIME     NOT NULL,
#       amount            DECIMAL(10,2) NOT NULL,
#       PRIMARY KEY (purchase_id)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO Purchases VALUES
#       (5001, 1, 'S1', 900, '2026-01-10 09:40:00', 299.00),
#       (5002, 3, 'S4', 900, '2026-03-04 20:30:00', 299.00);
#
#   CREATE TABLE dim_stage (
#       stage_key  INT         NOT NULL,
#       stage_name VARCHAR(16) NOT NULL,
#       PRIMARY KEY (stage_key)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO dim_stage VALUES
#       (1, 'browse'),       (2, 'search'),   (3, 'view_product'),
#       (4, 'add_to_cart'),  (5, 'checkout'), (6, 'purchase');
#
#   CREATE TABLE dim_user (
#       user_sk         INT          NOT NULL,
#       user_id         INT          NOT NULL,
#       country         VARCHAR(8)   NOT NULL,
#       signup_date     DATE         NOT NULL,
#       segment         VARCHAR(16)  NOT NULL,
#       effective_from  DATE         NOT NULL,
#       effective_to    DATE         NOT NULL,
#       is_current      TINYINT(1)   NOT NULL,
#       PRIMARY KEY (user_sk),
#       KEY idx_dim_user_pit (user_id, effective_from, effective_to)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO dim_user
#       (user_sk, user_id, country, signup_date, segment, effective_from, effective_to, is_current)
#   WITH changes AS (
#       SELECT 1 AS user_id, 'new'       AS segment, DATE'2025-11-01' AS changed_on UNION ALL
#       SELECT 1,            'returning',            DATE'2026-02-01'             UNION ALL
#       SELECT 1,            'vip',                  DATE'2026-03-01'             UNION ALL
#       SELECT 2,            'new',                  DATE'2026-01-05'             UNION ALL
#       SELECT 2,            'returning',            DATE'2026-02-15'             UNION ALL
#       SELECT 3,            'new',                  DATE'2026-02-20'
#   )
#   SELECT ROW_NUMBER() OVER (ORDER BY c.user_id, c.changed_on) AS user_sk,
#          c.user_id, u.country, u.signup_date, c.segment,
#          c.changed_on AS effective_from,
#          COALESCE(LEAD(c.changed_on) OVER (PARTITION BY c.user_id ORDER BY c.changed_on),
#                   DATE'9999-12-31') AS effective_to,
#          CASE WHEN LEAD(c.changed_on) OVER (PARTITION BY c.user_id ORDER BY c.changed_on) IS NULL
#               THEN 1 ELSE 0 END AS is_current
#   FROM changes c JOIN Users u ON u.user_id = c.user_id;
#
#   CREATE TABLE dim_product (
#       product_sk   INT             NOT NULL,
#       product_id   INT                 NULL,
#       product_name VARCHAR(64)         NULL,
#       category     VARCHAR(16)         NULL,
#       price        DECIMAL(10,2)       NULL,
#       PRIMARY KEY (product_sk)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO dim_product VALUES
#       (900, 900, 'Noise Cancelling Headphones', 'audio', 299.00),
#       (901, 901, 'Laptop Stand',                'desk',   49.00),
#       (902, 902, 'Mechanical Keyboard',         'desk',  129.00),
#       ( -1, NULL, '(not applicable)',           '(not applicable)', NULL);
#
#   CREATE TABLE dim_ab_variant (
#       ab_variant_sk INT         NOT NULL,
#       test_id       VARCHAR(16) NOT NULL,
#       user_id       INT         NOT NULL,
#       test_name     VARCHAR(32) NOT NULL,
#       variant       VARCHAR(16) NOT NULL,
#       assigned_date DATE        NOT NULL,
#       PRIMARY KEY (ab_variant_sk)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO dim_ab_variant
#       SELECT ROW_NUMBER() OVER (ORDER BY test_id, user_id), test_id, user_id, test_name, variant, assigned_date
#       FROM AB_Tests;
#
#   CREATE TABLE fact_funnel_event (
#       funnel_event_sk          INT          NOT NULL,
#       session_id               VARCHAR(8)   NOT NULL,    -- DEGENERATE dimension
#       user_sk                  INT          NOT NULL,
#       product_sk               INT          NOT NULL,
#       stage_key                INT          NOT NULL,
#       ab_variant_sk            INT              NULL,
#       device_type              VARCHAR(16)  NOT NULL,
#       marketing_channel        VARCHAR(16)  NOT NULL,
#       event_timestamp          DATETIME     NOT NULL,
#       event_date               DATE         NOT NULL,
#       seconds_since_prev_stage INT              NULL,
#       PRIMARY KEY (funnel_event_sk),
#       KEY idx_ffe_session_ts (session_id, event_timestamp),
#       KEY idx_ffe_user (user_sk)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO fact_funnel_event
#   SELECT e.event_id,
#          e.session_id, du.user_sk, COALESCE(e.product_id, -1), ds.stage_key,
#          ab.ab_variant_sk, s.device_type, s.marketing_channel,
#          e.event_timestamp, CAST(e.event_timestamp AS DATE),
#          CAST(TIMESTAMPDIFF(SECOND,
#               LAG(e.event_timestamp) OVER (PARTITION BY e.session_id ORDER BY e.event_timestamp, e.event_id),
#               e.event_timestamp) AS SIGNED)
#   FROM User_Events e
#   JOIN dim_stage     ds ON ds.stage_name = e.event_type
#   JOIN Sessions      s  ON s.session_id  = e.session_id
#   JOIN dim_user      du ON du.user_id    = e.user_id
#                         AND CAST(e.event_timestamp AS DATE) >= du.effective_from
#                         AND CAST(e.event_timestamp AS DATE) <  du.effective_to
#   LEFT JOIN dim_ab_variant ab ON ab.user_id = e.user_id AND ab.test_id = 'T1';
#
#   CREATE TABLE fact_session_funnel (
#       session_id               VARCHAR(8)   NOT NULL,
#       user_sk                  INT          NOT NULL,
#       ab_variant_sk            INT              NULL,
#       device_type              VARCHAR(16)  NOT NULL,
#       marketing_channel        VARCHAR(16)  NOT NULL,
#       session_date             DATE         NOT NULL,
#       browse_ts                DATETIME         NULL,
#       search_ts                DATETIME         NULL,
#       view_ts                  DATETIME         NULL,
#       cart_ts                  DATETIME         NULL,
#       checkout_ts              DATETIME         NULL,
#       purchase_ts              DATETIME         NULL,
#       purchase_amount          DECIMAL(10,2)    NULL,
#       seconds_view_to_purchase INT              NULL,
#       seconds_view_to_cart     INT              NULL,
#       max_stage_key            INT          NOT NULL,
#       PRIMARY KEY (session_id)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO fact_session_funnel
#   WITH milestones AS (
#       SELECT f.session_id, MIN(f.user_sk) AS user_sk, MIN(f.ab_variant_sk) AS ab_variant_sk,
#              MIN(f.device_type) AS device_type, MIN(f.marketing_channel) AS marketing_channel,
#              CAST(MIN(f.event_timestamp) AS DATE) AS session_date,
#              MIN(CASE WHEN d.stage_name = 'browse'       THEN f.event_timestamp END) AS browse_ts,
#              MIN(CASE WHEN d.stage_name = 'search'       THEN f.event_timestamp END) AS search_ts,
#              MIN(CASE WHEN d.stage_name = 'view_product' THEN f.event_timestamp END) AS view_ts,
#              MIN(CASE WHEN d.stage_name = 'add_to_cart'  THEN f.event_timestamp END) AS cart_ts,
#              MIN(CASE WHEN d.stage_name = 'checkout'     THEN f.event_timestamp END) AS checkout_ts,
#              MIN(CASE WHEN d.stage_name = 'purchase'     THEN f.event_timestamp END) AS purchase_ts
#       FROM fact_funnel_event f JOIN dim_stage d USING (stage_key)
#       GROUP BY f.session_id
#   )
#   SELECT m.session_id, m.user_sk, m.ab_variant_sk, m.device_type, m.marketing_channel,
#          m.session_date, m.browse_ts, m.search_ts, m.view_ts, m.cart_ts,
#          m.checkout_ts, m.purchase_ts,
#          p.amount AS purchase_amount,
#          CAST(TIMESTAMPDIFF(SECOND, m.view_ts, m.purchase_ts) AS SIGNED) AS seconds_view_to_purchase,
#          CAST(TIMESTAMPDIFF(SECOND, m.view_ts, m.cart_ts)     AS SIGNED) AS seconds_view_to_cart,
#          CASE WHEN m.purchase_ts IS NOT NULL THEN 6
#               WHEN m.checkout_ts IS NOT NULL THEN 5
#               WHEN m.cart_ts     IS NOT NULL THEN 4
#               WHEN m.view_ts     IS NOT NULL THEN 3
#               WHEN m.search_ts   IS NOT NULL THEN 2
#               ELSE 1 END AS max_stage_key
#   FROM milestones m LEFT JOIN Purchases p ON p.session_id = m.session_id;
#
#   -- Q1 view -> purchase conversion (distinct users) (expect block)
#   SELECT COUNT(DISTINCT CASE WHEN view_ts     IS NOT NULL THEN user_sk END) AS viewers,
#          COUNT(DISTINCT CASE WHEN purchase_ts IS NOT NULL THEN user_sk END) AS buyers,
#          ROUND(100.0 * COUNT(DISTINCT CASE WHEN purchase_ts IS NOT NULL THEN user_sk END)
#                      / COUNT(DISTINCT CASE WHEN view_ts IS NOT NULL THEN user_sk END), 2) AS view_to_purchase_pct
#   FROM fact_session_funnel;
#
#   -- Q1b same question at person grain (expect block)
#   SELECT COUNT(DISTINCT CASE WHEN f.view_ts IS NOT NULL THEN u.user_id END)     AS viewers,
#          COUNT(DISTINCT CASE WHEN f.purchase_ts IS NOT NULL THEN u.user_id END) AS buyers
#   FROM fact_session_funnel f JOIN dim_user u ON u.user_sk = f.user_sk;
#
#   -- Q2 drop-off by stage, LOOSE definition (expect block)
#   WITH reached AS (
#       SELECT d.stage_key, d.stage_name, COUNT(DISTINCT u.user_id) AS users
#       FROM fact_funnel_event f
#       JOIN dim_stage d USING (stage_key)
#       JOIN dim_user  u ON u.user_sk = f.user_sk
#       GROUP BY d.stage_key, d.stage_name
#   )
#   SELECT stage_name, users,
#          LAG(users) OVER (ORDER BY stage_key) AS prev_users,
#          ROUND(100.0 * (LAG(users) OVER (ORDER BY stage_key) - users)
#                      / LAG(users) OVER (ORDER BY stage_key), 2) AS drop_off_pct
#   FROM reached ORDER BY stage_key;
#
#   -- Q2-strict: the cumulative-chain check (expect block).
#   WITH per_session AS (
#       SELECT f.user_sk,
#              f.view_ts IS NOT NULL                                              AS r_view,
#              f.view_ts IS NOT NULL AND f.cart_ts     >= f.view_ts               AS r_cart,
#              f.view_ts IS NOT NULL AND f.cart_ts     >= f.view_ts
#                                       AND f.checkout_ts >= f.cart_ts           AS r_checkout,
#              f.view_ts IS NOT NULL AND f.cart_ts     >= f.view_ts
#                                       AND f.checkout_ts >= f.cart_ts
#                                       AND f.purchase_ts >= f.checkout_ts       AS r_purchase
#       FROM fact_session_funnel f
#   ),
#   reached AS (
#       SELECT u.user_id,
#              MAX(CASE WHEN p.r_view     THEN 1 ELSE 0 END) AS s_view,
#              MAX(CASE WHEN p.r_cart     THEN 1 ELSE 0 END) AS s_cart,
#              MAX(CASE WHEN p.r_checkout THEN 1 ELSE 0 END) AS s_checkout,
#              MAX(CASE WHEN p.r_purchase THEN 1 ELSE 0 END) AS s_purchase
#       FROM per_session p JOIN dim_user u ON u.user_sk = p.user_sk
#       GROUP BY u.user_id
#   )
#   SELECT 'view_product' AS stage_name, SUM(s_view)     AS users FROM reached UNION ALL
#   SELECT 'add_to_cart',                 SUM(s_cart)     FROM reached UNION ALL
#   SELECT 'checkout',                    SUM(s_checkout) FROM reached UNION ALL
#   SELECT 'purchase',                    SUM(s_purchase) FROM reached;
#
#   -- Q3 time view -> purchase (accumulating snapshot) (expect block)
#   SELECT ROUND(AVG(seconds_view_to_purchase) / 60.0, 2) AS avg_minutes_view_to_purchase,
#          COUNT(seconds_view_to_purchase)                AS sessions_measured
#   FROM fact_session_funnel;
#
#   -- Q4 conversion by device (expect block)
#   SELECT device_type,
#          COUNT(*) AS sessions,
#          COUNT(purchase_ts) AS purchases,
#          ROUND(100.0 * COUNT(purchase_ts) / COUNT(*), 2) AS session_cvr_pct
#   FROM fact_session_funnel
#   GROUP BY device_type ORDER BY session_cvr_pct DESC, device_type;
#
#   -- Q5 conversion by A/B variant (expect block)
#   SELECT ab.variant,
#          COUNT(*) AS sessions,
#          COUNT(f.purchase_ts) AS purchases,
#          ROUND(100.0 * COUNT(f.purchase_ts) / COUNT(*), 2) AS cvr_pct
#   FROM fact_session_funnel f
#   JOIN dim_ab_variant ab ON ab.ab_variant_sk = f.ab_variant_sk
#   GROUP BY ab.variant ORDER BY cvr_pct DESC, ab.variant;
#
#   -- Q6 purchase attribution by channel (expect block)
#   SELECT marketing_channel,
#          COUNT(*)                       AS purchase_sessions,
#          ROUND(SUM(purchase_amount), 2) AS revenue
#   FROM fact_session_funnel
#   WHERE purchase_ts IS NOT NULL
#   GROUP BY marketing_channel ORDER BY revenue DESC, marketing_channel;
#
# MySQL 8.0+ notes: TIMESTAMPDIFF(SECOND, a, b) replaces UNIX_TIMESTAMP(...)
# arithmetic -- it is portable and ignores DST. Spark's explode(sequence(...))
# for the session-id `range` becomes a recursive CTE or a numbers table at
# write time. dim_user is built ONCE from a change log via LEAD for the SCD2
# intervals -- the point-in-time join (idx_dim_user_pit) is what stops
# January sessions from relabelling as 'vip' (the survivorship bug). The
# fact_session_funnel "max_stage_key" column stores the deepest stage reached
# so an abandonment report is a single GROUP BY rather than a multi-stage
# CASE per stage. Two facts, two grain statements -- never collapse.
