"""
Q57: Merge Multiple DataFrames   [Medium | Inner Joins, Aggregate Functions, Merges]
DataVidhya slug: merge-multiple-dataframes

One row per user in `users` (keep every user) with total_orders, total_amount,
avg_rating, review_count. Missing aggregates are 0 -- INCLUDING avg_rating.

How to Think:
- AGGREGATE EACH FACT TABLE FIRST, then LEFT JOIN both summaries onto `users`.
  This is the same shape as Q55, and the same reason: two independent fact
  tables joined raw multiply each other.
- `users` drives the join, because "keep every user" is the requirement. Users
  3 and 5 have no reviews; user 4 has no orders. All five must appear.
- Grain, out loud: "one row per user in `users`."

The trap:
- THE FAN-OUT. User 1 has 2 orders AND 2 reviews. Joined raw, that is 2 x 2 = 4
  rows, so total_orders becomes 4 and total_amount becomes 388.54 -- exactly
  double. The correct values are 2 and 194.27. This is the question, and the
  sample data is built so only user 1 exposes it.
- avg_rating must be 0 for a user with no reviews, NOT NULL. That is
  statistically wrong (an average of nothing is undefined, not zero) but it is
  what the spec demands -- say so aloud and then implement the spec.
- COALESCE must wrap the aggregate AFTER rounding, and must be applied to all
  four columns. Missing it on one is the usual partial fix.
- A NULL rating: AVG skips NULLs but COUNT(*) counts the row, so avg_rating and
  review_count are computed over DIFFERENT denominators. Use COUNT(*) for
  review_count, not COUNT(rating).
- `total_amount` is DECIMAL money -- round to 2dp, and 194.27 must not come back
  as 194.26999999.

Spark note:
- Two small pre-aggregations then broadcast left joins. On real data this also
  avoids shuffling the wide fact tables against each other at all.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("57-merge-multiple-dataframes")
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


# ---------------------------------------------------------- sample data
# Exactly the rows DataVidhya ships with the question.
# User 1 has 2 orders AND 2 reviews -- the only row that exposes the fan-out.
# User 3 and 5: orders, no reviews. User 4: a review, no orders.
spark.sql("""
CREATE OR REPLACE TEMP VIEW orders AS
SELECT * FROM VALUES
    (1, 1, CAST( 66.38 AS DECIMAL(12,2)), DATE'2024-01-01'),
    (4, 1, CAST(127.89 AS DECIMAL(12,2)), DATE'2024-01-04'),
    (2, 2, CAST(308.44 AS DECIMAL(12,2)), DATE'2024-01-02'),
    (3, 3, CAST( 75.36 AS DECIMAL(12,2)), DATE'2024-01-03'),
    (6, 5, CAST(430.98 AS DECIMAL(12,2)), DATE'2024-01-06')
AS t(order_id, user_id, amount, order_date)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW reviews AS
SELECT * FROM VALUES
    (1, 1, 5, DATE'2024-01-10'),
    (3, 1, 4, DATE'2024-01-12'),
    (2, 2, 4, DATE'2024-01-11'),
    (4, 4, 3, DATE'2024-01-14')
AS t(review_id, user_id, rating, review_date)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW users AS
SELECT * FROM VALUES
    (1, 'User_1', DATE'2023-01-31'),
    (2, 'User_2', DATE'2023-02-28'),
    (3, 'User_3', DATE'2023-03-31'),
    (4, 'User_4', DATE'2023-04-30'),
    (5, 'User_5', DATE'2023-05-31')
AS t(user_id, name, join_date)
""")

from pyspark.sql import functions as F

SQL = """
WITH order_summary AS (
    SELECT user_id,
           COUNT(*)    AS total_orders,
           SUM(amount) AS total_amount
    FROM orders GROUP BY user_id
),
review_summary AS (
    SELECT user_id,
           AVG(rating) AS avg_rating,      -- skips NULL ratings
           COUNT(*)    AS review_count     -- counts every review row
    FROM reviews GROUP BY user_id
)
SELECT u.user_id,
       u.name,
       COALESCE(o.total_orders, 0)            AS total_orders,
       COALESCE(ROUND(o.total_amount, 2), 0)  AS total_amount,
       COALESCE(ROUND(r.avg_rating, 2), 0)    AS avg_rating,
       COALESCE(r.review_count, 0)            AS review_count
