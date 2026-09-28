"""
Problem 01: Top-N per group (e.g., top 3 posts per user by engagement).

Meta flavor: "Show the top 5 reels by watch-time per creator in the last 7 days."

Business Question
-----------------
For each creator, which are their N best-performing posts by engagement, and in
what order? This is the shape behind every "top content per X" surface — creator
dashboards, candidate generation before reranking, and the "your top posts this
week" notification. The grain of the answer is one row per (group, rank).

How to Think
------------
- Rank within a partition with ROW_NUMBER() or RANK(), then filter OUTSIDE the
  window. You cannot filter on the window alias in WHERE — the window is
  computed after WHERE, so `rn` is not in scope yet. The subquery/CTE is
  structural, not stylistic.
- ROW_NUMBER() = exactly N per group. RANK() = ties share a rank, so a group may
  return MORE than N rows. DENSE_RANK() = ties share with no gaps. Pick by
  whether the business wants "exactly 5" or "everyone tied for 5th".
- Always partition by the group key; order by the metric descending.
- Add a deterministic tiebreak (`post_id` here). Without it, two posts on the
  same score make the output non-reproducible across runs — which breaks any
  downstream snapshot comparison.

How to Remember
---------------
- "PARTITION BY group, ORDER BY metric DESC, then wrap and filter rn <= N."
- ROW_NUMBER breaks ties arbitrarily -> use when duplicates are not meaningful.
- RANK leaves gaps (1,1,3); DENSE_RANK does not (1,1,2).

Spark / Performance Note
------------------------
- One shuffle on the partition key, then a sort within each partition. The
  `rn <= N` filter cannot be pushed below the window, so the window sees every
  row — partitioning the source table by `user_id` is what makes this cheap at
  scale.
- On a skewed group (one creator with millions of posts) this is a hot-key
  problem: that partition's task dominates. Salting does NOT help here, because
  ranking needs all of a group's rows co-located. Reach for a pre-filter (last
  7 days) or a two-pass approximate top-N instead.

AI Use Cases
------------
- Top-k recommendation candidates before reranking.
- Per-user feature extraction (top 3 clicked items -> embedding).
- Anomaly detection: top-1 baseline vs current.
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number, col

spark = (SparkSession.builder
         .appName("01-top-n-per-group")
         .master("local[2]")
         .config("spark.sql.shuffle.partitions", "2")
         .config("spark.ui.showConsoleProgress", "false")
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")

TOP_N = 3

# posts(user_id, post_id, engagement_score, created_at)
# User 1 has FOUR posts, so the rn <= 3 cut actually does something — post 104
# must be excluded. Without that row the filter is a no-op and the example
# proves nothing.
data = [
    (1, 101, 50, "2026-01-01"),
    (1, 102, 80, "2026-01-02"),
    (1, 103, 30, "2026-01-03"),
    (1, 104, 20, "2026-01-04"),   # 4th best -> must be cut
    (2, 201, 90, "2026-01-01"),
    (2, 202, 70, "2026-01-02"),
]
posts = spark.createDataFrame(data, ["user_id", "post_id", "engagement_score", "created_at"])
posts.createOrReplaceTempView("posts")

w = Window.partitionBy("user_id").orderBy(col("engagement_score").desc(), col("post_id"))
top_n = (posts.withColumn("rn", row_number().over(w))
         .filter(col("rn") <= TOP_N)
         .select("user_id", "post_id", "engagement_score", "rn")
         .orderBy("user_id", "rn"))
top_n.show()

EXPECTED = [
    (1, 102, 80, 1),
    (1, 101, 50, 2),
    (1, 103, 30, 3),   # 104 (score 20) is cut
    (2, 201, 90, 1),
    (2, 202, 70, 2),   # user 2 has only 2 posts -> returns both
]
assert [tuple(r) for r in top_n.collect()] == EXPECTED
print("[PASS] top-N per group — DataFrame API")

# SQL equivalent (Presto / Hive). Meta asks standard SQL with a Presto flavor.
# Note: you cannot filter on the window alias in WHERE — it is not in scope yet.
# The window function must be computed in a subquery/CTE, then filtered outside it.
SQL = f"""
SELECT user_id, post_id, engagement_score, rn
FROM (
    SELECT user_id,
           post_id,
           engagement_score,
           created_at,
           ROW_NUMBER() OVER (
               PARTITION BY user_id
               ORDER BY engagement_score DESC, post_id
           ) AS rn
    FROM posts
) ranked
WHERE rn <= {TOP_N}
ORDER BY user_id, rn
"""

spark.sql(SQL).show()
assert [tuple(r) for r in spark.sql(SQL).collect()] == EXPECTED
print("[PASS] top-N per group — SQL matches DataFrame API")

# The rank-function contrast, asserted rather than described. Give user 1 a tie
# at the top and the three functions diverge:
spark.sql("""
CREATE OR REPLACE TEMP VIEW tied_posts AS
SELECT * FROM VALUES
    (1, 101, 80), (1, 102, 80), (1, 103, 50), (1, 104, 30)
