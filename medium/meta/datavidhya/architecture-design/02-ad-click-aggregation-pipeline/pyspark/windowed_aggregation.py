"""
Windowed aggregation — multi-grain rollups and the Super Bowl hot key.

Two things are being proved here, and they are the two the interviewer probes:

  1. MULTI-WINDOW ROLLUP. 1m / 5m / 1h / 1d must RECONCILE. If summing the
     1-minute buckets does not equal the 1-hour bucket, an advertiser will find
     it and you will spend a week explaining it. Asserted.

  2. HOT-KEY SALTING. One campaign at 10x volume hashes to ONE partition and
     that worker becomes the bottleneck. The fix is a two-stage salted
     aggregation, and the correctness requirement is that salting changes the
     PARALLELISM without changing the ANSWER. Asserted.

WHY TUMBLING AND NOT SLIDING:
  The problem statement says "sliding windows (1-min, 5-min, 1-hour, daily)".
  Worth a clarifying question: sliding windows OVERLAP, so every event lands in
  multiple windows and the buckets no longer sum to the total. For BILLING you
  want TUMBLING (disjoint) windows -- each click billed in exactly one bucket
  per grain. For a dashboard trend line, sliding is nicer to look at. Both are
  built below and the difference in total is asserted, because summing sliding
  windows and calling it revenue is a real and expensive mistake.

RUN: ../../../../../.env/bin/python pyspark/windowed_aggregation.py
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("ad-click-windowed-aggregation")
         .master("local[4]")
         .config("spark.sql.shuffle.partitions", "8")
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


from pyspark.sql import functions as F

SALT_BUCKETS = 64      # parallelism for the hot key
CPC_USD = 0.50

# ---------------------------------------------------------------- input
# Deduped clicks across 3 campaigns over ~1 hour.
# c_whale is the Super Bowl campaign: 10x the volume of the others.
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW deduped_clicks AS
SELECT CONCAT('e', CAST(id AS STRING))                        AS event_id,
       CASE WHEN id % 12 = 0 THEN 'c_small_a'
            WHEN id % 12 = 1 THEN 'c_small_b'
            ELSE 'c_whale' END                                AS campaign_id,
       CONCAT('ad_', CAST(id % 5 AS STRING))                  AS ad_id,
       CONCAT('u_', CAST(id AS STRING))                       AS user_id,
       TIMESTAMP'2026-02-08 18:00:00' + MAKE_INTERVAL(0,0,0,0,0,0, id % 3600) AS event_ts,
       CAST({CPC_USD} AS DECIMAL(10,2))                       AS cpc
FROM range(0, 6000) AS t(id)
""")

TOTAL_CLICKS = 6000
assert spark.table("deduped_clicks").count() == TOTAL_CLICKS

skew = spark.sql("""
SELECT campaign_id, COUNT(*) AS clicks,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM deduped_clicks GROUP BY campaign_id ORDER BY clicks DESC
""").collect()
print("[PASS] input skew (the Super Bowl shape):")
for r in skew:
    print(f"         {r.campaign_id:<12} {r.clicks:>6,} clicks  {r.pct:>5.1f}%")
whale_pct = [r.pct for r in skew if r.campaign_id == "c_whale"][0]
assert whale_pct > 80, whale_pct
print(f"       -> one campaign is {whale_pct:.0f}% of traffic. Hash-partitioned by")
print("          campaign_id, that is ONE worker doing all the work.")

# ======================================================== multi-grain rollup
# TUMBLING windows at four grains. window() with no slide argument is tumbling.
AGG_SQL = """
SELECT '1 minute' AS grain, campaign_id,
       window(event_ts, '1 minute').start AS window_start,
       COUNT(*) AS clicks, ROUND(SUM(cpc), 2) AS spend
FROM deduped_clicks GROUP BY campaign_id, window(event_ts, '1 minute')
"""

for grain, spec in [("1 minute", "1 minute"), ("5 minutes", "5 minutes"),
                    ("1 hour", "1 hour"), ("1 day", "1 day")]:
    spark.sql(f"""
    CREATE OR REPLACE TEMP VIEW agg_{grain.split()[1][:3]}_{grain.split()[0]} AS
    SELECT campaign_id,
           window(event_ts, '{spec}').start AS window_start,
           window(event_ts, '{spec}').end   AS window_end,
           COUNT(*)                          AS clicks,
           SUM(cpc)                          AS spend
    FROM deduped_clicks
    GROUP BY campaign_id, window(event_ts, '{spec}')
    """)

views = {"1m": "agg_min_1", "5m": "agg_min_5", "1h": "agg_hou_1", "1d": "agg_day_1"}
counts = {k: spark.table(v).count() for k, v in views.items()}
print(f"[PASS] rollup row counts: {counts}")
assert counts["1m"] > counts["5m"] > counts["1h"] >= counts["1d"], counts
print("       -> coarser grain = fewer rows, which is the whole point of the")
print("          retention rollup (1.3T rows at 1-min for 90d, see capacity_model.py)")

