"""
Q18: Average Friend Requests Sent Per Week   [Medium | Date Functions, Aggregation]

Average requests sent per week per user, based on their request activity span.

How to Think:
- "Per week over their activity span" needs a denominator DEFINITION, and the
  question does not give one. State your choice explicitly:
      weeks = FLOOR(DATEDIFF(last, first) / 7) + 1
  The +1 matters: a user whose requests all land in one week spans 1 week, not
  0 weeks, and dividing by 0 would error.
- This is the single most important habit in a Meta SQL round: when the metric
  is under-specified, define it out loud and move on. Do not silently pick one.
- Only 'sent' rows belong in the numerator; 'accepted' rows are a different
  event and would double-count.

The trap:
- A user with a single request has span 0 days. Without the +1 (or a GREATEST
  guard) the query divides by zero.

Spark note:
- One shuffle by sender. Denominator is arithmetic on aggregates, no extra pass.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("18-avg-requests-per-week")
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
    (1, 2, "sent",     "2026-01-05"), (1, 2, "accepted", "2026-01-06"),
    (1, 3, "sent",     "2026-01-10"), (1, 3, "accepted", "2026-01-12"),
    (2, 4, "sent",     "2026-01-20"),
    (3, 5, "sent",     "2026-02-02"), (3, 5, "accepted", "2026-02-03"),
    (4, 6, "sent",     "2026-02-14"),
],
    ["sender_id", "receiver_id", "action", "action_date"]
).createOrReplaceTempView("friend_requests")


SQL = """
SELECT sender_id,
       COUNT(*) AS requests_sent,
       FLOOR(DATEDIFF(MAX(action_date), MIN(action_date)) / 7) + 1 AS weeks_active,
       ROUND(COUNT(*) / (FLOOR(DATEDIFF(MAX(action_date), MIN(action_date)) / 7) + 1), 2)
           AS avg_requests_per_week
FROM friend_requests
WHERE action = 'sent'
GROUP BY sender_id
ORDER BY sender_id
"""

expect("Q18 avg requests per week", SQL, [
    (1, 2, 1, 2.00),
    (2, 1, 1, 1.00),
    (3, 1, 1, 1.00),
    (4, 1, 1, 1.00),
])

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports the same COUNT / DATEDIFF / FLOOR pattern. The
# "weeks_active = FLOOR(days_span / 7) + 1" definition is what avoids a
# divide-by-zero for a user whose requests all land in one week. The +1 is
# the safety; do not omit it. Only 'sent' rows are counted in the numerator
# -- 'accepted' rows are a different event and would double-count.
#
# CREATE TABLE friend_requests (
#     sender_id   INT         NOT NULL,
#     receiver_id INT         NOT NULL,
#     action      VARCHAR(16) NOT NULL,
#     action_date DATE        NOT NULL,
#     PRIMARY KEY (sender_id, receiver_id, action),
#     KEY ix_fr_action (action, sender_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO friend_requests (sender_id, receiver_id, action, action_date) VALUES
#     (1, 2, 'sent',     '2026-01-05'), (1, 2, 'accepted', '2026-01-06'),
#     (1, 3, 'sent',     '2026-01-10'), (1, 3, 'accepted', '2026-01-12'),
#     (2, 4, 'sent',     '2026-01-20'),
#     (3, 5, 'sent',     '2026-02-02'), (3, 5, 'accepted', '2026-02-03'),
#     (4, 6, 'sent',     '2026-02-14');
#
# SELECT sender_id,
#        COUNT(*) AS requests_sent,
#        FLOOR(DATEDIFF(MAX(action_date), MIN(action_date)) / 7) + 1 AS weeks_active,
#        ROUND(COUNT(*) / (FLOOR(DATEDIFF(MAX(action_date), MIN(action_date)) / 7) + 1), 2)
#            AS avg_requests_per_week
# FROM friend_requests
# WHERE action = 'sent'
# GROUP BY sender_id
# ORDER BY sender_id;
#
# -- Expected:
# -- 1  2  1  2.00
# -- 2  1  1  1.00
# -- 3  1  1  1.00
# -- 4  1  1  1.00
