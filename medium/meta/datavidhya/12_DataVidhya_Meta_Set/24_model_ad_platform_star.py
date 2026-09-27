"""
Q24: Ad Platform Click & Impression Analytics   [Medium | Dim Model — star schema]
Tags: Star Schema, multiple fact tables

Dashboard for ad performance: impressions, clicks, conversions.

THE ANSWER IS "MULTIPLE FACT TABLES AT DIFFERENT GRAINS." The tag says so, and
the reason is a hard one:

  fact_impression = one row per impression   (trillions/day at Meta scale)
  fact_click      = one row per click        (~1% of impressions)
  fact_conversion = one row per conversion   (~1% of clicks)

Why NOT one `ad_events` table with an event_type column:
  1. Each event has DIFFERENT attributes. Impressions have viewability and
     placement; clicks have a click position; conversions have a value and an
     attribution window. One table means most columns are NULL most of the time.
  2. The volume ratio is ~10,000:1. A single table forces every click query to
     scan impression-sized data.
  3. Billing runs off these numbers. Grain confusion here is a financial bug,
     not a reporting inconvenience.

THE CHAIN: fact_click carries impression_key, and fact_conversion carries
click_key. That lets you attribute a conversion back to the exact impression
that caused it — the whole point of an ad warehouse.

fact_campaign_daily = PERIODIC SNAPSHOT, one row per campaign per day.
  It exists ONLY so dashboards never scan the raw facts. It is pre-aggregated,
  and it is where CTR/CVR are computed for reporting. Naming the periodic
  snapshot as a deliberate serving layer (not a cache) is a senior signal.

CTR MUST BE A RATIO OF TOTALS, not an average of ratios:
      correct: SUM(clicks) / SUM(impressions)
      wrong:   AVG(clicks / impressions)     <- weights small days equally
This is the single most common error on ad dashboards.

THE INTEGER-DIVISION TRAP, precisely:
  Meta's reported screen question is "CTR by app to 2 decimals" and the trap is
  integer division. Be accurate about WHERE it bites:
    - PRESTO:  COUNT(x) / COUNT(y) on BIGINTs does INTEGER division -> 0
    - SPARK:   `/` always returns DOUBLE -> 0.25, no trap
    - HIVE:    `/` returns DOUBLE -> no trap
  Meta runs Presto, so in the real interview you MUST multiply by 100.0 or
  CAST. This file asserts Spark's actual behaviour and documents the difference
  rather than pretending the trap reproduces here.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("24-model-ad-platform-star")
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



DDL = """
-- Grain: one row per impression. Partitioned by date; the largest table.
CREATE TABLE fact_impression (
  impression_key BIGINT,      -- PK (surrogate)
  ad_key         BIGINT,      -- FK dim_ad
  campaign_key   BIGINT,      -- FK dim_campaign
  advertiser_key BIGINT,      -- FK dim_advertiser
  user_key       BIGINT,      -- FK dim_user
  date_key       INT,         -- FK dim_date  (PARTITION KEY)
  placement_key  INT,         -- FK dim_placement (feed/story/reels/right-rail)
  device_key     INT,         -- FK dim_device
  geo_key        INT,         -- FK dim_geo
  is_viewable    BOOLEAN,     -- >=50% pixels >=1s
  cost_micros    BIGINT       -- additive
);

-- Grain: one row per click. FK back to the impression it came from.
CREATE TABLE fact_click (
  click_key      BIGINT,      -- PK
  impression_key BIGINT,      -- FK fact_impression  <- the attribution chain
  ad_key         BIGINT,
  campaign_key   BIGINT,
  user_key       BIGINT,
  date_key       INT,
  click_position INT,
  cost_micros    BIGINT
);

-- Grain: one row per conversion. FK back to the click.
CREATE TABLE fact_conversion (
  conversion_key   BIGINT,    -- PK
  click_key        BIGINT,    -- FK fact_click
  campaign_key     BIGINT,
  user_key         BIGINT,
  date_key         INT,
  conversion_type  VARCHAR(30),  -- purchase / signup / install
  conversion_value DECIMAL(12,2),
  attribution_days INT           -- 1 / 7 / 28-day window
);

-- PERIODIC SNAPSHOT. Grain: one row per campaign per day. The serving layer.
CREATE TABLE fact_campaign_daily (
  campaign_key     BIGINT,
  date_key         INT,
  impressions      BIGINT,
  clicks           BIGINT,
  conversions      BIGINT,
  spend            DECIMAL(14,2),
  conversion_value DECIMAL(14,2)
);

CREATE TABLE dim_campaign (
  campaign_key BIGINT, campaign_id VARCHAR(40), campaign_name VARCHAR(120),
  advertiser_key BIGINT, objective VARCHAR(30), daily_budget DECIMAL(12,2),
  effective_from DATE, effective_to DATE, is_current BOOLEAN   -- SCD2: budgets change
);

