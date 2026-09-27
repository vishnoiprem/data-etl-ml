"""
Seed tables for the 25 Meta-tagged DataVidhya questions.

Every table is deliberately tiny and hand-checkable, and every one carries at
least one TRAP that the real question is testing:

  posts            - user 3 has exactly 1 post (fails the ">= 2 posts" filter)
  signups/activity - a user active on signup day only (D0 but not D1/D7)
  funnel           - one user skips a step, one repeats a step
  pages            - a page with zero likes (the LEFT JOIN/NULL case)
  actions          - a user active in June and August but NOT July (gap case)
  fraud_scores     - ties at the percentile boundary
  friend_requests  - a request sent and never accepted
  advertiser_pay   - a genuine resurrection (gap then return)
  posts_content    - 'spam' appears mid-word to test LIKE vs word matching

Run any solution from this folder:
    cd 12_DataVidhya_Meta_Set && ../../../../.env/bin/python 01_power_users.py
"""
import decimal
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_HERE))))
_PY = os.path.join(_REPO, ".env", "bin", "python")
if os.path.exists(_PY):
    os.environ.setdefault("PYSPARK_PYTHON", _PY)

from pyspark.sql import SparkSession  # noqa: E402

spark = (
    SparkSession.builder
    .appName("meta-datavidhya-set")
    .master("local[2]")
    .config("spark.sql.shuffle.partitions", "2")
    .config("spark.ui.enabled", "false")
    .config("spark.ui.showConsoleProgress", "false")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")


def _v(name, rows, cols):
    spark.createDataFrame(rows, cols).createOrReplaceTempView(name)


# --- Q01 Power users: posts with likes + comments --------------------------
# user 1: 2 posts, avg reactions (200+100)/2 = 150.0  -> qualifies (>= 150)
# user 2: 3 posts, avg (300+200+100)/3 = 200.0        -> qualifies
# user 3: 1 post, 500 reactions                       -> FAILS (only 1 post)
# user 4: 2 posts, avg (100+100)/2 = 100.0            -> FAILS (< 150)
_v("posts", [
    (1, 1, 150, 50), (2, 1, 80, 20),
    (3, 2, 250, 50), (4, 2, 150, 50), (5, 2, 70, 30),
    (6, 3, 400, 100),
    (7, 4, 60, 40), (8, 4, 70, 30),
], ["post_id", "user_id", "likes", "comments"])

# --- Q02 Retention cohorts (weekly) ---------------------------------------
# Week of 2026-01-05 (Mon): users 1,2,3 | Week of 2026-01-12: users 4,5
_v("signups", [
    (1, "2026-01-05"), (2, "2026-01-06"), (3, "2026-01-07"),
    (4, "2026-01-12"), (5, "2026-01-13"),
], ["user_id", "signup_date"])

_v("activity", [
    (1, "2026-01-05"), (1, "2026-01-06"), (1, "2026-01-12"),   # D0,D1,D7
    (2, "2026-01-06"), (2, "2026-01-07"),                      # D0,D1
    (3, "2026-01-07"),                                         # D0 only
    (4, "2026-01-12"), (4, "2026-01-13"), (4, "2026-01-19"),   # D0,D1,D7
    (5, "2026-01-13"),                                         # D0 only
], ["user_id", "activity_date"])

# --- Q03 / Q20 Funnel: view -> click -> purchase --------------------------
_v("funnel", [
    (1, "view", "2026-03-01 10:00:00"),
    (1, "click", "2026-03-01 10:02:00"),
    (1, "purchase", "2026-03-01 10:09:00"),
    (2, "view", "2026-03-01 11:00:00"),
    (2, "click", "2026-03-01 11:04:00"),
    (3, "view", "2026-03-01 12:00:00"),
    (4, "view", "2026-03-02 09:00:00"),
    (4, "view", "2026-03-02 09:06:00"),          # duplicate step
    (4, "click", "2026-03-02 09:11:00"),
    (5, "view", "2026-03-02 14:00:00"),
    (5, "purchase", "2026-03-02 14:20:00"),      # skipped 'click'
], ["user_id", "event_name", "event_ts"])

# --- Q04 Monthly active retention (Jun / Jul / Aug 2022) ------------------
# Qualifying actions are only 'sign-in', 'like', 'comment'.
# user 1: Jun + Jul  -> retained
# user 2: Jul only   -> new in Jul
# user 3: Jun only   -> churned in Jul
# user 4: Jun + Jul but Jul action is 'logout' (not qualifying) -> NOT retained
# user 5: Jun + Aug (skips Jul) -> resurrected in Aug
_v("user_actions", [
    (1, "sign-in", "2022-06-10"), (1, "like",    "2022-07-11"),
    (2, "comment", "2022-07-05"),
    (3, "like",    "2022-06-20"),
    (4, "sign-in", "2022-06-15"), (4, "logout",  "2022-07-15"),
    (5, "sign-in", "2022-06-01"), (5, "comment", "2022-08-02"),
], ["user_id", "action", "action_date"])

# --- Q05 Pages with no likes ---------------------------------------------
# page 103 and 104 have zero likes.
_v("pages", [
    (101, "Cooking Daily"), (102, "Tech Weekly"),
    (103, "Empty Page"), (104, "Also Empty"),
], ["page_id", "page_name"])

_v("page_likes", [
    (101, 1), (101, 2), (102, 1),
], ["page_id", "user_id"])

# --- Q06 MAU / churned / resurrected -------------------------------------
# Months: 2026-01, 2026-02, 2026-03
# u1: Jan,Feb,Mar  u2: Jan only (churn Feb)  u3: Feb,Mar (new Feb)
# u4: Jan,Mar (churn Feb, RESURRECTED Mar)
_v("activity_log", [
    (1, "2026-01-10"), (1, "2026-02-10"), (1, "2026-03-10"),
    (2, "2026-01-15"),
    (3, "2026-02-20"), (3, "2026-03-05"),
    (4, "2026-01-05"), (4, "2026-03-25"),
], ["user_id", "event_date"])

# --- Q07 Energy consumption by region ------------------------------------
_v("energy_asia",   [(2024, 100.0), (2025, 150.0)], ["year", "consumption"])
_v("energy_europe", [(2024, 200.0), (2025, 120.0)], ["year", "consumption"])
_v("energy_africa", [(2024,  50.0), (2025,  80.0)], ["year", "consumption"])
# 2024 total = 350.0 ; 2025 total = 350.0  -> deliberate TIE

# --- Q08 Customer revenue in March ---------------------------------------
_v("cust_orders", [
    (1, 10, "2026-03-02", 2, 25.00),
    (2, 10, "2026-03-15", 1, 10.00),
    (3, 11, "2026-03-20", 3, 30.00),
    (4, 12, "2026-02-28", 5, 100.00),   # February - excluded
    (5, 11, "2026-04-01", 1, 99.00),    # April - excluded
], ["order_id", "customer_id", "order_date", "quantity", "unit_cost"])

# --- Q09 Fraud score percentile per state --------------------------------
_v("fraud_scores", [
    (1, "CA", 10.0), (2, "CA", 20.0), (3, "CA", 30.0), (4, "CA", 90.0),
    (5, "NY", 40.0), (6, "NY", 95.0),
    (7, "TX", 50.0),
], ["record_id", "state", "fraud_score"])

# --- Q10 / Q18 Friend requests -------------------------------------------
# 'sent' and 'accepted' rows. Jan: 3 sent, 2 accepted. Feb: 2 sent, 1 accepted.
_v("friend_requests", [
    (1, 2, "sent",     "2026-01-05"), (1, 2, "accepted", "2026-01-06"),
    (1, 3, "sent",     "2026-01-10"), (1, 3, "accepted", "2026-01-12"),
    (2, 4, "sent",     "2026-01-20"),
    (3, 5, "sent",     "2026-02-02"), (3, 5, "accepted", "2026-02-03"),
    (4, 6, "sent",     "2026-02-14"),
], ["sender_id", "receiver_id", "action", "action_date"])

# --- Q11 Campaign success by language ------------------------------------
_v("campaigns", [
    (1, "en", 1), (2, "en", 1), (3, "en", 0), (4, "en", 0),   # 2/4 = 50.00
    (5, "th", 1), (6, "th", 1), (7, "th", 1),                 # 3/3 = 100.00
    (8, "ja", 0), (9, "ja", 0),                               # 0/2 = 0.00
], ["campaign_id", "language", "is_success"])

# --- Q12 Monthly revenue + MoM change ------------------------------------
_v("monthly_rev", [
    ("2026-01", 1000.0),
    ("2026-02", 1200.0),   # +20.00%
    ("2026-03",  900.0),   # -25.00%
    ("2026-04",  900.0),   #   0.00%
], ["month", "revenue"])

# --- Q13 Popularity by domain --------------------------------------------
_v("domain_views", [
    ("facebook.com", 500), ("instagram.com", 300),
    ("whatsapp.com", 150), ("threads.net", 50),
], ["domain", "views"])   # total 1000 -> 50.00 / 30.00 / 15.00 / 5.00

# --- Q14 Days between first and last post (2024) -------------------------
# u1: 2 posts 2024, 30 days apart | u2: 3 posts, 2024-01-01..2024-12-31 = 365
# u3: 1 post in 2024 -> excluded | u4: 2 posts but one in 2023 -> only 2024 counts
_v("user_posts", [
    (1, "2024-01-01"), (1, "2024-01-31"),
    (2, "2024-01-01"), (2, "2024-06-15"), (2, "2024-12-31"),
    (3, "2024-05-05"),
    (4, "2023-12-01"), (4, "2024-03-01"), (4, "2024-03-11"),
], ["user_id", "post_date"])

# --- Q15 Running distinct count of users ---------------------------------
# d1: {1,2} -> 2 | d2: {2,3} -> cumulative {1,2,3} = 3 | d3: {1} -> still 3
_v("daily_users", [
    (1, "2026-01-01"), (2, "2026-01-01"),
    (2, "2026-01-02"), (3, "2026-01-02"),
    (1, "2026-01-03"),
], ["user_id", "activity_date"])

# --- Q16 Spam post percentage by day -------------------------------------
# 'spamming' contains 'spam' as a substring: tests LIKE '%spam%' semantics.
_v("posts_content", [
    (1, "buy cheap spam now"),
    (2, "normal holiday photo"),
    (3, "SPAM offer inside"),
    (4, "anti-spamming tools review"),
    (5, "just a regular post"),
], ["post_id", "content"])

_v("post_views", [
    (1, "2026-01-01"), (2, "2026-01-01"), (3, "2026-01-01"), (5, "2026-01-01"),
    (2, "2026-01-02"), (5, "2026-01-02"),
], ["post_id", "view_date"])

# --- Q17 Advertiser payment status ---------------------------------------
# a1: Jan,Feb    -> Feb = Existing
# a2: Feb only   -> Feb = New
# a3: Jan only   -> Feb = Churn
# a4: Jan,Mar    -> Mar = Resurrected
_v("advertiser_pay", [
    ("a1", "2026-01-10"), ("a1", "2026-02-10"),
    ("a2", "2026-02-05"),
    ("a3", "2026-01-20"),
    ("a4", "2026-01-15"), ("a4", "2026-03-15"),
], ["advertiser_id", "payment_date"])

# --- Q19 Most friends, bidirectional -------------------------------------
# accepted: 1-2, 1-3, 2-3, 3-4  -> u3 has 3 friends (1,2,4) = winner
_v("friendships", [
    (1, 2, "accepted"), (1, 3, "accepted"),
    (2, 3, "accepted"), (3, 4, "accepted"),
    (1, 5, "pending"),
], ["user1_id", "user2_id", "status"])

# --- Q20b View-to-lead conversion by location ----------------------------
_v("listing_views", [
    (1, "Bangkok"), (2, "Bangkok"), (3, "Bangkok"), (4, "Bangkok"),
    (5, "Hanoi"), (6, "Hanoi"),
    (7, "Manila"),
], ["view_id", "location"])

_v("listing_leads", [
    (1, "Bangkok"), (2, "Bangkok"),   # 2/4 = 50.00
    (5, "Hanoi"),                     # 1/2 = 50.00
                                      # Manila 0/1 = 0.00
], ["lead_id", "location"])


def _norm(v):
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, float):
        return round(v, 6)
    return v


def expect(title, sql, expected_rows):
    """Run a query and assert its exact rows, in order."""
    got = [tuple(_norm(c) for c in r) for r in spark.sql(sql).collect()]
    exp = [tuple(_norm(c) for c in r) for r in expected_rows]
    if got != exp:
        print(f"[FAIL] {title}")
        print(f"   expected: {exp}")
        print(f"   got:      {got}")
        raise AssertionError(title)
    print(f"[PASS] {title}")
    return got
