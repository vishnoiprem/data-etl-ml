"""
Q28: What is a Type 6 (hybrid) SCD?
Article: "50 Data Modeling Interview Questions for DEs" — SCDs & History Tracking

Meta flavor: "Analysts keep asking two different questions of dim_creator. One
is 'what tier was this creator in when the video was posted' and the other is
'show me lifetime views grouped by their tier TODAY'. Support both without two
dimensions and without a self-join."

How to Think:
- Type 6 = 1 + 2 + 3. Three mechanisms in one table, each answering a different
  question, and you should name which is which:
    Type 2 rows (effective_from / effective_to / is_current) -> historical truth
    Type 1 column (current_tier, overwritten on EVERY row of the key) -> today's truth
    Type 3 column (previous_tier) -> the immediately prior value, for A/B comparison
- The Type 1 column is the whole point and the part people get wrong. It is
  stamped on ALL versions of a key, including expired ones, so a query can join
  on the historical interval AND still read today's value off the same row --
  no second join, no window function.
- That gives three query styles off one table:
    as-was   -> join on the date interval, read `tier`
    as-is    -> join on the date interval, read `current_tier`
    delta    -> read `tier` vs `previous_tier` on one row

The trap:
- `tier` and `current_tier` are NOT the same column and are not
  interchangeable. On an EXPIRED row they differ: `tier` is what was true then,
  `current_tier` is what is true now. Grabbing the wrong one is a silent
  attribution bug -- January revenue lands under the March tier. Asserted below.
- The Type 1 column must be refreshed on every historical row at load time. Cheap
  to forget, and the symptom is that `current_tier` is only right on the open
  row -- which is exactly where you would not notice, since there `tier` and
  `current_tier` agree anyway.
- `previous_tier` on the FIRST version has no prior value: NULL, not the same
  value. `LAG` gives you that for free; a self-join invites a default.
- Type 6 does NOT remove the need for a correct half-open interval. The boundary
  double-count from `02_scd_type2_merge.py` applies unchanged.
- Storage: you carry a redundant copy of the current value on every row. With 3
  versions per creator that is fine; it is a deliberate trade of space for one
  fewer join.

Spark note:
- Built with two windows over the same partition -- LAG for the Type 3 column and
  LAST_VALUE for the Type 1 column -- so Spark shuffles once and sorts once.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("03-scd-type6-hybrid")
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


OPEN_END = "9999-12-31"

# ---------------------------------------------------------- source change log
# Creator 901 moves bronze -> silver -> gold. Creator 902 never changes.
spark.sql("""
CREATE OR REPLACE TEMP VIEW creator_changes AS
SELECT * FROM VALUES
    (901, 'bronze', DATE'2026-01-01'),
    (901, 'silver', DATE'2026-02-01'),
    (901, 'gold',   DATE'2026-03-01'),
    (902, 'silver', DATE'2026-01-15')
AS t(creator_id, tier, changed_on)
""")

from pyspark.sql import functions as F, Window as W

# Type 2 intervals via LEAD; Type 3 via LAG; Type 1 via LAST_VALUE.
BUILD_T6 = f"""
SELECT creator_id,
       tier,                                                    -- Type 2: as-was
       LAG(tier) OVER w                     AS previous_tier,   -- Type 3: prior
       LAST_VALUE(tier) OVER (
           PARTITION BY creator_id ORDER BY changed_on
           ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
       )                                    AS current_tier,    -- Type 1: as-is
       changed_on                           AS effective_from,
       COALESCE(LEAD(changed_on) OVER w, DATE'{OPEN_END}') AS effective_to,
       LEAD(changed_on) OVER w IS NULL      AS is_current
FROM creator_changes
WINDOW w AS (PARTITION BY creator_id ORDER BY changed_on)
"""

spark.sql(f"CREATE OR REPLACE TEMP VIEW dim_creator AS {BUILD_T6}")
spark.table("dim_creator").orderBy("creator_id", "effective_from").show(truncate=False)

import datetime as dt


def d(s):
    return dt.date(*(int(x) for x in s.split("-")))


DIM = """
SELECT creator_id, tier, previous_tier, current_tier,
       effective_from, effective_to, is_current
