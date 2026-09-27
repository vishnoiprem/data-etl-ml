"""
Q27: Cumulative Rank with Reset (Session Running Total)   [Hard | Window Functions, Session Analysis]
DataVidhya slug: session-running-total

Every `login` opens a new session; purchases belong to the most recently opened
session. Emit each event with its session_id and the running purchase total
inside that session, where the total resets at each login.

How to Think:
- This is the canonical two-window pattern, and the order matters:
    window 1  ->  SUM(is_login) running, PARTITION BY user  ->  session_id
    window 2  ->  SUM(amount)   running, PARTITION BY user, session_id
  You cannot do it in one window. The first window MANUFACTURES the partition
  key the second window needs, so they must live in separate CTE layers.
- "A login increments session_id" and "the login row itself belongs to the new
  session" together mean the running login-count is inclusive of the current
  row -- so the frame ends at CURRENT ROW, not `1 PRECEDING`.
- Events before the first login land in session 0 for free: the running
  login-count is still 0 there. No special-casing needed.

The trap:
- `event_date` is not unique -- three events share 2024-01-01. Ordering by date
  alone makes the running sums non-deterministic, so ties MUST break on
  `event_id`. This is the single most common way this question is failed.
- Do not filter to purchases before summing. Login rows must survive to the
  output (with total 0.00), and they are what reset the window.

Spark note:
- Both windows share `PARTITION BY user_id`, so Spark shuffles once and sorts
  twice. On a real event stream you would also filter the date partition first.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("27-session-running-total")
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
spark.sql("""
CREATE OR REPLACE TEMP VIEW user_sessions AS
SELECT * FROM VALUES
    (1, 1, DATE'2024-01-01', 'login',    CAST(0.00  AS DECIMAL(10,2))),
    (2, 1, DATE'2024-01-01', 'purchase', CAST(50.00 AS DECIMAL(10,2))),
    (3, 1, DATE'2024-01-01', 'purchase', CAST(30.00 AS DECIMAL(10,2))),
    (4, 1, DATE'2024-01-02', 'login',    CAST(0.00  AS DECIMAL(10,2))),
    (5, 1, DATE'2024-01-02', 'purchase', CAST(75.00 AS DECIMAL(10,2)))
AS t(event_id, user_id, event_date, event_type, amount)
""")

from pyspark.sql import functions as F, Window as W

SQL = """
WITH sessioned AS (
    SELECT event_id,
           user_id,
           event_date,
           event_type,
           amount,
           SUM(CASE WHEN event_type = 'login' THEN 1 ELSE 0 END) OVER (
               PARTITION BY user_id
               ORDER BY event_date, event_id
               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
           ) AS session_id
    FROM user_sessions
)
SELECT user_id,
       event_date,
       event_type,
       amount,
       session_id,
       SUM(amount) OVER (
           PARTITION BY user_id, session_id
           ORDER BY event_date, event_id
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS session_running_total
FROM sessioned
ORDER BY user_id, event_date, event_id
"""

spark.sql(SQL).show(truncate=False)

import datetime as dt

D1, D2 = dt.date(2024, 1, 1), dt.date(2024, 1, 2)
expect("Q27 session running total", SQL, [
    (1, D1, "login",    0.0,  1, 0.0),
    (1, D1, "purchase", 50.0, 1, 50.0),
    (1, D1, "purchase", 30.0, 1, 80.0),
    (1, D2, "login",    0.0,  2, 0.0),
    (1, D2, "purchase", 75.0, 2, 75.0),
])

# DataFrame API equivalent -- same two-window plan.
w_sess = (W.partitionBy("user_id").orderBy("event_date", "event_id")
          .rowsBetween(W.unboundedPreceding, W.currentRow))
df = spark.table("user_sessions").withColumn(
    "session_id",
    F.sum(F.when(F.col("event_type") == "login", 1).otherwise(0)).over(w_sess))
w_tot = (W.partitionBy("user_id", "session_id").orderBy("event_date", "event_id")
         .rowsBetween(W.unboundedPreceding, W.currentRow))
df = (df.withColumn("session_running_total", F.sum("amount").over(w_tot))
      .select("user_id", "event_date", "event_type", "amount",
              "session_id", "session_running_total")
      .orderBy("user_id", "event_date", "event_id"))
assert [(r[0], r[1], r[2], float(r[3]), r[4], float(r[5])) for r in df.collect()] == [
    (1, D1, "login", 0.0, 1, 0.0),
    (1, D1, "purchase", 50.0, 1, 50.0),
    (1, D1, "purchase", 30.0, 1, 80.0),
    (1, D2, "login", 0.0, 2, 0.0),
    (1, D2, "purchase", 75.0, 2, 75.0),
]
print("[PASS] Q27 DataFrame API matches SQL")

# ---------------------------------------------------------- the session-0 trap
# The shipped sample data never exercises it, so assert it explicitly:
# a purchase BEFORE the user's first login must land in session 0.
spark.sql("""
CREATE OR REPLACE TEMP VIEW user_sessions AS
SELECT * FROM VALUES
    (1, 9, DATE'2024-03-01', 'purchase', CAST(10.00 AS DECIMAL(10,2))),
    (2, 9, DATE'2024-03-01', 'purchase', CAST(20.00 AS DECIMAL(10,2))),
    (3, 9, DATE'2024-03-02', 'login',    CAST(0.00  AS DECIMAL(10,2))),
    (4, 9, DATE'2024-03-02', 'purchase', CAST(40.00 AS DECIMAL(10,2)))
AS t(event_id, user_id, event_date, event_type, amount)
""")
expect("Q27 pre-login events belong to session 0", SQL, [
    (9, dt.date(2024, 3, 1), "purchase", 10.0, 0, 10.0),
    (9, dt.date(2024, 3, 1), "purchase", 20.0, 0, 30.0),
    (9, dt.date(2024, 3, 2), "login",    0.0,  1, 0.0),
    (9, dt.date(2024, 3, 2), "purchase", 40.0, 1, 40.0),
])