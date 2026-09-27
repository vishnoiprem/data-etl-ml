"""
Q19 / Q26: Many-to-many in a star schema — bridge tables and double-counting.
Article: "50 Data Modeling Interview Questions for DEs" — Star Schema / SCDs

Meta flavor: "A Reel can carry several hashtags and a hashtag appears on many
Reels. Product wants views by hashtag. Total views by hashtag came out at 2.4x
total views overall — explain and fix."

How to Think:
- A many-to-many cannot sit in a star's fact-to-dimension edge, so you insert a
  BRIDGE table (reel_key, hashtag_key) that splits it into two one-to-many
  relationships. That part is mechanical.
- The part that is actually being tested: the bridge FANS OUT the fact. A Reel
  with 3 hashtags becomes 3 rows, so SUM(views) counts its views three times.
  The join is correct; the AGGREGATE is what breaks.
- Two legitimate fixes, and you should name both and say when each applies:
    1. ALLOCATE (weighting factor): give each bridge row 1/n of the measure, so
       the parts sum back to the whole. Use when the total must reconcile --
       revenue, spend, anything finance reads.
    2. DON'T ADD (impact reporting): report views per hashtag WITHOUT summing
       across hashtags, and state that the column does not total. Use when the
       question is "how did this hashtag do", not "how do hashtags split the pie".
  Choosing silently is the failure; the interviewer wants the trade-off named.
- The weighting factor lives ON the bridge, not in the query. Computed once at
  load time, every downstream query is correct by construction.

The trap:
- The un-weighted SUM looks completely plausible. 2.4x is not an obviously wrong
  number the way a negative or a 100x would be, so this ships.
- COUNT(DISTINCT reel_id) is NOT a fix for a SUM. It fixes "how many Reels",
  but views are additive and still triple. Different metrics need different
  treatment -- additive measures need allocation, distinct counts need DISTINCT.
- Weights must sum to exactly 1.0 per fact row. In floating point that is not
  guaranteed for every n -- 3 x (1/3) happens to be exact, while 49 x (1/49)
  drifts off 1.0 -- so an equality check on the reconciliation can fail for
  reasons that have nothing to do with the model. Keep weights DECIMAL, and
  round at the comparison rather than in the weight.
- A fact row with NO bridge entry (a Reel with no hashtags) is DROPPED by an
  inner join through the bridge, so the allocated total silently under-reports.
  Asserted below -- this is the mirror image of the double-count and is missed
  far more often.

Spark note:
- The bridge is small and broadcasts. Compute the weight once on write; a
  per-query window over the bridge costs a shuffle on every read.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("04-bridge-table-double-count")
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
# 3 Reels, 6000 total views. Reel 1 has 3 hashtags, Reel 2 has 2, Reel 3 has 1.
spark.sql("""
CREATE OR REPLACE TEMP VIEW fact_reel_views AS
SELECT * FROM VALUES
    (1, DATE'2026-03-01', 3000),
    (2, DATE'2026-03-01', 2000),
    (3, DATE'2026-03-01', 1000)
AS t(reel_id, view_date, views)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW bridge_reel_hashtag AS
SELECT * FROM VALUES
    (1, 'cooking'), (1, 'recipe'), (1, 'food'),
    (2, 'cooking'), (2, 'vegan'),
    (3, 'cooking')
