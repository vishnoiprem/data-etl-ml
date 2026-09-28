"""
Q39: Acceptance Rate By Date   [Medium | Inner Joins, CTEs, Date/Time Functions]
DataVidhya slug: friend-request-acceptance-rate

One log table holds both 'sent' and 'accepted' rows. In an 'accepted' row the
sender/receiver are SWAPPED and the date may be later. Per send-date, report
the share of that day's sends that were ever accepted.

How to Think:
- One table, two logical tables. Split it first:
    sent -> (request_date, sender, receiver)
    acc  -> (sender, receiver)  with NO date, because the accept date is
            explicitly irrelevant
  Then LEFT JOIN sent to acc on the REVERSED pair. Everything else is counting.
- LEFT, not INNER: an unaccepted send must survive as a denominator row. INNER
  JOIN gives every date 100% and drops 2026-01-02 entirely -- the single most
  common failure on retention-shaped questions.
- Grain: one output row per DATE A REQUEST WAS SENT.

The trap:
- The reversed join key. `ON a.sender_id = s.sender_id AND a.receiver_id =
  s.receiver_id` matches nothing and every rate is 0.00 -- which looks like a
  data problem rather than a bug. It must be
  `a.sender_id = s.receiver_id AND a.receiver_id = s.sender_id`.
- Do NOT join on date. The 18->19 send on 2026-01-03 is accepted on 2026-01-04,
  and that acceptance still counts for the 3rd. Adding the date to the join
  condition drops it and gives 0.00.
- 2026-01-04 produces NO output row. It contains only an 'accepted' row, and the
  grain is send-dates. Grouping the raw table by request_date invents a 4th row.
- Dedupe `acc` before joining. Two accepted rows for the same pair would fan the
  send out to 2 rows, so the numerator could exceed the denominator and a rate
  could exceed 100%.
- 0.00 must be reported, not omitted or NULL.
- Integer division: use 100.0.
- Distinct from Q10 (`aggregation-friend-request-acceptance-rate`), which is a
  different question with an action/status column rather than a swapped pair.

Spark note:
- Both sides derive from one scan of a small table, so Spark broadcasts `acc`.
  On a real log, filter the date partitions of the SEND side only -- the accept
  side must stay unbounded or late acceptances are lost.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("39-acceptance-rate-by-date")
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
# Note: 19->18 accepts on 01-04 a request sent on 01-03 (late acceptance),
# and the 01-04 row is an accept only, so it yields no output row.
spark.sql("""
CREATE OR REPLACE TEMP VIEW friend_requests AS
SELECT * FROM VALUES
    (DATE'2026-01-01',  1,  2, 'sent'),
    (DATE'2026-01-01',  3,  4, 'sent'),
    (DATE'2026-01-01',  2,  1, 'accepted'),
    (DATE'2026-01-02', 10, 11, 'sent'),
    (DATE'2026-01-02', 12, 13, 'sent'),
    (DATE'2026-01-03', 18, 19, 'sent'),
    (DATE'2026-01-03', 20, 21, 'sent'),
    (DATE'2026-01-03', 22, 23, 'sent'),
    (DATE'2026-01-04', 19, 18, 'accepted')
AS t(request_date, sender_id, receiver_id, action)
""")

from pyspark.sql import functions as F

SQL = """
WITH sent AS (
    SELECT request_date, sender_id, receiver_id
    FROM friend_requests
    WHERE action = 'sent'
),
acc AS (
    -- DISTINCT so a repeated acceptance cannot fan out a send
    SELECT DISTINCT sender_id, receiver_id
    FROM friend_requests
    WHERE action = 'accepted'
)
SELECT s.request_date AS date,
       ROUND(100.0 * SUM(CASE WHEN a.sender_id IS NOT NULL THEN 1 ELSE 0 END)
                   / COUNT(*), 2) AS percentage_acceptance
FROM sent s
LEFT JOIN acc a
       ON a.sender_id   = s.receiver_id     -- reversed
      AND a.receiver_id = s.sender_id       -- reversed
GROUP BY s.request_date
ORDER BY s.request_date
"""

spark.sql(SQL).show(truncate=False)

import datetime as dt


def d(day):
    return dt.date(2026, 1, day)


expect("Q39 acceptance rate by send date", SQL, [
    (d(1), 50.00),
    (d(2), 0.00),
    (d(3), 33.33),
])

# DataFrame API equivalent.
fr = spark.table("friend_requests")
sent = fr.filter(F.col("action") == "sent").select(
    "request_date", "sender_id", "receiver_id").alias("s")
acc = (fr.filter(F.col("action") == "accepted")
       .select(F.col("sender_id").alias("a_sender"),
               F.col("receiver_id").alias("a_receiver"))
       .distinct())
df = (sent.join(F.broadcast(acc),
                (F.col("a_sender") == F.col("s.receiver_id")) &
                (F.col("a_receiver") == F.col("s.sender_id")), "left")
      .groupBy(F.col("s.request_date").alias("date"))
      .agg(F.round(F.lit(100.0) * F.sum(F.when(F.col("a_sender").isNotNull(), 1).otherwise(0))
                   / F.count(F.lit(1)), 2).alias("percentage_acceptance"))
      .orderBy("date"))
assert [(r[0], float(r[1])) for r in df.collect()] == [
    (d(1), 50.0), (d(2), 0.0), (d(3), 33.33),
]
print("[PASS] Q39 DataFrame API matches SQL")

# ------------------------------------------------ the INNER JOIN trap
inner = spark.sql("""
WITH sent AS (SELECT * FROM friend_requests WHERE action = 'sent'),
     acc  AS (SELECT DISTINCT sender_id, receiver_id FROM friend_requests WHERE action = 'accepted')
