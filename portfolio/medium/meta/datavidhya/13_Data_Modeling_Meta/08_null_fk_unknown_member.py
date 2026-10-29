"""
Q44: How do you handle NULL values in dimension tables (and NULL foreign keys)?
Article: "50 Data Modeling Interview Questions for DEs" — Warehouse Design

Meta flavor: "Feed impressions from logged-out sessions have no user_id. Total
impressions on the dashboard is 12% below the raw event count and nobody can
say where the gap is."

How to Think:
- NEVER leave a NULL foreign key in a fact table. Instead put a dedicated
  UNKNOWN row in each dimension (surrogate key -1 or 0) and point every NULL FK
  at it. Two properties follow immediately:
    * every fact row joins, so counts reconcile against the raw event count
    * "Unknown" becomes an explicit, filterable CATEGORY rather than an absence
- The reason this matters is not tidiness, it is that NULL FKs fail SILENTLY.
  An inner join drops them with no error and no warning, so the dashboard is
  simply wrong and nothing in the pipeline complains.
- Reserve a NEGATIVE surrogate key (-1). Real keys are positive and generated,
  so -1 can never collide, and seeing -1 in a query result is self-explaining.
  0 works too but collides with "unset integer" bugs.
- Distinguish the two nearby cases and say which you mean:
    UNKNOWN (-1)          -> we have no key (logged-out session)
    NOT APPLICABLE (-2)   -> a key is meaningless here (a system-generated post
                             has no human author)
  Collapsing both into -1 loses a real distinction analysts will ask about.
- An inferred member (see `07_late_arriving_dimension.py`) is a THIRD thing: one
  row per unseen real key, resolvable later. -1 is not resolvable.

The trap:
- A LEFT JOIN is not the fix. It keeps the fact row but yields NULL ATTRIBUTES,
  so `GROUP BY country` produces a NULL bucket and `WHERE country <> 'US'`
  excludes it -- because NULL <> 'US' is NULL, not true. So the rows survive the
  join and then disappear at the filter. Asserted below; this is the part people
  miss after "fixing" the join.
- COUNT(*) vs COUNT(fk): COUNT ignores NULLs, so COUNT(user_key) silently
  under-reports while COUNT(*) does not. Two "row counts" that disagree.
- NULLs in a GROUP BY collapse together, so a NULL in a GRAIN column makes the
  grain check pass while the join still drops the row -- see
  `01_grain_violation_detection.py` for that interaction.
- Don't forget the dimension's own NULL ATTRIBUTES. A real advertiser row with a
  NULL `country` produces the same GROUP BY / filter problem one level down;
  default those to '(unknown)' at load time too.

Spark note:
- Resolve the FK to -1 during the ETL write with COALESCE, not at query time.
  One COALESCE on load versus one in every downstream query.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("08-null-fk-unknown-member")
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


UNKNOWN_KEY = -1        # no key available (logged-out)
NOT_APPLICABLE_KEY = -2  # a key is meaningless here (system-generated)

# ---------------------------------------------------------- the broken state
# 8 impressions; 3 have a NULL user_key (logged-out or system-generated).
spark.sql("""
CREATE OR REPLACE TEMP VIEW dim_user_raw AS
SELECT * FROM VALUES
    (101, 'US', 'ios'),
    (102, 'IN', 'android'),
    (103, 'US', 'web')
AS t(user_key, country, platform)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW fact_impression_raw AS
SELECT * FROM VALUES
    (1, 101), (2, 101), (3, 102), (4, 103), (5, 103),
    (6, CAST(NULL AS INT)), (7, CAST(NULL AS INT)), (8, CAST(NULL AS INT))