AS t(reel_id, hashtag)
""")

from pyspark.sql import functions as F, Window as W

TRUE_TOTAL = 6000

# ---------------------------------------------------------- the bug
NAIVE = """
SELECT b.hashtag, SUM(f.views) AS views
FROM fact_reel_views f
JOIN bridge_reel_hashtag b ON b.reel_id = f.reel_id
GROUP BY b.hashtag
ORDER BY views DESC, b.hashtag
"""
spark.sql(NAIVE).show(truncate=False)
expect("Q19 un-weighted SUM through the bridge", NAIVE, [
    ("cooking", 6000),
    ("food",    3000),
    ("recipe",  3000),
    ("vegan",   2000),
])

naive_total = spark.sql(f"SELECT SUM(views) FROM ({NAIVE})").collect()[0][0]
assert naive_total == 14000, naive_total
print(f"[PASS] Q19 hashtag totals sum to {naive_total} against a true {TRUE_TOTAL} "
      f"-- {naive_total / TRUE_TOTAL:.2f}x inflation")

# ---------------------------------------------------------- fix 1: allocate
# weight = 1 / (number of hashtags on that reel), stamped on the bridge.
spark.sql("""
CREATE OR REPLACE TEMP VIEW bridge_weighted AS
SELECT reel_id,
       hashtag,
       1.0 / COUNT(*) OVER (PARTITION BY reel_id) AS weight
FROM bridge_reel_hashtag
""")
spark.table("bridge_weighted").orderBy("reel_id", "hashtag").show(truncate=False)

ALLOCATED = """
SELECT b.hashtag, ROUND(SUM(f.views * b.weight), 2) AS allocated_views
FROM fact_reel_views f
JOIN bridge_weighted b ON b.reel_id = f.reel_id
GROUP BY b.hashtag
ORDER BY allocated_views DESC, b.hashtag
"""
spark.sql(ALLOCATED).show(truncate=False)
expect("Q19 weighted allocation reconciles to the true total", ALLOCATED, [
    ("cooking", 3000.00),   # 3000/3 + 2000/2 + 1000/1 = 1000 + 1000 + 1000
    ("food",    1000.00),
    ("recipe",  1000.00),
    ("vegan",   1000.00),
])

alloc_total = spark.sql(f"SELECT ROUND(SUM(allocated_views), 2) FROM ({ALLOCATED})") \
    .collect()[0][0]
assert float(alloc_total) == float(TRUE_TOTAL), alloc_total
print(f"[PASS] Q19 allocated totals sum to exactly {alloc_total} = the true total")

# DataFrame API equivalent.
bridge_w = spark.table("bridge_reel_hashtag").withColumn(
    "weight", F.lit(1.0) / F.count("*").over(W.partitionBy("reel_id")))
df = (spark.table("fact_reel_views").alias("f")
      .join(F.broadcast(bridge_w.alias("b")), "reel_id")
      .groupBy("hashtag")
      .agg(F.round(F.sum(F.col("views") * F.col("weight")), 2).alias("allocated_views"))
      .orderBy(F.col("allocated_views").desc(), F.col("hashtag")))
assert [(r[0], float(r[1])) for r in df.collect()] == [
    ("cooking", 3000.0), ("food", 1000.0), ("recipe", 1000.0), ("vegan", 1000.0),
]
print("[PASS] Q19 DataFrame API matches SQL")

# ---------------------------------------------------------- weights sum to 1 per fact
per_reel = spark.sql("""
SELECT reel_id, ROUND(SUM(weight), 10) AS w FROM bridge_weighted GROUP BY reel_id
ORDER BY reel_id
""").collect()
assert [(r[0], float(r[1])) for r in per_reel] == [(1, 1.0), (2, 1.0), (3, 1.0)], per_reel
print("[PASS] Q19 weights sum to 1.0 per reel -- the invariant that makes totals reconcile")

# Float weights are not exact for every n. 1/3 happens to sum cleanly, but a
# fact row split 49 ways does not -- so compare with a rounding tolerance.
n3 = float(spark.sql(
    "SELECT SUM(CAST(1.0 AS DOUBLE)/3) FROM VALUES (1),(2),(3) AS t(i)").collect()[0][0])
n49 = float(spark.sql(
    "SELECT SUM(CAST(1.0 AS DOUBLE)/49) FROM range(49)").collect()[0][0])
assert n3 == 1.0 and n49 != 1.0, (n3, n49)
print(f"[PASS] Q19 float weights: 3-way sums to {n3}, 49-way sums to {n49!r} "
      "-- keep weights DECIMAL and round at the comparison")

# ---------------------------------------------------------- fix 2: don't add
# Per-hashtag impact is the un-weighted number; it just must not be totalled.
IMPACT = """
SELECT b.hashtag,
       SUM(f.views)                  AS views_on_reels_with_tag,
       COUNT(DISTINCT f.reel_id)     AS reels