SELECT s.request_date AS date,
       ROUND(100.0 * COUNT(*) / COUNT(*), 2) AS percentage_acceptance
FROM sent s
JOIN acc a ON a.sender_id = s.receiver_id AND a.receiver_id = s.sender_id
GROUP BY s.request_date ORDER BY s.request_date
""").collect()
assert [(r[0], float(r[1])) for r in inner] == [(d(1), 100.0), (d(3), 100.0)], inner
print("[PASS] Q39 INNER JOIN loses 2026-01-02 and reports 100% everywhere")

# ------------------------------------------------ the un-reversed key trap
unreversed = spark.sql("""
WITH sent AS (SELECT * FROM friend_requests WHERE action = 'sent'),
     acc  AS (SELECT DISTINCT sender_id, receiver_id FROM friend_requests WHERE action = 'accepted')
SELECT ROUND(100.0 * SUM(CASE WHEN a.sender_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct
FROM sent s
LEFT JOIN acc a ON a.sender_id = s.sender_id AND a.receiver_id = s.receiver_id
""").collect()[0][0]
assert float(unreversed) == 0.0, unreversed
print("[PASS] Q39 matching the pair un-reversed gives 0.00 everywhere")

# ------------------------------------------------ the join-on-date trap
# The 18->19 send is accepted the NEXT day; joining on date loses it.
on_date = spark.sql("""
WITH sent AS (SELECT * FROM friend_requests WHERE action = 'sent'),
     acc  AS (SELECT DISTINCT request_date, sender_id, receiver_id
              FROM friend_requests WHERE action = 'accepted')
SELECT s.request_date AS date,
       ROUND(100.0 * SUM(CASE WHEN a.sender_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct
FROM sent s
LEFT JOIN acc a ON a.sender_id = s.receiver_id AND a.receiver_id = s.sender_id
                AND a.request_date = s.request_date
GROUP BY s.request_date ORDER BY s.request_date
""").collect()
assert [(r[0], float(r[1])) for r in on_date] == [(d(1), 50.0), (d(2), 0.0), (d(3), 0.0)], on_date
print("[PASS] Q39 joining on date drops the late acceptance (01-03 becomes 0.00, not 33.33)")

# ------------------------------------------------ accept-only dates produce no row
dates = [r[0] for r in spark.sql(SQL).collect()]
assert d(4) not in dates and len(dates) == 3, dates
print("[PASS] Q39 2026-01-04 is accept-only -- no output row for it")

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports CTEs and the LEFT JOIN + reversed-key pattern. The
# distinctness on `acc` matters: two accepted rows for the same pair would fan
# out a send and could push a rate above 100%. The 18->19 acceptance on
# 2026-01-04 belongs to the 2026-01-03 send, so the join must NOT filter on
# the accept date -- drop `request_date` from the acc projection.
#
# CREATE TABLE friend_requests (
#     request_date DATE        NOT NULL,
#     sender_id    INT         NOT NULL,
#     receiver_id  INT         NOT NULL,
#     action       VARCHAR(16) NOT NULL,
#     PRIMARY KEY (request_date, sender_id, receiver_id, action),
#     KEY ix_fr_action (action, sender_id, receiver_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO friend_requests (request_date, sender_id, receiver_id, action) VALUES
#     ('2026-01-01',  1,  2, 'sent'),
#     ('2026-01-01',  3,  4, 'sent'),
#     ('2026-01-01',  2,  1, 'accepted'),
#     ('2026-01-02', 10, 11, 'sent'),
#     ('2026-01-02', 12, 13, 'sent'),
#     ('2026-01-03', 18, 19, 'sent'),
#     ('2026-01-03', 20, 21, 'sent'),
#     ('2026-01-03', 22, 23, 'sent'),
#     ('2026-01-04', 19, 18, 'accepted');
#
# WITH sent AS (
#     SELECT request_date, sender_id, receiver_id
#     FROM friend_requests
#     WHERE action = 'sent'
# ),
# acc AS (
#     -- DISTINCT so a repeated acceptance cannot fan out a send
#     SELECT DISTINCT sender_id, receiver_id
#     FROM friend_requests
#     WHERE action = 'accepted'
# )
# SELECT s.request_date AS date,
#        ROUND(100.0 * SUM(CASE WHEN a.sender_id IS NOT NULL THEN 1 ELSE 0 END)
#                    / COUNT(*), 2) AS percentage_acceptance
# FROM sent s
# LEFT JOIN acc a
#        ON a.sender_id   = s.receiver_id
#       AND a.receiver_id = s.sender_id
# GROUP BY s.request_date
# ORDER BY s.request_date;
#
# -- Expected:
# -- 2026-01-01  50.00
# -- 2026-01-02   0.00
# -- 2026-01-03  33.33
