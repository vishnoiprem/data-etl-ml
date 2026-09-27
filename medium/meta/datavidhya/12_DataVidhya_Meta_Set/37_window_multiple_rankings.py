"""
Q37: Window Function Optimization   [Hard | Window Functions]
DataVidhya slug: window-function-multiple-rankings

Return every event unchanged plus three window columns:
  user_rank      RANK over the user's events by amount DESC   (ties share, gaps)
  category_rank  DENSE_RANK over the category by amount DESC  (ties share, no gaps)
  running_total  cumulative amount per user in event_date order

How to Think:
- The verbal spec tells you exactly which function to use; the skill is
  translating the phrasing, not inventing logic:
    "equal values share a rank and the next rank is SKIPPED (1,1,3)" -> RANK()
    "equal values share a rank with NO gaps (1,1,2)"                 -> DENSE_RANK()
    "cumulative, up to and including the current row"                -> SUM() OVER
      (... ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
- Three windows, three DIFFERENT specs. Two partition by user_id but with
  different ORDER BY (amount vs event_date), and the third partitions by
  category. Only identical window specs get collapsed into one shuffle, so
  write all three out plainly -- nesting them in CTEs buys nothing.
- No row is filtered or aggregated. The output cardinality equals the input
  cardinality; if it does not, a window became a GROUP BY.

The trap:
- RANK vs DENSE_RANK is the entire question and the sample data is built to
  catch it. Category `electronics` has TWO events at 250 (E002, E012). Both get
  category_rank 3, and the next value (180, E009) gets 4 -- no gap. RANK() would
  give it 5 and fail. Meanwhile user_rank is RANK, and no user has a tie, so it
  coincidentally equals DENSE_RANK there -- the user column will NOT reveal the
  mistake. Only the category column does.
- ROW_NUMBER() looks right on this data for user_rank (no ties) but is wrong by
  spec: it breaks ties arbitrarily instead of sharing them, so it is
  non-deterministic the moment a user has two equal amounts.
- running_total is ordered by event_date, NOT by amount. Reusing the
  amount-ordered window gives a cumulative-by-size total, which is meaningless
  and is the second most common failure.
- The default window frame with an ORDER BY is RANGE UNBOUNDED PRECEDING, which
  aggregates over PEER rows (all rows with the same date) rather than row by
  row. It agrees here because each user's dates are unique -- state ROWS
  explicitly so duplicate dates do not silently change the answer.
- Final ORDER BY is event_id, which is a VARCHAR ('E001'..'E020'). Zero-padding
  makes string order match numeric order here; unpadded ids would not.

Spark note:
- Three window specs = three shuffles. The two user_id windows share a partition
  key, so Spark reuses the exchange and only re-sorts. Partitioning the source
  by user_id would remove the shuffle for both.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("37-window-multiple-rankings")
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
# E002 and E012 both sit at 250 in `electronics` -- that tie is the test.
spark.sql("""
CREATE OR REPLACE TEMP VIEW events AS
SELECT * FROM VALUES
    ('E001', 'U001', DATE'2024-01-05', 100, 'electronics'),
    ('E002', 'U001', DATE'2024-01-10', 250, 'electronics'),
    ('E003', 'U001', DATE'2024-01-15', 150, 'clothing'),
    ('E004', 'U002', DATE'2024-01-08', 200, 'clothing'),
    ('E005', 'U002', DATE'2024-01-12',  80, 'electronics'),
    ('E006', 'U002', DATE'2024-01-20', 300, 'home'),
    ('E007', 'U003', DATE'2024-01-05', 120, 'home'),
    ('E008', 'U003', DATE'2024-01-10',  90, 'clothing'),
    ('E009', 'U003', DATE'2024-01-18', 180, 'electronics'),
    ('E010', 'U001', DATE'2024-02-05', 220, 'home'),
    ('E011', 'U002', DATE'2024-02-08', 110, 'clothing'),
    ('E012', 'U003', DATE'2024-02-15', 250, 'electronics'),
    ('E013', 'U001', DATE'2024-02-20', 160, 'clothing'),
    ('E014', 'U002', DATE'2024-02-25', 270, 'electronics'),
    ('E015', 'U003', DATE'2024-02-28', 140, 'home'),
    ('E016', 'U001', DATE'2024-03-10', 300, 'electronics'),
    ('E017', 'U002', DATE'2024-03-12', 190, 'home'),
    ('E018', 'U003', DATE'2024-03-15', 100, 'clothing'),
    ('E019', 'U001', DATE'2024-03-20', 170, 'home'),
    ('E020', 'U002', DATE'2024-03-25', 240, 'clothing')