AS t(impression_id, user_key)
""")

RAW_TOTAL = 8

from pyspark.sql import functions as F

# ---------------------------------------------------------- the silent loss
inner = spark.sql("""
SELECT COUNT(*) FROM fact_impression_raw f JOIN dim_user_raw d ON d.user_key = f.user_key
""").collect()[0][0]
assert inner == 5, inner
print(f"[PASS] Q44 inner join reports {inner} of {RAW_TOTAL} impressions "
      f"-- {(RAW_TOTAL - inner) / RAW_TOTAL:.0%} lost, silently")

# COUNT(*) and COUNT(fk) disagree on the same table.
counts = spark.sql("""
SELECT COUNT(*) AS star, COUNT(user_key) AS fk FROM fact_impression_raw
""").collect()[0]
assert (counts[0], counts[1]) == (8, 5), counts
print("[PASS] Q44 COUNT(*) = 8 but COUNT(user_key) = 5 -- two disagreeing 'row counts'")

# ---------------------------------------------------------- the fix
# Add explicit members to the dimension, and COALESCE the FK on load.
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW dim_user AS
SELECT * FROM VALUES
    ({UNKNOWN_KEY},        '(unknown)',        '(unknown)'),
    ({NOT_APPLICABLE_KEY}, '(not applicable)', '(not applicable)'),
    (101, 'US', 'ios'),
    (102, 'IN', 'android'),
    (103, 'US', 'web')
AS t(user_key, country, platform)
""")
# Impression 8 is a system-generated placement -> NOT APPLICABLE, not UNKNOWN.
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW fact_impression AS
SELECT impression_id,
       CASE WHEN impression_id = 8 THEN {NOT_APPLICABLE_KEY}
            ELSE COALESCE(user_key, {UNKNOWN_KEY}) END AS user_key
FROM fact_impression_raw
""")

nulls_left = spark.sql(
    "SELECT COUNT(*) FROM fact_impression WHERE user_key IS NULL").collect()[0][0]
assert nulls_left == 0
print("[PASS] Q44 zero NULL foreign keys remain in the fact table")

BY_COUNTRY = """
SELECT d.country, COUNT(*) AS impressions
FROM fact_impression f
JOIN dim_user d ON d.user_key = f.user_key
GROUP BY d.country
ORDER BY impressions DESC, d.country
"""
spark.sql(BY_COUNTRY).show(truncate=False)
expect("Q44 every row joins; Unknown is an explicit category", BY_COUNTRY, [
    ("US",               4),   # users 101 (x2) and 103 (x2)
    ("(unknown)",        2),   # impressions 6, 7 -- logged out
    ("(not applicable)", 1),   # impression 8 -- system generated
    ("IN",               1),   # '(' sorts before 'I', so this is last
])

reconciled = spark.sql(f"SELECT SUM(impressions) FROM ({BY_COUNTRY})").collect()[0][0]
assert reconciled == RAW_TOTAL, reconciled
print(f"[PASS] Q44 the dashboard total now reconciles to {reconciled} = the raw event count")

# DataFrame API equivalent.
df = (spark.table("fact_impression")
      .join(F.broadcast(spark.table("dim_user")), "user_key")
      .groupBy("country").agg(F.count(F.lit(1)).alias("impressions"))
      .orderBy(F.col("impressions").desc(), F.col("country")))
assert [tuple(r) for r in df.collect()] == [
    ("US", 4), ("(unknown)", 2), ("(not applicable)", 1), ("IN", 1),
]
print("[PASS] Q44 DataFrame API matches SQL")

# ---------------------------------------------------------- LEFT JOIN is NOT the fix
# It keeps the rows but the attributes are NULL, so the next filter drops them.
left_join = spark.sql("""
SELECT COUNT(*) AS rows_kept,
       COUNT(d.country) AS rows_with_country
