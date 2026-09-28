"""
Q03: Event Funnel Drop-Off Analysis   [Hard | Joins, CTEs]

Users progress view -> click -> purchase. Compute the drop-off percentage at
each stage and identify where the funnel leaks worst.

How to Think:
- Count DISTINCT USERS per step, not events — user 4 viewed twice and would
  otherwise be double counted.
- Define the funnel order yourself; the event table has no inherent order.
  A VALUES list of (step, step_order) is the cleanest way to pin it.
- "Conversion from previous" uses LAG over the ordered steps.
- drop_off_pct = 100 - conversion_from_previous_pct.

The traps:
- User 5 purchased WITHOUT clicking. A strict funnel should arguably not count
  them, but the naive per-step count does. Say this out loud in the interview:
  "Do you want a strict ordered funnel, or independent step counts?" That single
  question is the product signal Meta is scoring.
- This query uses the LOOSE definition (independent step counts).

Spark note:
- Counting distinct users per step is one shuffle; window over 3 rows is free.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("03-funnel-dropoff")
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
    (1, "view", "2026-03-01 10:00:00"),
    (1, "click", "2026-03-01 10:02:00"),
    (1, "purchase", "2026-03-01 10:09:00"),
    (2, "view", "2026-03-01 11:00:00"),
    (2, "click", "2026-03-01 11:04:00"),
    (3, "view", "2026-03-01 12:00:00"),
    (4, "view", "2026-03-02 09:00:00"),
    (4, "view", "2026-03-02 09:06:00"),          # duplicate step
    (4, "click", "2026-03-02 09:11:00"),
    (5, "view", "2026-03-02 14:00:00"),
    (5, "purchase", "2026-03-02 14:20:00"),      # skipped 'click'
],
    ["user_id", "event_name", "event_ts"]
).createOrReplaceTempView("funnel")


SQL = """
WITH step_order AS (
    SELECT * FROM VALUES ('view', 1), ('click', 2), ('purchase', 3)
                      AS t(step, step_num)
),
per_step AS (
    SELECT s.step,
           s.step_num,
           COUNT(DISTINCT f.user_id) AS users
    FROM step_order s
    LEFT JOIN funnel f ON f.event_name = s.step
    GROUP BY s.step, s.step_num
)
SELECT step,
       users,
       ROUND(100.0 * users / LAG(users) OVER (ORDER BY step_num), 2) AS conv_from_prev_pct,
       ROUND(100.0 - 100.0 * users / LAG(users) OVER (ORDER BY step_num), 2) AS drop_off_pct
FROM per_step
ORDER BY step_num
"""

expect("Q03 funnel drop-off", SQL, [
    ("view", 5, None, None),
    ("click", 3, 60.00, 40.00),
    ("purchase", 2, 66.67, 33.33),
])

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports window functions and the LAG form. There is no native
# VALUES table in MySQL 8 (rows constructors work but the CTE form is cleaner
# using a subquery with UNION ALL). Counting distinct users per step gives a
# "loose" funnel where user 5 -- who purchased without clicking -- still
# counts as a purchase. The first step has no prior step, so LAG returns NULL.
#
# CREATE TABLE funnel (
#     user_id    INT          NOT NULL,
#     event_name VARCHAR(16)  NOT NULL,
#     event_ts   TIMESTAMP    NOT NULL,
#     KEY ix_funnel_event (event_name, user_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO funnel (user_id, event_name, event_ts) VALUES
#     (1, 'view',     '2026-03-01 10:00:00'),
#     (1, 'click',    '2026-03-01 10:02:00'),
#     (1, 'purchase', '2026-03-01 10:09:00'),
#     (2, 'view',     '2026-03-01 11:00:00'),
#     (2, 'click',    '2026-03-01 11:04:00'),
#     (3, 'view',     '2026-03-01 12:00:00'),
#     (4, 'view',     '2026-03-02 09:00:00'),
#     (4, 'view',     '2026-03-02 09:06:00'),
#     (4, 'click',    '2026-03-02 09:11:00'),
#     (5, 'view',     '2026-03-02 14:00:00'),
#     (5, 'purchase', '2026-03-02 14:20:00');
#
# WITH RECURSIVE step_order AS (
#     SELECT 1 AS step_num, 'view' AS step
#     UNION ALL SELECT 2, 'click' UNION ALL SELECT 3, 'purchase'
# ),
# per_step AS (
#     SELECT s.step,
#            s.step_num,
#            COUNT(DISTINCT f.user_id) AS users
#     FROM step_order s
#     LEFT JOIN funnel f ON f.event_name = s.step
#     GROUP BY s.step, s.step_num
# )
# SELECT step,
#        users,
#        ROUND(100.0 * users / LAG(users) OVER (ORDER BY step_num), 2) AS conv_from_prev_pct,
#        ROUND(100.0 - 100.0 * users / LAG(users) OVER (ORDER BY step_num), 2) AS drop_off_pct
# FROM per_step
# ORDER BY step_num;
#
# -- Expected:
# -- view      5  NULL  NULL
# -- click     3  60.00  40.00
# -- purchase  2  66.67  33.33
