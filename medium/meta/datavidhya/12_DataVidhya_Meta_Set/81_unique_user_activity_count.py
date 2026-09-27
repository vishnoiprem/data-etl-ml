"""
Q81: Unique User Activity Count   [Easy | Left Outer Joins]
DataVidhya slug: unique-user-activity-count

Per REGISTERED user, count distinct activity types. Users with no activity get 0.

How to Think:
- "Every registered user, including those who never acted" names the driving
  table for you: cuat_user_information LEFT JOIN cuat_user_activity. The
  information table is the spine; activity is optional.
- COUNT(DISTINCT activity_type) over a left join gives 0 for the unmatched
  users automatically -- COUNT ignores NULLs, so no COALESCE is needed. That is
  the one genuinely elegant thing in this question and worth saying out loud.

The trap:
- Joining in the wrong DIRECTION. `activity LEFT JOIN information` (or an inner
  join) drops users 3 and 4 entirely instead of reporting 0. This is the
  question, and it is the same defect as an inner join in a retention query.
- COUNT(*) instead of COUNT(DISTINCT activity_type): on a left join, COUNT(*)
  counts the manufactured NULL row, so users 3 and 4 come back as 1, not 0.
  Both look like plausible small integers. COUNT(activity_type) would give 0
  correctly but would also count repeats of the same type -- only the DISTINCT
  form satisfies "distinct activity types".
- No COALESCE is needed on the count, but it IS needed if you switch to
  SUM(CASE...) -- worth knowing which constructs are NULL-safe.

Spark note:
- One shuffle; the activity table is the larger side and the dimension
  broadcasts. On real data you would aggregate activity per user FIRST and then
  left join, which keeps the wide table out of the join.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("81-unique-user-activity-count")
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
# Users 3 and 4 are registered but have NO activity rows -> must report 0.
spark.sql("""
CREATE OR REPLACE TEMP VIEW cuat_user_activity AS
SELECT * FROM VALUES
    (1, 'like',     DATE'2024-09-22'),
    (1, 'comment',  DATE'2024-07-27'),
    (2, 'purchase', DATE'2024-07-16'),
    (2, 'comment',  DATE'2024-07-24')
AS t(user_id, activity_type, activity_timestamp)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW cuat_user_information AS
SELECT * FROM VALUES
    (1, 'Alice',   'alice@example.com',   DATE'2024-06-26'),
    (2, 'Bob',     'bob@example.com',     DATE'2023-07-29'),
    (3, 'Charlie', 'charlie@example.com', DATE'2022-05-30'),
    (4, 'David',   'david@example.com',   DATE'2024-01-10')
AS t(user_id, name, email, signup_date)
""")

from pyspark.sql import functions as F

# information LEFT JOIN activity: the registered-user list is the spine.
# COUNT(DISTINCT ...) ignores NULLs, so unmatched users report 0 with no COALESCE.
SQL = """
SELECT i.user_id,
       COUNT(DISTINCT a.activity_type) AS unique_activity_count
FROM cuat_user_information i
LEFT JOIN cuat_user_activity a ON a.user_id = i.user_id
GROUP BY i.user_id
ORDER BY i.user_id
"""

spark.sql(SQL).show(truncate=False)

EXPECTED = [(1, 2), (2, 2), (3, 0), (4, 0)]
expect("Q81 distinct activity types per registered user", SQL, EXPECTED)

# DataFrame API equivalent.
df = (spark.table("cuat_user_information").alias("i")
      .join(spark.table("cuat_user_activity").alias("a"), "user_id", "left")
      .groupBy("user_id")
      .agg(F.countDistinct("activity_type").alias("unique_activity_count"))
      .orderBy("user_id"))
assert [tuple(r) for r in df.collect()] == EXPECTED
print("[PASS] Q81 DataFrame API matches SQL")

# ------------------------------------------------ the join-direction trap
inner = spark.sql("""
SELECT i.user_id, COUNT(DISTINCT a.activity_type) AS c
FROM cuat_user_information i
JOIN cuat_user_activity a ON a.user_id = i.user_id
GROUP BY i.user_id ORDER BY i.user_id
""").collect()
assert [(r[0], r[1]) for r in inner] == [(1, 2), (2, 2)], inner
print("[PASS] Q81 INNER JOIN drops users 3 and 4 instead of reporting 0")

# ------------------------------------------------ the COUNT(*) trap
star = spark.sql("""
SELECT i.user_id, COUNT(*) AS c
FROM cuat_user_information i
LEFT JOIN cuat_user_activity a ON a.user_id = i.user_id
GROUP BY i.user_id ORDER BY i.user_id
""").collect()
assert [(r[0], r[1]) for r in star] == [(1, 2), (2, 2), (3, 1), (4, 1)], star
print("[PASS] Q81 COUNT(*) counts the manufactured NULL row -> users 3 and 4 report 1")

# ------------------------------------------------ DISTINCT matters on repeats
# Give user 1 a second 'like': COUNT(activity_type) says 3, DISTINCT says 2.
spark.sql("""
CREATE OR REPLACE TEMP VIEW cuat_user_activity AS
SELECT * FROM VALUES
    (1, 'like',     DATE'2024-09-22'),
    (1, 'comment',  DATE'2024-07-27'),
    (1, 'like',     DATE'2024-09-25'),
    (2, 'purchase', DATE'2024-07-16'),
    (2, 'comment',  DATE'2024-07-24')
AS t(user_id, activity_type, activity_timestamp)
""")
expect("Q81 a repeated activity type counts once", SQL, [(1, 2), (2, 2), (3, 0), (4, 0)])

non_distinct = spark.sql("""
SELECT i.user_id, COUNT(a.activity_type) AS c
FROM cuat_user_information i
LEFT JOIN cuat_user_activity a ON a.user_id = i.user_id
GROUP BY i.user_id ORDER BY i.user_id
""").collect()
assert [(r[0], r[1]) for r in non_distinct] == [(1, 3), (2, 2), (3, 0), (4, 0)], non_distinct
print("[PASS] Q81 COUNT(activity_type) gives user 1 three -- DISTINCT is required")

# ------------------------------------------------ activity from an unregistered user
# A user_id present only in the activity table must NOT appear in the output.
spark.sql("""
CREATE OR REPLACE TEMP VIEW cuat_user_activity AS
SELECT * FROM VALUES
    (1,  'like',    DATE'2024-09-22'),
    (99, 'comment', DATE'2024-07-27')
AS t(user_id, activity_type, activity_timestamp)
""")
expect("Q81 unregistered user 99 is excluded", SQL, [(1, 1), (2, 0), (3, 0), (4, 0)])
print("[PASS] Q81 driving from cuat_user_information keeps user 99 out")
