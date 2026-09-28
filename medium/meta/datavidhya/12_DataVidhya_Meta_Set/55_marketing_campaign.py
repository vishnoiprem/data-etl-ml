"""
Q55: Marketing Campaign Effectiveness   [Medium | Inner Joins, Aggregate Functions]
DataVidhya slug: marketing-campaign

Three tables (impressions, clicks, conversions). Per campaign that was shown at
least once: impressions (rows), clicks (DISTINCT users), conversions (rows),
total_revenue, ctr, conversion_rate (NULL when clicks = 0).

How to Think:
- AGGREGATE EACH TABLE FIRST, then LEFT JOIN the three one-row-per-campaign
  summaries. Joining raw tables multiplies rows across all three and every
  number is wrong -- the classic multi-fact-table mistake.
- `impressions` is the driving table: "each campaign that was shown at least
  once." Drive from clicks or conversions and C004 vanishes.
- Read the counting rules per column -- they deliberately differ:
      impressions -> COUNT(*)                rows
      clicks      -> COUNT(DISTINCT user_id) users
      conversions -> COUNT(*)                rows
  Using COUNT(*) for clicks gives C001 three instead of two (U001 clicked twice).

The trap:
- The fan-out. C001 has 4 impressions x 3 clicks x 2 conversions = 24 rows if
  joined raw. That inflates everything simultaneously, so the ratios can still
  look like plausible percentages.
- conversion_rate is NULL for C004, not 0. Both denominators are zero-valued,
  and the spec asks for DIFFERENT answers: ctr = 0.00 (because impressions is 4,
  a real denominator, and clicks is 0) but conversion_rate = NULL (because
  clicks itself is the denominator and it is 0). Wrapping the whole thing in
  COALESCE(..., 0) is the intended failure. Spark's x/0 yields NULL for free --
  so the correct answer here is to NOT defend against it.
- COALESCE the COUNTS to 0 (C004 has no click or conversion rows at all) but
  leave the RATE null.
- Percentages need 100.0, or integer division truncates.

Spark note:
- Three small pre-aggregations, then two broadcast joins. This is also the
  cheapest shape on real data: each fact table is reduced to one row per
  campaign before anything is joined.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("55-marketing-campaign")
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
# U001 clicks C001 twice (so clicks = 2 distinct, not 3).
# C004 has impressions only -> ctr 0.00 but conversion_rate NULL.
spark.sql("""
CREATE OR REPLACE TEMP VIEW clicks AS
SELECT * FROM VALUES
    ('C001', 'U001', DATE'2024-01-02'),
    ('C001', 'U002', DATE'2024-01-01'),
    ('C002', 'U004', DATE'2024-01-02'),
    ('C002', 'U005', DATE'2024-01-05'),
    ('C003', 'U002', DATE'2024-01-10'),
    ('C001', 'U001', DATE'2024-01-03')
AS t(campaign_id, user_id, click_date)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW conversions AS
SELECT * FROM VALUES
    ('C001', 'U001', DATE'2024-01-03', CAST(150 AS DECIMAL(12,2))),
    ('C001', 'U002', DATE'2024-01-02', CAST(200 AS DECIMAL(12,2))),
    ('C002', 'U004', DATE'2024-01-05', CAST(300 AS DECIMAL(12,2))),
    ('C003', 'U002', DATE'2024-01-12', CAST(250 AS DECIMAL(12,2)))
AS t(campaign_id, user_id, conversion_date, revenue)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW impressions AS
SELECT * FROM VALUES
    ('C001', 'U001', DATE'2024-01-01'),
    ('C001', 'U001', DATE'2024-01-02'),
    ('C001', 'U002', DATE'2024-01-01'),
    ('C001', 'U003', DATE'2024-01-05'),
    ('C002', 'U002', DATE'2024-01-01'),
    ('C002', 'U004', DATE'2024-01-02'),
    ('C002', 'U004', DATE'2024-01-03'),
    ('C002', 'U005', DATE'2024-01-05'),
    ('C003', 'U001', DATE'2024-01-10'),
    ('C003', 'U002', DATE'2024-01-10'),
    ('C003', 'U003', DATE'2024-01-12'),
    ('C004', 'U006', DATE'2024-01-06'),
    ('C004', 'U007', DATE'2024-01-07')
