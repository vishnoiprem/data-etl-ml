"""
Problem 01: Funnel step counts and drop-off (LOOSE definition).

Meta flavor: "Marketplace funnel is view -> message -> purchase. Where do we
leak the most users?"

Business Question
-----------------
For each step of the marketplace funnel (view -> message -> purchase), how
many distinct users reached that step, and what fraction of the previous step
made it here? The LOOSE definition counts each step independently: a user who
skipped a middle step still gets credit for the step they did. This is the
definition most growth dashboards show because it is the most forgiving signal
of where the top of the funnel leaks.

How to Think
------------
- COUNT(DISTINCT user_id) per step. Events, not users, is the wrong grain
  — user 5 viewed twice, and counting rows would double-count them.
- The `funnel_events` table has no inherent step order. Pin it with a VALUES
  spine so the window functions have something stable to ORDER BY.
- conv_from_prev = users / LAG(users); drop_off = 100 - that.
- LOOSE means each step is counted independently. User 3 purchased without
  messaging and still counts in `purchase` here. Ask which definition the
  interviewer wants — see 02_strict_ordered_funnel.py for the other one.
- Always include a step_num column in the spine so ORDER BY is over an int,
  not a string (sorting by step alphabetically would put purchase before
  view).

How to Remember
---------------
"Loose = independent counts. Strict = monotonically increasing timestamps."

Spark / Performance Note
------------------------
- One distinct-count shuffle is unavoidable; the 3-row window is free.
- Prefer the SQL form in production — the DataFrame API shown below is a
  useful parity check while writing the query, but it pays for two extra
  shuffle stages (the join + the groupBy) that the SQL form folds into one.

AI Use Cases
------------
- Drop-off at step N is the headline KPI for onboarding flow reviews.
- conv_from_prev_pct is a feature in funnel-completion classifiers.
- A/B test primary endpoint for any "increase X -> Y conversion" experiment.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("01-step-counts-dropoff")
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
spark.createDataFrame(
    [
    (1, "view",     "2026-01-01 10:00:00"),
    (1, "message",  "2026-01-01 10:05:00"),
    (1, "purchase", "2026-01-01 10:20:00"),
    (2, "view",     "2026-01-01 11:00:00"),
    (2, "message",  "2026-01-01 11:30:00"),
    (3, "view",     "2026-01-01 12:00:00"),
    (3, "purchase", "2026-01-01 12:10:00"),   # skipped 'message'
    (4, "view",     "2026-01-02 09:00:00"),
    (5, "view",     "2026-01-02 09:30:00"),
    (5, "view",     "2026-01-02 09:40:00"),   # duplicate step
    (5, "message",  "2026-01-02 09:50:00"),
],
    ["user_id", "step", "event_ts"]
).createOrReplaceTempView("funnel_events")

from pyspark.sql import functions as F, Window

SQL = """
WITH spine AS (
    SELECT * FROM VALUES ('view',1), ('message',2), ('purchase',3) AS t(step, step_num)
),
per_step AS (
    SELECT s.step, s.step_num, COUNT(DISTINCT f.user_id) AS users
    FROM spine s
    LEFT JOIN funnel_events f ON f.step = s.step
    GROUP BY s.step, s.step_num
)
SELECT step, users,
       ROUND(100.0 * users / LAG(users) OVER (ORDER BY step_num), 2) AS conv_from_prev_pct,
       ROUND(100.0 - 100.0 * users / LAG(users) OVER (ORDER BY step_num), 2) AS drop_off_pct
FROM per_step
ORDER BY step_num
"""
expect("loose funnel step counts", SQL, [
    ("view", 5, None, None),
    ("message", 3, 60.00, 40.00),
    ("purchase", 2, 66.67, 33.33),
])

# ---- PySpark DataFrame API, same result -----------------------------------
spine = spark.createDataFrame([("view", 1), ("message", 2), ("purchase", 3)],
                              ["step", "step_num"])
per_step = (spine.join(spark.table("funnel_events"), "step", "left")
            .groupBy("step", "step_num")
            .agg(F.countDistinct("user_id").alias("users")))
w = Window.orderBy("step_num")
out = (per_step
       .withColumn("prev", F.lag("users").over(w))
       .withColumn("conv_from_prev_pct", F.round(100.0 * F.col("users") / F.col("prev"), 2))
       .withColumn("drop_off_pct", F.round(100.0 - 100.0 * F.col("users") / F.col("prev"), 2))
       .orderBy("step_num")
       .select("step", "users", "conv_from_prev_pct", "drop_off_pct"))
assert [tuple(r) for r in out.collect()] == [
    ("view", 5, None, None), ("message", 3, 60.00, 40.00), ("purchase", 2, 66.67, 33.33)]
print("[PASS] loose funnel — DataFrame API matches SQL")
