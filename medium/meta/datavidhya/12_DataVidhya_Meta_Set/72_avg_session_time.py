"""
Q72: Users by Average Session Time   [Medium | Date/Time Functions, Aggregate Functions]
DataVidhya slug: aggregation-users-avg-session-time

A session runs from a page_load to the VERY NEXT page_exit for the same user on
the same calendar day. Report each user's average session length in minutes.

How to Think:
- "The very next exit" is a LEAD/next-value problem, not a join. Put loads and
  exits in one ordered stream per (user, day) and ask each load for the next
  exit time:
      MIN(exit_time) OVER (PARTITION BY user, day ORDER BY time
                           ROWS BETWEEN 1 FOLLOWING AND UNBOUNDED FOLLOWING)
  where exit_time is the timestamp on exit rows and NULL on load rows. MIN
  skips NULLs, so this reads "the earliest exit strictly after me."
- Then filter to load rows with a non-null pairing, take the difference in
  seconds, and average / 60.
- Grain ladder, say it out loud: event -> session -> user.

The trap:
- JOINING loads to exits on (user, day) pairs EVERY load with EVERY exit. User
  1 has 2 loads and 2 exits on Jan 1, so a join yields 4 candidate pairs, and
  taking MIN(exit) per load would pair BOTH loads with the 10:15 exit -- the
  second session becomes negative (10:20 -> 10:15). The "strictly after"
  condition is what makes it correct, and once you add it you are back to the
  window formulation anyway.
- Sessions never cross midnight: the partition must include event_date. Without
  it, Jan 1's last load would pair with Jan 2's first exit.
- An unmatched page_load contributes NOTHING -- it is not a zero-length session.
  Averaging with a 0 in the list would drag the mean down; the row must be
  dropped. Likewise a user with no complete session must not appear at all.
- Average of SESSIONS, not of days. User 1 has 15, 15, 20 -> 50/3 = 16.67.
  Averaging the two DAYS (15 mean on Jan 1, 20 on Jan 2) gives 17.5.
- Divide by 60.0, not 60 -- integer seconds / 60 truncates.

Spark note:
- One shuffle on (user_id, event_date). The window replaces what would
  otherwise be a self-join with an inequality predicate -- far cheaper.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("72-avg-session-time")
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
# Two sessions on Jan 1 (15 min each) and one on Jan 2 (20 min) -> 16.67.
spark.sql("""
CREATE OR REPLACE TEMP VIEW web_log AS
SELECT * FROM VALUES
    (1, 'page_load', DATE'2024-01-01', TIMESTAMP'2024-01-01 10:00:00'),
    (1, 'page_exit', DATE'2024-01-01', TIMESTAMP'2024-01-01 10:15:00'),
    (1, 'page_load', DATE'2024-01-01', TIMESTAMP'2024-01-01 10:20:00'),
    (1, 'page_exit', DATE'2024-01-01', TIMESTAMP'2024-01-01 10:35:00'),
    (1, 'page_load', DATE'2024-01-02', TIMESTAMP'2024-01-02 09:00:00'),
    (1, 'page_exit', DATE'2024-01-02', TIMESTAMP'2024-01-02 09:20:00')
AS t(user_id, event_type, event_date, event_time)
""")

from pyspark.sql import functions as F, Window as W

# "The earliest exit strictly after this load", per user AND day.
SQL = """
WITH paired AS (
    SELECT user_id,
           event_type,
           event_time,
           MIN(CASE WHEN event_type = 'page_exit' THEN event_time END) OVER (
               PARTITION BY user_id, event_date            -- never cross midnight
               ORDER BY event_time
               ROWS BETWEEN 1 FOLLOWING AND UNBOUNDED FOLLOWING
           ) AS next_exit
    FROM web_log
),
sessions AS (
    SELECT user_id,
           (UNIX_TIMESTAMP(next_exit) - UNIX_TIMESTAMP(event_time)) / 60.0 AS minutes
    FROM paired
    WHERE event_type = 'page_load'
      AND next_exit IS NOT NULL          -- unmatched load contributes nothing
)
SELECT user_id,
       ROUND(AVG(minutes), 2) AS avg_session_minutes
