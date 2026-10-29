"""
Q33: What is a junk dimension?
Article: "50 Data Modeling Interview Questions for DEs" — Advanced Patterns

Meta flavor: "fact_ad_impression carries 6 low-cardinality flags — is_video,
is_autoplay, is_sponsored, placement_type, device_class, sound_on. At 40 billion
rows a day those columns are most of the table. Clean it up."

How to Think:
- A junk dimension collapses several unrelated, low-cardinality flags into ONE
  dimension whose rows are the observed COMBINATIONS of those flags. The fact
  then carries a single integer surrogate key instead of six columns.
- The win is arithmetic and worth stating out loud: 6 flags x 40B rows of string
  columns versus 1 x 4-byte int, with the strings stored once in a dimension
  that has at most a few dozen rows. It also removes six tiny dimension tables
  that would otherwise clutter the star.
- "Junk" is about the ATTRIBUTES, not the quality — they are flags with no
  natural home, not bad data.
- Build it from the OBSERVED combinations, not the Cartesian product. The
  theoretical maximum here is 2x2x2x3x3x2 = 144; real traffic uses far fewer,
  and materialising 144 rows to use 5 is how the pattern gets a bad name.

The trap:
- A junk dimension is for flags you filter/group on TOGETHER and that are
  LOW-cardinality. Putting a high-cardinality attribute in it is the classic
  error: add `country` (200 values) and the combination count multiplies by 200,
  so the "small" dimension is suddenly larger than some real dimensions and the
  key stops being stable. Asserted below.
- The surrogate key must be assigned DETERMINISTICALLY (order the combinations)
  or a rebuild renumbers the dimension and every historical fact row now points
  at the wrong combination. This is the failure that silently corrupts history.
- A NEW combination appearing in tomorrow's data must ADD a row, not renumber
  existing ones. That is the same requirement stated as an incremental load.
- The flags must be genuinely unrelated. If two of them are correlated (say
  `is_video` and `sound_on` only vary together), you have encoded a hierarchy
  into a flat combination table and lost the ability to reason about it.

Spark note:
- The dimension broadcasts (dozens of rows), so the fact-side lookup is a
  broadcast hash join -- no shuffle. On write, resolve the key once in the ETL
  rather than joining six string columns at query time.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("05-junk-dimension")
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


FLAGS = ["is_video", "is_autoplay", "is_sponsored", "placement_type"]

# ---------------------------------------------------------- the wide fact
# Impressions carrying the flags inline -- what we are trying to get rid of.
spark.sql("""
CREATE OR REPLACE TEMP VIEW raw_impressions AS
SELECT * FROM VALUES
    (1, 501, TRUE,  TRUE,  TRUE,  'feed'),
    (2, 501, TRUE,  TRUE,  TRUE,  'feed'),
    (3, 502, FALSE, FALSE, TRUE,  'feed'),
    (4, 502, TRUE,  FALSE, FALSE, 'reels'),
    (5, 503, TRUE,  TRUE,  TRUE,  'reels'),
    (6, 503, FALSE, FALSE, FALSE, 'stories'),
    (7, 504, TRUE,  TRUE,  TRUE,  'feed'),
    (8, 504, TRUE,  FALSE, FALSE, 'reels')
AS t(impression_id, ad_id, is_video, is_autoplay, is_sponsored, placement_type)
""")

from pyspark.sql import functions as F, Window as W

# ---------------------------------------------------------- build the dimension
# DETERMINISTIC key: order the observed combinations, then number them.
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW dim_impression_flags AS
SELECT ROW_NUMBER() OVER (ORDER BY {', '.join(FLAGS)}) AS flag_key,
       {', '.join(FLAGS)}
FROM (SELECT DISTINCT {', '.join(FLAGS)} FROM raw_impressions)
""")
spark.table("dim_impression_flags").orderBy("flag_key").show(truncate=False)

DIM = f"SELECT flag_key, {', '.join(FLAGS)} FROM dim_impression_flags ORDER BY flag_key"
expect("Q33 junk dimension holds only the OBSERVED combinations", DIM, [
    (1, False, False, False, "stories"),
    (2, False, False, True,  "feed"),
    (3, True,  False, False, "reels"),
    (4, True,  True,  True,  "feed"),
    (5, True,  True,  True,  "reels"),
])

observed = spark.table("dim_impression_flags").count()
cartesian = 2 * 2 * 2 * 3      # is_video x is_autoplay x is_sponsored x 3 placements
assert (observed, cartesian) == (5, 24), (observed, cartesian)
print(f"[PASS] Q33 {observed} observed combinations vs {cartesian} theoretical -- "
      "build from what occurs, not the Cartesian product")

# ---------------------------------------------------------- the narrow fact
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW fact_ad_impression AS
SELECT r.impression_id, r.ad_id, d.flag_key
FROM raw_impressions r
JOIN dim_impression_flags d
  ON {' AND '.join(f'd.{c} = r.{c}' for c in FLAGS)}
