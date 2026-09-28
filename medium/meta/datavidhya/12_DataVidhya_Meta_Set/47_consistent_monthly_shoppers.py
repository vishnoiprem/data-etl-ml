"""
Q47: Consistent Monthly Shoppers   [Medium | Aggregate Functions]
DataVidhya slug: consistent-monthly-shoppers

Customers with at least 4 transactions in BOTH 2019 and 2020.

!! SOURCE DATA DEFECT -- READ THIS FIRST !!
DataVidhya's published expected output for this question is `Eve, Alice`, but
`Eve` does not exist: csf_users contains only Alice (101), Bob (102),
Charlie (103) and David (104), and no transaction references any other user.
The expected output is inconsistent with the sample data it ships with.
This file asserts the answer the data actually supports -- `Alice` -- and
proves the per-year counts row by row below so the derivation is checkable.
If you submit against the site's grader, expect a mismatch on their `Eve` row.

How to Think:
- "At least 4 in BOTH years" is a conjunction over two conditional counts, so
  it is one GROUP BY with a two-part HAVING -- not two subqueries intersected:
      HAVING COUNT(CASE WHEN year = 2019 THEN 1 END) >= 4
         AND COUNT(CASE WHEN year = 2020 THEN 1 END) >= 4
- Grain: one row per user. Join to csf_users only for the name.
- created_at is a TIMESTAMP, so bucket by YEAR(created_at).

The trap:
- Filtering `WHERE YEAR(created_at) IN (2019, 2020)` and then testing
  `COUNT(*) >= 8` is WRONG: Charlie-style users can clear 8 with an 8/0 split.
  The threshold is per year, so the counts must stay separate.
- COUNT(CASE WHEN ... THEN 1 END) is correct because COUNT skips NULLs. Using
  SUM(CASE ... ELSE 0 END) also works; COUNT(cond) does NOT -- `false` is not
  NULL, so it counts every row.
- "Transactions may reference deleted accounts" -> INNER JOIN to csf_users, so
  orphan user_ids cannot reach the output.
- The near-misses are planted: Charlie has 4 in 2020 but 0 in 2019; David has 3
  and 3, clearing neither. Both are excluded.
- No ORDER BY is specified, so sort by name for a reproducible result.

Spark note:
- One shuffle for the GROUP BY; csf_users is a small dimension and broadcasts.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("47-consistent-monthly-shoppers")
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


MIN_PER_YEAR = 4

# ---------------------------------------------------------- sample data
# Exactly the rows DataVidhya ships with the question.
# Alice: 4 in 2019 + 4 in 2020 -> qualifies.
# Bob: 1 + 1. Charlie: 0 + 4. David: 3 + 3. All fall short.
spark.sql("""
CREATE OR REPLACE TEMP VIEW csf_users AS
SELECT * FROM VALUES
    (101, 'Alice'), (102, 'Bob'), (103, 'Charlie'), (104, 'David')
AS t(id, name)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW csf_transactions AS
SELECT * FROM VALUES
    ( 1, 101, TIMESTAMP'2019-01-10 10:00:00', 501, 1),
    ( 2, 101, TIMESTAMP'2019-03-15 12:00:00', 502, 2),
    ( 3, 101, TIMESTAMP'2019-05-20 09:30:00', 503, 1),
    ( 4, 101, TIMESTAMP'2019-09-10 14:45:00', 504, 1),
    ( 5, 101, TIMESTAMP'2020-01-05 10:00:00', 505, 1),
    ( 6, 101, TIMESTAMP'2020-04-10 11:30:00', 506, 1),
    ( 7, 101, TIMESTAMP'2020-07-20 15:00:00', 507, 1),
    ( 8, 101, TIMESTAMP'2020-11-25 16:20:00', 508, 1),
    ( 9, 102, TIMESTAMP'2019-02-15 10:00:00', 509, 1),
    (10, 102, TIMESTAMP'2020-02-15 10:00:00', 510, 1),
    (11, 103, TIMESTAMP'2020-03-01 11:00:00', 511, 2),
    (12, 103, TIMESTAMP'2020-05-01 14:00:00', 512, 1),
    (13, 103, TIMESTAMP'2020-07-01 16:00:00', 513, 2),
    (14, 103, TIMESTAMP'2020-08-01 18:00:00', 514, 1),
    (15, 104, TIMESTAMP'2019-06-15 10:00:00', 515, 1),
    (16, 104, TIMESTAMP'2019-07-15 10:00:00', 516, 1),
    (17, 104, TIMESTAMP'2019-08-15 10:00:00', 517, 1),
    (18, 104, TIMESTAMP'2020-06-15 10:00:00', 518, 1),
    (19, 104, TIMESTAMP'2020-07-15 10:00:00', 519, 1),
    (20, 104, TIMESTAMP'2020-08-15 10:00:00', 520, 1)
