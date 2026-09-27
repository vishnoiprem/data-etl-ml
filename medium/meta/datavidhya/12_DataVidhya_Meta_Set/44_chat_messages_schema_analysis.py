"""
Q44: Chat Messages Schema Analysis   [Medium | Aggregate Functions]
DataVidhya slug: chat-messages-schema-analysis

Per conversation with at least one message: message_count, unique_senders,
first_message and last_message as FORMATTED TEXT, and avg_messages_per_day =
message_count / distinct one-hour windows, to 1dp.

How to Think:
- Everything needed lives in `messages`. The `conversations` table is a decoy --
  it contributes no output column, and touching it is how conversation 3
  (which has no messages) leaks into the result.
- Four aggregates, one GROUP BY. The only non-obvious one is the denominator of
  avg_messages_per_day: COUNT(DISTINCT date_trunc('HOUR', sent_at)) -- truncate
  first, then count distinct, so several messages in the same hour collapse to
  one window.
- Read the column name sceptically: `avg_messages_per_day` is defined over
  HOUR windows, so it is messages per active hour, not per day. Say so out loud
  and then implement the spec as written -- flagging a misleading metric name is
  product signal; silently "fixing" it fails the test.

The trap:
- Conversation 3 has no messages and must be ABSENT. Starting from
  `conversations LEFT JOIN messages` yields a phantom row with count 0. Grouping
  `messages` alone gives the inner semantics for free.
- first_message/last_message must be TEXT in 'yyyy-MM-dd HH:mm:ss'. Returning
  the raw TIMESTAMP is a type mismatch, and Spark's default rendering has no
  guaranteed zero-padded seconds.
- Spark's format pattern is 'HH:mm:ss' (Java), NOT the spec's Postgres-style
  'HH24:MI:SS'. Passing HH24/MI to date_format raises or misformats -- translate
  the pattern, do not copy it.
- Distinct HOURS, not distinct DAYS and not distinct timestamps. Conversation 1's
  00:00 and 00:30 are ONE window: 3 / 2 = 1.5. Counting distinct timestamps gives
  3/3 = 1.0, which is exactly what conversation 2 legitimately returns -- so the
  bug hides behind a plausible number.
- Round to 1 decimal place, so 1.0 not 1.00.

Spark note:
- One shuffle on conversation_id. date_trunc inside COUNT(DISTINCT ...) is a
  per-row projection, so it costs nothing extra.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("44-chat-messages-schema-analysis")
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
# Conversation 3 has NO messages. Sender 108 sends two of conversation 1's
# three messages, and 00:00 + 00:30 share one hour window.
spark.sql("""
CREATE OR REPLACE TEMP VIEW conversations AS
SELECT * FROM VALUES
    (1, DATE'2023-01-01', 4),
    (2, DATE'2023-01-02', 3),
    (3, DATE'2023-01-03', 5)
AS t(conversation_id, created_at, participant_count)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW messages AS
SELECT * FROM VALUES
    (1, 1, 108, 'msg', TIMESTAMP'2023-01-01 00:00:00'),
    (2, 1, 104, 'msg', TIMESTAMP'2023-01-01 00:30:00'),
    (3, 1, 108, 'msg', TIMESTAMP'2023-01-01 01:00:00'),
    (6, 2, 107, 'msg', TIMESTAMP'2023-01-01 05:00:00'),
    (7, 2, 106, 'msg', TIMESTAMP'2023-01-01 06:00:00')
AS t(message_id, conversation_id, sender_id, message_text, sent_at)
""")

from pyspark.sql import functions as F

# Group `messages` only -- `conversations` is not needed and would leak conv 3.
# Spark's format pattern is Java's 'HH:mm:ss', not Postgres' 'HH24:MI:SS'.
SQL = """
SELECT conversation_id,
       COUNT(*)                                             AS message_count,
       COUNT(DISTINCT sender_id)                            AS unique_senders,
       DATE_FORMAT(MIN(sent_at), 'yyyy-MM-dd HH:mm:ss')     AS first_message,
       DATE_FORMAT(MAX(sent_at), 'yyyy-MM-dd HH:mm:ss')     AS last_message,
       ROUND(COUNT(*) / COUNT(DISTINCT DATE_TRUNC('HOUR', sent_at)), 1) AS avg_messages_per_day