""")

narrow_cols = spark.table("fact_ad_impression").columns
assert narrow_cols == ["impression_id", "ad_id", "flag_key"], narrow_cols
print(f"[PASS] Q33 fact went from 6 columns to {len(narrow_cols)}: {narrow_cols}")

# Every impression still resolves to exactly one flag combination.
assert spark.table("fact_ad_impression").count() == 8
dupes = spark.sql("""
SELECT impression_id, COUNT(*) FROM fact_ad_impression
GROUP BY impression_id HAVING COUNT(*) > 1
""").count()
assert dupes == 0
print("[PASS] Q33 8 impressions in, 8 out, no fan-out -- the lookup is a true 1:1")

# ---------------------------------------------------------- queries still work
BY_FLAGS = """
SELECT d.placement_type, d.is_video, COUNT(*) AS impressions
FROM fact_ad_impression f
JOIN dim_impression_flags d ON d.flag_key = f.flag_key
GROUP BY d.placement_type, d.is_video
ORDER BY impressions DESC, d.placement_type
"""
expect("Q33 grouping through the dimension matches the raw table", BY_FLAGS, [
    ("feed",    True,  3),
    ("reels",   True,  3),
    ("feed",    False, 1),
    ("stories", False, 1),
])

raw_equiv = spark.sql("""
SELECT placement_type, is_video, COUNT(*) AS impressions
FROM raw_impressions GROUP BY placement_type, is_video
ORDER BY impressions DESC, placement_type
""").collect()
assert [(r[0], r[1], r[2]) for r in raw_equiv] == [
    ("feed", True, 3), ("reels", True, 3), ("feed", False, 1), ("stories", False, 1),
]
print("[PASS] Q33 identical answer from the raw wide table -- the refactor is lossless")

# DataFrame API equivalent.
dim = spark.table("dim_impression_flags")
df = (spark.table("fact_ad_impression")
      .join(F.broadcast(dim), "flag_key")
      .groupBy("placement_type", "is_video")
      .agg(F.count(F.lit(1)).alias("impressions"))
      .orderBy(F.col("impressions").desc(), F.col("placement_type")))
assert [tuple(r) for r in df.collect()] == [
    ("feed", True, 3), ("reels", True, 3), ("feed", False, 1), ("stories", False, 1),
]
print("[PASS] Q33 DataFrame API matches SQL")

# ---------------------------------------------------------- the high-cardinality trap
# Adding `country` to the junk dimension multiplies the combinations.
spark.sql("""
CREATE OR REPLACE TEMP VIEW raw_with_country AS
SELECT r.*, c.country
FROM raw_impressions r
CROSS JOIN (SELECT explode(array('US','IN','BR','DE','JP')) AS country) c
""")
bloated = spark.sql(f"""
SELECT COUNT(*) FROM (
    SELECT DISTINCT {', '.join(FLAGS)}, country FROM raw_with_country
)
""").collect()[0][0]
assert (observed, bloated) == (5, 25), (observed, bloated)
print(f"[PASS] Q33 adding a 5-value country column takes the dimension from "
      f"{observed} to {bloated} rows -- with 200 countries it is 1000")

# ---------------------------------------------------------- the renumbering trap
# A rebuild that drops a combination RENUMBERS the survivors, so old fact rows
# now point at a different combination. This is silent history corruption.
before = {r.flag_key: (r.is_video, r.placement_type)
          for r in spark.table("dim_impression_flags").collect()}
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW dim_rebuilt AS
SELECT ROW_NUMBER() OVER (ORDER BY {', '.join(FLAGS)}) AS flag_key, {', '.join(FLAGS)}
FROM (SELECT DISTINCT {', '.join(FLAGS)} FROM raw_impressions
      WHERE placement_type <> 'stories')
""")
after = {r.flag_key: (r.is_video, r.placement_type)
         for r in spark.table("dim_rebuilt").collect()}
assert before[1] == (False, "stories") and after[1] == (False, "feed"), (before[1], after[1])
print(f"[PASS] Q33 after a rebuild, flag_key 1 means {after[1]} instead of {before[1]} "
      "-- every historical fact row is now mislabelled")

# The fix: a stable hash key, immune to which combinations happen to be present.
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW dim_stable AS
SELECT md5(concat_ws('|', {', '.join(f'CAST({c} AS STRING)' for c in FLAGS)})) AS flag_key,
       {', '.join(FLAGS)}
FROM (SELECT DISTINCT {', '.join(FLAGS)} FROM raw_impressions)
""")
key_full = spark.sql("""
SELECT flag_key FROM dim_stable WHERE placement_type = 'feed' AND is_video
""").collect()[0][0]
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW dim_stable_subset AS
SELECT md5(concat_ws('|', {', '.join(f'CAST({c} AS STRING)' for c in FLAGS)})) AS flag_key,
       {', '.join(FLAGS)}
FROM (SELECT DISTINCT {', '.join(FLAGS)} FROM raw_impressions
      WHERE placement_type <> 'stories')
""")
key_subset = spark.sql("""
SELECT flag_key FROM dim_stable_subset WHERE placement_type = 'feed' AND is_video
""").collect()[0][0]
assert key_full == key_subset, (key_full, key_subset)
print(f"[PASS] Q33 a hash key survives the rebuild unchanged ({key_full[:12]}...) "
      "-- deterministic, order-independent, safe to recompute")