AS t(id, user_id, created_at, product_id, quantity)
""")

from pyspark.sql import functions as F

SQL = f"""
SELECT u.name AS customer_name
FROM csf_transactions t
JOIN csf_users u ON u.id = t.user_id          -- INNER: drops deleted accounts
GROUP BY u.name
HAVING COUNT(CASE WHEN YEAR(t.created_at) = 2019 THEN 1 END) >= {MIN_PER_YEAR}
   AND COUNT(CASE WHEN YEAR(t.created_at) = 2020 THEN 1 END) >= {MIN_PER_YEAR}
ORDER BY customer_name
"""

spark.sql(SQL).show(truncate=False)

expect("Q47 customers with 4+ transactions in both years", SQL, [("Alice",)])

# DataFrame API equivalent.
y = F.year("created_at")
df = (spark.table("csf_transactions").alias("t")
      .join(F.broadcast(spark.table("csf_users").alias("u")),
            F.col("u.id") == F.col("t.user_id"))
      .groupBy("name")
      .agg(F.count(F.when(y == 2019, 1)).alias("n2019"),
           F.count(F.when(y == 2020, 1)).alias("n2020"))
      .filter((F.col("n2019") >= MIN_PER_YEAR) & (F.col("n2020") >= MIN_PER_YEAR))
      .select(F.col("name").alias("customer_name"))
      .orderBy("customer_name"))
assert [tuple(r) for r in df.collect()] == [("Alice",)]
print("[PASS] Q47 DataFrame API matches SQL")

# ------------------------------------------------ show the derivation
per_year = spark.sql("""
SELECT u.name,
       COUNT(CASE WHEN YEAR(t.created_at) = 2019 THEN 1 END) AS n2019,
       COUNT(CASE WHEN YEAR(t.created_at) = 2020 THEN 1 END) AS n2020
FROM csf_transactions t JOIN csf_users u ON u.id = t.user_id
GROUP BY u.name ORDER BY u.name
""").collect()
counts = [(r[0], r[1], r[2]) for r in per_year]
assert counts == [("Alice", 4, 4), ("Bob", 1, 1), ("Charlie", 0, 4), ("David", 3, 3)], counts
print(f"[PASS] Q47 per-year counts: {counts}")
print("[NOTE] Q47 the site's published output also lists 'Eve', who has no row in "
      "csf_users and no transactions -- that expected output is defective")

# ------------------------------------------------ the combined-threshold trap
# Charlie clears 4 overall but has nothing in 2019, so a >= 8 total test is not
# equivalent -- and an 8/0 split would slip through it entirely.
combined = spark.sql("""
SELECT u.name FROM csf_transactions t JOIN csf_users u ON u.id = t.user_id
WHERE YEAR(t.created_at) IN (2019, 2020)
GROUP BY u.name HAVING COUNT(*) >= 8 ORDER BY u.name
""").collect()
assert [r[0] for r in combined] == ["Alice"], combined

spark.sql("""
CREATE OR REPLACE TEMP VIEW csf_transactions AS
SELECT * FROM VALUES
    (1, 103, TIMESTAMP'2020-01-01 10:00:00', 1, 1),
    (2, 103, TIMESTAMP'2020-02-01 10:00:00', 2, 1),
    (3, 103, TIMESTAMP'2020-03-01 10:00:00', 3, 1),
    (4, 103, TIMESTAMP'2020-04-01 10:00:00', 4, 1),
    (5, 103, TIMESTAMP'2020-05-01 10:00:00', 5, 1),
    (6, 103, TIMESTAMP'2020-06-01 10:00:00', 6, 1),
    (7, 103, TIMESTAMP'2020-07-01 10:00:00', 7, 1),
    (8, 103, TIMESTAMP'2020-08-01 10:00:00', 8, 1)