AS t(campaign_id, user_id, impression_date)
""")

from pyspark.sql import functions as F

# conversion_rate is deliberately NOT coalesced: x/0 -> NULL is the spec.
SQL = """
WITH imp AS (
    SELECT campaign_id, COUNT(*) AS impressions
    FROM impressions GROUP BY campaign_id
),
clk AS (
    SELECT campaign_id, COUNT(DISTINCT user_id) AS clicks   -- DISTINCT users
    FROM clicks GROUP BY campaign_id
),
conv AS (
    SELECT campaign_id, COUNT(*) AS conversions, SUM(revenue) AS total_revenue
    FROM conversions GROUP BY campaign_id
)
SELECT i.campaign_id,
       i.impressions,
       COALESCE(c.clicks, 0)         AS clicks,
       COALESCE(v.conversions, 0)    AS conversions,
       COALESCE(v.total_revenue, 0)  AS total_revenue,
       ROUND(COALESCE(c.clicks, 0) * 100.0 / i.impressions, 2)  AS ctr,
       ROUND(COALESCE(v.conversions, 0) * 100.0 / c.clicks, 2)  AS conversion_rate
FROM imp i
LEFT JOIN clk  c ON c.campaign_id = i.campaign_id
LEFT JOIN conv v ON v.campaign_id = i.campaign_id
ORDER BY i.campaign_id
"""

spark.sql(SQL).show(truncate=False)

EXPECTED = [
    ("C001", 4, 2, 2, 350.0,  50.00, 100.00),
    ("C002", 4, 2, 1, 300.0,  50.00,  50.00),
    ("C003", 3, 1, 1, 250.0,  33.33, 100.00),
    ("C004", 2, 0, 0,   0.0,   0.00,  None),
]
expect("Q55 campaign effectiveness", SQL, EXPECTED)

# DataFrame API equivalent.
imp = spark.table("impressions").groupBy("campaign_id").agg(
    F.count(F.lit(1)).alias("impressions"))
clk = spark.table("clicks").groupBy("campaign_id").agg(
    F.countDistinct("user_id").alias("clicks"))
conv = spark.table("conversions").groupBy("campaign_id").agg(
    F.count(F.lit(1)).alias("conversions"), F.sum("revenue").alias("total_revenue"))
df = (imp.join(F.broadcast(clk), "campaign_id", "left")
      .join(F.broadcast(conv), "campaign_id", "left")
      .select("campaign_id", "impressions",
              F.coalesce("clicks", F.lit(0)).alias("clicks"),
              F.coalesce("conversions", F.lit(0)).alias("conversions"),
              F.coalesce("total_revenue", F.lit(0)).alias("total_revenue"),
              F.round(F.coalesce("clicks", F.lit(0)) * F.lit(100.0)
                      / F.col("impressions"), 2).alias("ctr"),
              F.round(F.coalesce("conversions", F.lit(0)) * F.lit(100.0)
                      / F.col("clicks"), 2).alias("conversion_rate"))
      .orderBy("campaign_id"))
assert [(r[0], r[1], r[2], r[3], float(r[4]), float(r[5]),
         None if r[6] is None else float(r[6])) for r in df.collect()] == EXPECTED
print("[PASS] Q55 DataFrame API matches SQL")

# ------------------------------------------------ the fan-out trap
fanned = spark.sql("""
SELECT i.campaign_id, COUNT(*) AS rows_after_join
FROM impressions i
LEFT JOIN clicks c      ON c.campaign_id = i.campaign_id
LEFT JOIN conversions v ON v.campaign_id = i.campaign_id
GROUP BY i.campaign_id ORDER BY i.campaign_id
""").collect()
assert [(r[0], r[1]) for r in fanned] == [
    ("C001", 24), ("C002", 8), ("C003", 3), ("C004", 2),
], fanned
print("[PASS] Q55 joining raw tables blows C001 up to 24 rows (4 x 3 x 2)")

# ------------------------------------------------ DISTINCT users vs rows
click_counts = spark.sql("""
SELECT campaign_id, COUNT(*) AS click_rows, COUNT(DISTINCT user_id) AS click_users
FROM clicks GROUP BY campaign_id ORDER BY campaign_id
""").collect()
assert [(r[0], r[1], r[2]) for r in click_counts] == [
    ("C001", 3, 2), ("C002", 2, 2), ("C003", 1, 1),
], click_counts
print("[PASS] Q55 C001 has 3 click rows but 2 distinct users -- ctr uses 2")

# ------------------------------------------------ the NULL conversion_rate trap
c004 = [r for r in spark.sql(SQL).collect() if r[0] == "C004"][0]
assert float(c004[5]) == 0.0 and c004[6] is None, c004
print("[PASS] Q55 C004 has ctr 0.00 but conversion_rate NULL -- not both zero")

coalesced = spark.sql("""
WITH imp AS (SELECT campaign_id, COUNT(*) AS impressions FROM impressions GROUP BY campaign_id),
     clk AS (SELECT campaign_id, COUNT(DISTINCT user_id) AS clicks FROM clicks GROUP BY campaign_id),
     conv AS (SELECT campaign_id, COUNT(*) AS conversions FROM conversions GROUP BY campaign_id)
