"""
Q10: Friend Request Acceptance Rate   [Medium | Aggregation]

Monthly acceptance rate = accepted / sent * 100, per request month.

How to Think:
- The log holds both 'sent' and 'accepted' rows for the SAME request pair.
  The denominator is sent requests; the numerator is those that were accepted.
- Attribute by the month the request was SENT, not the month it was accepted.
  Otherwise a request sent Jan 31 and accepted Feb 1 inflates February's
  numerator against a denominator it was never part of — a rate above 100%.
- Self-join sent-to-accepted on the (sender, receiver) pair, LEFT, then count.

The traps:
- Integer division: COUNT(...)/COUNT(...) is 0 in Presto/Hive. Force decimal.
- A request sent and never accepted (2->4, 4->6) must stay in the denominator.

Spark note:
- LEFT JOIN on the pair then conditional count = one shuffle, one pass.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("10-friend-request-acceptance")
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
WITH sent AS (
    SELECT sender_id, receiver_id, action_date AS sent_date
    FROM friend_requests WHERE action = 'sent'
),
accepted AS (
    SELECT sender_id, receiver_id
    FROM friend_requests WHERE action = 'accepted'
)
SELECT DATE_FORMAT(s.sent_date, 'yyyy-MM') AS request_month,
       COUNT(*) AS requests_sent,
       COUNT(a.sender_id) AS requests_accepted,
       ROUND(100.0 * COUNT(a.sender_id) / COUNT(*), 2) AS acceptance_rate_pct
FROM sent s
LEFT JOIN accepted a
       ON a.sender_id = s.sender_id
      AND a.receiver_id = s.receiver_id
GROUP BY DATE_FORMAT(s.sent_date, 'yyyy-MM')
ORDER BY request_month
"""

expect("Q10 friend request acceptance rate", SQL, [
    ("2026-01", 3, 2, 66.67),
    ("2026-02", 2, 1, 50.00),
])

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports CTEs and the LEFT JOIN + COUNT pattern. The denominator
# is the count of SENT rows; the numerator is the count of those for which
# a matching ACCEPTED row exists. Group by the SENT month -- never the
# accepted month, or a late acceptance inflates a different month's numerator.
# DATE_FORMAT uses MySQL's %Y-%m codes; Spark's 'yyyy-MM' is Java and does
# NOT work in MySQL.
#
# CREATE TABLE friend_requests (
#     sender_id   INT         NOT NULL,
#     receiver_id INT         NOT NULL,
#     action      VARCHAR(16) NOT NULL,
#     action_date DATE        NOT NULL,
#     PRIMARY KEY (sender_id, receiver_id, action),
#     KEY ix_fr_action_date (action, action_date)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO friend_requests (sender_id, receiver_id, action, action_date) VALUES
#     (1, 2, 'sent',     '2026-01-05'), (1, 2, 'accepted', '2026-01-06'),
#     (1, 3, 'sent',     '2026-01-10'), (1, 3, 'accepted', '2026-01-12'),
#     (2, 4, 'sent',     '2026-01-20'),
#     (3, 5, 'sent',     '2026-02-02'), (3, 5, 'accepted', '2026-02-03'),
#     (4, 6, 'sent',     '2026-02-14');
#
# WITH sent AS (
#     SELECT sender_id, receiver_id, action_date AS sent_date
#     FROM friend_requests WHERE action = 'sent'
# ),
# accepted AS (
#     SELECT sender_id, receiver_id
#     FROM friend_requests WHERE action = 'accepted'
# )
# SELECT DATE_FORMAT(s.sent_date, '%Y-%m') AS request_month,
#        COUNT(*) AS requests_sent,
#        COUNT(a.sender_id) AS requests_accepted,
#        ROUND(100.0 * COUNT(a.sender_id) / COUNT(*), 2) AS acceptance_rate_pct
# FROM sent s
# LEFT JOIN accepted a
#        ON a.sender_id = s.sender_id
#       AND a.receiver_id = s.receiver_id
# GROUP BY DATE_FORMAT(s.sent_date, '%Y-%m')
# ORDER BY request_month;
#
# -- Expected:
# -- 2026-01  3  2  66.67
# -- 2026-02  2  1  50.00