AS t(user_id, post_id, engagement_score)
""")
trio = spark.sql("""
SELECT post_id, engagement_score,
       ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY engagement_score DESC, post_id) AS rn,
       RANK()       OVER (PARTITION BY user_id ORDER BY engagement_score DESC) AS rnk,
       DENSE_RANK() OVER (PARTITION BY user_id ORDER BY engagement_score DESC) AS dense
FROM tied_posts ORDER BY engagement_score DESC, post_id
""").collect()
assert [(r.post_id, r.rn, r.rnk, r.dense) for r in trio] == [
    (101, 1, 1, 1),
    (102, 2, 1, 1),   # tied on 80: ROW_NUMBER splits them, RANK/DENSE share
    (103, 3, 3, 2),   # RANK skips 2, DENSE_RANK does not
    (104, 4, 4, 3),
]
print("[PASS] ROW_NUMBER 1,2,3,4 / RANK 1,1,3,4 / DENSE_RANK 1,1,2,3")

# ...and the consequence for "top 3". A tie at the TOP does not diverge: RANK
# gives 1,1,3 so `rank <= 3` still yields 3 rows. The divergence needs a tie
# that SPANS the cut — three posts tied for 2nd:
spark.sql("""
CREATE OR REPLACE TEMP VIEW spanning_tie AS
SELECT * FROM VALUES
    (1, 101, 90), (1, 102, 80), (1, 103, 80), (1, 104, 80), (1, 105, 30)
AS t(user_id, post_id, engagement_score)
""")
counts = spark.sql(f"""
SELECT
  (SELECT COUNT(*) FROM (SELECT ROW_NUMBER() OVER (PARTITION BY user_id
       ORDER BY engagement_score DESC, post_id) AS r FROM spanning_tie) x
   WHERE x.r <= {TOP_N}) AS by_row_number,
  (SELECT COUNT(*) FROM (SELECT RANK() OVER (PARTITION BY user_id
       ORDER BY engagement_score DESC) AS r FROM spanning_tie) y
   WHERE y.r <= {TOP_N}) AS by_rank,
  (SELECT COUNT(*) FROM (SELECT DENSE_RANK() OVER (PARTITION BY user_id
       ORDER BY engagement_score DESC) AS r FROM spanning_tie) z
   WHERE z.r <= {TOP_N}) AS by_dense_rank
