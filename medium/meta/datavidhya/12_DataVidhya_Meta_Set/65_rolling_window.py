"""
Q65: Rolling Window Calculations   [Medium | Window Functions, Time Series Analysis]
DataVidhya slug: rolling-window

Per ticker and trade_date: rolling average, max and min of close_price over the
current ROW and the two previous ROWS. The first two rows of each ticker use
whatever rows exist.

How to Think:
- Three aggregates, one window spec: `PARTITION BY ticker ORDER BY trade_date
  ROWS BETWEEN 2 PRECEDING AND CURRENT ROW`. Write the frame once, reuse it.
- Read the frame width carefully: a "3-row window" is 2 PRECEDING + CURRENT, not
  3 PRECEDING. Off-by-one here is the most common error and it looks plausible.
- The partial-window behaviour at the start is FREE. A window frame silently
  clamps to available rows, so row 1 averages 1 value and row 2 averages 2. No
  special-casing, no COALESCE -- which is exactly why the spec bothers to
  mention it.

The trap:
- ROWS vs RANGE, and here the spec explicitly wants ROWS: "gaps in calendar
  dates do not add empty days." Contrast Q33, where the spec wanted a 7-DAY
  window and ROWS was wrong. Same-looking question, opposite answer -- the
  wording decides. With a calendar gap the two diverge; asserted below.
- The DEFAULT frame is also wrong. `AVG(x) OVER (PARTITION BY ... ORDER BY ...)`
  with no frame clause means RANGE UNBOUNDED PRECEDING -- a cumulative average
  over all prior rows, not a rolling 3. Always state the frame.
- Round only the AVG to 2dp. max/min are existing data points and must come
  back at their original scale.
- Only avg needs rounding, but all three need the same frame -- a mismatched
  frame on one of the three is a subtle and very common bug.

Spark note:
- One exchange on ticker, one sort on trade_date, and all three aggregates
  compute in a single window operator.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("65-rolling-window")
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


WINDOW_ROWS = 3   # current row + 2 preceding

# ---------------------------------------------------------- sample data
# Exactly the rows DataVidhya ships with the question.
spark.sql("""
CREATE OR REPLACE TEMP VIEW daily_stock AS
SELECT * FROM VALUES
    (DATE'2024-01-01', 'AAPL', CAST(106.71 AS DECIMAL(10,2)), 3361366),
    (DATE'2024-01-02', 'AAPL', CAST(126.55 AS DECIMAL(10,2)), 1307277),
    (DATE'2024-01-03', 'AAPL', CAST(128.06 AS DECIMAL(10,2)), 3121834),
    (DATE'2024-01-04', 'AAPL', CAST(118.67 AS DECIMAL(10,2)), 4914373),
    (DATE'2024-01-05', 'AAPL', CAST(112.63 AS DECIMAL(10,2)), 1288531)
AS t(trade_date, ticker, close_price, volume)
""")

from pyspark.sql import functions as F, Window as W

# ROWS (not RANGE): calendar gaps must not insert empty days.
SQL = """
SELECT trade_date,
       ticker,
       close_price,
       ROUND(AVG(close_price) OVER w, 2) AS rolling_3day_avg,
       MAX(close_price) OVER w           AS rolling_3day_max,
       MIN(close_price) OVER w           AS rolling_3day_min
