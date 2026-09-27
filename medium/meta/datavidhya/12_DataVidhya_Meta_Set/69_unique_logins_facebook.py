"""
Q69: Unique Logins by User on facebook.com   [Medium | Date/Time Functions]
DataVidhya slug: unique-logins-facebook

Per user, count DISTINCT DAYS with a facebook.com login. Other domains ignored.

How to Think:
- Two reductions stacked in one aggregate: filter the domain, then count
  distinct DATES (not rows, not timestamps). `COUNT(DISTINCT
  CAST(login_datetime AS DATE))` says both in one expression.
- The cast is the operative step. login_datetime is a TIMESTAMP, so two logins
  on the same day are two distinct timestamps but ONE distinct day.

The trap:
- COUNT(*) instead of COUNT(DISTINCT date). User 2 logs in twice on 2021-01-01
  (07:00 and 08:00), so rows give 3 and days give 2. That row exists precisely
  to catch this.
- COUNT(DISTINCT login_datetime) is equally wrong and looks more careful -- the
  timestamps differ, so user 2 still comes back as 3. Truncating to a DATE is
  what collapses them.
- User 1 has a linkedin.com login on 2021-01-01, a day they ALSO used Facebook.
  So forgetting the domain filter does not change user 1's answer (still 3) --
  it would only inflate a user whose only activity on some day was elsewhere.
  Verified below on a constructed row, since the shipped data cannot show it.
- Users with no Facebook logins at all should not appear; grouping the filtered
  rows handles that.

Spark note:
- `WHERE domain = 'facebook.com'` is sargable and prunes if the table is
  partitioned by domain. Casting inside COUNT(DISTINCT ...) is a per-row
  projection -- no extra shuffle.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("69-unique-logins-facebook")
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


DOMAIN = "facebook.com"

# ---------------------------------------------------------- sample data
# Exactly the rows DataVidhya ships with the question.
# User 2 logs in TWICE on 2021-01-01 -> 2 distinct days from 3 rows.
# User 1 has a linkedin login on a day they also used Facebook.
spark.sql("""
CREATE OR REPLACE TEMP VIEW login_events AS
SELECT * FROM VALUES
    (1, TIMESTAMP'2021-01-01 08:00:00', 'facebook.com'),
    (1, TIMESTAMP'2021-01-01 10:30:00', 'linkedin.com'),
    (1, TIMESTAMP'2021-01-02 08:00:00', 'facebook.com'),
    (1, TIMESTAMP'2021-01-03 09:15:00', 'facebook.com'),
    (2, TIMESTAMP'2021-01-01 07:00:00', 'facebook.com'),
    (2, TIMESTAMP'2021-01-01 08:00:00', 'facebook.com'),
    (2, TIMESTAMP'2021-01-02 07:30:00', 'facebook.com'),
    (3, TIMESTAMP'2021-01-01 09:00:00', 'facebook.com')
AS t(user_id, login_datetime, domain)
""")

from pyspark.sql import functions as F

SQL = f"""
SELECT user_id,
       COUNT(DISTINCT CAST(login_datetime AS DATE)) AS unique_login_days
FROM login_events
WHERE domain = '{DOMAIN}'
GROUP BY user_id
ORDER BY user_id
"""

spark.sql(SQL).show(truncate=False)

expect("Q69 distinct Facebook login days", SQL, [(1, 3), (2, 2), (3, 1)])

# DataFrame API equivalent.
df = (spark.table("login_events")
      .filter(F.col("domain") == DOMAIN)
      .groupBy("user_id")
      .agg(F.countDistinct(F.to_date("login_datetime")).alias("unique_login_days"))
      .orderBy("user_id"))
assert [tuple(r) for r in df.collect()] == [(1, 3), (2, 2), (3, 1)]
print("[PASS] Q69 DataFrame API matches SQL")

# ------------------------------------------------ rows vs timestamps vs days
variants = spark.sql(f"""
SELECT user_id,
       COUNT(*)                                     AS rows,
       COUNT(DISTINCT login_datetime)               AS distinct_timestamps,
       COUNT(DISTINCT CAST(login_datetime AS DATE)) AS distinct_days
FROM login_events WHERE domain = '{DOMAIN}'
GROUP BY user_id ORDER BY user_id
""").collect()
assert [(r[0], r[1], r[2], r[3]) for r in variants] == [
    (1, 3, 3, 3), (2, 3, 3, 2), (3, 1, 1, 1),
], variants
print("[PASS] Q69 user 2: 3 rows, 3 distinct timestamps, but only 2 distinct DAYS")

# ------------------------------------------------ the domain filter
# On the shipped data user 1's linkedin login lands on a day they also used
# Facebook, so dropping the filter changes nothing -- it is a silent bug here.
unfiltered = spark.sql("""
SELECT user_id, COUNT(DISTINCT CAST(login_datetime AS DATE)) AS days
FROM login_events GROUP BY user_id ORDER BY user_id
""").collect()
assert [(r[0], r[1]) for r in unfiltered] == [(1, 3), (2, 2), (3, 1)], unfiltered
print("[PASS] Q69 dropping the domain filter coincidentally agrees on this data")

# A linkedin-only day makes the bug visible.
spark.sql("""
CREATE OR REPLACE TEMP VIEW login_events AS
SELECT * FROM VALUES
    (1, TIMESTAMP'2021-01-01 08:00:00', 'facebook.com'),
    (1, TIMESTAMP'2021-01-05 10:30:00', 'linkedin.com'),
    (4, TIMESTAMP'2021-01-07 10:30:00', 'linkedin.com')
AS t(user_id, login_datetime, domain)
""")
expect("Q69 linkedin-only days and users are excluded", SQL, [(1, 1)])

leaky = spark.sql("""
SELECT user_id, COUNT(DISTINCT CAST(login_datetime AS DATE)) AS days
FROM login_events GROUP BY user_id ORDER BY user_id
""").collect()
assert [(r[0], r[1]) for r in leaky] == [(1, 2), (4, 1)], leaky
print("[PASS] Q69 without the filter, user 1 inflates to 2 days and user 4 appears")