FROM fact_impression_raw f
LEFT JOIN dim_user_raw d ON d.user_key = f.user_key
""").collect()[0]
assert (left_join[0], left_join[1]) == (8, 5), left_join
print("[PASS] Q44 LEFT JOIN keeps all 8 rows but only 5 have a country")

# The three-valued-logic bite: NULL <> 'US' is NULL, so the filter excludes them.
filtered = spark.sql("""
SELECT COUNT(*) FROM fact_impression_raw f
LEFT JOIN dim_user_raw d ON d.user_key = f.user_key
WHERE d.country <> 'US'
""").collect()[0][0]
assert filtered == 1, filtered
print("[PASS] Q44 `WHERE country <> 'US'` returns 1, not 4 -- NULL <> 'US' is NULL, "
      "so the LEFT-joined rows vanish at the filter")

# With explicit members the same filter behaves as an analyst expects.
filtered_fixed = spark.sql("""
SELECT COUNT(*) FROM fact_impression f
JOIN dim_user d ON d.user_key = f.user_key
WHERE d.country <> 'US'
""").collect()[0][0]
assert filtered_fixed == 4, filtered_fixed
print("[PASS] Q44 with explicit members the same filter returns 4 -- no NULL logic")

# ---------------------------------------------------------- Unknown vs Not Applicable
split = spark.sql(f"""
SELECT d.country, COUNT(*) AS n
FROM fact_impression f JOIN dim_user d ON d.user_key = f.user_key
WHERE f.user_key < 0
GROUP BY d.country ORDER BY d.country
""").collect()
assert [(r[0], r[1]) for r in split] == [("(not applicable)", 1), ("(unknown)", 2)], split
print("[PASS] Q44 -1 and -2 keep 'no key' and 'key is meaningless' distinguishable")

# Negative keys cannot collide with generated positive keys.
real_min = spark.sql(
    "SELECT MIN(user_key) FROM dim_user WHERE user_key > 0").collect()[0][0]
assert real_min > 0 > UNKNOWN_KEY > NOT_APPLICABLE_KEY
print(f"[PASS] Q44 real keys start at {real_min}; -1/-2 are collision-proof by construction")

# ---------------------------------------------------------- NULL dimension ATTRIBUTES
# Same problem one level down: a real user row with a NULL country.
spark.sql("""
CREATE OR REPLACE TEMP VIEW dim_user AS
SELECT * FROM VALUES
    (-1,  '(unknown)', '(unknown)'),
    (101, 'US',        'ios'),
    (104, CAST(NULL AS STRING), 'web')
AS t(user_key, country, platform)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW fact_impression AS
SELECT * FROM VALUES (1, 101), (2, 104) AS t(impression_id, user_key)
""")
leaky = spark.sql("""
SELECT COUNT(*) FROM fact_impression f
JOIN dim_user d ON d.user_key = f.user_key
WHERE d.country <> 'US'
""").collect()[0][0]
assert leaky == 0, leaky
print("[PASS] Q44 a NULL ATTRIBUTE on a real dimension row re-creates the bug "
      "(filter returns 0, not 1) -- default attributes at load time too")

spark.sql("""
CREATE OR REPLACE TEMP VIEW dim_user_clean AS
SELECT user_key,
       COALESCE(country, '(unknown)')  AS country,
       COALESCE(platform, '(unknown)') AS platform
