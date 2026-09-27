"""
Problem 03: "The number dropped 5% this week. Walk me through your investigation."

Meta flavor: the fourth step of the combined round, every time.

How to Think - investigate in THIS order, cheapest and most likely first:
  1. IS IT REAL? Check the pipeline before the product. A late partition, a
     dropped upstream partition, or a schema change explains more 5% drops than
     user behaviour ever will. Always say this first — candidates who jump
     straight to product hypotheses look naive.
  2. IS IT EVERYWHERE OR SOMEWHERE? Cut by dimension: country, platform, app
     version, new-vs-returning. A uniform drop suggests measurement or a global
     change; a single-segment drop localises the cause immediately.
  3. NUMERATOR OR DENOMINATOR? A "rate" can fall because the numerator fell OR
     the denominator grew. These have opposite explanations and people skip it.
  4. SEASONALITY / MIX. Compare week-over-week AND year-over-year. A drop that
     happens every year in the same week is a calendar, not a bug.
  5. ONLY THEN product hypotheses, each with a query that could falsify it.

The Simpson's-paradox trap this data encodes:
  Every platform's own conversion rate is FLAT or UP week over week, yet the
  total fell. The cause is MIX: android (low-converting) grew as a share of
  traffic. If you only look at the total you will hunt a bug that does not
  exist. Segmenting is what saves you.

Spark note:
- Pre-aggregate to (week, segment) before any rate arithmetic, or per-row
  division gives you an average-of-ratios instead of a ratio-of-totals.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("03-metric-drop-investigation")
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



# views/leads per (week, platform). Per-platform rates hold; the total drops.
spark.createDataFrame([
    ("w1", "ios",     1000, 100),
    ("w1", "android",  200,  10),
    ("w2", "ios",      600,  60),
    ("w2", "android",  800,  44),
], ["week", "platform", "views", "leads"]).createOrReplaceTempView("conv")

# Step 2a: the headline. 9.17% -> 7.43%, a real drop of ~1.7pp.
expect("headline conversion by week", """
SELECT week,
       SUM(views) AS views,
       SUM(leads) AS leads,
       ROUND(100.0 * SUM(leads) / SUM(views), 2) AS conv_pct
FROM conv GROUP BY week ORDER BY week
""", [
    ("w1", 1200, 110, 9.17),
    ("w2", 1400, 104, 7.43),
])

# Step 2b: segment it. iOS flat at 10%, android IMPROVED 5% -> 5.5%.
# Neither segment got worse, so no segment caused the drop.
expect("conversion by platform — both flat or up", """
SELECT platform, week,
       ROUND(100.0 * leads / views, 2) AS conv_pct
FROM conv ORDER BY platform, week
""", [
    ("android", "w1", 5.00),
    ("android", "w2", 5.50),
    ("ios",     "w1", 10.00),
    ("ios",     "w2", 10.00),
])

# Step 3: the actual cause — traffic MIX. Android went 16.67% -> 57.14% of
# views, and it converts at half the iOS rate. The metric fell without any
# segment regressing. This is Simpson's paradox, and naming it is the answer.
expect("traffic mix shift explains it", """
SELECT week, platform,
       ROUND(100.0 * views / SUM(views) OVER (PARTITION BY week), 2) AS share_of_views_pct
