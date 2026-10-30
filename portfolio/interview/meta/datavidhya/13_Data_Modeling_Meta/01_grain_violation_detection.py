"""
Q45: Detect grain violations (duplicate rows) in a fact table.
Article: "50 Data Modeling Interview Questions for DEs" — Warehouse Design

Meta flavor: "Ads revenue came in 1.8x higher than the finance number. Find out
why." The answer is almost always a fan-out that broke the fact grain.

How to Think:
- State the grain FIRST, as a sentence: "one row per ad_id per campaign_id per
  placement per event_date." The grain IS the uniqueness constraint, so the
  check writes itself: GROUP BY the grain columns, HAVING COUNT(*) > 1.
- A grain check is not a monitoring afterthought. It is the assertion that makes
  the model's central claim falsifiable, so it belongs in the pipeline as a
  blocking test, not in a dashboard someone looks at on Tuesdays.
- Report the BLAST RADIUS, not just the row count. "142 duplicate keys" is not
  actionable; "142 keys inflating revenue by $2.1M, all from placement=Reels
  after the Nov 3 backfill" is.

The trap:
- COUNT(*) > 1 tells you duplicates EXIST but not how much damage they do. Two
  rows that are byte-identical (a re-run that appended twice) are a different
  bug from two rows with DIFFERENT measures (a join fan-out). The first is fixed
  by dedup; the second means your join multiplied the fact. Distinguish them by
  also counting DISTINCT measures per key -- asserted below.
- Checking `COUNT(*) vs COUNT(DISTINCT pk)` on the whole table is a weaker test:
  it says "something is duplicated" without telling you which keys, so it cannot
  drive a fix.
- If the grain includes a NULLABLE column, GROUP BY groups all NULLs together
  but a JOIN on that column matches nothing -- so the check can pass while the
  join still drops rows. Never allow NULLs in grain columns (see
  `08_null_fk_unknown_member.py`).

Spark note:
- One shuffle on the grain columns. Run it on the freshly written partition
  only, not the whole table -- the check should cost seconds, or it gets
  disabled the first time someone is in a hurry.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("01-grain-violation-detection")
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


# The grain, stated as data so the check and the docs cannot drift apart.
GRAIN = ["ad_id", "campaign_id", "placement", "event_date"]

# ---------------------------------------------------------- sample data
# A Meta-shaped ads fact with TWO different kinds of duplication planted:
#   ad 300 -> two byte-identical rows      (a re-run appended twice)
#   ad 400 -> two rows with DIFFERENT spend (a join fan-out)
spark.sql("""
CREATE OR REPLACE TEMP VIEW fact_ad_performance AS
SELECT * FROM VALUES
    (100, 10, 'feed',        DATE'2026-03-01', CAST( 500.00 AS DECIMAL(12,2)), 1200),
    (200, 10, 'feed',        DATE'2026-03-01', CAST( 750.00 AS DECIMAL(12,2)), 1800),
    (300, 11, 'reels',       DATE'2026-03-01', CAST( 900.00 AS DECIMAL(12,2)), 2200),
    (300, 11, 'reels',       DATE'2026-03-01', CAST( 900.00 AS DECIMAL(12,2)), 2200),
    (400, 12, 'stories',     DATE'2026-03-01', CAST( 300.00 AS DECIMAL(12,2)),  700),
    (400, 12, 'stories',     DATE'2026-03-01', CAST( 450.00 AS DECIMAL(12,2)),  900),
    (500, 12, 'marketplace', DATE'2026-03-02', CAST(1000.00 AS DECIMAL(12,2)), 2500)
AS t(ad_id, campaign_id, placement, event_date, spend, impressions)
""")

from pyspark.sql import functions as F

# ---------------------------------------------------------- the check
GRAIN_CHECK = f"""
SELECT {', '.join(GRAIN)},
       COUNT(*) AS row_count