FROM fact_reel_views f
JOIN bridge_reel_hashtag b ON b.reel_id = f.reel_id
GROUP BY b.hashtag
ORDER BY views_on_reels_with_tag DESC, b.hashtag
"""
expect("Q19 impact framing: correct per row, explicitly NOT summable", IMPACT, [
    ("cooking", 6000, 3),
    ("food",    3000, 1),
    ("recipe",  3000, 1),
    ("vegan",   2000, 1),
])
print("[PASS] Q19 'cooking reached 6000 views' is true; adding the column is not meaningful")

# ---------------------------------------------------------- COUNT DISTINCT is not a fix
distinct_reels = spark.sql("""
SELECT COUNT(DISTINCT f.reel_id) AS reels, SUM(f.views) AS views
FROM fact_reel_views f JOIN bridge_reel_hashtag b ON b.reel_id = f.reel_id
""").collect()[0]
assert (distinct_reels[0], distinct_reels[1]) == (3, 14000), distinct_reels
print("[PASS] Q19 COUNT(DISTINCT reel_id) = 3 is right while SUM(views) = 14000 is wrong "
      "-- distinct counts and additive measures need different fixes")

# ---------------------------------------------------------- the unbridged-fact trap
# Reel 4 has no hashtags. The inner join drops it, so allocation UNDER-reports.
spark.sql("""
CREATE OR REPLACE TEMP VIEW fact_reel_views AS
SELECT * FROM VALUES
    (1, DATE'2026-03-01', 3000),
    (2, DATE'2026-03-01', 2000),
    (3, DATE'2026-03-01', 1000),
    (4, DATE'2026-03-01',  500)
AS t(reel_id, view_date, views)
""")
new_total = spark.sql("SELECT SUM(views) FROM fact_reel_views").collect()[0][0]
alloc_after = spark.sql(f"SELECT ROUND(SUM(allocated_views), 2) FROM ({ALLOCATED})") \
    .collect()[0][0]
assert (new_total, float(alloc_after)) == (6500, 6000.0), (new_total, alloc_after)
print(f"[PASS] Q19 Reel 4 has no hashtag: true total {new_total}, "
      f"allocated {alloc_after} -- 500 views silently vanish")

# The fix: an 'Unassigned' bridge member, so every fact row has a home.
spark.sql("""
CREATE OR REPLACE TEMP VIEW bridge_weighted AS
WITH covered AS (
    SELECT reel_id, hashtag FROM bridge_reel_hashtag
    UNION ALL
    SELECT f.reel_id, '(unassigned)' AS hashtag
    FROM fact_reel_views f
    WHERE NOT EXISTS (SELECT 1 FROM bridge_reel_hashtag b WHERE b.reel_id = f.reel_id)
)
SELECT reel_id, hashtag, 1.0 / COUNT(*) OVER (PARTITION BY reel_id) AS weight
FROM covered
""")
expect("Q19 an '(unassigned)' member keeps the allocation complete", ALLOCATED, [
    ("cooking",      3000.00),
    ("food",         1000.00),
    ("recipe",       1000.00),
    ("vegan",        1000.00),
    ("(unassigned)",  500.00),
])
fixed_total = spark.sql(f"SELECT ROUND(SUM(allocated_views), 2) FROM ({ALLOCATED})") \
    .collect()[0][0]
assert float(fixed_total) == 6500.0, fixed_total
print(f"[PASS] Q19 allocation now reconciles to {fixed_total} = the true total")