FROM daily_stock
WINDOW w AS (PARTITION BY ticker ORDER BY trade_date
             ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
ORDER BY ticker, trade_date
"""

spark.sql(SQL).show(truncate=False)

import datetime as dt


def d(day):
    return dt.date(2024, 1, day)


EXPECTED = [
    (d(1), "AAPL", 106.71, 106.71, 106.71, 106.71),
    (d(2), "AAPL", 126.55, 116.63, 126.55, 106.71),
    (d(3), "AAPL", 128.06, 120.44, 128.06, 106.71),
    (d(4), "AAPL", 118.67, 124.43, 128.06, 118.67),
    (d(5), "AAPL", 112.63, 119.79, 128.06, 112.63),
]
expect("Q65 rolling 3-row stats", SQL, EXPECTED)

# DataFrame API equivalent -- one frame, three aggregates.
w = (W.partitionBy("ticker").orderBy("trade_date")
     .rowsBetween(-(WINDOW_ROWS - 1), W.currentRow))
df = (spark.table("daily_stock")
      .select("trade_date", "ticker", "close_price",
              F.round(F.avg("close_price").over(w), 2).alias("rolling_3day_avg"),
              F.max("close_price").over(w).alias("rolling_3day_max"),
              F.min("close_price").over(w).alias("rolling_3day_min"))
      .orderBy("ticker", "trade_date"))
assert [(r[0], r[1], float(r[2]), float(r[3]), float(r[4]), float(r[5]))
        for r in df.collect()] == EXPECTED
print("[PASS] Q65 DataFrame API matches SQL")

# ------------------------------------------------ verify one row by hand
# 2024-01-04 window is Jan 2, 3, 4: 126.55, 128.06, 118.67
manual = round((126.55 + 128.06 + 118.67) / 3, 2)
assert manual == 124.43, manual
print(f"[PASS] Q65 hand-computed Jan 4 average = {manual}")

# ------------------------------------------------ partial windows at the start
first_two = spark.sql(SQL).collect()[:2]
assert float(first_two[0][3]) == 106.71                       # 1 row
assert float(first_two[1][3]) == round((106.71 + 126.55) / 2, 2) == 116.63
print("[PASS] Q65 rows 1 and 2 average over 1 and 2 values -- the frame clamps itself")

# ------------------------------------------------ the default-frame trap
# No frame clause means RANGE UNBOUNDED PRECEDING: a CUMULATIVE average.
cumulative = spark.sql("""
SELECT trade_date, ROUND(AVG(close_price) OVER (PARTITION BY ticker ORDER BY trade_date), 2) AS a
FROM daily_stock ORDER BY trade_date
""").collect()
got_cumulative = [float(r[1]) for r in cumulative]
assert got_cumulative == [106.71, 116.63, 120.44, 120.00, 118.52], got_cumulative
# Rolling equivalents are 106.71, 116.63, 120.44, 124.43, 119.79 -- they only
# agree for the first three rows, while the frame is still filling up.
print(f"[PASS] Q65 omitting the frame gives a cumulative average {got_cumulative} "
      "-- diverges from row 4 on")

# ------------------------------------------------ the off-by-one trap
four_rows = spark.sql("""
SELECT trade_date, ROUND(AVG(close_price) OVER (
           PARTITION BY ticker ORDER BY trade_date
           ROWS BETWEEN 3 PRECEDING AND CURRENT ROW), 2) AS a
FROM daily_stock WHERE ticker = 'AAPL' ORDER BY trade_date
""").collect()
assert float(four_rows[3][1]) == round((106.71 + 126.55 + 128.06 + 118.67) / 4, 2) == 120.0
print("[PASS] Q65 '3 PRECEDING' averages FOUR rows -> Jan 4 becomes 120.0, not 124.43")

# ------------------------------------------------ ROWS vs RANGE on a calendar gap
# Jan 10 is 6 days after Jan 4. ROWS still looks back 2 trading rows; a
# 3-DAY RANGE window would see only itself.
spark.sql("""
CREATE OR REPLACE TEMP VIEW daily_stock AS
SELECT * FROM VALUES
    (DATE'2024-01-01', 'MSFT', CAST(100.00 AS DECIMAL(10,2)), 1),
    (DATE'2024-01-02', 'MSFT', CAST(200.00 AS DECIMAL(10,2)), 1),
    (DATE'2024-01-10', 'MSFT', CAST(300.00 AS DECIMAL(10,2)), 1)
AS t(trade_date, ticker, close_price, volume)
""")
expect("Q65 ROWS ignores the calendar gap (3 trading rows averaged)", SQL, [
    (d(1),  "MSFT", 100.00, 100.00, 100.00, 100.00),
    (d(2),  "MSFT", 200.00, 150.00, 200.00, 100.00),
    (d(10), "MSFT", 300.00, 200.00, 300.00, 100.00),
])

# Spark cannot put an INTERVAL range frame over a DATE ordering column --
# a RANGE frame needs a NUMERIC order key, so convert the date to a day number.
try:
    spark.sql("""
    SELECT AVG(close_price) OVER (PARTITION BY ticker ORDER BY trade_date
           RANGE BETWEEN INTERVAL 2 DAYS PRECEDING AND CURRENT ROW) FROM daily_stock
    """).collect()
    raise AssertionError("expected an INTERVAL range frame over DATE to be rejected")
except Exception as e:
    assert "RANGE_FRAME_INVALID_TYPE" in str(e), str(e)[:200]
    print("[PASS] Q65 an INTERVAL RANGE frame over a DATE column is rejected -- "
          "RANGE needs a numeric order key")

range_based = spark.sql("""
SELECT trade_date, ROUND(AVG(close_price) OVER (
           PARTITION BY ticker
           ORDER BY DATEDIFF(trade_date, DATE'1970-01-01')
           RANGE BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS a
FROM daily_stock ORDER BY trade_date
""").collect()
got_range = [float(r[1]) for r in range_based]
assert got_range == [100.0, 150.0, 300.0], got_range
print("[PASS] Q65 a 2-day RANGE window gives Jan 10 = 300.0 (itself only), not 200.0")