# -- THE RECONCILIATION INVARIANT ----------------------------------------
# Every grain must total identically. This is the check that belongs in the
# pipeline, because a mismatch is how advertisers lose trust.
totals = {}
for k, v in views.items():
    r = spark.sql(f"SELECT COUNT(*) AS n, SUM(clicks) AS c, ROUND(SUM(spend),2) AS s "
                  f"FROM {v}").collect()[0]
    totals[k] = (r.c, float(r.s))
print("[PASS] per-grain totals:")
for k, (c, s) in totals.items():
    print(f"         {k:<4} {c:>6,} clicks  ${s:>10,.2f}")
assert len({c for c, _ in totals.values()}) == 1, totals
assert len({s for _, s in totals.values()}) == 1, totals
assert totals["1m"][0] == TOTAL_CLICKS
print(f"       -> all four grains total {TOTAL_CLICKS:,} clicks / "
      f"${totals['1m'][1]:,.2f}. RECONCILED.")

# -- 1-minute buckets must sum to their containing 1-hour bucket ----------
nested = spark.sql("""
WITH from_minutes AS (
    SELECT campaign_id, date_trunc('HOUR', window_start) AS hr, SUM(clicks) AS clicks
    FROM agg_min_1 GROUP BY campaign_id, date_trunc('HOUR', window_start)
)
SELECT m.campaign_id, m.clicks AS from_1min, h.clicks AS from_1hour
FROM from_minutes m
JOIN agg_hou_1 h ON h.campaign_id = m.campaign_id AND h.window_start = m.hr
ORDER BY m.campaign_id
""").collect()
assert all(r.from_1min == r.from_1hour for r in nested), nested
print(f"[PASS] 1-min buckets sum exactly to their 1-hour parent for all "
      f"{len(nested)} campaigns")

# ======================================================== sliding vs tumbling
# A 5-minute window sliding every 1 minute: each click lands in 5 windows.
SLIDING = """
SELECT SUM(clicks) AS summed_clicks FROM (
    SELECT COUNT(*) AS clicks
    FROM deduped_clicks
    GROUP BY campaign_id, window(event_ts, '5 minutes', '1 minute')
)
"""
slid = spark.sql(SLIDING).collect()[0][0]
assert slid == TOTAL_CLICKS * 5, (slid, TOTAL_CLICKS)
print(f"[PASS] summing a 5m/1m SLIDING window gives {slid:,} = {TOTAL_CLICKS:,} x 5")
print(f"       -> ${slid * CPC_USD:,.2f} instead of ${TOTAL_CLICKS * CPC_USD:,.2f}.")
print("          Sliding windows OVERLAP. Never sum them for money; use tumbling")
print("          for billing and sliding only for a trend line.")

# ======================================================== the hot key
# Establish the skew in the aggregation itself: rows per campaign partition.
part_skew = spark.sql("""
SELECT campaign_id, COUNT(*) AS clicks FROM deduped_clicks
GROUP BY campaign_id ORDER BY clicks DESC
""").collect()
hottest = part_skew[0].clicks
coldest = part_skew[-1].clicks
ratio = hottest / coldest
assert ratio > 9, ratio
print(f"[PASS] hot/cold partition ratio = {ratio:.0f}x ({hottest:,} vs {coldest:,} "
      "clicks)\n       -> without salting, one task runs "
      f"{ratio:.0f}x longer than its peers")

# -- two-stage salted aggregation ----------------------------------------
# Stage 1: aggregate on (campaign_id, salt) -> 64x the parallelism for the hot key
# Stage 2: sum the partials -> the same answer
SALTED = f"""
WITH stage1 AS (
    SELECT campaign_id,
           pmod(hash(event_id), {SALT_BUCKETS})   AS salt,
           window(event_ts, '1 minute').start      AS window_start,
           COUNT(*)                                AS partial_clicks,
           SUM(cpc)                                AS partial_spend
    FROM deduped_clicks
    GROUP BY campaign_id, pmod(hash(event_id), {SALT_BUCKETS}),
             window(event_ts, '1 minute')
)
SELECT campaign_id, window_start,
       SUM(partial_clicks)          AS clicks,
       ROUND(SUM(partial_spend), 2) AS spend
FROM stage1
GROUP BY campaign_id, window_start
"""

salted_total = spark.sql(f"""
SELECT SUM(clicks) AS c, ROUND(SUM(spend), 2) AS s FROM ({SALTED})
""").collect()[0]
assert (salted_total.c, float(salted_total.s)) == (TOTAL_CLICKS, totals["1m"][1])
print(f"[PASS] salted two-stage aggregation totals {salted_total.c:,} clicks / "
      f"${float(salted_total.s):,.2f}\n       -- IDENTICAL to the unsalted answer. "
      "Salting changes parallelism, not results.")