FROM dim_creator ORDER BY creator_id, effective_from
"""
expect("Q28 Type 6 dimension: 2 + 1 + 3 in one table", DIM, [
    (901, "bronze", None,     "gold",   d("2026-01-01"), d("2026-02-01"), False),
    (901, "silver", "bronze", "gold",   d("2026-02-01"), d("2026-03-01"), False),
    (901, "gold",   "silver", "gold",   d("2026-03-01"), d(OPEN_END),     True),
    (902, "silver", None,     "silver", d("2026-01-15"), d(OPEN_END),     True),
])

# DataFrame API equivalent -- same two windows.
w = W.partitionBy("creator_id").orderBy("changed_on")
w_all = w.rowsBetween(W.unboundedPreceding, W.unboundedFollowing)
df = (spark.table("creator_changes")
      .select("creator_id", "tier",
              F.lag("tier").over(w).alias("previous_tier"),
              F.last("tier").over(w_all).alias("current_tier"),
              F.col("changed_on").alias("effective_from"),
              F.coalesce(F.lead("changed_on").over(w),
                         F.lit(OPEN_END).cast("date")).alias("effective_to"),
              F.lead("changed_on").over(w).isNull().alias("is_current"))
      .orderBy("creator_id", "effective_from"))
assert [tuple(r) for r in df.collect()] == [
    (901, "bronze", None, "gold", d("2026-01-01"), d("2026-02-01"), False),
    (901, "silver", "bronze", "gold", d("2026-02-01"), d("2026-03-01"), False),
    (901, "gold", "silver", "gold", d("2026-03-01"), d(OPEN_END), True),
    (902, "silver", None, "silver", d("2026-01-15"), d(OPEN_END), True),
]
print("[PASS] Q28 DataFrame API matches SQL")

# ---------------------------------------------------------- the Type 1 column
# `current_tier` is 'gold' on EVERY 901 row, including the expired ones.
stamped = spark.sql("""
SELECT DISTINCT current_tier FROM dim_creator WHERE creator_id = 901
""").collect()
assert [r[0] for r in stamped] == ["gold"], stamped
print("[PASS] Q28 current_tier = 'gold' on all 3 versions of creator 901, expired included")

# ---------------------------------------------------------- the payoff
# One fact table, one join, three different questions.
spark.sql("""
CREATE OR REPLACE TEMP VIEW fact_video_views AS
SELECT * FROM VALUES
    (901, DATE'2026-01-10', 1000),
    (901, DATE'2026-02-14', 2000),
    (901, DATE'2026-03-20', 4000),
    (902, DATE'2026-02-01',  500)
AS t(creator_id, view_date, views)
""")

# as-was: attribute each view to the tier held AT THE TIME
AS_WAS = """
SELECT d.tier AS tier_at_the_time, SUM(f.views) AS views
FROM fact_video_views f
JOIN dim_creator d
  ON d.creator_id = f.creator_id
 AND f.view_date >= d.effective_from AND f.view_date < d.effective_to
GROUP BY d.tier ORDER BY views DESC
"""
expect("Q28 as-was: views grouped by the tier held at the time", AS_WAS, [
    ("gold", 4000), ("silver", 2500), ("bronze", 1000),
])

# as-is: same join, but read the Type 1 column -> everything under today's tier
AS_IS = """
SELECT d.current_tier AS tier_today, SUM(f.views) AS views
FROM fact_video_views f
JOIN dim_creator d
  ON d.creator_id = f.creator_id
 AND f.view_date >= d.effective_from AND f.view_date < d.effective_to
GROUP BY d.current_tier ORDER BY views DESC
"""
expect("Q28 as-is: the SAME join, reading current_tier, rolls all history to today", AS_IS, [
    ("gold", 7000), ("silver", 500),
])

print("[PASS] Q28 one join, two groupings -- no second dimension, no self-join")

# ---------------------------------------------------------- the columns differ
# On an expired row, tier != current_tier. That gap IS the bug surface.
mismatch = spark.sql("""
SELECT COUNT(*) FROM dim_creator WHERE tier <> current_tier
""").collect()[0][0]
assert mismatch == 2, mismatch
print("[PASS] Q28 2 rows have tier <> current_tier -- picking the wrong one misattributes")

# The size of that error, concretely: January's 1000 views.
jan = spark.sql("""
SELECT d.tier, d.current_tier, f.views
FROM fact_video_views f
JOIN dim_creator d
  ON d.creator_id = f.creator_id
 AND f.view_date >= d.effective_from AND f.view_date < d.effective_to
WHERE f.view_date = DATE'2026-01-10'
""").collect()[0]
assert (jan[0], jan[1], jan[2]) == ("bronze", "gold", 1000), jan
print("[PASS] Q28 January's 1000 views are 'bronze' as-was but 'gold' as-is")

# ---------------------------------------------------------- Type 3 on the first version
first = spark.sql("""
SELECT previous_tier FROM dim_creator
WHERE creator_id = 901 AND effective_from = DATE'2026-01-01'
""").collect()[0][0]
assert first is None
print("[PASS] Q28 previous_tier is NULL on the first version, not a repeated value")

# ---------------------------------------------------------- Type 3 enables delta reads
delta = """
SELECT creator_id, previous_tier, tier AS new_tier, effective_from
FROM dim_creator
WHERE previous_tier IS NOT NULL AND previous_tier <> tier
ORDER BY creator_id, effective_from
"""
expect("Q28 Type 3 column gives tier transitions with no self-join", delta, [
    (901, "bronze", "silver", d("2026-02-01")),
    (901, "silver", "gold",   d("2026-03-01")),
])

# ---------------------------------------------------------- the stale-Type-1 trap
# If the Type 1 column is only stamped on the open row, the as-is query breaks
# on exactly the rows where it matters.
stale = spark.sql("""
SELECT COALESCE(SUM(f.views), 0) AS views
FROM fact_video_views f
JOIN dim_creator d
  ON d.creator_id = f.creator_id
 AND f.view_date >= d.effective_from AND f.view_date < d.effective_to
WHERE d.is_current                      -- pretending only open rows carry it
  AND d.creator_id = 901
""").collect()[0][0]
assert stale == 4000, stale
print("[PASS] Q28 stamping current_tier only on the open row would report 4000, not 7000")