SELECT i.campaign_id,
       COALESCE(ROUND(COALESCE(v.conversions,0) * 100.0 / c.clicks, 2), 0) AS conversion_rate
FROM imp i LEFT JOIN clk c ON c.campaign_id=i.campaign_id
           LEFT JOIN conv v ON v.campaign_id=i.campaign_id
WHERE i.campaign_id = 'C004'
""").collect()[0][1]
assert float(coalesced) == 0.0
print("[PASS] Q55 a blanket COALESCE turns C004's NULL rate into 0.00 -- wrong")

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports the same three-CTE pre-aggregation + LEFT JOIN shape.
# The conversion_rate formula is deliberately NOT coalesced to 0: x/0 is
# NULL in MySQL too, and the spec asks for NULL there.
#
# CREATE TABLE impressions (
#     campaign_id     VARCHAR(8) NOT NULL,
#     user_id         INT        NOT NULL,
#     impression_date DATE       NOT NULL,
#     PRIMARY KEY (campaign_id, user_id, impression_date),
#     KEY ix_imp_campaign (campaign_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE clicks (
#     campaign_id VARCHAR(8) NOT NULL,
#     user_id     INT        NOT NULL,
#     click_date  DATE       NOT NULL,
#     PRIMARY KEY (campaign_id, user_id, click_date),
#     KEY ix_clk_campaign (campaign_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE conversions (
#     campaign_id    VARCHAR(8)    NOT NULL,
#     user_id        INT           NOT NULL,
#     conversion_date DATE         NOT NULL,
#     revenue        DECIMAL(12,2) NOT NULL,
#     PRIMARY KEY (campaign_id, user_id, conversion_date),
#     KEY ix_conv_campaign (campaign_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO impressions (campaign_id, user_id, impression_date) VALUES
#     ('C001','U001','2024-01-01'),('C001','U001','2024-01-02'),
#     ('C001','U002','2024-01-01'),('C001','U003','2024-01-05'),
#     ('C002','U002','2024-01-01'),('C002','U004','2024-01-02'),
#     ('C002','U004','2024-01-03'),('C002','U005','2024-01-05'),
#     ('C003','U001','2024-01-10'),('C003','U002','2024-01-10'),
#     ('C003','U003','2024-01-12'),('C004','U006','2024-01-06'),
#     ('C004','U007','2024-01-07');
#
# INSERT INTO clicks (campaign_id, user_id, click_date) VALUES
#     ('C001','U001','2024-01-02'),('C001','U002','2024-01-01'),
#     ('C002','U004','2024-01-02'),('C002','U005','2024-01-05'),
#     ('C003','U002','2024-01-10'),('C001','U001','2024-01-03');
#
# INSERT INTO conversions (campaign_id, user_id, conversion_date, revenue) VALUES
#     ('C001','U001','2024-01-03', 150.00),
#     ('C001','U002','2024-01-02', 200.00),
#     ('C002','U004','2024-01-05', 300.00),
#     ('C003','U002','2024-01-12', 250.00);
#
# WITH imp AS (
#     SELECT campaign_id, COUNT(*) AS impressions FROM impressions GROUP BY campaign_id
# ),
# clk AS (
#     SELECT campaign_id, COUNT(DISTINCT user_id) AS clicks FROM clicks GROUP BY campaign_id
# ),
# conv AS (
#     SELECT campaign_id, COUNT(*) AS conversions, SUM(revenue) AS total_revenue
#     FROM conversions GROUP BY campaign_id
# )
# SELECT i.campaign_id,
#        i.impressions,
#        COALESCE(c.clicks, 0)        AS clicks,
#        COALESCE(v.conversions, 0)   AS conversions,
#        COALESCE(v.total_revenue, 0) AS total_revenue,
#        ROUND(COALESCE(c.clicks, 0) * 100.0 / i.impressions, 2) AS ctr,
#        ROUND(COALESCE(v.conversions, 0) * 100.0 / c.clicks, 2) AS conversion_rate
# FROM imp i
# LEFT JOIN clk  c ON c.campaign_id = i.campaign_id
# LEFT JOIN conv v ON v.campaign_id = i.campaign_id
# ORDER BY i.campaign_id;
#
# -- Expected:
# -- C001 4 2 2 350.00  50.00 100.00
# -- C002 4 2 1 300.00  50.00  50.00
# -- C003 3 1 1 250.00  33.33 100.00
# -- C004 2 0 0   0.00   0.00   NULL
