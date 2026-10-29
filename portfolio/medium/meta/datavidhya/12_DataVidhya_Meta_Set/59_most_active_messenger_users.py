"""
Q59: Most Active Users On Messenger   [Medium | Window Functions, Aggregate Functions]
DataVidhya slug: most-active-users-on-messenger

message_count = messages where the user is sender OR receiver. Rank descending
with ties sharing a rank. Only users who participate in a message appear.

How to Think:
- "Sender OR receiver" means each message contributes to TWO users. So UNPIVOT
  first: UNION ALL the sender column and the receiver column into one
  participant stream, then GROUP BY. That is the whole trick -- once the data is
  in participant form, the rest is COUNT + RANK.
- UNION ALL, not UNION. UNION would dedupe (user, message) pairs, which matters
  the moment someone messages themselves.
- Only participants appear, so INNER JOIN to `users` for the name.

The trap:
- An OR in the join condition (`ON u.user_id = m.sender_id OR u.user_id =
  m.receiver_id`) is the obvious-looking answer. It gets the right count here
  but Spark cannot hash an OR-join, so it degrades to a broadcast nested loop --
  O(users x messages). The UNION ALL rewrite is the performance answer, and
  saying that out loud is the point of a "most active users" question.
- Ties share a rank -> RANK or DENSE_RANK, not ROW_NUMBER. Charlie and David
  both have 1 message and must both be rank 3.
- RANK vs DENSE_RANK: counts here are 4, 2, 1, 1 -- consecutive, so both give
  1, 2, 3, 3 and the sample CANNOT tell them apart. Add a gap in the counts and
  they diverge; asserted below. The spec says only "tied users share a rank",
  which RANK satisfies, so RANK is the safe reading.
- Alice's count is 4, not 3: she sent messages 1, 2, 4 and RECEIVED message 3.
  Counting only sender rows gives 3.
- Sort by activity_rank then user_id -- not by message_count.

Spark note:
- UNION ALL then one shuffle on participant id. `users` broadcasts. The OR-join
  version shuffles nothing but scans the cross product -- far worse at scale.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("59-most-active-messenger-users")
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
# Alice (1) sends 1, 2, 4 and RECEIVES 3 -> count 4.
spark.sql("""
CREATE OR REPLACE TEMP VIEW messages AS
SELECT * FROM VALUES
    (1, 1, 2, DATE'2023-01-15'),
    (2, 1, 3, DATE'2023-01-20'),
    (3, 2, 1, DATE'2023-02-10'),
    (4, 1, 4, DATE'2023-02-22')
AS t(message_id, sender_id, receiver_id, message_date)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW users AS
SELECT * FROM VALUES
    (1, 'alice'), (2, 'bob'), (3, 'charlie'), (4, 'david')
AS t(user_id, username)
""")

from pyspark.sql import functions as F, Window as W

# UNION ALL to a participant stream -- avoids an unhashable OR-join.
SQL = """
WITH participants AS (
    SELECT sender_id   AS user_id FROM messages
    UNION ALL
    SELECT receiver_id AS user_id FROM messages
),
counted AS (
    SELECT user_id, COUNT(*) AS message_count
    FROM participants
    GROUP BY user_id
)
SELECT c.user_id,
       u.username,
       c.message_count,
       RANK() OVER (ORDER BY c.message_count DESC) AS activity_rank