""").collect()[0]
# ranks are 1, 2,2,2, 5  -> rank <= 3 captures the whole 3-way tie
# dense    are 1, 2,2,2, 3  -> dense <= 3 captures everything
assert (counts.by_row_number, counts.by_rank, counts.by_dense_rank) == (3, 4, 5), counts
print(f"[PASS] with a tie spanning the cut: rn<=3 gives {counts.by_row_number} rows, "
      f"rank<=3 gives {counts.by_rank}, dense<=3 gives {counts.by_dense_rank}")
print("       -> 'top 3' is ambiguous until you say WHICH function. Ask.")


# ============================================================================
# MySQL equivalent (MySQL 8.0+) -- paste the un-commented block into a
# `mysql` client to reproduce the same results outside of PySpark.
# ============================================================================
# CREATE DATABASE IF NOT EXISTS window_demo;
# USE window_demo;
#
# CREATE TABLE posts (
#     user_id          INT         NOT NULL,
#     post_id          INT         NOT NULL,
#     engagement_score INT         NOT NULL,
#     created_at       DATE        NOT NULL,
#     PRIMARY KEY (post_id)
# );
#
# INSERT INTO posts (user_id, post_id, engagement_score, created_at) VALUES
#     (1, 101, 50, '2026-01-01'),
#     (1, 102, 80, '2026-01-02'),
#     (1, 103, 30, '2026-01-03'),
#     (1, 104, 20, '2026-01-04'),   -- 4th best for user 1 -> cut by rn <= 3
#     (2, 201, 90, '2026-01-01'),
#     (2, 202, 70, '2026-01-02');
#
# -- ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...) is identical in
# -- MySQL 8.0+ and Spark. The same scoping rule applies: `rn` cannot appear
# -- in WHERE, so the window must be computed in a derived table or CTE first.
# --
# -- On MySQL 5.7 there are NO window functions at all. The portable 5.7
# -- workaround is a correlated count, which is O(n^2) and only acceptable on
# -- small tables:
# --   SELECT p.* FROM posts p
# --   WHERE (SELECT COUNT(*) FROM posts x
# --          WHERE x.user_id = p.user_id
# --            AND (x.engagement_score > p.engagement_score
# --                 OR (x.engagement_score = p.engagement_score
# --                     AND x.post_id < p.post_id))) < 3;
# WITH ranked AS (
#     SELECT user_id,
#            post_id,
#            engagement_score,
#            ROW_NUMBER() OVER (
#                PARTITION BY user_id
#                ORDER BY engagement_score DESC, post_id
#            ) AS rn
#     FROM posts
# )
# SELECT user_id, post_id, engagement_score, rn
# FROM ranked
# WHERE rn <= 3
# ORDER BY user_id, rn;
#
# -- Expected output (same as the PySpark assertion above):
# -- +---------+---------+------------------+----+
# -- | user_id | post_id | engagement_score | rn |
# -- +---------+---------+------------------+----+
# -- |       1 |     102 |               80 |  1 |
# -- |       1 |     101 |               50 |  2 |
# -- |       1 |     103 |               30 |  3 |
# -- |       2 |     201 |               90 |  1 |
# -- |       2 |     202 |               70 |  2 |
# -- +---------+---------+------------------+----+
#
# -- The rank-family contrast, same data as the Spark assertion:
# CREATE TABLE tied_posts (
#     user_id          INT NOT NULL,
#     post_id          INT NOT NULL,
#     engagement_score INT NOT NULL
# );
# INSERT INTO tied_posts VALUES
#     (1, 101, 80), (1, 102, 80), (1, 103, 50), (1, 104, 30);
#
# SELECT post_id, engagement_score,
#        ROW_NUMBER() OVER (PARTITION BY user_id
#                           ORDER BY engagement_score DESC, post_id) AS rn,
#        RANK()       OVER (PARTITION BY user_id ORDER BY engagement_score DESC) AS rnk,
#        DENSE_RANK() OVER (PARTITION BY user_id ORDER BY engagement_score DESC) AS dense_rnk
# FROM tied_posts
# ORDER BY engagement_score DESC, post_id;
#
# -- +---------+------------------+----+-----+-----------+
# -- | post_id | engagement_score | rn | rnk | dense_rnk |
# -- +---------+------------------+----+-----+-----------+
# -- |     101 |               80 |  1 |   1 |         1 |
# -- |     102 |               80 |  2 |   1 |         1 |
# -- |     103 |               50 |  3 |   3 |         2 |
# -- |     104 |               30 |  4 |   4 |         3 |
# -- +---------+------------------+----+-----+-----------+