FROM conv ORDER BY week, platform
""", [
    ("w1", "android", 16.67),
    ("w1", "ios",     83.33),
    ("w2", "android", 57.14),
    ("w2", "ios",     42.86),
])

# Step 3b: prove it by holding the mix constant at w1 weights and re-scoring
# w2's rates. The counterfactual comes out ABOVE w1, confirming that mix — not
# performance — drove the decline.
expect("mix-adjusted w2 conversion (w1 weights)", """
WITH r AS (
    SELECT platform,
           MAX(CASE WHEN week = 'w1' THEN views END) AS w1_views,
           MAX(CASE WHEN week = 'w2' THEN 1.0 * leads / views END) AS w2_rate
    FROM conv GROUP BY platform
)
SELECT ROUND(100.0 * SUM(w1_views * w2_rate) / SUM(w1_views), 2) AS mix_adjusted_pct
FROM r
""", [(9.25,)])


# ===========================================================================
# PySpark DataFrame API — same four investigations, expressed with DataFrame
# ops. Each block asserts the result matches the SQL form above so a drift
# between the two implementations fails the file loudly.
# ===========================================================================
from pyspark.sql import functions as F, Window

conv_df = spark.table("conv")

# Step 2a: headline conversion by week — pre-aggregate to (week) THEN divide,
# never divide per-row first or you get an average-of-ratios.
w0 = Window.partitionBy()                                       # whole table
headline_df = (conv_df
               .groupBy("week")
               .agg(F.sum("views").alias("views"),
                    F.sum("leads").alias("leads"),
                    F.round(100.0 * F.sum("leads") / F.sum("views"), 2)
                        .alias("conv_pct"))
               .orderBy("week"))
assert [tuple(r) for r in headline_df.collect()] == [
    ("w1", 1200, 110, 9.17),
    ("w2", 1400, 104, 7.43),
]
print("[PASS] headline conversion by week — DataFrame API matches SQL")

# Step 2b: per-platform rate. Because the grain is already (week, platform)
# in the source table, no aggregation needed — divide leads/views in place.
seg_df = (conv_df
          .withColumn("conv_pct",
                      F.round(100.0 * F.col("leads") / F.col("views"), 2))
          .select("platform", "week", "conv_pct")
          .orderBy("platform", "week"))
assert [tuple(r) for r in seg_df.collect()] == [
    ("android", "w1", 5.00),
    ("android", "w2", 5.50),
    ("ios",     "w1", 10.00),
    ("ios",     "w2", 10.00),
]
print("[PASS] conversion by platform — DataFrame API matches SQL")

# Step 3: traffic-mix shift. Window function over PARTITION BY week gives each
# row its share of total views for that week. Same idea as the SQL form.
w_week = Window.partitionBy("week")
mix_df = (conv_df
          .withColumn("share_of_views_pct",
                      F.round(100.0 * F.col("views") / F.sum("views").over(w_week), 2))
          .select("week", "platform", "share_of_views_pct")
          .orderBy("week", "platform"))
assert [tuple(r) for r in mix_df.collect()] == [
    ("w1", "android", 16.67),
    ("w1", "ios",     83.33),
    ("w2", "android", 57.14),
    ("w2", "ios",     42.86),
]
print("[PASS] traffic mix shift — DataFrame API matches SQL")

# Step 3b: mix-adjusted w2 — pivot to (platform, w1_views, w2_rate) THEN
# reduce. Equivalent of the MAX(CASE WHEN ...) CTE in SQL. With only two
# weeks, we can also use a conditional aggregate on the same groupBy:
# .agg(F.sum(...).when('w1')... .when('w2')...) is ugly, so pivot-on-pivot
# via .filter + .alias is clearer:
w1_weights = (conv_df.filter(F.col("week") == "w1")
              .select(F.col("platform"), F.col("views").alias("w1_views")))
w2_rates   = (conv_df.filter(F.col("week") == "w2")
              .select(F.col("platform"),
                      (F.col("leads") / F.col("views")).alias("w2_rate")))
joined = w1_weights.join(w2_rates, "platform")
mix_adj_df = joined.agg(
    F.round(100.0 * F.sum(F.col("w1_views") * F.col("w2_rate"))
                 / F.sum("w1_views"),
            2).alias("mix_adjusted_pct")
)
assert [tuple(r) for r in mix_adj_df.collect()] == [(9.25,)]
print("[PASS] mix-adjusted w2 conversion (w1 weights) — DataFrame API matches SQL")