FROM users u
LEFT JOIN order_summary  o ON o.user_id = u.user_id
LEFT JOIN review_summary r ON r.user_id = u.user_id
ORDER BY u.user_id
"""

spark.sql(SQL).show(truncate=False)

EXPECTED = [
    (1, "User_1", 2, 194.27, 4.50, 2),
    (2, "User_2", 1, 308.44, 4.00, 1),
    (3, "User_3", 1,  75.36, 0.00, 0),
    (4, "User_4", 0,   0.00, 3.00, 1),
    (5, "User_5", 1, 430.98, 0.00, 0),
]
expect("Q57 per-user commerce summary", SQL, EXPECTED)

# DataFrame API equivalent.
order_summary = (spark.table("orders").groupBy("user_id")
                 .agg(F.count(F.lit(1)).alias("total_orders"),
                      F.sum("amount").alias("total_amount")))
review_summary = (spark.table("reviews").groupBy("user_id")
                  .agg(F.avg("rating").alias("avg_rating"),
                       F.count(F.lit(1)).alias("review_count")))
df = (spark.table("users")
      .join(F.broadcast(order_summary), "user_id", "left")
      .join(F.broadcast(review_summary), "user_id", "left")
      .select("user_id", "name",
              F.coalesce("total_orders", F.lit(0)).alias("total_orders"),
              F.coalesce(F.round("total_amount", 2), F.lit(0)).alias("total_amount"),
              F.coalesce(F.round("avg_rating", 2), F.lit(0)).alias("avg_rating"),
              F.coalesce("review_count", F.lit(0)).alias("review_count"))
      .orderBy("user_id"))
assert [(r[0], r[1], r[2], float(r[3]), float(r[4]), r[5]) for r in df.collect()] == EXPECTED
print("[PASS] Q57 DataFrame API matches SQL")

# ------------------------------------------------ the fan-out trap
fanned = spark.sql("""
SELECT u.user_id,
       COUNT(o.order_id) AS total_orders,
       ROUND(SUM(o.amount), 2) AS total_amount
FROM users u
LEFT JOIN orders  o ON o.user_id = u.user_id
LEFT JOIN reviews r ON r.user_id = u.user_id
GROUP BY u.user_id ORDER BY u.user_id
""").collect()
user1 = [r for r in fanned if r[0] == 1][0]
assert (user1[1], float(user1[2])) == (4, 388.54), user1
print("[PASS] Q57 joining orders and reviews raw doubles user 1 to 4 orders / 388.54")

# ------------------------------------------------ 0 not NULL
u3 = [r for r in spark.sql(SQL).collect() if r[0] == 3][0]
assert float(u3[4]) == 0.0 and u3[4] is not None, u3
print("[PASS] Q57 user 3 has no reviews -> avg_rating is 0, not NULL")

no_coalesce = spark.sql("""
WITH rs AS (SELECT user_id, AVG(rating) AS avg_rating FROM reviews GROUP BY user_id)
SELECT u.user_id, ROUND(r.avg_rating, 2) AS avg_rating
FROM users u LEFT JOIN rs r ON r.user_id = u.user_id
WHERE u.user_id = 3
""").collect()[0][1]
assert no_coalesce is None
print("[PASS] Q57 without COALESCE, user 3's avg_rating comes back NULL")

# ------------------------------------------------ every user survives
assert spark.sql(SQL).count() == spark.table("users").count() == 5
print("[PASS] Q57 all 5 users returned, including those with no orders or no reviews")

# ------------------------------------------------ the NULL-rating trap
# review_count counts rows; avg_rating averages only non-NULL ratings.
spark.sql("""
CREATE OR REPLACE TEMP VIEW reviews AS
SELECT * FROM VALUES
    (1, 1, 5,                    DATE'2024-01-10'),
    (3, 1, 4,                    DATE'2024-01-12'),
    (5, 1, CAST(NULL AS INT),    DATE'2024-01-13'),
    (2, 2, 4,                    DATE'2024-01-11'),
    (4, 4, 3,                    DATE'2024-01-14')