FROM counted c
JOIN users u ON u.user_id = c.user_id
ORDER BY activity_rank, c.user_id
"""

spark.sql(SQL).show(truncate=False)

EXPECTED = [
    (1, "alice",   4, 1),
    (2, "bob",     2, 2),
    (3, "charlie", 1, 3),
    (4, "david",   1, 3),
]
expect("Q59 messenger activity ranking", SQL, EXPECTED)

# DataFrame API equivalent.
msgs = spark.table("messages")
participants = (msgs.select(F.col("sender_id").alias("user_id"))
                .unionAll(msgs.select(F.col("receiver_id").alias("user_id"))))
df = (participants.groupBy("user_id").agg(F.count(F.lit(1)).alias("message_count"))
      .join(F.broadcast(spark.table("users")), "user_id")
      .withColumn("activity_rank",
                  F.rank().over(W.orderBy(F.col("message_count").desc())))
      .select("user_id", "username", "message_count", "activity_rank")
      .orderBy("activity_rank", "user_id"))
assert [tuple(r) for r in df.collect()] == EXPECTED
print("[PASS] Q59 DataFrame API matches SQL")

# ------------------------------------------------ sender-only undercounts
sender_only = spark.sql("""
SELECT sender_id AS user_id, COUNT(*) AS c FROM messages GROUP BY sender_id ORDER BY sender_id
""").collect()
assert [(r[0], r[1]) for r in sender_only] == [(1, 3), (2, 1)], sender_only
print("[PASS] Q59 counting senders only gives alice 3 (not 4) and loses charlie/david")

# ------------------------------------------------ the OR-join gives the same numbers
or_join = spark.sql("""
SELECT u.user_id, COUNT(*) AS message_count
FROM users u
JOIN messages m ON u.user_id = m.sender_id OR u.user_id = m.receiver_id
GROUP BY u.user_id ORDER BY u.user_id
""").collect()
assert [(r[0], r[1]) for r in or_join] == [(1, 4), (2, 2), (3, 1), (4, 1)], or_join
plan = spark.sql("""
EXPLAIN SELECT u.user_id FROM users u
JOIN messages m ON u.user_id = m.sender_id OR u.user_id = m.receiver_id
""").collect()[0][0]
assert "NestedLoop" in plan or "Cartesian" in plan, plan[:400]
print("[PASS] Q59 the OR-join is correct but plans as a nested loop, not a hash join")

# ------------------------------------------------ ROW_NUMBER breaks the tie
row_num = spark.sql("""
WITH participants AS (
    SELECT sender_id AS user_id FROM messages
    UNION ALL SELECT receiver_id FROM messages
), counted AS (SELECT user_id, COUNT(*) AS mc FROM participants GROUP BY user_id)
SELECT user_id, mc, ROW_NUMBER() OVER (ORDER BY mc DESC, user_id) AS rn
FROM counted ORDER BY rn
""").collect()
assert [(r[0], r[2]) for r in row_num] == [(1, 1), (2, 2), (3, 3), (4, 4)], row_num
print("[PASS] Q59 ROW_NUMBER gives david rank 4 -- ties must share rank 3")

# ------------------------------------------------ RANK vs DENSE_RANK need a gap
# Shipped counts (4,2,1,1) are consecutive, so both functions agree. Insert a
# gap and they diverge.
spark.sql("""
CREATE OR REPLACE TEMP VIEW messages AS
SELECT * FROM VALUES
    (1, 1, 2, DATE'2023-01-15'),
    (2, 1, 2, DATE'2023-01-16'),
    (3, 1, 2, DATE'2023-01-17'),
    (4, 3, 4, DATE'2023-02-10')
AS t(message_id, sender_id, receiver_id, message_date)
""")
gapped = spark.sql("""
WITH participants AS (
    SELECT sender_id AS user_id FROM messages
    UNION ALL SELECT receiver_id FROM messages
), counted AS (SELECT user_id, COUNT(*) AS mc FROM participants GROUP BY user_id)
SELECT user_id, mc,
       RANK()       OVER (ORDER BY mc DESC) AS rnk,
       DENSE_RANK() OVER (ORDER BY mc DESC) AS dense
FROM counted ORDER BY mc DESC, user_id
""").collect()
assert [(r[0], r[1], r[2], r[3]) for r in gapped] == [
    (1, 3, 1, 1), (2, 3, 1, 1), (3, 1, 3, 2), (4, 1, 3, 2),
], gapped
print("[PASS] Q59 with a count gap, RANK gives 1,1,3,3 and DENSE_RANK gives 1,1,2,2")

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports the same UNION ALL into a participant stream and
# RANK() OVER (ORDER BY ...). The OR-join workaround is portable too but
# the optimizer cannot use a hash join on an OR predicate.
#
# CREATE TABLE users (
#     user_id  INT         NOT NULL,
#     username VARCHAR(32) NOT NULL,
#     PRIMARY KEY (user_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE messages (
#     message_id   INT       NOT NULL,
#     sender_id    INT       NOT NULL,
#     receiver_id  INT       NOT NULL,
#     message_date DATE      NOT NULL,
#     PRIMARY KEY (message_id),
#     KEY ix_msg_sender   (sender_id),
#     KEY ix_msg_receiver (receiver_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO users (user_id, username) VALUES
#     (1, 'alice'), (2, 'bob'), (3, 'charlie'), (4, 'david');
#
# INSERT INTO messages (message_id, sender_id, receiver_id, message_date) VALUES
#     (1, 1, 2, '2023-01-15'),
#     (2, 1, 3, '2023-01-20'),
#     (3, 2, 1, '2023-02-10'),
#     (4, 1, 4, '2023-02-22');
#
# WITH participants AS (
#     SELECT sender_id   AS user_id FROM messages
#     UNION ALL
#     SELECT receiver_id AS user_id FROM messages
# ),
# counted AS (
#     SELECT user_id, COUNT(*) AS message_count
#     FROM participants
#     GROUP BY user_id
# )
# SELECT c.user_id, u.username, c.message_count,
#        RANK() OVER (ORDER BY c.message_count DESC) AS activity_rank
# FROM counted c
# JOIN users u ON u.user_id = c.user_id
# ORDER BY activity_rank, c.user_id;
#
# -- Expected:
# -- (1, 'alice',   4, 1)
# -- (2, 'bob',     2, 2)
# -- (3, 'charlie', 1, 3)
# -- (4, 'david',   1, 3)
