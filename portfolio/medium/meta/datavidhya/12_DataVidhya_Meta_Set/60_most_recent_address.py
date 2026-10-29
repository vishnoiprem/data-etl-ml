"""
Q60: Most Recent Record per Group   [Medium | Window Functions, Deduplication]
DataVidhya slug: most-recent-address

Per user, return the single address with the latest updated_at.

How to Think:
- Latest-row-per-group, the most common pattern in this whole set. Rank by
  `updated_at DESC` inside the user partition and keep rank 1.
- ROW_NUMBER is the right choice here BECAUSE the spec says "if two share the
  latest date, return either one (be consistent)". ROW_NUMBER guarantees exactly
  one row; RANK would return both and violate "exactly one row per user".
  That is the opposite of Q56, where the spec demanded all ties -- read which
  one the question wants.
- "Be consistent" is the operative phrase: add a deterministic tiebreak
  (address_id) so repeated runs return the same row. Without it the answer is
  reproducible only by luck.

The trap:
- `MAX(updated_at)` GROUP BY user_id gives the DATE but not the street/city --
  you need the whole row, so it is a ranking problem, not an aggregate one.
  Joining back on (user_id, max_date) works but re-reads the table and still
  returns two rows on a tie.
- Users are NOT contiguous (1, 3, 7) and user 3's latest is the MIDDLE row by
  address_id (id 6, 2024-04-01) -- not the highest id and not the last inserted.
  Any solution that assumes "latest id = latest address" gets user 3 wrong.
- `ORDER BY updated_at` without DESC returns each user's OLDEST address, which
  still yields exactly 3 well-formed rows.

Spark note:
- One shuffle on user_id. This is also the canonical SCD-Type-1 "current
  snapshot" query -- worth naming, since it is how you collapse a change log
  into a dimension.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("60-most-recent-address")
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
# User 3's newest address is id 6 -- the MIDDLE of its three rows by id.
spark.sql("""
CREATE OR REPLACE TEMP VIEW user_addresses AS
SELECT * FROM VALUES
    ( 1, 1, '123 Main St',   'New York', 'NY', DATE'2024-01-15'),
    ( 2, 1, '456 Oak Ave',   'Boston',   'MA', DATE'2024-03-20'),
    ( 5, 3, '654 Maple Dr',  'Denver',   'CO', DATE'2024-02-28'),
    ( 6, 3, '987 Cedar Ln',  'Austin',   'TX', DATE'2024-04-01'),
    ( 7, 3, '111 Birch Way', 'Portland', 'OR', DATE'2024-03-15'),
    (13, 7, '777 Elm Ave',   'Dallas',   'TX', DATE'2024-01-30'),
    (14, 7, '888 Pine St',   'Houston',  'TX', DATE'2024-03-05')