FROM messages
GROUP BY conversation_id
ORDER BY conversation_id
"""

spark.sql(SQL).show(truncate=False)

EXPECTED = [
    (1, 3, 2, "2023-01-01 00:00:00", "2023-01-01 01:00:00", 1.5),
    (2, 2, 2, "2023-01-01 05:00:00", "2023-01-01 06:00:00", 1.0),
]
expect("Q44 per-conversation activity summary", SQL, EXPECTED)

# DataFrame API equivalent.
df = (spark.table("messages")
      .groupBy("conversation_id")
      .agg(F.count(F.lit(1)).alias("message_count"),
           F.countDistinct("sender_id").alias("unique_senders"),
           F.date_format(F.min("sent_at"), "yyyy-MM-dd HH:mm:ss").alias("first_message"),
           F.date_format(F.max("sent_at"), "yyyy-MM-dd HH:mm:ss").alias("last_message"),
           F.countDistinct(F.date_trunc("HOUR", F.col("sent_at"))).alias("hour_windows"),
           F.count(F.lit(1)).alias("_n"))
      .withColumn("avg_messages_per_day", F.round(F.col("_n") / F.col("hour_windows"), 1))
      .select("conversation_id", "message_count", "unique_senders",
              "first_message", "last_message", "avg_messages_per_day")
      .orderBy("conversation_id"))
assert [tuple(r) for r in df.collect()] == EXPECTED
print("[PASS] Q44 DataFrame API matches SQL")

# ------------------------------------------------ the empty-conversation trap
ids = [r[0] for r in spark.sql(SQL).collect()]
assert ids == [1, 2] and spark.table("conversations").count() == 3
left_joined = spark.sql("""
SELECT c.conversation_id, COUNT(m.message_id) AS message_count
FROM conversations c LEFT JOIN messages m ON m.conversation_id = c.conversation_id
GROUP BY c.conversation_id ORDER BY c.conversation_id
""").collect()
assert [(r[0], r[1]) for r in left_joined] == [(1, 3), (2, 2), (3, 0)], left_joined
print("[PASS] Q44 LEFT JOIN from conversations invents a row for conv 3 with count 0")

# ------------------------------------------------ hours, not timestamps
windows = spark.sql("""
SELECT conversation_id,
       COUNT(DISTINCT DATE_TRUNC('HOUR', sent_at)) AS hour_windows,
       COUNT(DISTINCT sent_at)                     AS distinct_timestamps
FROM messages GROUP BY conversation_id ORDER BY conversation_id
""").collect()
assert [(r[0], r[1], r[2]) for r in windows] == [(1, 2, 3), (2, 2, 2)], windows
print("[PASS] Q44 conv 1 has 2 hour windows but 3 distinct timestamps -> 1.5, not 1.0")

# ------------------------------------------------ the format-pattern trap
# 'HH24:MI:SS' is Postgres syntax; Spark needs Java's 'HH:mm:ss'.
try:
    bad = spark.sql("""
    SELECT DATE_FORMAT(TIMESTAMP'2023-01-01 13:05:09', 'YYYY-MM-DD HH24:MI:SS') AS s
    """).collect()[0][0]
    assert bad != "2023-01-01 13:05:09", f"Postgres pattern unexpectedly worked: {bad}"
    print(f"[PASS] Q44 Postgres pattern renders wrong in Spark: {bad!r}")
except Exception as e:
    assert type(e).__name__ != "AssertionError", e
    print("[PASS] Q44 Spark rejects the Postgres 'HH24:MI:SS' pattern outright")

good = spark.sql("""
SELECT DATE_FORMAT(TIMESTAMP'2023-01-01 13:05:09', 'yyyy-MM-dd HH:mm:ss') AS s
""").collect()[0][0]
assert good == "2023-01-01 13:05:09", good
print("[PASS] Q44 Java pattern 'yyyy-MM-dd HH:mm:ss' produces the required text")