FROM fact_ad_performance
GROUP BY {', '.join(GRAIN)}
HAVING COUNT(*) > 1
ORDER BY row_count DESC, ad_id
"""

spark.sql(GRAIN_CHECK).show(truncate=False)

import datetime as dt

D1 = dt.date(2026, 3, 1)
expect("Q45 grain check finds both violating keys", GRAIN_CHECK, [
    (300, 11, "reels",   D1, 2),
    (400, 12, "stories", D1, 2),
])

# DataFrame API equivalent.
df = (spark.table("fact_ad_performance")
      .groupBy(*GRAIN).agg(F.count(F.lit(1)).alias("row_count"))
      .filter(F.col("row_count") > 1)
      .orderBy(F.col("row_count").desc(), F.col("ad_id")))
assert [tuple(r) for r in df.collect()] == [
    (300, 11, "reels", D1, 2), (400, 12, "stories", D1, 2),
]
print("[PASS] Q45 DataFrame API matches SQL")

# ---------------------------------------------------------- classify the damage
# Identical duplicates are a dedup problem; differing measures are a fan-out.
CLASSIFY = f"""
SELECT {', '.join(GRAIN)},
       COUNT(*)                  AS row_count,
       COUNT(DISTINCT spend)     AS distinct_spend,
       CASE WHEN COUNT(DISTINCT spend) = 1
            THEN 'identical -> dedup'
            ELSE 'differing -> join fan-out'
       END AS diagnosis
FROM fact_ad_performance
GROUP BY {', '.join(GRAIN)}
HAVING COUNT(*) > 1
ORDER BY ad_id
"""
spark.sql(CLASSIFY).show(truncate=False)
expect("Q45 the two duplicate kinds are distinguishable", CLASSIFY, [
    (300, 11, "reels",   D1, 2, 1, "identical -> dedup"),
    (400, 12, "stories", D1, 2, 2, "differing -> join fan-out"),
])

# ---------------------------------------------------------- the blast radius
# What the duplicates are actually costing, which is what you report.
IMPACT = f"""
WITH dupes AS (
    SELECT {', '.join(GRAIN)}, COUNT(*) AS n, SUM(spend) AS dup_spend, MIN(spend) AS keep_spend
    FROM fact_ad_performance
    GROUP BY {', '.join(GRAIN)}
    HAVING COUNT(*) > 1
)
SELECT COUNT(*)                            AS violating_keys,
       SUM(n) - COUNT(*)                   AS excess_rows,
       ROUND(SUM(dup_spend - keep_spend), 2) AS overstated_spend
FROM dupes
"""
spark.sql(IMPACT).show(truncate=False)
expect("Q45 blast radius is quantified, not just counted", IMPACT, [(2, 2, 1350.00)])

total = spark.sql("SELECT ROUND(SUM(spend), 2) FROM fact_ad_performance").collect()[0][0]
assert float(total) == 4800.00, total
print(f"[PASS] Q45 reported spend {total} overstates truth by 1350.00 (28%)")

# ---------------------------------------------------------- the weaker check
# Table-level counts detect that something is wrong but name no key.
weak = spark.sql(f"""
SELECT COUNT(*) AS rows, COUNT(DISTINCT {', '.join(GRAIN)}) AS distinct_keys
FROM fact_ad_performance
""").collect()[0]
assert (weak[0], weak[1]) == (7, 5), weak
print("[PASS] Q45 7 rows vs 5 distinct keys flags a problem but identifies no key")

# ---------------------------------------------------------- a clean table passes
spark.sql("""
CREATE OR REPLACE TEMP VIEW fact_ad_performance AS
SELECT * FROM VALUES
    (100, 10, 'feed',  DATE'2026-03-01', CAST(500.00 AS DECIMAL(12,2)), 1200),
    (200, 10, 'feed',  DATE'2026-03-01', CAST(750.00 AS DECIMAL(12,2)), 1800),
    (300, 11, 'reels', DATE'2026-03-01', CAST(900.00 AS DECIMAL(12,2)), 2200)
AS t(ad_id, campaign_id, placement, event_date, spend, impressions)
""")
expect("Q45 a table at its stated grain returns no rows", GRAIN_CHECK, [])
print("[PASS] Q45 the check is a blocking assertion: empty result == grain holds")

# ---------------------------------------------------------- the NULL grain trap
# GROUP BY groups NULLs together, so the check PASSES -- but a join on that
# column matches nothing and silently drops the row.
spark.sql("""
CREATE OR REPLACE TEMP VIEW fact_ad_performance AS
SELECT * FROM VALUES
    (100, 10, 'feed',                   DATE'2026-03-01', CAST(500.00 AS DECIMAL(12,2)), 1200),
    (200, 10, CAST(NULL AS STRING),     DATE'2026-03-01', CAST(750.00 AS DECIMAL(12,2)), 1800)
AS t(ad_id, campaign_id, placement, event_date, spend, impressions)
""")
expect("Q45 a NULL grain column still passes the duplicate check", GRAIN_CHECK, [])

dropped = spark.sql("""
SELECT COUNT(*) FROM fact_ad_performance f
JOIN (SELECT 'feed' AS placement UNION ALL SELECT 'reels') d
  ON d.placement = f.placement