# Per-window equality, not just the grand total.
mismatch = spark.sql(f"""
SELECT COUNT(*) FROM (
    SELECT campaign_id, window_start, clicks FROM ({SALTED})
) s
FULL OUTER JOIN agg_min_1 u
  ON u.campaign_id = s.campaign_id AND u.window_start = s.window_start
WHERE COALESCE(s.clicks, -1) <> COALESCE(u.clicks, -1)
""").collect()[0][0]
assert mismatch == 0, mismatch
print("[PASS] every (campaign, minute) bucket matches between salted and unsalted "
      "-- 0 mismatches")

# -- the parallelism gain, measured ---------------------------------------
stage1_groups = spark.sql(f"""
SELECT COUNT(*) FROM (
    SELECT campaign_id, pmod(hash(event_id), {SALT_BUCKETS}) AS salt,
           window(event_ts, '1 minute') AS w
    FROM deduped_clicks
    GROUP BY campaign_id, pmod(hash(event_id), {SALT_BUCKETS}),
             window(event_ts, '1 minute')
)
""").collect()[0][0]
unsalted_groups = counts["1m"]
gain = stage1_groups / unsalted_groups
print(f"[PASS] stage-1 groups {stage1_groups:,} vs unsalted {unsalted_groups:,} "
      f"= {gain:.1f}x more\n       independent work units -> the hot key spreads "
      f"across up to {SALT_BUCKETS} tasks")

whale_salts = spark.sql(f"""
SELECT COUNT(DISTINCT pmod(hash(event_id), {SALT_BUCKETS})) AS salts
FROM deduped_clicks WHERE campaign_id = 'c_whale'
""").collect()[0][0]
assert whale_salts == SALT_BUCKETS, whale_salts
print(f"[PASS] the whale campaign's clicks spread across all {whale_salts} salt "
      "buckets\n       -> its aggregation parallelism went from 1 to 64")

# -- salt on event_id, NOT on user_id -------------------------------------
# Salting by a BUSINESS key inherits that key's own skew. The main dataset has
# one click per user so both look uniform; real click traffic has power users,
# so build that shape explicitly to show the difference.
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW power_user_clicks AS
SELECT CONCAT('pe', CAST(id AS STRING)) AS event_id,
       -- 90% of clicks come from just 5 users (bot-farm / power-user shape)
       CASE WHEN id % 10 < 9 THEN CONCAT('heavy_', CAST(id % 5 AS STRING))
            ELSE CONCAT('light_', CAST(id AS STRING)) END AS user_id
FROM range(0, 10000) AS t(id)
""")

concentration = spark.sql("""
SELECT ROUND(100.0 * SUM(CASE WHEN user_id LIKE 'heavy%' THEN 1 ELSE 0 END)
             / COUNT(*), 1) AS pct_from_heavy,
       COUNT(DISTINCT user_id) AS distinct_users
FROM power_user_clicks
""").collect()[0]
print(f"[PASS] power-user shape: {float(concentration.pct_from_heavy):.0f}% of clicks "
      f"from 5 of {concentration.distinct_users:,} users")

def imbalance(col):
    return float(spark.sql(f"""
    SELECT MAX(cnt) * 1.0 / MIN(cnt) FROM (
        SELECT pmod(hash({col}), {SALT_BUCKETS}) AS salt, COUNT(*) AS cnt
        FROM power_user_clicks GROUP BY pmod(hash({col}), {SALT_BUCKETS})
    )
    """).collect()[0][0])

by_event, by_user = imbalance("event_id"), imbalance("user_id")
assert by_event < 2.0 and by_user > 50, (by_event, by_user)
print(f"[PASS] bucket imbalance on this traffic: salt on event_id = {by_event:.2f}x, "
      f"on user_id = {by_user:,.0f}x")
print("       -> event_id is unique per event so it spreads evenly. user_id")
print("          concentrates the 5 heavy users into 5 buckets and re-creates the")
print("          skew INSIDE the salted key -- the salt has to be event-scoped.")

# ======================================================== spend is derived
spend_check = spark.sql(f"""
SELECT ROUND(SUM(spend), 2) AS spend, SUM(clicks) * {CPC_USD} AS expected
FROM agg_min_1
""").collect()[0]
assert float(spend_check.spend) == float(spend_check.expected)
print(f"[PASS] spend ${float(spend_check.spend):,.2f} = clicks x ${CPC_USD} CPC "
      "exactly\n       -> spend is DERIVED from billable clicks, never counted "
      "separately, or the\n       two can drift apart")

print("\n[PASS] aggregation verified: four grains reconcile, sliding windows "
      "demonstrably\n       cannot be summed for money, and salting fixes the hot "
      "key without\n       changing a single number")
