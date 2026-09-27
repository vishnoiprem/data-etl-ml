"""
Q28: Handle Data Skew in Joins   [Hard | Inner Joins, Data Skew, Optimization, Partitioning]
DataVidhya slug: handle-data-skew-joins

Join events to users, keep only matched events, and summarize engagement per
account_type: total_events, unique_users, events_per_user.

How to Think:
- The query itself is an inner join plus a GROUP BY. What makes this "Hard" is
  that the interviewer wants the SKEW conversation, not the SQL.
- Two different counts in one aggregate: COUNT(*) counts matched EVENTS,
  COUNT(DISTINCT user_id) counts USERS. Mixing them up is the whole question.
- Narrate the grain out loud: "one output row = one account_type."

The trap:
- Event 11 belongs to user 99, who is absent from `users`. INNER JOIN drops it,
  and it must not appear in any total. A LEFT JOIN would keep it and produce a
  NULL account_type bucket -- the answer the question is screening for.
- `events_per_user` is total_events / unique_users, NOT AVG of a per-user
  count. They agree only when every user has the same event count; here
  Premium is 3+2+2 events over 3 users, so 7/3 = 2.33.
- Integer division: in Spark `COUNT(*) / COUNT(DISTINCT ...)` is fine because
  `/` promotes to double, but in Presto/Hive with integer operands this returns
  2, not 2.33. Multiply by 1.0 if you are unsure which engine you are on.

Spark note (the actual point of the question):
- "A handful of power users generate a disproportionate share of events" is a
  skewed join key. Three mitigations, in the order you should offer them:
    1. BROADCAST the small side. `users` is a dimension -- broadcast it and the
       join stops shuffling entirely, so skew becomes irrelevant. This is the
       right answer here and should be said first.
    2. Adaptive Query Execution: `spark.sql.adaptive.enabled` plus
       `adaptive.skewJoin.enabled` splits oversized partitions at runtime.
    3. Salting: append a random bucket to the hot key on the fact side and
       explode the dim side by the same bucket count. Only reach for this when
       the dim is too large to broadcast -- it is the most code and the most
       ways to get wrong.
- Pre-aggregating events per user BEFORE the join also shrinks the skewed side,
  and works here because both metrics are derivable from a per-user count.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("28-data-skew-joins")
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
# Note event 11 -> user 99, who is NOT in `users`. That row must be dropped.
spark.createDataFrame(
    [
        (1, 1, "purchase", "2024-01-05"),
        (2, 1, "view", "2024-01-06"),
        (3, 1, "click", "2024-01-09"),
        (4, 4, "view", "2024-01-11"),
        (5, 4, "share", "2024-01-12"),
        (6, 7, "purchase", "2024-01-14"),
        (7, 7, "view", "2024-01-18"),
        (8, 2, "click", "2024-01-08"),
        (9, 2, "purchase", "2024-01-15"),
        (10, 3, "view", "2024-01-20"),
        (11, 99, "click", "2024-01-22"),
    ],
    ["event_id", "user_id", "event_type", "event_date"],
).createOrReplaceTempView("events")

spark.createDataFrame(
    [
        (1, "User_1", "Premium"),
        (2, "User_2", "Basic"),
        (3, "User_3", "Standard"),
        (4, "User_4", "Premium"),
        (7, "User_7", "Premium"),
    ],
    ["user_id", "user_name", "account_type"],
).createOrReplaceTempView("users")

from pyspark.sql import functions as F

SQL = """
SELECT u.account_type,
       COUNT(*)                      AS total_events,
       COUNT(DISTINCT e.user_id)     AS unique_users,
       ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT e.user_id), 2) AS events_per_user
FROM events e
JOIN users u ON e.user_id = u.user_id
GROUP BY u.account_type
ORDER BY total_events DESC
"""

spark.sql(SQL).show(truncate=False)

expect("Q28 engagement by account type", SQL, [
    ("Premium", 7, 3, 2.33),
    ("Basic", 2, 1, 2.00),
    ("Standard", 1, 1, 1.00),
])

# DataFrame API equivalent, with the broadcast hint that makes skew moot.
df = (spark.table("events").alias("e")
      .join(F.broadcast(spark.table("users").alias("u")), "user_id", "inner")
      .groupBy("account_type")
      .agg(F.count(F.lit(1)).alias("total_events"),
           F.countDistinct("user_id").alias("unique_users"))
      .withColumn("events_per_user",
                  F.round(F.col("total_events") * 1.0 / F.col("unique_users"), 2))
      .orderBy(F.col("total_events").desc()))
assert [(r[0], r[1], r[2], float(r[3])) for r in df.collect()] == [
    ("Premium", 7, 3, 2.33),
    ("Basic", 2, 1, 2.0),
    ("Standard", 1, 1, 1.0),
]
print("[PASS] Q28 DataFrame API matches SQL")

# The dropped-row trap, asserted so it stays documented: user 99 has an event
# but no `users` row, so INNER JOIN must yield 10 matched events, not 11.
matched = spark.sql("""
SELECT COUNT(*) FROM events e JOIN users u ON e.user_id = u.user_id
""").collect()[0][0]
total = spark.sql("SELECT COUNT(*) FROM events").collect()[0][0]
assert (matched, total) == (10, 11), f"expected 10 of 11 events to match, got {matched} of {total}"
print("[PASS] Q28 unmatched event (user 99) dropped by INNER JOIN")

# Pre-aggregating the skewed side gives the same answer with a smaller shuffle.
SQL_PREAGG = """
WITH per_user AS (
    SELECT user_id, COUNT(*) AS events
    FROM events
    GROUP BY user_id
)
SELECT u.account_type,
       SUM(p.events)                 AS total_events,
       COUNT(*)                      AS unique_users,
       ROUND(SUM(p.events) * 1.0 / COUNT(*), 2) AS events_per_user
FROM per_user p
JOIN users u ON p.user_id = u.user_id
GROUP BY u.account_type
ORDER BY total_events DESC
"""
expect("Q28 pre-aggregated variant agrees", SQL_PREAGG, [
    ("Premium", 7, 3, 2.33),
    ("Basic", 2, 1, 2.00),
    ("Standard", 1, 1, 1.00),
])