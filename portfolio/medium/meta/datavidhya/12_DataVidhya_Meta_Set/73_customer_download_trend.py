"""
Q73: Customer Download Trend Analysis   [Easy | Aggregate Functions]
DataVidhya slug: customer-download-trend-analysis

Per date, total downloads by 'free' users vs 'premium' users. Return only the
dates where free STRICTLY EXCEEDS premium.

How to Think:
- Both totals come from the same rows, split by user_type -> conditional
  aggregate, one GROUP BY date. Two subqueries joined on date would also work
  but is strictly more code and more chances to lose a date.
- The comparison is between two AGGREGATES, so it belongs in HAVING. It cannot
  go in WHERE -- neither total exists yet at WHERE time.

The trap:
- STRICTLY greater. A date where free == premium must be EXCLUDED. `>=` is the
  intended slip and the shipped data cannot catch it (the three dates are 7v3,
  4v6, 5v2 -- no ties). Asserted on a constructed tie below.
- Filtering user_type in WHERE breaks the other total: `WHERE user_type='free'`
  makes paying_downloads always 0, and then every date trivially qualifies.
  The split must happen inside the aggregate, not before it.
- SUM(downloads), not COUNT(*). Each row already carries a download COUNT, so
  counting rows would give "number of users" instead. On 2024-01-01 that is
  2 vs 1 rather than 7 vs 3 -- and 2 > 1 still qualifies, so the date list
  looks right while both numbers are wrong.
- A date with only free users (no premium row at all) has premium total 0 and
  qualifies. SUM(CASE ... ELSE 0) gives 0 rather than NULL, which is what makes
  the comparison work; a bare SUM(CASE...) with no ELSE returns NULL and
  `7 > NULL` is NULL, so the date silently disappears. Asserted below.

Spark note:
- One shuffle on cdate. Both conditional sums compute in the same pass.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("73-customer-download-trend")
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
# Jan 1: 7 free vs 3 premium (qualifies). Jan 2: 4 vs 6 (no). Jan 3: 5 vs 2 (yes).
spark.sql("""
CREATE OR REPLACE TEMP VIEW adtc_customer AS
SELECT * FROM VALUES
    ('u1', 'free',    5, DATE'2024-01-01'),
    ('u2', 'premium', 3, DATE'2024-01-01'),
    ('u3', 'free',    2, DATE'2024-01-01'),
    ('u4', 'premium', 6, DATE'2024-01-02'),
    ('u5', 'free',    4, DATE'2024-01-02'),
    ('u6', 'premium', 2, DATE'2024-01-03'),
    ('u7', 'free',    5, DATE'2024-01-03')
AS t(user_id, user_type, downloads, cdate)
""")

from pyspark.sql import functions as F

# ELSE 0 (not a bare CASE) so a missing user_type gives 0, never NULL.
SQL = """
SELECT cdate,
       SUM(CASE WHEN user_type = 'free'    THEN downloads ELSE 0 END) AS non_paying_downloads,
       SUM(CASE WHEN user_type = 'premium' THEN downloads ELSE 0 END) AS paying_downloads
FROM adtc_customer
GROUP BY cdate
HAVING SUM(CASE WHEN user_type = 'free'    THEN downloads ELSE 0 END)
     > SUM(CASE WHEN user_type = 'premium' THEN downloads ELSE 0 END)   -- strictly
ORDER BY cdate
"""

spark.sql(SQL).show(truncate=False)

import datetime as dt

expect("Q73 dates where free downloads exceed premium", SQL, [
    (dt.date(2024, 1, 1), 7, 3),
    (dt.date(2024, 1, 3), 5, 2),
])

# DataFrame API equivalent.
free = F.sum(F.when(F.col("user_type") == "free", F.col("downloads")).otherwise(0))
prem = F.sum(F.when(F.col("user_type") == "premium", F.col("downloads")).otherwise(0))
df = (spark.table("adtc_customer").groupBy("cdate")
      .agg(free.alias("non_paying_downloads"), prem.alias("paying_downloads"))
      .filter(F.col("non_paying_downloads") > F.col("paying_downloads"))
      .orderBy("cdate"))
assert [tuple(r) for r in df.collect()] == [
    (dt.date(2024, 1, 1), 7, 3), (dt.date(2024, 1, 3), 5, 2),
]
print("[PASS] Q73 DataFrame API matches SQL")

# ------------------------------------------------ SUM vs COUNT
counts = spark.sql("""
SELECT cdate,
       SUM(CASE WHEN user_type = 'free' THEN downloads ELSE 0 END) AS free_downloads,
       COUNT(CASE WHEN user_type = 'free' THEN 1 END)              AS free_users
