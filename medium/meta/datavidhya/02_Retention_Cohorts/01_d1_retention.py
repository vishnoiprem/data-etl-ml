"""
Problem 01: D1 retention by signup cohort.

Meta flavor: "What share of users who signed up on a given day came back the
next day?"

How to Think:
- Retention is ALWAYS (cohort, day-offset). Name both out loud before any SQL.
- "D1" = active on exactly signup_date + 1 (bounded / classic retention).
- The D1 target date is DIFFERENT FOR EVERY USER, because it is relative to
  that user's own signup. u1 signed up 01-01 so their D1 is 01-02; u4 signed up
  01-02 so their D1 is 01-03. That is why the join computes
  DATE_ADD(u.signup_date, 1) instead of comparing against one fixed date.
- Denominator = cohort size, NOT total users. This is the #1 error.
- LEFT JOIN the activity, never INNER. An INNER JOIN drops churned users from
  the denominator too, and retention comes out as 100% every time.

Why DATE_ADD on the USERS side and not DATEDIFF on the events side:
    GOOD:  e.event_date = DATE_ADD(u.signup_date, 1)
    BAD:   DATEDIFF(e.event_date, u.signup_date) = 1
  Both are logically identical. The first leaves `e.event_date` as a bare
  column, so a partitioned events table can still prune. The second wraps the
  events column in a function, which kills partition pruning and forces a full
  scan. Meta asks "would this scan the whole table?" — this is that answer.

The integer-division trap:
- In PRESTO, COUNT(...)/COUNT(...) on BIGINTs is integer division and returns 0.
  Multiply by 100.0 (a decimal literal) to force decimal arithmetic.
  (Spark and Hive return a double here, so the trap is Presto-specific — but
  Meta runs Presto, so always write the 100.0.)

AI Use Cases:
- Early-churn labels for a propensity model.
- Cohort features for LTV regression.
"""
from pyspark.sql import SparkSession, functions as F