AS t(event_id, user_id, event_date, amount, category)
""")

from pyspark.sql import functions as F, Window as W

SQL = """
SELECT event_id,
       user_id,
       category,
       amount,
       event_date,
       RANK()       OVER (PARTITION BY user_id  ORDER BY amount DESC) AS user_rank,
       DENSE_RANK() OVER (PARTITION BY category ORDER BY amount DESC) AS category_rank,
       SUM(amount)  OVER (PARTITION BY user_id  ORDER BY event_date
                          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM events
ORDER BY event_id
"""

spark.sql(SQL).show(25, truncate=False)

import datetime as dt


def d(month, day):
    return dt.date(2024, month, day)


EXPECTED = [
    ("E001", "U001", "electronics", 100, d(1, 5),  7, 5, 100),
    ("E002", "U001", "electronics", 250, d(1, 10), 2, 3, 350),
    ("E003", "U001", "clothing",    150, d(1, 15), 6, 4, 500),
    ("E004", "U002", "clothing",    200, d(1, 8),  4, 2, 200),
    ("E005", "U002", "electronics",  80, d(1, 12), 7, 6, 280),
    ("E006", "U002", "home",        300, d(1, 20), 1, 1, 580),
    ("E007", "U003", "home",        120, d(1, 5),  4, 6, 120),
    ("E008", "U003", "clothing",     90, d(1, 10), 6, 7, 210),
    ("E009", "U003", "electronics", 180, d(1, 18), 2, 4, 390),
    ("E010", "U001", "home",        220, d(2, 5),  3, 2, 720),
    ("E011", "U002", "clothing",    110, d(2, 8),  6, 5, 690),
    ("E012", "U003", "electronics", 250, d(2, 15), 1, 3, 640),
    ("E013", "U001", "clothing",    160, d(2, 20), 5, 3, 880),
    ("E014", "U002", "electronics", 270, d(2, 25), 2, 2, 960),
    ("E015", "U003", "home",        140, d(2, 28), 3, 5, 780),
    ("E016", "U001", "electronics", 300, d(3, 10), 1, 1, 1180),
    ("E017", "U002", "home",        190, d(3, 12), 5, 3, 1150),
    ("E018", "U003", "clothing",    100, d(3, 15), 5, 6, 880),
    ("E019", "U001", "home",        170, d(3, 20), 4, 4, 1350),
    ("E020", "U002", "clothing",    240, d(3, 25), 3, 1, 1390),
]

expect("Q37 three window columns", SQL, EXPECTED)

# DataFrame API equivalent -- three distinct window specs.
w_user_amt = W.partitionBy("user_id").orderBy(F.col("amount").desc())
w_cat_amt = W.partitionBy("category").orderBy(F.col("amount").desc())
w_user_date = (W.partitionBy("user_id").orderBy("event_date")
               .rowsBetween(W.unboundedPreceding, W.currentRow))

df = (spark.table("events")
      .select("event_id", "user_id", "category", "amount", "event_date",
              F.rank().over(w_user_amt).alias("user_rank"),
              F.dense_rank().over(w_cat_amt).alias("category_rank"),
              F.sum("amount").over(w_user_date).alias("running_total"))
      .orderBy("event_id"))
assert [tuple(r) for r in df.collect()] == EXPECTED
print("[PASS] Q37 DataFrame API matches SQL")

# ------------------------------------------------ no rows lost
assert spark.sql(SQL).count() == spark.table("events").count() == 20
print("[PASS] Q37 20 rows in, 20 rows out -- windows, not aggregates")

# ------------------------------------------------ the RANK vs DENSE_RANK trap
# electronics: 300, 270, 250, 250, 180, 100, 80.
# DENSE_RANK gives 180 -> 4 (correct). RANK gives 180 -> 5 (wrong).
ranks = spark.sql("""
SELECT event_id, amount,
       RANK()       OVER (PARTITION BY category ORDER BY amount DESC) AS with_rank,
       DENSE_RANK() OVER (PARTITION BY category ORDER BY amount DESC) AS with_dense
FROM events
WHERE category = 'electronics'
ORDER BY amount DESC, event_id
""").collect()
tied = [(r.event_id, r.with_rank, r.with_dense) for r in ranks if r.amount in (250, 180)]
assert tied == [("E002", 3, 3), ("E012", 3, 3), ("E009", 5, 4)], tied
print("[PASS] Q37 after the 250 tie, RANK jumps to 5 and DENSE_RANK gives 4 -- spec wants 4")

# ------------------------------------------------ the running_total ordering trap
# Ordering the cumulative sum by amount instead of event_date changes E001's
# total from 100 to U001's full 1350 (100 is that user's smallest amount).
by_amount = spark.sql("""
SELECT running_total FROM (
    SELECT event_id,
           SUM(amount) OVER (PARTITION BY user_id ORDER BY amount DESC
                             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
    FROM events
) WHERE event_id = 'E001'
""").collect()[0][0]
assert by_amount == 1350, by_amount
print("[PASS] Q37 ordering running_total by amount gives E001 = 1350, not 100")