AS t(address_id, user_id, street, city, state, updated_at)
""")

from pyspark.sql import functions as F, Window as W

# ROW_NUMBER guarantees exactly one row; address_id makes ties reproducible.
SQL = """
SELECT user_id, street, city, state, updated_at
FROM (
    SELECT user_id, street, city, state, updated_at,
           ROW_NUMBER() OVER (PARTITION BY user_id
                              ORDER BY updated_at DESC, address_id DESC) AS rn
    FROM user_addresses
)
WHERE rn = 1
ORDER BY user_id
"""

spark.sql(SQL).show(truncate=False)

import datetime as dt

EXPECTED = [
    (1, "456 Oak Ave",  "Boston",  "MA", dt.date(2024, 3, 20)),
    (3, "987 Cedar Ln", "Austin",  "TX", dt.date(2024, 4, 1)),
    (7, "888 Pine St",  "Houston", "TX", dt.date(2024, 3, 5)),
]
expect("Q60 most recent address per user", SQL, EXPECTED)

# DataFrame API equivalent.
w = W.partitionBy("user_id").orderBy(F.col("updated_at").desc(),
                                     F.col("address_id").desc())
df = (spark.table("user_addresses")
      .withColumn("rn", F.row_number().over(w))
      .filter(F.col("rn") == 1)
      .select("user_id", "street", "city", "state", "updated_at")
      .orderBy("user_id"))
assert [tuple(r) for r in df.collect()] == EXPECTED
print("[PASS] Q60 DataFrame API matches SQL")

# ------------------------------------------------ latest id is not latest address
by_max_id = spark.sql("""
SELECT street FROM user_addresses
WHERE user_id = 3 AND address_id = (SELECT MAX(address_id) FROM user_addresses WHERE user_id = 3)
""").collect()[0][0]
assert by_max_id == "111 Birch Way", by_max_id
print("[PASS] Q60 user 3's highest address_id (7) is '111 Birch Way' -- "
      "the correct answer is '987 Cedar Ln' (id 6)")

# ------------------------------------------------ MAX() gives the date, not the row
max_dates = spark.sql("""
SELECT user_id, MAX(updated_at) AS latest FROM user_addresses GROUP BY user_id ORDER BY user_id
""").collect()
assert [(r[0], r[1]) for r in max_dates] == [
    (1, dt.date(2024, 3, 20)), (3, dt.date(2024, 4, 1)), (7, dt.date(2024, 3, 5)),
], max_dates
print("[PASS] Q60 MAX(updated_at) yields the dates but carries no street/city")

# ------------------------------------------------ ascending order gives the oldest
oldest = spark.sql("""
SELECT user_id, street FROM (
    SELECT user_id, street,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY updated_at) AS rn
    FROM user_addresses
) WHERE rn = 1 ORDER BY user_id
""").collect()
assert [(r[0], r[1]) for r in oldest] == [
    (1, "123 Main St"), (3, "654 Maple Dr"), (7, "777 Elm Ave"),
], oldest
print("[PASS] Q60 forgetting DESC returns each user's OLDEST address -- still 3 tidy rows")

# ------------------------------------------------ exactly one row per user on a tie
# Two addresses share user 9's latest date. ROW_NUMBER returns one (the higher
# address_id, deterministically); RANK would return both and break the contract.
spark.sql("""
CREATE OR REPLACE TEMP VIEW user_addresses AS
SELECT * FROM VALUES
    (20, 9, 'A St', 'Austin', 'TX', DATE'2024-05-01'),
    (21, 9, 'B St', 'Boston', 'MA', DATE'2024-05-01')
AS t(address_id, user_id, street, city, state, updated_at)
""")
expect("Q60 tie yields exactly one row, chosen deterministically", SQL, [
    (9, "B St", "Boston", "MA", dt.date(2024, 5, 1)),
])

tied_rank = spark.sql("""
SELECT COUNT(*) FROM (
    SELECT RANK() OVER (PARTITION BY user_id ORDER BY updated_at DESC) AS rnk
    FROM user_addresses
) WHERE rnk = 1
""").collect()[0][0]
assert tied_rank == 2, tied_rank
print("[PASS] Q60 RANK returns 2 rows for user 9 -- violates 'exactly one row per user'")

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...) and
# RANK() with the same semantics as Spark. The two-column ORDER BY (date
# DESC, id DESC) makes ties deterministic.
#
# CREATE TABLE user_addresses (
#     address_id  INT          NOT NULL,
#     user_id     INT          NOT NULL,
#     street      VARCHAR(128) NOT NULL,
#     city        VARCHAR(64)  NOT NULL,
#     state       CHAR(2)      NOT NULL,
#     updated_at  DATE         NOT NULL,
#     PRIMARY KEY (address_id),
#     KEY ix_ua_user_date (user_id, updated_at DESC, address_id DESC)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO user_addresses (address_id, user_id, street, city, state, updated_at) VALUES
#     ( 1, 1, '123 Main St',   'New York', 'NY', '2024-01-15'),
#     ( 2, 1, '456 Oak Ave',   'Boston',   'MA', '2024-03-20'),
#     ( 5, 3, '654 Maple Dr',  'Denver',   'CO', '2024-02-28'),
#     ( 6, 3, '987 Cedar Ln',  'Austin',   'TX', '2024-04-01'),
#     ( 7, 3, '111 Birch Way', 'Portland', 'OR', '2024-03-15'),
#     (13, 7, '777 Elm Ave',   'Dallas',   'TX', '2024-01-30'),
#     (14, 7, '888 Pine St',   'Houston',  'TX', '2024-03-05');
#
# SELECT user_id, street, city, state, updated_at
# FROM (
#     SELECT user_id, street, city, state, updated_at,
#            ROW_NUMBER() OVER (PARTITION BY user_id
#                               ORDER BY updated_at DESC, address_id DESC) AS rn
#     FROM user_addresses
# ) t
# WHERE rn = 1
# ORDER BY user_id;
#
# -- Expected:
# -- (1, '456 Oak Ave',  'Boston',  'MA', '2024-03-20')
# -- (3, '987 Cedar Ln', 'Austin',  'TX', '2024-04-01')
# -- (7, '888 Pine St',  'Houston', 'TX', '2024-03-05')
