"""
Q25: What is a mini-dimension, and when do you use one?
Article: "50 Data Modeling Interview Questions for DEs" — SCDs & History Tracking

Meta flavor: "dim_user has 3 billion rows. Two attributes — engagement_band and
follower_band — are recomputed WEEKLY. SCD Type 2 on the full dimension would
add 3 billion rows a week. Fix it."

How to Think:
- The problem is that SCD2 row growth is driven by the VOLATILE attributes but
  paid for by the WIDTH of the whole dimension. So split them:
    dim_user             stable attributes, SCD2 (or Type 1), grows slowly
    dim_user_profile     the volatile BANDS ONLY, with its own surrogate key
  The fact then carries TWO foreign keys, one to each.
- The key insight, and the thing to say out loud: the mini-dimension holds the
  DISTINCT COMBINATIONS of the banded attributes, not one row per user. Two
  bands with a handful of levels each is a few dozen rows TOTAL, forever --
  it does not scale with user count at all.
- BANDING is what makes this work. Raw follower_count has ~billions of distinct
  values, so a mini-dimension keyed on it would be as large as dim_user. Buckets
  ('0-1k', '1k-10k', ...) collapse it to a handful. If the attribute cannot be
  banded, a mini-dimension is the wrong tool.
- History is then captured by which profile key the FACT points at, so you get
  point-in-time behaviour with no dimension versioning at all.

The trap:
- Putting a HIGH-CARDINALITY attribute in the mini-dimension. Add raw
  follower_count and the combination count explodes back to dimension scale --
  same failure mode as the junk dimension in `05_junk_dimension.py`. Asserted.
- Forgetting that the fact now needs BOTH keys. Carry only the user key and you
  have lost the profile entirely; carry only the profile key and you cannot
  identify the user.
- The profile key must be assigned to the fact AT EVENT TIME. Resolve it at
  query time against "today's" profile and you have rebuilt a Type 1 dimension:
  January events get March bands. Asserted -- this is the real trap.
- The mini-dimension is NOT a substitute for SCD2 on the stable attributes. A
  country change still belongs in dim_user's own history.

Spark note:
- The mini-dimension is tiny and broadcasts. Resolving the profile key on write
  costs one small join in the ETL; resolving at read costs it on every query.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("11-mini-dimension")
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


from pyspark.sql import functions as F

ENGAGEMENT_BANDS = ["low", "medium", "high"]
FOLLOWER_BANDS = ["0-1k", "1k-10k", "10k-100k", "100k+"]

# ---------------------------------------------------------- the mini-dimension
# Every COMBINATION of the two bands. 3 x 4 = 12 rows, regardless of user count.
# Keys are spelled out rather than generated so the key -> band mapping is
# readable, and so a rebuild cannot renumber it (see 05_junk_dimension.py).
spark.sql("""
CREATE OR REPLACE TEMP VIEW dim_user_profile AS
SELECT * FROM VALUES
    ( 1, 'low',    '0-1k'),     ( 2, 'low',    '1k-10k'),
    ( 3, 'low',    '10k-100k'), ( 4, 'low',    '100k+'),
    ( 5, 'medium', '0-1k'),     ( 6, 'medium', '1k-10k'),
    ( 7, 'medium', '10k-100k'), ( 8, 'medium', '100k+'),
    ( 9, 'high',   '0-1k'),     (10, 'high',   '1k-10k'),
    (11, 'high',   '10k-100k'), (12, 'high',   '100k+')
AS t(profile_key, engagement_band, follower_band)
""")
profile_rows = spark.table("dim_user_profile").count()
assert profile_rows == len(ENGAGEMENT_BANDS) * len(FOLLOWER_BANDS) == 12
print(f"[PASS] Q25 mini-dimension has {profile_rows} rows total -- independent of user count")

# ---------------------------------------------------------- the big dimension
# Stable attributes only. NOT versioned by the weekly band churn.
spark.sql("""
CREATE OR REPLACE TEMP VIEW dim_user AS
SELECT * FROM VALUES
    (1, 7001, 'US', DATE'2024-05-01'),
    (2, 7002, 'IN', DATE'2024-06-15'),
    (3, 7003, 'BR', DATE'2025-01-20')
AS t(user_sk, user_id, country, signup_date)
""")

# ---------------------------------------------------------- the fact
# TWO foreign keys. profile_key is stamped AT EVENT TIME, which is what
# preserves history without versioning either dimension.
spark.sql("""
CREATE OR REPLACE TEMP VIEW fact_reel_post AS
SELECT * FROM VALUES
    (1, 1, 2,  DATE'2026-01-10',  500),
    (2, 1, 2,  DATE'2026-01-24',  700),
    (3, 1, 11, DATE'2026-03-14', 9000),
    (4, 2, 5,  DATE'2026-01-11',  300),
    (5, 3, 2,  DATE'2026-03-02',  150)
AS t(post_id, user_sk, profile_key, post_date, views)
""")

# ---------------------------------------------------------- the payoff
BANDED = """
SELECT p.engagement_band,
       p.follower_band,
       u.country,
       COUNT(*)      AS posts,
       SUM(f.views)  AS views