FROM adtc_customer WHERE cdate = DATE'2024-01-01' GROUP BY cdate
""").collect()[0]
assert (counts[1], counts[2]) == (7, 2), counts
print("[PASS] Q73 Jan 1 has 7 downloads from 2 free users -- SUM(downloads), not COUNT(*)")

# ------------------------------------------------ the strict-inequality trap
# Jan 4 ties at 5 vs 5 and must NOT appear.
spark.sql("""
CREATE OR REPLACE TEMP VIEW adtc_customer AS
SELECT * FROM VALUES
    ('u1', 'free',    5, DATE'2024-01-01'),
    ('u2', 'premium', 3, DATE'2024-01-01'),
    ('u8', 'free',    5, DATE'2024-01-04'),
    ('u9', 'premium', 5, DATE'2024-01-04')
AS t(user_id, user_type, downloads, cdate)
""")
expect("Q73 a tied date is excluded", SQL, [(dt.date(2024, 1, 1), 5, 3)])

with_ge = spark.sql("""
SELECT cdate FROM adtc_customer GROUP BY cdate
HAVING SUM(CASE WHEN user_type='free' THEN downloads ELSE 0 END)
    >= SUM(CASE WHEN user_type='premium' THEN downloads ELSE 0 END)
ORDER BY cdate
""").collect()
assert [str(r[0]) for r in with_ge] == ["2024-01-01", "2024-01-04"], with_ge
print("[PASS] Q73 using >= wrongly admits the 5-vs-5 tie")

# ------------------------------------------------ the missing-ELSE trap
# A date with no premium row at all: ELSE 0 gives 0 and the date qualifies;
# a bare CASE gives NULL and `5 > NULL` is NULL, so the date vanishes.
spark.sql("""
CREATE OR REPLACE TEMP VIEW adtc_customer AS
SELECT * FROM VALUES
    ('u1', 'free', 5, DATE'2024-01-05'),
    ('u2', 'free', 1, DATE'2024-01-05')
AS t(user_id, user_type, downloads, cdate)
""")
expect("Q73 a free-only date qualifies with paying_downloads 0", SQL,
       [(dt.date(2024, 1, 5), 6, 0)])

no_else = spark.sql("""
SELECT cdate FROM adtc_customer GROUP BY cdate
HAVING SUM(CASE WHEN user_type='free' THEN downloads END)
     > SUM(CASE WHEN user_type='premium' THEN downloads END)
""").collect()
assert no_else == [], no_else
print("[PASS] Q73 omitting ELSE 0 makes the premium total NULL and the date disappears")

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports the same SUM(CASE WHEN ... THEN ... ELSE 0 END) pattern.
# The ELSE 0 is critical because SUM over an all-NULL set returns NULL,
# and `5 > NULL` evaluates to NULL (filtered out by HAVING).
#
# CREATE TABLE adtc_customer (
#     user_id    VARCHAR(16) NOT NULL,
#     user_type  ENUM('free','premium') NOT NULL,
#     downloads  INT         NOT NULL,
#     cdate      DATE        NOT NULL,
#     PRIMARY KEY (user_id, cdate),
#     KEY ix_adtc_date_type (cdate, user_type)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO adtc_customer (user_id, user_type, downloads, cdate) VALUES
#     ('u1', 'free',    5, '2024-01-01'),
#     ('u2', 'premium', 3, '2024-01-01'),
#     ('u3', 'free',    2, '2024-01-01'),
#     ('u4', 'premium', 6, '2024-01-02'),
#     ('u5', 'free',    4, '2024-01-02'),
#     ('u6', 'premium', 2, '2024-01-03'),
#     ('u7', 'free',    5, '2024-01-03');
#
# SELECT cdate,
#        SUM(CASE WHEN user_type = 'free'    THEN downloads ELSE 0 END) AS non_paying_downloads,
#        SUM(CASE WHEN user_type = 'premium' THEN downloads ELSE 0 END) AS paying_downloads
# FROM adtc_customer
# GROUP BY cdate
# HAVING SUM(CASE WHEN user_type = 'free'    THEN downloads ELSE 0 END)
#      > SUM(CASE WHEN user_type = 'premium' THEN downloads ELSE 0 END)
# ORDER BY cdate;
#
# -- Expected: ('2024-01-01', 7, 3), ('2024-01-03', 5, 2).