CREATE TABLE dim_ad        ( ad_key BIGINT, ad_id VARCHAR(40), creative_type VARCHAR(20) );
CREATE TABLE dim_placement ( placement_key INT, placement_name VARCHAR(30) );
CREATE TABLE dim_geo       ( geo_key INT, country VARCHAR(60), region VARCHAR(60) );
CREATE TABLE dim_date      ( date_key INT, full_date DATE, week_of_year INT, month INT );
"""

# c1: 4 impressions, 1 click, 1 conversion  -> CTR 25.00%, CVR 100.00%
# c2: 2 impressions, 1 click, 0 conversions -> CTR 50.00%, CVR   0.00%
spark.createDataFrame([
    (1, "c1"), (2, "c1"), (3, "c1"), (4, "c1"), (5, "c2"), (6, "c2"),
], ["impression_key", "campaign_key"]).createOrReplaceTempView("fact_impression")

spark.createDataFrame([
    (901, 1, "c1"), (902, 5, "c2"),
], ["click_key", "impression_key", "campaign_key"]
).createOrReplaceTempView("fact_click")

spark.createDataFrame([
    (5001, 901, "c1", 40.00),
], ["conversion_key", "click_key", "campaign_key", "conversion_value"]
).createOrReplaceTempView("fact_conversion")

# 1. Aggregate EACH fact to the common grain first, then join. Joining the raw
#    facts fans out: 4 c1 impressions x 1 c1 click = 4 rows, and CTR breaks.
expect("Q24 CTR and CVR by campaign (to 2dp)", """
WITH i AS (SELECT campaign_key, COUNT(*) AS impressions FROM fact_impression GROUP BY campaign_key),
     c AS (SELECT campaign_key, COUNT(*) AS clicks      FROM fact_click      GROUP BY campaign_key),
     v AS (SELECT campaign_key, COUNT(*) AS conversions FROM fact_conversion GROUP BY campaign_key)
SELECT i.campaign_key,
       i.impressions,
       COALESCE(c.clicks, 0) AS clicks,
       COALESCE(v.conversions, 0) AS conversions,
       ROUND(100.0 * COALESCE(c.clicks, 0) / i.impressions, 2) AS ctr_pct,
       ROUND(100.0 * COALESCE(v.conversions, 0)
                   / NULLIF(COALESCE(c.clicks, 0), 0), 2) AS cvr_pct
FROM i
LEFT JOIN c ON c.campaign_key = i.campaign_key
LEFT JOIN v ON v.campaign_key = i.campaign_key
ORDER BY i.campaign_key
""", [
    ("c1", 4, 1, 1, 25.00, 100.00),
    ("c2", 2, 1, 0, 50.00, 0.00),
])

# 2. Build the periodic snapshot, then serve the dashboard from it.
spark.sql("""
CREATE OR REPLACE TEMP VIEW fact_campaign_daily AS
WITH i AS (SELECT campaign_key, COUNT(*) AS impressions FROM fact_impression GROUP BY campaign_key),
     c AS (SELECT campaign_key, COUNT(*) AS clicks      FROM fact_click      GROUP BY campaign_key),
     v AS (SELECT campaign_key, COUNT(*) AS conversions,
                  SUM(conversion_value) AS conversion_value
           FROM fact_conversion GROUP BY campaign_key)
SELECT i.campaign_key, 20260301 AS date_key, i.impressions,
       COALESCE(c.clicks, 0) AS clicks,
       COALESCE(v.conversions, 0) AS conversions,
       COALESCE(v.conversion_value, 0) AS conversion_value
FROM i LEFT JOIN c ON c.campaign_key = i.campaign_key
       LEFT JOIN v ON v.campaign_key = i.campaign_key
""")

# 3. RATIO OF TOTALS vs AVERAGE OF RATIOS — both asserted so the gap is visible.
# Overall CTR = 2 clicks / 6 impressions = 33.33%.
# Averaging the per-campaign CTRs gives 37.50% — it weights c2's 2 impressions
# the same as c1's 4. On real data with a tiny high-CTR campaign, this is how
# dashboards end up reporting numbers nobody can reproduce.
expect("Q24 overall CTR — ratio of totals (CORRECT)", """
SELECT ROUND(100.0 * SUM(clicks) / SUM(impressions), 2) AS ctr_pct
FROM fact_campaign_daily
""", [(33.33,)])

expect("Q24 overall CTR — average of ratios (WRONG)", """
SELECT ROUND(AVG(100.0 * clicks / impressions), 2) AS ctr_pct
FROM fact_campaign_daily
""", [(37.50,)])

# 4. Spark's division is DOUBLE, so the Presto integer-division trap does not
#    reproduce here. Documented honestly rather than faked.
expect("Q24 Spark `/` returns double (Presto would return 0)", """
SELECT CAST(1 AS BIGINT) / CAST(4 AS BIGINT) AS spark_result
""", [(0.25,)])

# 5. The attribution chain: conversion -> click -> impression.
expect("Q24 conversion attributed back to its impression", """
SELECT v.conversion_key, cl.click_key, i.impression_key, i.campaign_key
FROM fact_conversion v
JOIN fact_click cl      ON cl.click_key = v.click_key
JOIN fact_impression i  ON i.impression_key = cl.impression_key
ORDER BY v.conversion_key
""", [(5001, 901, 1, "c1")])