FROM fact_reel_post f
JOIN dim_user         u ON u.user_sk     = f.user_sk
JOIN dim_user_profile p ON p.profile_key = f.profile_key
GROUP BY p.engagement_band, p.follower_band, u.country
ORDER BY views DESC, p.engagement_band, u.country
"""
spark.sql(BANDED).show(truncate=False)
expect("Q25 two keys, one query, bands as of the post date", BANDED, [
    ("medium", "1k-10k",   "US", 1, 9000),
    ("high",   "1k-10k",   "US", 2, 1200),
    ("high",   "10k-100k", "IN", 1,  300),
    ("high",   "1k-10k",   "BR", 1,  150),
])

# DataFrame API equivalent.
df = (spark.table("fact_reel_post")
      .join(F.broadcast(spark.table("dim_user")), "user_sk")
      .join(F.broadcast(spark.table("dim_user_profile")), "profile_key")
      .groupBy("engagement_band", "follower_band", "country")
      .agg(F.count(F.lit(1)).alias("posts"), F.sum("views").alias("views"))
      .orderBy(F.col("views").desc(), F.col("engagement_band"), F.col("country")))
assert [tuple(r) for r in df.collect()] == [
    ("medium", "1k-10k", "US", 1, 9000),
    ("high", "1k-10k", "US", 2, 1200),
    ("high", "10k-100k", "IN", 1, 300),
    ("high", "1k-10k", "BR", 1, 150),
]
print("[PASS] Q25 DataFrame API matches SQL")

# ---------------------------------------------------------- history without versioning
# User 1 was profile 2 in January and profile 11 in March. dim_user was never
# versioned, and dim_user_profile never grew.
user1 = spark.sql("""
SELECT f.post_date, p.engagement_band, p.follower_band
FROM fact_reel_post f JOIN dim_user_profile p ON p.profile_key = f.profile_key
WHERE f.user_sk = 1 ORDER BY f.post_date
""").collect()
assert [(str(r[0]), r[1], r[2]) for r in user1] == [
    ("2026-01-10", "high",   "1k-10k"),
    ("2026-01-24", "high",   "1k-10k"),
    ("2026-03-14", "medium", "1k-10k"),
], user1
print("[PASS] Q25 user 1's January posts read 'high' and March reads 'medium' -- "
      "point-in-time bands with ZERO dimension versions")

assert spark.table("dim_user").count() == 3
assert spark.table("dim_user_profile").count() == 12
print("[PASS] Q25 dim_user still 3 rows, mini-dimension still 12 -- neither grew")

# ---------------------------------------------------------- the SCD2 cost avoided
# What weekly Type 2 versioning on the full dimension would have cost.
USERS = 3_000_000_000
WEEKS = 52
scd2_rows = USERS * WEEKS
print(f"[PASS] Q25 weekly SCD2 on {USERS:,} users would add {scd2_rows:,} rows/year; "
      f"the mini-dimension stays at {profile_rows}")

# ---------------------------------------------------------- the resolve-at-query trap
# Resolving the band from TODAY's profile instead of the stamped key rebuilds a
# Type 1 dimension: January posts get March bands.
spark.sql("""
CREATE OR REPLACE TEMP VIEW current_user_profile AS
SELECT user_sk, profile_key FROM (
    SELECT user_sk, profile_key,
           ROW_NUMBER() OVER (PARTITION BY user_sk ORDER BY post_date DESC) AS rn
    FROM fact_reel_post
) WHERE rn = 1
""")
as_is = spark.sql("""
SELECT f.post_date, p.engagement_band
FROM fact_reel_post f
JOIN current_user_profile c ON c.user_sk = f.user_sk
JOIN dim_user_profile     p ON p.profile_key = c.profile_key
WHERE f.user_sk = 1 ORDER BY f.post_date
""").collect()
assert [(str(r[0]), r[1]) for r in as_is] == [
    ("2026-01-10", "medium"), ("2026-01-24", "medium"), ("2026-03-14", "medium"),
], as_is
print("[PASS] Q25 resolving against today's profile relabels January as 'medium' -- "
      "history lost, the key must be stamped at event time")

# ---------------------------------------------------------- the banding trap
# Raw follower_count instead of a band explodes the mini-dimension.
spark.sql("""
CREATE OR REPLACE TEMP VIEW user_metrics AS
SELECT id AS user_id,
       CASE WHEN id % 3 = 0 THEN 'low' WHEN id % 3 = 1 THEN 'medium' ELSE 'high' END
           AS engagement_band,
       CAST(id * 137 AS INT) AS follower_count
FROM range(1, 1001)
""")
banded_combos = spark.sql("""
SELECT COUNT(*) FROM (
    SELECT DISTINCT engagement_band,
           CASE WHEN follower_count <   1000 THEN '0-1k'
                WHEN follower_count <  10000 THEN '1k-10k'
                WHEN follower_count < 100000 THEN '10k-100k'
                ELSE '100k+' END AS follower_band
    FROM user_metrics
)
""").collect()[0][0]
raw_combos = spark.sql("""
SELECT COUNT(*) FROM (SELECT DISTINCT engagement_band, follower_count FROM user_metrics)
""").collect()[0][0]
assert (banded_combos, raw_combos) == (10, 1000), (banded_combos, raw_combos)
print(f"[PASS] Q25 banding gives {banded_combos} combinations from 1000 users; "
      f"raw follower_count gives {raw_combos} -- as large as the dimension itself")