# ---- MySQL way ----------------------------------------------------------
# CREATE TABLE + sample data:
#   CREATE TABLE raw_impressions (
#       impression_id  INT         NOT NULL,
#       ad_id          INT         NOT NULL,
#       is_video       TINYINT(1)  NOT NULL,
#       is_autoplay    TINYINT(1)  NOT NULL,
#       is_sponsored   TINYINT(1)  NOT NULL,
#       placement_type VARCHAR(16) NOT NULL,
#       PRIMARY KEY (impression_id),
#       KEY idx_raw_impressions_ad (ad_id)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO raw_impressions
#       (impression_id, ad_id, is_video, is_autoplay, is_sponsored, placement_type) VALUES
#       (1, 501, 1, 1, 1, 'feed'),
#       (2, 501, 1, 1, 1, 'feed'),
#       (3, 502, 0, 0, 1, 'feed'),
#       (4, 502, 1, 0, 0, 'reels'),
#       (5, 503, 1, 1, 1, 'reels'),
#       (6, 503, 0, 0, 0, 'stories'),
#       (7, 504, 1, 1, 1, 'feed'),
#       (8, 504, 1, 0, 0, 'reels');
#
#   CREATE TABLE dim_impression_flags (
#       flag_key        CHAR(32)    NOT NULL,
#       is_video        TINYINT(1)  NOT NULL,
#       is_autoplay     TINYINT(1)  NOT NULL,
#       is_sponsored    TINYINT(1)  NOT NULL,
#       placement_type  VARCHAR(16) NOT NULL,
#       PRIMARY KEY (flag_key)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO dim_impression_flags
#       (flag_key, is_video, is_autoplay, is_sponsored, placement_type) VALUES
#       (MD5(CONCAT_WS('|', '0', '0', '0', 'stories')), 0, 0, 0, 'stories'),
#       (MD5(CONCAT_WS('|', '0', '0', '1', 'feed')),    0, 0, 1, 'feed'),
#       (MD5(CONCAT_WS('|', '1', '0', '0', 'reels')),   1, 0, 0, 'reels'),
#       (MD5(CONCAT_WS('|', '1', '1', '1', 'feed')),    1, 1, 1, 'feed'),
#       (MD5(CONCAT_WS('|', '1', '1', '1', 'reels')),   1, 1, 1, 'reels');
#
#   CREATE TABLE fact_ad_impression (
#       impression_id  INT      NOT NULL,
#       ad_id          INT      NOT NULL,
#       flag_key       CHAR(32) NOT NULL,
#       PRIMARY KEY (impression_id),
#       KEY idx_fact_impression_flag (flag_key)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO fact_ad_impression (impression_id, ad_id, flag_key) VALUES
#       (1, 501, MD5(CONCAT_WS('|', '1', '1', '1', 'feed'))),
#       (2, 501, MD5(CONCAT_WS('|', '1', '1', '1', 'feed'))),
#       (3, 502, MD5(CONCAT_WS('|', '0', '0', '1', 'feed'))),
#       (4, 502, MD5(CONCAT_WS('|', '1', '0', '0', 'reels'))),
#       (5, 503, MD5(CONCAT_WS('|', '1', '1', '1', 'reels'))),
#       (6, 503, MD5(CONCAT_WS('|', '0', '0', '0', 'stories'))),
#       (7, 504, MD5(CONCAT_WS('|', '1', '1', '1', 'feed'))),
#       (8, 504, MD5(CONCAT_WS('|', '1', '0', '0', 'reels')));
#
#   -- Q33 junk dimension holds only the OBSERVED combinations (expect block).
#   -- Use MD5(CONCAT_WS(...)) as a STABLE key -- ROW_NUMBER() renumbers on
#   -- rebuild, which silently mislabels every historical fact row.
#   SELECT flag_key, is_video, is_autoplay, is_sponsored, placement_type
#   FROM dim_impression_flags ORDER BY flag_key;
#
#   -- Q33 grouping through the dimension matches the raw table (expect block)
#   SELECT d.placement_type, d.is_video, COUNT(*) AS impressions
#   FROM fact_ad_impression f
#   JOIN dim_impression_flags d ON d.flag_key = f.flag_key
#   GROUP BY d.placement_type, d.is_video
#   ORDER BY impressions DESC, d.placement_type;
#
# MySQL 8.0+ notes: a CHAR(32) MD5 hash key is the stable alternative to
# ROW_NUMBER() -- the Spark renumbering trap (rebuild flips flag_key=1 from
# 'stories' to 'feed') is identical in MySQL but a hash key is order-
# independent and safe to recompute. TINYINT(1) replaces BOOLEAN. INDEX on
# flag_key keeps the fact-side lookup a single-row probe; with 40B impressions
# a day that broadcast-on-write pattern is the one that scales.
