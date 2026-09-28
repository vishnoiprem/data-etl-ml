"""
Q49: Deduplication Across Multiple Columns   [Medium | Window Functions, Deduplication]
DataVidhya slug: deduplication-multi-column

Flag duplicates on (customer_id, merchant, amount, txn_date). Keep the lowest
txn_id as the original. is_duplicate is a 0/1 INT flag. No rows are removed.

How to Think:
- FLAG, do not filter. Every input row appears in the output; only the extra
  column distinguishes originals from copies. Read that carefully -- the
  instinct on a dedup question is to delete, and here deleting is wrong.
- ROW_NUMBER() OVER (PARTITION BY <the business key> ORDER BY txn_id) gives 1
  to the keeper, so `CASE WHEN rn = 1 THEN 0 ELSE 1 END` is the flag.
- Write the partition key out explicitly. It is the ONE thing the interviewer
  is checking, and "the whole row" is the wrong answer.

The trap:
- card_last4 is NOT part of the key, even though it is in the table and looks
  like identity. The same purchase on a different card is still a duplicate.
  `PARTITION BY *` or `dropDuplicates()` with no subset silently includes it and
  then finds nothing. The shipped data has matching cards on T001/T002 so it
  cannot catch this -- asserted separately below.
- ORDER BY txn_id is what makes "keep the first" DETERMINISTIC. Without it the
  keeper is arbitrary, so the same input can produce different output on
  different runs. `dropDuplicates()` has exactly this defect: it is
  non-reproducible, which means a re-run of the pipeline is not idempotent.
- is_duplicate must be INT 0/1, not boolean true/false.
- amount is DECIMAL. Comparing money as FLOAT would make 5.50 and 5.50 unequal
  in the partition key on some paths -- keep it decimal.

Spark note:
- One shuffle on the 4-column key. Prefer ROW_NUMBER over dropDuplicates in any
  retryable pipeline precisely because it is deterministic.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("49-deduplication-multi-column")
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


# The business key. card_last4 is deliberately absent.
DUP_KEY = ["customer_id", "merchant", "amount", "txn_date"]

# ---------------------------------------------------------- sample data
# Exactly the rows DataVidhya ships with the question.
# T001/T002 are the same purchase -> T001 kept (lowest txn_id), T002 flagged.
spark.sql("""
CREATE OR REPLACE TEMP VIEW transactions AS
SELECT * FROM VALUES
    ('T001', 'C101', 'Starbucks', CAST( 5.50 AS DECIMAL(10,2)), DATE'2024-01-15', 4242),
    ('T002', 'C101', 'Starbucks', CAST( 5.50 AS DECIMAL(10,2)), DATE'2024-01-15', 4242),
    ('T003', 'C102', 'Amazon',    CAST(99.99 AS DECIMAL(10,2)), DATE'2024-01-15', 5555),
    ('T004', 'C101', 'Walmart',   CAST(25.00 AS DECIMAL(10,2)), DATE'2024-01-16', 4242),
    ('T005', 'C103', 'Shell Gas', CAST(45.00 AS DECIMAL(10,2)), DATE'2024-01-15', 6666)
AS t(txn_id, customer_id, merchant, amount, txn_date, card_last4)
""")

from pyspark.sql import functions as F, Window as W

SQL = """
SELECT txn_id, customer_id, merchant, amount, txn_date,
       CASE WHEN rn = 1 THEN 0 ELSE 1 END AS is_duplicate
FROM (
    SELECT txn_id, customer_id, merchant, amount, txn_date,
           ROW_NUMBER() OVER (
               PARTITION BY customer_id, merchant, amount, txn_date  -- NOT card_last4
               ORDER BY txn_id                                       -- deterministic keeper
           ) AS rn
    FROM transactions
)
ORDER BY txn_id
"""

spark.sql(SQL).show(truncate=False)

import datetime as dt

D15, D16 = dt.date(2024, 1, 15), dt.date(2024, 1, 16)
EXPECTED = [
    ("T001", "C101", "Starbucks",  5.50, D15, 0),
    ("T002", "C101", "Starbucks",  5.50, D15, 1),
    ("T003", "C102", "Amazon",    99.99, D15, 0),
    ("T004", "C101", "Walmart",   25.00, D16, 0),
    ("T005", "C103", "Shell Gas", 45.00, D15, 0),
]
expect("Q49 duplicate flags", SQL, EXPECTED)

# DataFrame API equivalent.
w = W.partitionBy(*DUP_KEY).orderBy("txn_id")
df = (spark.table("transactions")
      .withColumn("rn", F.row_number().over(w))
      .withColumn("is_duplicate", F.when(F.col("rn") == 1, 0).otherwise(1))
      .select("txn_id", "customer_id", "merchant", "amount", "txn_date", "is_duplicate")
      .orderBy("txn_id"))
assert [(r[0], r[1], r[2], float(r[3]), r[4], r[5]) for r in df.collect()] == EXPECTED
print("[PASS] Q49 DataFrame API matches SQL")

# ------------------------------------------------ no rows removed
assert spark.sql(SQL).count() == spark.table("transactions").count() == 5
print("[PASS] Q49 5 rows in, 5 rows out -- flagged, not filtered")

# ------------------------------------------------ the card_last4 trap
# Same purchase on a DIFFERENT card is still a duplicate.
spark.sql("""
CREATE OR REPLACE TEMP VIEW transactions AS
SELECT * FROM VALUES
    ('T001', 'C101', 'Starbucks', CAST(5.50 AS DECIMAL(10,2)), DATE'2024-01-15', 4242),
    ('T002', 'C101', 'Starbucks', CAST(5.50 AS DECIMAL(10,2)), DATE'2024-01-15', 9999)