spark = (SparkSession.builder
         .appName("d1-retention")
         .master("local[2]")
         .config("spark.sql.shuffle.partitions", "2")
         .config("spark.ui.showConsoleProgress", "false")
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")

# ---------------------------------------------------------------- sample data
# users(user_id, signup_date) — the cohort table.
users_data = [
    (1, "2026-01-01"),
    (2, "2026-01-01"),
    (3, "2026-01-01"),
    (4, "2026-01-02"),
    (5, "2026-01-02"),
    (6, "2026-01-02"),
    (7, "2026-01-08"),
    (8, "2026-01-08"),
]
users = spark.createDataFrame(users_data, ["user_id", "signup_date"])
users.createOrReplaceTempView("users")

# events(user_id, event_date, event_name) — the activity table.
# Designed so each cohort has at least one churned user:
#   u1 D0,D1,D7   u2 D0 only(churn)  u3 D0,D1
#   u4 D0,D1,D7   u5 D0 only(churn)  u6 D0,D1,D28
#   u7 D0 only(churn)                u8 D0,D1
events_data = [
    (1, "2026-01-01", "open"), (1, "2026-01-02", "open"), (1, "2026-01-08", "open"),
    (2, "2026-01-01", "open"),
    (3, "2026-01-01", "open"), (3, "2026-01-02", "open"),
    (4, "2026-01-02", "open"), (4, "2026-01-03", "open"), (4, "2026-01-09", "open"),
    (5, "2026-01-02", "open"),
    (6, "2026-01-02", "open"), (6, "2026-01-03", "open"), (6, "2026-01-30", "open"),
    (7, "2026-01-08", "open"),
    (8, "2026-01-08", "open"), (8, "2026-01-09", "open"),
]
events = spark.createDataFrame(events_data, ["user_id", "event_date", "event_name"])
events.createOrReplaceTempView("events")

# ------------------------------------------- show the per-user logic first
# Always eyeball this before trusting the aggregate. Note d1_target changes
# per user, and that d1_hit uses an INT flag — MAX() over the strings
# 'YES'/'no' would return 'no' every time, because 'n' > 'Y' in ASCII.
print("\n--- per-user D1 check (verify the aggregate against this) ---")
spark.sql("""
SELECT u.user_id, u.signup_date,
       DATE_ADD(u.signup_date, 1) AS d1_target,
       CONCAT_WS(',', SORT_ARRAY(COLLECT_LIST(e.event_date))) AS active_dates,
       MAX(CASE WHEN e.event_date = DATE_ADD(u.signup_date, 1) THEN 1 ELSE 0 END) AS d1_hit
FROM users u
LEFT JOIN events e ON e.user_id = u.user_id
GROUP BY u.user_id, u.signup_date
ORDER BY u.signup_date, u.user_id
""").show(truncate=False)

# ---------------------------------------------------------------- SQL solution
SQL = """
SELECT u.signup_date AS cohort,
       COUNT(DISTINCT u.user_id) AS cohort_size,
       COUNT(DISTINCT e.user_id) AS retained_d1,
       ROUND(100.0 * COUNT(DISTINCT e.user_id) / COUNT(DISTINCT u.user_id), 2) AS pct_d1
FROM users u
LEFT JOIN events e
       ON e.user_id = u.user_id
      AND e.event_date = DATE_ADD(u.signup_date, 1)
GROUP BY u.signup_date
ORDER BY u.signup_date
"""

print("--- D1 retention by cohort (SQL) ---")
result = spark.sql(SQL)
result.show(truncate=False)

EXPECTED = [
    ("2026-01-01", 3, 2, 66.67),
    ("2026-01-02", 3, 2, 66.67),
    ("2026-01-08", 2, 1, 50.00),
]
got = [(r[0], r[1], r[2], float(r[3])) for r in result.collect()]
assert got == EXPECTED, f"\nexpected {EXPECTED}\ngot      {got}"
print("[PASS] D1 retention by cohort (SQL)")

# ------------------------------------------------- PySpark DataFrame API
# Same plan: build the D1 target on the cohort side, LEFT JOIN, count distinct.
df = (users
      .withColumn("d1_target", F.date_add(F.col("signup_date"), 1))
      .join(events.alias("e"),
            (F.col("e.user_id") == users["user_id"])
            & (F.col("e.event_date") == F.col("d1_target")),
            "left")
      .groupBy(users["signup_date"].alias("cohort"))
      .agg(F.countDistinct(users["user_id"]).alias("cohort_size"),
           F.countDistinct(F.col("e.user_id")).alias("retained_d1"))
      .withColumn("pct_d1",
                  F.round(100.0 * F.col("retained_d1") / F.col("cohort_size"), 2))
      .orderBy("cohort"))

print("--- D1 retention by cohort (DataFrame API) ---")
df.show(truncate=False)
got_df = [(r[0], r[1], r[2], float(r[3])) for r in df.collect()]
assert got_df == EXPECTED, f"\nexpected {EXPECTED}\ngot      {got_df}"
print("[PASS] D1 retention — DataFrame API matches SQL")

# --------------------------------------------- the INNER JOIN failure mode
# Asserted so the bug is documented: churned users vanish from the DENOMINATOR
# too, so every cohort reports 100% retention.
print("--- WRONG: INNER JOIN inflates retention to 100% ---")
wrong = spark.sql("""
SELECT u.signup_date AS cohort,
       COUNT(DISTINCT u.user_id) AS cohort_size,
       COUNT(DISTINCT e.user_id) AS retained_d1,
       ROUND(100.0 * COUNT(DISTINCT e.user_id) / COUNT(DISTINCT u.user_id), 2) AS pct_d1
FROM users u
JOIN events e ON e.user_id = u.user_id
             AND e.event_date = DATE_ADD(u.signup_date, 1)
GROUP BY u.signup_date ORDER BY u.signup_date
""")
wrong.show(truncate=False)
got_wrong = [(r[0], r[1], r[2], float(r[3])) for r in wrong.collect()]
assert got_wrong == [
    ("2026-01-01", 2, 2, 100.00),
    ("2026-01-02", 2, 2, 100.00),
    ("2026-01-08", 1, 1, 100.00),
], got_wrong
print("[PASS] INNER JOIN failure mode reproduced (cohort_size shrank: 3->2, 3->2, 2->1)")
