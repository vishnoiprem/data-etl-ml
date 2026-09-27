"""
Problem 02: D7 retention by signup cohort.

Meta flavor: "D7 retention for the January 1 cohort."

Business Question
-----------------
Of the users who signed up on each day, how many came back exactly seven
days later? This is the canonical "early-habit" KPI for consumer products:
D1 measures onboarding, D7 measures whether the product has earned a second
visit, D28 measures habit.

How to Think
------------
- Retention is ALWAYS (cohort, day-offset). Say both out loud before writing
  SQL or you will silently produce the wrong denominator.
- "D7" at Meta = active on exactly signup_date + 7 (bounded / classic
  retention), not "active any time during days 1..7" (rolling retention).
- Denominator = cohort size, NOT total users. Mixing them up is the #1 bug.
- LEFT JOIN the activity, never INNER — an INNER JOIN silently drops churned
  users and inflates retention to 100%.
- Watch the reporting window: a cohort younger than 7 days CANNOT have D7
  data. Reporting 0% for an immature cohort is a real bug — exclude it
  instead. Here the 2026-01-08 cohort genuinely has no D7 activity in the
  seed data.
- D7 differs from D1 only by the offset (7 vs 1). Parameterise the offset
  rather than writing seven near-identical queries (see
  06_retention_curve_d0_d7.py).

How to Remember
---------------
"Same skeleton, new offset. Guard the immature cohorts."

The Integer-Division Trap
-------------------------
COUNT(...) / COUNT(...) is integer division in Presto/Hive and returns 0.
Multiply by 100.0 (a decimal literal) to force floating point. Spark is
slightly more forgiving than Presto here, but write it defensively anyway
because the same query will run on both engines at Meta.

Spark-Native Rewrite (CTE + window-friendly aggregation)
-------------------------------------------------------
The classic LEFT JOIN form duplicates the cohort_size denominator next to
the retained numerator. In this rewrite we split the work into stages:

    1. `cohorts`     CTE  — one row per signup_date with cohort_size
                            pre-computed and the literal `signup_date + 7`
                            marker cached for the join below.
    2. `d7_activity` CTE  — one row per (cohort, retained_user) whose
                            event_date lands exactly on the D7 marker.
                            DISTINCT inside the CTE keeps the join from
                            blowing up when a user fires multiple events
                            on day +7.
    3. Outer query        — LEFT JOIN cohorts -> d7_activity so churned
                            users survive, then aggregate with
                            COUNT(DISTINCT) and divide against the
                            pre-computed cohort_size. No integer division
                            because 100.0 * COUNT(DISTINCT ...) is a
                            double literal.

The window-function alternative (COUNT(...) OVER (PARTITION BY cohort))
is shown as a comment below the SQL for reviewers who prefer that style.

AI Use Cases
------------
- D7 is the standard early-retention target variable for growth models
  (churn-propensity classifier, lifecycle-stage regressor).
- Cohort × offset matrix is a feature block for LTV regression.
- D7 lift is the primary north-star metric in most onboarding A/B tests.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("02-d7-retention")
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
    (1, "2026-01-01", "organic",  "US"),
    (2, "2026-01-01", "paid",     "US"),
    (3, "2026-01-01", "organic",  "IN"),
    (4, "2026-01-02", "paid",     "US"),
    (5, "2026-01-02", "referral", "BR"),
    (6, "2026-01-02", "organic",  "IN"),
    (7, "2026-01-08", "paid",     "US"),
    (8, "2026-01-08", "organic",  "BR"),
],
    ["user_id", "signup_date", "channel", "country"]
).createOrReplaceTempView("users")

spark.createDataFrame(
    [
    (1, "2026-01-01", "open"),  (1, "2026-01-02", "open"),  (1, "2026-01-08", "open"),
    (2, "2026-01-01", "open"),
    (3, "2026-01-01", "open"),  (3, "2026-01-02", "open"),
    (4, "2026-01-02", "open"),  (4, "2026-01-03", "open"),  (4, "2026-01-09", "open"),
    (5, "2026-01-02", "open"),
    (6, "2026-01-02", "open"),  (6, "2026-01-03", "open"),  (6, "2026-01-30", "open"),
    (7, "2026-01-08", "open"),
    (8, "2026-01-08", "open"),  (8, "2026-01-09", "open"),
],
    ["user_id", "event_date", "event_name"]
).createOrReplaceTempView("events")


SQL = """
WITH cohorts AS (
    -- One row per signup cohort with its size pre-computed.
    SELECT signup_date                                        AS cohort,
           COUNT(DISTINCT user_id)                            AS cohort_size,
           MAX(DATE_ADD(signup_date, 7))                      AS d7_marker
    FROM users
    GROUP BY signup_date
),
d7_activity AS (
    -- One row per user who was active exactly 7 days after signup.
    SELECT DISTINCT
           u.signup_date                                      AS cohort,
           u.user_id                                          AS retained_user
    FROM users u
    JOIN events e
      ON e.user_id    = u.user_id
     AND e.event_date = DATE_ADD(u.signup_date, 7)
)
SELECT c.cohort                                                    AS cohort,
       c.cohort_size                                               AS cohort_size,
       COUNT(DISTINCT a.retained_user)                             AS retained_d7,
       ROUND(
           100.0 * COUNT(DISTINCT a.retained_user) / c.cohort_size,
           2
       )                                                           AS pct_d7
FROM cohorts c
LEFT JOIN d7_activity a
       ON a.cohort = c.cohort
GROUP BY c.cohort, c.cohort_size
ORDER BY c.cohort
"""

# Alternative compact form using a window function over the joined set:
#
# SELECT cohort,
#        MAX(cohort_size)                                            AS cohort_size,
#        COUNT(DISTINCT CASE WHEN is_active_d7 THEN user_id END)     AS retained_d7,
#        ROUND(
#            100.0 * COUNT(DISTINCT CASE WHEN is_active_d7 THEN user_id END)
#                  / MAX(cohort_size),
#            2
#        )                                                          AS pct_d7
# FROM (
#     SELECT u.signup_date                                           AS cohort,
#            u.user_id,
#            COUNT(DISTINCT u.user_id)                               OVER (PARTITION BY u.signup_date)
#                                                                     AS cohort_size,
#            MAX(CASE WHEN e.event_date = DATE_ADD(u.signup_date, 7)
#                     THEN 1 ELSE 0 END)                             AS is_active_d7
#     FROM users u
#     LEFT JOIN events e ON e.user_id = u.user_id
#     GROUP BY u.signup_date, u.user_id
# ) t
# GROUP BY cohort
# ORDER BY cohort;

expect("D7 retention by cohort", SQL, [
    ("2026-01-01", 3, 1, 33.33),
    ("2026-01-02", 3, 1, 33.33),
    ("2026-01-08", 2, 0, 0.00),
])