FROM dim_user
""")
fixed = spark.sql("""
SELECT COUNT(*) FROM fact_impression f
JOIN dim_user_clean d ON d.user_key = f.user_key
WHERE d.country <> 'US'
""").collect()[0][0]
assert fixed == 1, fixed
print("[PASS] Q44 defaulting the attribute restores the expected filter result (1)")

# ---- MySQL way ----------------------------------------------------------
# CREATE TABLE + sample data:
#   CREATE TABLE dim_user (
#       user_key   INT          NOT NULL,
#       country    VARCHAR(32)  NOT NULL,
#       platform   VARCHAR(32)  NOT NULL,
#       PRIMARY KEY (user_key)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   -- Always ship explicit Unknown (-1) and Not Applicable (-2) members; real
#   -- keys are generated positive so negatives cannot collide.
#   INSERT INTO dim_user (user_key, country, platform) VALUES
#       (-1, '(unknown)',        '(unknown)'),
#       (-2, '(not applicable)', '(not applicable)'),
#       (101, 'US', 'ios'),
#       (102, 'IN', 'android'),
#       (103, 'US', 'web');
#
#   CREATE TABLE fact_impression (
#       impression_id  INT NOT NULL,
#       user_key       INT NOT NULL,
#       PRIMARY KEY (impression_id),
#       KEY idx_fact_imp_user (user_key)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   -- COALESCE the FK on LOAD, not at query time.
#   INSERT INTO fact_impression (impression_id, user_key)
#   SELECT impression_id,
#          CASE WHEN impression_id = 8 THEN -2 ELSE COALESCE(user_key, -1) END AS user_key
#   FROM (VALUES ROW(1, 101), ROW(2, 101), ROW(3, 102), ROW(4, 103), ROW(5, 103),
#                ROW(6, NULL), ROW(7, NULL), ROW(8, NULL)) AS t(impression_id, user_key);
#
#   -- Q44 every row joins; Unknown is an explicit category (expect block)
#   SELECT d.country, COUNT(*) AS impressions
#   FROM fact_impression f
#   JOIN dim_user d ON d.user_key = f.user_key
#   GROUP BY d.country
#   ORDER BY impressions DESC, d.country;
#
#   -- Q44 LEFT JOIN keeps all 8 rows but only 5 have a country (the trap).
#   SELECT COUNT(*) AS rows_kept,
#          COUNT(d.country) AS rows_with_country
#   FROM (VALUES ROW(1,101),ROW(2,101),ROW(3,102),ROW(4,103),ROW(5,103),
#                ROW(6,NULL),ROW(7,NULL),ROW(8,NULL)) AS f(impression_id, user_key)
#   LEFT JOIN dim_user_raw d ON d.user_key = f.user_key;
#
#   -- Q44 `WHERE country <> 'US'` returns 1, not 4 -- NULL <> 'US' is NULL.
#   SELECT COUNT(*)
#   FROM (VALUES ROW(1,101),ROW(2,101),ROW(3,102),ROW(4,103),ROW(5,103),
#                ROW(6,NULL),ROW(7,NULL),ROW(8,NULL)) AS f(impression_id, user_key)
#   LEFT JOIN dim_user_raw d ON d.user_key = f.user_key
#   WHERE d.country <> 'US';
#
#   -- Q44 -1 and -2 keep 'no key' and 'key is meaningless' distinguishable
#   SELECT d.country, COUNT(*) AS n
#   FROM fact_impression f JOIN dim_user d ON d.user_key = f.user_key
#   WHERE f.user_key < 0
#   GROUP BY d.country ORDER BY d.country;
#
#   -- Q44 NULL attribute on a real dimension row re-creates the bug --
#   -- a LEFT JOIN keeps the row but the filter loses it.
#   INSERT INTO dim_user (user_key, country, platform) VALUES
#       (104, NULL, 'web');
#   INSERT INTO fact_impression (impression_id, user_key) VALUES (1, 101), (2, 104);
#   SELECT COUNT(*) FROM fact_impression f
#   JOIN dim_user d ON d.user_key = f.user_key
#   WHERE d.country <> 'US';     -- returns 0, not 1
#
#   -- Defaulting the attribute restores the expected filter result:
#   CREATE OR REPLACE VIEW dim_user_clean AS
#   SELECT user_key,
#          COALESCE(country, '(unknown)')  AS country,
#          COALESCE(platform, '(unknown)') AS platform
#   FROM dim_user;
#   SELECT COUNT(*) FROM fact_impression f
#   JOIN dim_user_clean d ON d.user_key = f.user_key
#   WHERE d.country <> 'US';     -- returns 1
#
# MySQL 8.0+ notes: TINYINT(1) is the explicit BOOLEAN. ROW(... ) VALUES is
# MySQL 8.0.19+ portable table-constructor syntax (replaces Spark's
# SELECT * FROM VALUES ROW(...) AS t(...)). The three-valued-logic bite
# (NULL <> 'US' is NULL, so the LEFT-joined rows vanish at the filter) is
# the silent-failure mode that makes a dashboard 12% low at Meta volume --
# shipping explicit Unknown / Not Applicable members turns absence into a
# filterable category and stops the gap from being invisible.