AS t(id, user_id, created_at, product_id, quantity)
""")
combined_8_0 = spark.sql("""
SELECT u.name FROM csf_transactions t JOIN csf_users u ON u.id = t.user_id
WHERE YEAR(t.created_at) IN (2019, 2020)
GROUP BY u.name HAVING COUNT(*) >= 8
""").collect()
assert [r[0] for r in combined_8_0] == ["Charlie"], combined_8_0
expect("Q47 an 8/0 split must NOT qualify", SQL, [])
print("[PASS] Q47 COUNT(*) >= 8 wrongly admits Charlie's 8-in-2020/0-in-2019 split")

# ------------------------------------------------ the orphan-transaction trap
spark.sql("""
CREATE OR REPLACE TEMP VIEW csf_transactions AS
SELECT * FROM VALUES
    (1, 999, TIMESTAMP'2019-01-01 10:00:00', 1, 1),
    (2, 999, TIMESTAMP'2019-02-01 10:00:00', 2, 1),
    (3, 999, TIMESTAMP'2019-03-01 10:00:00', 3, 1),
    (4, 999, TIMESTAMP'2019-04-01 10:00:00', 4, 1),
    (5, 999, TIMESTAMP'2020-01-01 10:00:00', 5, 1),
    (6, 999, TIMESTAMP'2020-02-01 10:00:00', 6, 1),
    (7, 999, TIMESTAMP'2020-03-01 10:00:00', 7, 1),
    (8, 999, TIMESTAMP'2020-04-01 10:00:00', 8, 1)
AS t(id, user_id, created_at, product_id, quantity)
""")
expect("Q47 deleted account (user 999) qualifies on counts but has no name", SQL, [])
print("[PASS] Q47 INNER JOIN excludes orphan user_ids even when they clear the threshold")

# ------------------------------------------------ COUNT(cond) counts everything
bad, good = spark.sql("""
SELECT COUNT(YEAR(created_at) = 2019)                        AS bad,
       COUNT(CASE WHEN YEAR(created_at) = 2019 THEN 1 END)   AS good
FROM csf_transactions
""").collect()[0]
assert (bad, good) == (8, 4), (bad, good)
print("[PASS] Q47 COUNT(cond) returns 8 (false is not NULL); COUNT(CASE...) returns 4")

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports YEAR() on TIMESTAMP/DATETIME and the same HAVING clause
# with two conditional counts. The same COUNT(CASE WHEN ... THEN 1 END)
# form is needed; COUNT(boolean) would count every row.
#
# CREATE TABLE csf_users (
#     id   INT         NOT NULL,
#     name VARCHAR(64) NOT NULL,
#     PRIMARY KEY (id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE csf_transactions (
#     id          INT       NOT NULL,
#     user_id     INT       NOT NULL,
#     created_at  TIMESTAMP NOT NULL,
#     product_id  INT       NOT NULL,
#     quantity    INT       NOT NULL,
#     PRIMARY KEY (id),
#     KEY ix_csf_user_date (user_id, created_at),
#     CONSTRAINT fk_csf_user FOREIGN KEY (user_id) REFERENCES csf_users(id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO csf_users (id, name) VALUES
#     (101, 'Alice'), (102, 'Bob'), (103, 'Charlie'), (104, 'David');
#
# INSERT INTO csf_transactions (id, user_id, created_at, product_id, quantity) VALUES
#     ( 1, 101, '2019-01-10 10:00:00', 501, 1),
#     ( 2, 101, '2019-03-15 12:00:00', 502, 1),
#     ( 3, 101, '2019-05-20 09:30:00', 503, 1),
#     ( 4, 101, '2019-09-10 14:45:00', 504, 1),
#     ( 5, 101, '2020-01-05 10:00:00', 505, 1),
#     ( 6, 101, '2020-04-10 11:30:00', 506, 1),
#     ( 7, 101, '2020-07-20 15:00:00', 507, 1),
#     ( 8, 101, '2020-11-25 16:20:00', 508, 1),
#     ( 9, 102, '2019-02-15 10:00:00', 509, 1),
#     (10, 102, '2020-02-15 10:00:00', 510, 1),
#     (11, 103, '2020-03-01 11:00:00', 511, 2),
#     (12, 103, '2020-05-01 14:00:00', 512, 1),
#     (13, 103, '2020-07-01 16:00:00', 513, 2),
#     (14, 103, '2020-08-01 18:00:00', 514, 1),
#     (15, 104, '2019-06-15 10:00:00', 515, 1),
#     (16, 104, '2019-07-15 10:00:00', 516, 1),
#     (17, 104, '2019-08-15 10:00:00', 517, 1),
#     (18, 104, '2020-06-15 10:00:00', 518, 1),
#     (19, 104, '2020-07-15 10:00:00', 519, 1),
#     (20, 104, '2020-08-15 10:00:00', 520, 1);
#
# SELECT u.name AS customer_name
# FROM csf_transactions t
# JOIN csf_users u ON u.id = t.user_id
# GROUP BY u.name
# HAVING COUNT(CASE WHEN YEAR(t.created_at) = 2019 THEN 1 END) >= 4
#    AND COUNT(CASE WHEN YEAR(t.created_at) = 2020 THEN 1 END) >= 4
# ORDER BY customer_name;
#
# -- Expected: ('Alice',).
# -- The site's published 'Eve' is a source-data defect: csf_users has no Eve.