FROM sessions
GROUP BY user_id
ORDER BY user_id
"""

spark.sql(SQL).show(truncate=False)

expect("Q72 average session minutes", SQL, [(1, 16.67)])

# DataFrame API equivalent.
w = (W.partitionBy("user_id", "event_date").orderBy("event_time")
     .rowsBetween(1, W.unboundedFollowing))
paired = spark.table("web_log").withColumn(
    "next_exit",
    F.min(F.when(F.col("event_type") == "page_exit", F.col("event_time"))).over(w))
df = (paired.filter((F.col("event_type") == "page_load") & F.col("next_exit").isNotNull())
      .withColumn("minutes",
                  (F.unix_timestamp("next_exit") - F.unix_timestamp("event_time")) / F.lit(60.0))
      .groupBy("user_id")
      .agg(F.round(F.avg("minutes"), 2).alias("avg_session_minutes"))
      .orderBy("user_id"))
assert [(r[0], float(r[1])) for r in df.collect()] == [(1, 16.67)]
print("[PASS] Q72 DataFrame API matches SQL")

# ------------------------------------------------ show the individual sessions
durations = spark.sql("""
WITH paired AS (
    SELECT user_id, event_type, event_time,
           MIN(CASE WHEN event_type = 'page_exit' THEN event_time END) OVER (
               PARTITION BY user_id, event_date ORDER BY event_time
               ROWS BETWEEN 1 FOLLOWING AND UNBOUNDED FOLLOWING) AS next_exit
    FROM web_log
)
SELECT (UNIX_TIMESTAMP(next_exit) - UNIX_TIMESTAMP(event_time)) / 60.0 AS m
FROM paired WHERE event_type = 'page_load' AND next_exit IS NOT NULL
ORDER BY event_time
""").collect()
mins = [float(r[0]) for r in durations]
assert mins == [15.0, 15.0, 20.0], mins
assert round(sum(mins) / len(mins), 2) == 16.67
print(f"[PASS] Q72 sessions are {mins} -> 50/3 = 16.67")

# ------------------------------------------------ average of sessions, not days
per_day = spark.sql("""
WITH paired AS (
    SELECT user_id, event_date, event_type, event_time,
           MIN(CASE WHEN event_type = 'page_exit' THEN event_time END) OVER (
               PARTITION BY user_id, event_date ORDER BY event_time
               ROWS BETWEEN 1 FOLLOWING AND UNBOUNDED FOLLOWING) AS next_exit
    FROM web_log
), s AS (
    SELECT user_id, event_date,
           (UNIX_TIMESTAMP(next_exit) - UNIX_TIMESTAMP(event_time)) / 60.0 AS m
    FROM paired WHERE event_type = 'page_load' AND next_exit IS NOT NULL
), daily AS (
    SELECT user_id, event_date, AVG(m) AS day_avg FROM s GROUP BY user_id, event_date
)
SELECT ROUND(AVG(day_avg), 2) FROM daily GROUP BY user_id
""").collect()[0][0]
assert float(per_day) == 17.5, per_day
print("[PASS] Q72 averaging DAYS first gives 17.50 -- the spec averages SESSIONS (16.67)")

# ------------------------------------------------ the fan-out trap
# 2 loads x 2 exits on Jan 1 = 4 candidate pairs, and the naive MIN pairs the
# 10:20 load with the 10:15 exit -> a NEGATIVE session.
naive = spark.sql("""
SELECT l.event_time AS load_at, MIN(x.event_time) AS paired_exit,
       (UNIX_TIMESTAMP(MIN(x.event_time)) - UNIX_TIMESTAMP(l.event_time)) / 60.0 AS m
FROM web_log l
JOIN web_log x ON x.user_id = l.user_id AND x.event_date = l.event_date
              AND x.event_type = 'page_exit'