AS t(txn_id, customer_id, merchant, amount, txn_date, card_last4)
""")
expect("Q49 different card, same purchase -> still a duplicate", SQL, [
    ("T001", "C101", "Starbucks", 5.50, D15, 0),
    ("T002", "C101", "Starbucks", 5.50, D15, 1),
])

with_card = spark.sql("""
SELECT txn_id, CASE WHEN rn = 1 THEN 0 ELSE 1 END AS is_duplicate
FROM (
    SELECT txn_id, ROW_NUMBER() OVER (
        PARTITION BY customer_id, merchant, amount, txn_date, card_last4
        ORDER BY txn_id) AS rn
    FROM transactions
) ORDER BY txn_id
""").collect()
assert [(r[0], r[1]) for r in with_card] == [("T001", 0), ("T002", 0)], with_card
print("[PASS] Q49 including card_last4 in the key finds zero duplicates")

# ------------------------------------------------ dropDuplicates is non-deterministic
# It also REMOVES rows, so it cannot produce the required flag at all.
deduped = spark.table("transactions").dropDuplicates(DUP_KEY)
assert deduped.count() == 1, deduped.count()
print("[PASS] Q49 dropDuplicates removes a row (1 of 2 left) and cannot flag -- "
      "and picks its survivor non-deterministically")

# ------------------------------------------------ the keeper must be the lowest txn_id
spark.sql("""
CREATE OR REPLACE TEMP VIEW transactions AS
SELECT * FROM VALUES
    ('T009', 'C101', 'Starbucks', CAST(5.50 AS DECIMAL(10,2)), DATE'2024-01-15', 4242),
    ('T003', 'C101', 'Starbucks', CAST(5.50 AS DECIMAL(10,2)), DATE'2024-01-15', 4242),
    ('T007', 'C101', 'Starbucks', CAST(5.50 AS DECIMAL(10,2)), DATE'2024-01-15', 4242)
AS t(txn_id, customer_id, merchant, amount, txn_date, card_last4)
""")
expect("Q49 lowest txn_id is kept regardless of input order", SQL, [
    ("T003", "C101", "Starbucks", 5.50, D15, 0),
    ("T007", "C101", "Starbucks", 5.50, D15, 1),
    ("T009", "C101", "Starbucks", 5.50, D15, 1),
])

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports the same ROW_NUMBER() OVER (PARTITION BY ... ORDER BY
# ...) flag pattern. The four-column business key excludes card_last4.
#
# CREATE TABLE transactions (
#     txn_id      VARCHAR(8)    NOT NULL,
#     customer_id VARCHAR(8)    NOT NULL,
#     merchant    VARCHAR(32)   NOT NULL,
#     amount      DECIMAL(10,2) NOT NULL,
#     txn_date    DATE          NOT NULL,
#     card_last4  INT           NOT NULL,
#     PRIMARY KEY (txn_id),
#     KEY ix_txn_business_key (customer_id, merchant, amount, txn_date)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO transactions (txn_id, customer_id, merchant, amount, txn_date, card_last4) VALUES
#     ('T001', 'C101', 'Starbucks',  5.50, '2024-01-15', 4242),
#     ('T002', 'C101', 'Starbucks',  5.50, '2024-01-15', 4242),
#     ('T003', 'C102', 'Amazon',    99.99, '2024-01-15', 5555),
#     ('T004', 'C101', 'Walmart',   25.00, '2024-01-16', 4242),
#     ('T005', 'C103', 'Shell Gas', 45.00, '2024-01-15', 6666);
#
# SELECT txn_id, customer_id, merchant, amount, txn_date,
#        CASE WHEN rn = 1 THEN 0 ELSE 1 END AS is_duplicate
# FROM (
#     SELECT txn_id, customer_id, merchant, amount, txn_date,
#            ROW_NUMBER() OVER (
#                PARTITION BY customer_id, merchant, amount, txn_date
#                ORDER BY txn_id
#            ) AS rn
#     FROM transactions
# ) t
# ORDER BY txn_id;
#
# -- Expected:
# -- T001 C101 Starbucks  5.50 2024-01-15 0
# -- T002 C101 Starbucks  5.50 2024-01-15 1
# -- T003 C102 Amazon    99.99 2024-01-15 0
# -- T004 C101 Walmart   25.00 2024-01-16 0
# -- T005 C103 Shell Gas 45.00 2024-01-15 0
