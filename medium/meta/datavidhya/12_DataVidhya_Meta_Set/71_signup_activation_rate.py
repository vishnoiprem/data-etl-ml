"""
Q71: User Signup Activation Rate   [Medium | Casting, Inner Joins, Aggregate Functions]
DataVidhya slug: user-signup-activation-rate

confirm_rate = share of arate_emails signups that have a 'Confirmed' text.
Expected: 0.67 (2 of 3).

How to Think:
- The denominator is EVERY signup in arate_emails (3). The numerator is the
  signups that have at least one 'Confirmed' row (125 and 236, so 2).
  2/3 = 0.67. Name both grains before writing anything.
- "At least one Confirmed" is a SEMI-JOIN, not a join: you want to know whether
  a matching row exists, not to multiply by how many exist. COUNT(DISTINCT
  email_id) over a filtered join does the same job.
- One output row, one column, no GROUP BY.

The trap (this IS the question):
- FAN-OUT. email_id 236 has TWO text rows: 'Not Confirmed' AND 'Confirmed'.
  A plain join to arate_texts turns 3 signups into 3 text rows, and counting
  those gives the wrong denominator. Worse, counting 'Confirmed' rows as the
  numerator happens to give 2 here -- so the numerator looks fine while the
  denominator is quietly broken.
- A signup with BOTH statuses still counts as confirmed. Filtering
  `signup_action <> 'Not Confirmed'` or taking the "latest" status invites a
  different answer; the spec only asks whether a Confirmed row exists.
- email_id 433 has NO text rows at all. It must stay in the denominator, so the
  driving table has to be arate_emails (a LEFT JOIN or a subquery), never an
  INNER JOIN -- which would give 2/2 = 1.00.
- Integer division: `COUNT(...)/COUNT(*)` on bigints truncates to 0 in
  Presto/Hive. Cast or multiply by 1.0.
- 2/3 = 0.6667 -> ROUND to 0.67 (half-up), not TRUNCATE to 0.66.

Spark note:
- Pre-aggregate arate_texts to a DISTINCT set of confirmed email_ids, then left
  join. That is both the correct-by-construction shape and the cheap one.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("71-signup-activation-rate")
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
# email 236 has TWO texts (Not Confirmed AND Confirmed) -> the fan-out.
# email 433 has NO texts -> must stay in the denominator.
spark.sql("""
CREATE OR REPLACE TEMP VIEW arate_emails AS
SELECT * FROM VALUES
    (125, 7771, TIMESTAMP'2022-06-14 00:00:00'),
    (236, 6950, TIMESTAMP'2022-07-01 00:00:00'),
    (433, 1052, TIMESTAMP'2022-07-09 00:00:00')
AS t(email_id, user_id, signup_date)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW arate_texts AS
SELECT * FROM VALUES
    (6878, 125, 'Confirmed'),
    (6920, 236, 'Not Confirmed'),
    (6994, 236, 'Confirmed')
AS t(text_id, email_id, signup_action)
""")

from pyspark.sql import functions as F

# EXISTS is a semi-join: no fan-out, so the denominator stays 3.
SQL = """
SELECT ROUND(
           SUM(CASE WHEN EXISTS (
                   SELECT 1 FROM arate_texts t
                   WHERE t.email_id = e.email_id
                     AND t.signup_action = 'Confirmed'
               ) THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 2) AS confirm_rate
FROM arate_emails e
"""

spark.sql(SQL).show(truncate=False)

expect("Q71 activation rate", SQL, [(0.67,)])

# DataFrame API equivalent -- left-semi join is the EXISTS.
emails = spark.table("arate_emails")
confirmed = (spark.table("arate_texts")
             .filter(F.col("signup_action") == "Confirmed")
             .select("email_id").distinct())
df = (emails.join(F.broadcast(confirmed), "email_id", "left_semi")
      .agg(F.count(F.lit(1)).alias("n_confirmed"))
      .crossJoin(emails.agg(F.count(F.lit(1)).alias("n_total")))
      .select(F.round(F.col("n_confirmed") * F.lit(1.0) / F.col("n_total"), 2)
               .alias("confirm_rate")))
assert [(float(r[0]),) for r in df.collect()] == [(0.67,)]
print("[PASS] Q71 DataFrame API matches SQL")

# ------------------------------------------------ the numbers, stated
parts = spark.sql("""
SELECT (SELECT COUNT(*) FROM arate_emails) AS total,
       (SELECT COUNT(DISTINCT email_id) FROM arate_texts WHERE signup_action = 'Confirmed')
           AS confirmed
""").collect()[0]
assert (parts[0], parts[1]) == (3, 2), parts
print(f"[PASS] Q71 {parts[1]} confirmed of {parts[0]} signups = 0.67")

# ------------------------------------------------ the fan-out trap
# Joining raw texts gives 3 text rows; the denominator is no longer signups.
fanned = spark.sql("""
SELECT COUNT(*) AS joined_rows FROM arate_emails e JOIN arate_texts t ON t.email_id = e.email_id
""").collect()[0][0]
assert fanned == 3, fanned
left_fanned = spark.sql("""
SELECT ROUND(SUM(CASE WHEN t.signup_action = 'Confirmed' THEN 1 ELSE 0 END) * 1.0
             / COUNT(*), 2) AS rate
FROM arate_emails e LEFT JOIN arate_texts t ON t.email_id = e.email_id
""").collect()[0][0]
assert float(left_fanned) == 0.5, left_fanned
print("[PASS] Q71 the fan-out makes the denominator 4 rows -> 0.50, not 0.67")

# ------------------------------------------------ the INNER JOIN trap
# email 433 has no texts; an inner join drops it and reports 100%.
inner = spark.sql("""
SELECT ROUND(COUNT(DISTINCT CASE WHEN t.signup_action = 'Confirmed' THEN e.email_id END) * 1.0
             / COUNT(DISTINCT e.email_id), 2) AS rate
FROM arate_emails e JOIN arate_texts t ON t.email_id = e.email_id
""").collect()[0][0]
assert float(inner) == 1.0, inner
print("[PASS] Q71 INNER JOIN drops email 433 and reports 1.00")

# ------------------------------------------------ both statuses still counts
mixed = spark.sql("""
SELECT signup_action FROM arate_texts WHERE email_id = 236 ORDER BY text_id
""").collect()
assert [r[0] for r in mixed] == ["Not Confirmed", "Confirmed"], mixed
print("[PASS] Q71 email 236 has both statuses and still counts as confirmed")

# ------------------------------------------------ integer division
int_div, float_div = spark.sql("""
SELECT CAST(2 AS BIGINT) / CAST(3 AS BIGINT) AS spark_div,
       2 * 1.0 / 3                           AS explicit
""").collect()[0]
assert round(float(int_div), 4) == round(float(float_div), 4) == 0.6667
print("[PASS] Q71 Spark's / promotes to double; Presto/Hive would truncate to 0")

# ------------------------------------------------ rounding, not truncation
r, t = spark.sql("SELECT ROUND(2.0/3, 2) AS r, FLOOR(2.0/3 * 100)/100 AS t").collect()[0]
assert (float(r), float(t)) == (0.67, 0.66), (r, t)
print("[PASS] Q71 ROUND gives 0.67; truncation would give 0.66")