""").collect()[0][0]
assert dropped == 1, dropped
print("[PASS] Q45 ...yet the NULL row is silently dropped by the dimension join "
      "(1 of 2 survives) -- grain columns must be NOT NULL")

# ---- MySQL way ----------------------------------------------------------
# CREATE TABLE + sample data:
#   CREATE TABLE fact_ad_performance (
#       ad_id          INT             NOT NULL,
#       campaign_id    INT             NOT NULL,
#       placement      VARCHAR(32)     NOT NULL,
#       event_date     DATE            NOT NULL,
#       spend          DECIMAL(12,2)   NOT NULL,
#       impressions    INT             NOT NULL,
#       KEY idx_fact_ad_perf_ad (ad_id),
#       KEY idx_fact_ad_perf_date (event_date),
#       KEY idx_fact_ad_perf_grain (ad_id, campaign_id, placement, event_date)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO fact_ad_performance
#       (ad_id, campaign_id, placement, event_date, spend, impressions) VALUES
#       (100, 10, 'feed',        '2026-03-01',  500.00, 1200),
#       (200, 10, 'feed',        '2026-03-01',  750.00, 1800),
#       (300, 11, 'reels',       '2026-03-01',  900.00, 2200),
#       (300, 11, 'reels',       '2026-03-01',  900.00, 2200),
#       (400, 12, 'stories',     '2026-03-01',  300.00,  700),
#       (400, 12, 'stories',     '2026-03-01',  450.00,  900),
#       (500, 12, 'marketplace', '2026-03-02', 1000.00, 2500);
#
#   -- Q45 grain check finds both violating keys (expect block)
#   SELECT ad_id, campaign_id, placement, event_date, COUNT(*) AS row_count
#   FROM fact_ad_performance
#   GROUP BY ad_id, campaign_id, placement, event_date
#   HAVING COUNT(*) > 1
#   ORDER BY row_count DESC, ad_id;
#
#   -- Q45 the two duplicate kinds are distinguishable (expect block)
#   SELECT ad_id, campaign_id, placement, event_date,
#          COUNT(*)                  AS row_count,
#          COUNT(DISTINCT spend)     AS distinct_spend,
#          CASE WHEN COUNT(DISTINCT spend) = 1
#               THEN 'identical -> dedup'
#               ELSE 'differing -> join fan-out'
#          END AS diagnosis
#   FROM fact_ad_performance
#   GROUP BY ad_id, campaign_id, placement, event_date
#   HAVING COUNT(*) > 1
#   ORDER BY ad_id;
#
#   -- Q45 blast radius is quantified, not just counted (expect block)
#   WITH dupes AS (
#       SELECT ad_id, campaign_id, placement, event_date,
#              COUNT(*) AS n, SUM(spend) AS dup_spend, MIN(spend) AS keep_spend
#       FROM fact_ad_performance
#       GROUP BY ad_id, campaign_id, placement, event_date
#       HAVING COUNT(*) > 1
#   )
#   SELECT COUNT(*)                              AS violating_keys,
#          SUM(n) - COUNT(*)                     AS excess_rows,
#          ROUND(SUM(dup_spend - keep_spend), 2) AS overstated_spend
#   FROM dupes;
#
#   -- Q45 a table at its stated grain returns no rows (cleaned table expect block)
#   DELETE FROM fact_ad_performance WHERE ad_id IN (300, 400, 500);
#   -- then re-run the grain check; result is empty.
#
#   -- Q45 a NULL grain column still passes the duplicate check (expect block):
#   INSERT INTO fact_ad_performance
#       (ad_id, campaign_id, placement, event_date, spend, impressions) VALUES
#       (100, 10, 'feed',   '2026-03-01', 500.00, 1200),
#       (200, 10, NULL,     '2026-03-01', 750.00, 1800);
#   -- grain check returns 0 rows; the NULL still fails the dimension join.
#
# MySQL 8.0+ notes: GROUP BY/HAVING behaves the same; COUNT(DISTINCT spend) works
# identically. The NULL grain trap is identical -- GROUP BY groups NULLs together
# but the dimension join still drops the row. A covering index on the grain
# columns (idx_fact_ad_perf_grain) keeps the check cheap at Meta volume so the
# pipeline does not disable it when someone is in a hurry.