AS t(review_id, user_id, rating, review_date)
""")
got = expect("Q57 NULL rating: counted in review_count, skipped by avg_rating", SQL, [
    (1, "User_1", 2, 194.27, 4.50, 3),   # avg still 4.5, count now 3
    (2, "User_2", 1, 308.44, 4.00, 1),
    (3, "User_3", 1,  75.36, 0.00, 0),
    (4, "User_4", 0,   0.00, 3.00, 1),
    (5, "User_5", 1, 430.98, 0.00, 0),
])
assert got[0][4] == 4.5 and got[0][5] == 3, got[0]

count_rating = spark.sql("""
SELECT COUNT(*) AS all_rows, COUNT(rating) AS non_null FROM reviews WHERE user_id = 1
""").collect()[0]
assert (count_rating[0], count_rating[1]) == (3, 2), count_rating
print("[PASS] Q57 COUNT(*) = 3 but COUNT(rating) = 2 -- review_count must use COUNT(*)")

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports the same two-CTE pre-aggregation + LEFT JOIN shape.
# The same AVG/COUNT semantics apply: AVG skips NULL ratings, COUNT(*)
# counts every row.
#
# CREATE TABLE users (
#     user_id    INT          NOT NULL,
#     name       VARCHAR(64)  NOT NULL,
#     join_date  DATE         NOT NULL,
#     PRIMARY KEY (user_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE orders (
#     order_id   INT            NOT NULL,
#     user_id    INT            NOT NULL,
#     amount     DECIMAL(12,2)  NOT NULL,
#     order_date DATE           NOT NULL,
#     PRIMARY KEY (order_id),
#     KEY ix_orders_user (user_id),
#     CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(user_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE reviews (
#     review_id   INT          NOT NULL,
#     user_id     INT          NOT NULL,
#     rating      TINYINT      NULL,             -- ratings are 1..5
#     review_date DATE         NOT NULL,
#     PRIMARY KEY (review_id),
#     KEY ix_reviews_user (user_id),
#     CONSTRAINT fk_reviews_user FOREIGN KEY (user_id) REFERENCES users(user_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO users (user_id, name, join_date) VALUES
#     (1,'User_1','2023-01-31'),(2,'User_2','2023-02-28'),
#     (3,'User_3','2023-03-31'),(4,'User_4','2023-04-30'),
#     (5,'User_5','2023-05-31');
#
# INSERT INTO orders (order_id, user_id, amount, order_date) VALUES
#     (1,1,  66.38,'2024-01-01'),(4,1,127.89,'2024-01-04'),
#     (2,2,308.44,'2024-01-02'),(3,3, 75.36,'2024-01-03'),
#     (6,5,430.98,'2024-01-06');
#
# INSERT INTO reviews (review_id, user_id, rating, review_date) VALUES
#     (1,1,5,'2024-01-10'),(3,1,4,'2024-01-12'),
#     (2,2,4,'2024-01-11'),(4,4,3,'2024-01-14');
#
# WITH order_summary AS (
#     SELECT user_id,
#            COUNT(*)    AS total_orders,
#            SUM(amount) AS total_amount
#     FROM orders GROUP BY user_id
# ),
# review_summary AS (
#     SELECT user_id,
#            AVG(rating) AS avg_rating,
#            COUNT(*)    AS review_count
#     FROM reviews GROUP BY user_id
# )
# SELECT u.user_id,
#        u.name,
#        COALESCE(o.total_orders, 0)           AS total_orders,
#        COALESCE(ROUND(o.total_amount, 2), 0) AS total_amount,
#        COALESCE(ROUND(r.avg_rating, 2), 0)   AS avg_rating,
#        COALESCE(r.review_count, 0)           AS review_count
# FROM users u
# LEFT JOIN order_summary  o ON o.user_id = u.user_id
# LEFT JOIN review_summary r ON r.user_id = u.user_id
# ORDER BY u.user_id;
#
# -- Expected:
# -- (1,'User_1', 2, 194.27, 4.50, 2)
# -- (2,'User_2', 1, 308.44, 4.00, 1)
# -- (3,'User_3', 1,  75.36, 0.00, 0)
# -- (4,'User_4', 0,   0.00, 3.00, 1)
# -- (5,'User_5', 1, 430.98, 0.00, 0)