WHERE l.event_type = 'page_load' AND l.event_date = DATE'2024-01-01'
GROUP BY l.event_time ORDER BY l.event_time
""").collect()
assert [float(r[2]) for r in naive] == [15.0, -5.0], [float(r[2]) for r in naive]
print("[PASS] Q72 pairing without 'strictly after' yields a -5.0 minute session")

# ------------------------------------------------ the midnight trap
# Drop Jan 1's exit. Without event_date in the partition, Jan 1's 10:00 load
# would pair with Jan 2's 09:20 exit -- a 1400-minute session.
spark.sql("""
CREATE OR REPLACE TEMP VIEW web_log AS
SELECT * FROM VALUES
    (1, 'page_load', DATE'2024-01-01', TIMESTAMP'2024-01-01 10:00:00'),
    (1, 'page_load', DATE'2024-01-02', TIMESTAMP'2024-01-02 09:00:00'),
    (1, 'page_exit', DATE'2024-01-02', TIMESTAMP'2024-01-02 09:20:00')
AS t(user_id, event_type, event_date, event_time)
""")
expect("Q72 sessions never cross midnight", SQL, [(1, 20.0)])

no_date_partition = spark.sql("""
WITH paired AS (
    SELECT user_id, event_type, event_time,
           MIN(CASE WHEN event_type = 'page_exit' THEN event_time END) OVER (
               PARTITION BY user_id ORDER BY event_time
               ROWS BETWEEN 1 FOLLOWING AND UNBOUNDED FOLLOWING) AS next_exit
    FROM web_log
)
SELECT ROUND(AVG((UNIX_TIMESTAMP(next_exit) - UNIX_TIMESTAMP(event_time)) / 60.0), 2)
FROM paired WHERE event_type = 'page_load' AND next_exit IS NOT NULL
""").collect()[0][0]
assert float(no_date_partition) == 710.0, no_date_partition
print("[PASS] Q72 omitting event_date from the partition averages in a "
      "1400-minute overnight session (710.0)")

# ------------------------------------------------ users with no session vanish
spark.sql("""
CREATE OR REPLACE TEMP VIEW web_log AS
SELECT * FROM VALUES
    (7, 'page_load', DATE'2024-01-01', TIMESTAMP'2024-01-01 10:00:00'),
    (8, 'page_exit', DATE'2024-01-01', TIMESTAMP'2024-01-01 11:00:00')
AS t(user_id, event_type, event_date, event_time)
""")
expect("Q72 a lone load and a lone exit produce no rows at all", SQL, [])

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports window frames including ROWS BETWEEN ... FOLLOWING
# and UNIX_TIMESTAMP, so the same window pattern works verbatim. The
# partition must still include event_date or sessions will cross midnight.
#
# CREATE TABLE web_log (
#     user_id    INT       NOT NULL,
#     event_type ENUM('page_load','page_exit') NOT NULL,
#     event_date DATE      NOT NULL,
#     event_time TIMESTAMP NOT NULL,
#     KEY ix_wl_user_day (user_id, event_date, event_time)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO web_log (user_id, event_type, event_date, event_time) VALUES
#     (1, 'page_load', '2024-01-01', '2024-01-01 10:00:00'),
#     (1, 'page_exit', '2024-01-01', '2024-01-01 10:15:00'),
#     (1, 'page_load', '2024-01-01', '2024-01-01 10:20:00'),
#     (1, 'page_exit', '2024-01-01', '2024-01-01 10:35:00'),
#     (1, 'page_load', '2024-01-02', '2024-01-02 09:00:00'),
#     (1, 'page_exit', '2024-01-02', '2024-01-02 09:20:00');
#
# WITH paired AS (
#     SELECT user_id, event_type, event_time,
#            MIN(CASE WHEN event_type = 'page_exit' THEN event_time END) OVER (
#                PARTITION BY user_id, event_date
#                ORDER BY event_time
#                ROWS BETWEEN 1 FOLLOWING AND UNBOUNDED FOLLOWING
#            ) AS next_exit
#     FROM web_log
# ),
# sessions AS (
#     SELECT user_id,
#            (UNIX_TIMESTAMP(next_exit) - UNIX_TIMESTAMP(event_time)) / 60.0 AS minutes
#     FROM paired
#     WHERE event_type = 'page_load' AND next_exit IS NOT NULL
# )
# SELECT user_id, ROUND(AVG(minutes), 2) AS avg_session_minutes
# FROM sessions
# GROUP BY user_id
# ORDER BY user_id;
#
# -- Expected: (1, 16.67).
