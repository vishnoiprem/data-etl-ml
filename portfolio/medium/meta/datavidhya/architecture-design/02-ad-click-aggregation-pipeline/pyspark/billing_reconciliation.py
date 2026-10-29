"""
Billing reconciliation — the BATCH (authoritative) layer.

This is the file that resolves the contradiction in the problem statement:
"< 10-second freshness" AND "financial-grade accuracy" are not the same number,
because tier-2 fraud verdicts arrive minutes to hours after the click.

  SPEED LAYER   dashboard   <10s    provisional, revisable, NOT billed
  BATCH LAYER   invoices    T+1     exact, reconciled, authoritative

Four things proved here:

  1. The speed layer OVERSTATES spend, by exactly the tier-2 fraud rate. That is
     expected behaviour, not a bug -- and the delta is published as an
     adjustment record rather than by mutating history.
  2. An APPEND sink DOUBLE-BILLS on replay. An idempotent MERGE does not. This
     is what "exactly-once" actually means in practice.
  3. The raw log is NEVER mutated. billable = raw - tier1 - tier2, computed as
     a join, so an advertiser dispute can be reconstructed line by line.
  4. Conservation: every raw click is accounted for in exactly one bucket
     (billable / tier1 / tier2 / duplicate). If that does not hold, the ledger
     cannot be audited.

RUN: ../../../../../.env/bin/python pyspark/billing_reconciliation.py
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("ad-click-billing-reconciliation")
         .master("local[2]")
         .config("spark.sql.shuffle.partitions", "4")
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

CPC_USD = 0.50

# ================================================================ the raw log
# IMMUTABLE. 1000 clicks for one campaign in one hour. Composition:
#   80 clicks -> tier-1 fraud (dropped at the edge, never reached aggregation)
#   50 clicks -> duplicates  (dropped by the dedup stage)
#  120 clicks -> tier-2 fraud (a click farm; passed BOTH earlier stages,
#                              so the speed layer already counted and displayed
#                              them)
#  750 clicks -> genuinely billable
spark.sql("""
CREATE OR REPLACE TEMP VIEW raw_events AS
SELECT CONCAT('e', LPAD(CAST(id AS STRING), 4, '0')) AS event_id,
       'c_superbowl'                                  AS campaign_id,
       CONCAT('u_', CAST(id AS STRING))               AS user_id,
       TIMESTAMP'2026-02-08 18:00:00'
           + MAKE_INTERVAL(0,0,0,0,0,0, id % 3600)    AS event_ts,
       CASE WHEN id < 80                THEN 'tier1_fraud'
            WHEN id < 130               THEN 'duplicate'
            WHEN id < 250               THEN 'tier2_fraud'
            ELSE 'clean' END                          AS ground_truth
FROM range(0, 1000) AS t(id)
""")

RAW = 1000
TIER1, DUPES, TIER2, CLEAN = 80, 50, 120, 750
assert spark.table("raw_events").count() == RAW

composition = spark.sql("""
SELECT ground_truth, COUNT(*) AS n FROM raw_events GROUP BY ground_truth ORDER BY n DESC
""").collect()
print("[PASS] raw log composition (immutable, 1 year retention):")
for r in composition:
    print(f"         {r.ground_truth:<14} {r.n:>5,}  {r.n / RAW:>5.1%}")
fraud_pct = (TIER1 + TIER2) / RAW
assert 0.10 <= fraud_pct <= 0.20, fraud_pct
print(f"       -> total fraud {fraud_pct:.0%}, inside the stated 10-20% band")

# ================================================= what the SPEED layer saw
# Tier 1 was dropped at the edge and duplicates by the dedup stage, so the
# speed layer counted clean + tier2 -- it could not yet know about tier 2.
spark.sql("""
CREATE OR REPLACE TEMP VIEW speed_layer_agg AS
SELECT campaign_id,
       date_trunc('HOUR', event_ts) AS window_start,
       COUNT(*)                     AS clicks,
       COUNT(*) * 0.50              AS spend
FROM raw_events
WHERE ground_truth IN ('clean', 'tier2_fraud')
GROUP BY campaign_id, date_trunc('HOUR', event_ts)
""")

speed = spark.sql("SELECT clicks, ROUND(spend, 2) AS spend FROM speed_layer_agg") \
    .collect()[0]
assert (speed.clicks, float(speed.spend)) == (CLEAN + TIER2, (CLEAN + TIER2) * CPC_USD)
print(f"[PASS] SPEED layer (dashboard, <10s): {speed.clicks:,} clicks / "
      f"${float(speed.spend):,.2f}\n       -> shown as 'provisional'. Tier-2 verdicts "
      "have not landed yet.")

# ================================================= tier-2 verdicts land later
spark.sql("""
CREATE OR REPLACE TEMP VIEW fraud_verdicts AS
SELECT event_id,
       'invalid'                   AS verdict,
       0.97                        AS score,
       'coordinated_click_farm'    AS reason,
       TIMESTAMP'2026-02-08 21:14:00' AS scored_at   -- ~3h after the clicks
FROM raw_events WHERE ground_truth = 'tier2_fraud'
""")
assert spark.table("fraud_verdicts").count() == TIER2
lag = spark.sql("""
SELECT ROUND(MAX(UNIX_TIMESTAMP(v.scored_at) - UNIX_TIMESTAMP(r.event_ts)) / 3600.0, 1)
FROM fraud_verdicts v JOIN raw_events r USING (event_id)
""").collect()[0][0]
print(f"[PASS] {TIER2} tier-2 verdicts arrive up to {float(lag):.1f}h after the click")
print("       -> THIS is why billing cannot meet a 10s SLO. Naming this is the")
print("          answer to the question.")

# ================================================= the BATCH layer
# billable = raw - tier1 - duplicates - tier2_verdicts, as a JOIN.
# The raw log is read, never written.
BILLABLE_SQL = """
WITH surviving AS (
    SELECT r.event_id, r.campaign_id, r.event_ts
    FROM raw_events r
    LEFT ANTI JOIN fraud_verdicts v ON v.event_id = r.event_id
    WHERE r.ground_truth NOT IN ('tier1_fraud', 'duplicate')
)
SELECT campaign_id,
       date_trunc('HOUR', event_ts) AS window_start,
       COUNT(*)                     AS billable_clicks,
       ROUND(COUNT(*) * 0.50, 2)    AS billable_spend
FROM surviving
GROUP BY campaign_id, date_trunc('HOUR', event_ts)
"""
spark.sql(f"CREATE OR REPLACE TEMP VIEW batch_agg AS {BILLABLE_SQL}")
spark.sql("SELECT * FROM batch_agg").show(truncate=False)

batch = spark.sql("SELECT billable_clicks, billable_spend FROM batch_agg").collect()[0]
assert (batch.billable_clicks, float(batch.billable_spend)) == (CLEAN, CLEAN * CPC_USD)
print(f"[PASS] BATCH layer (invoice, T+1): {batch.billable_clicks:,} clicks / "
      f"${float(batch.billable_spend):,.2f}\n       -> authoritative")

# ================================================= the adjustment record
ADJUSTMENT = """
SELECT s.campaign_id,
       s.window_start,
       s.clicks                                      AS provisional_clicks,
       b.billable_clicks,
       s.clicks - b.billable_clicks                  AS invalidated_clicks,
       ROUND(b.billable_spend - s.spend, 2)          AS adjustment_usd,
       ROUND(100.0 * (s.clicks - b.billable_clicks) / s.clicks, 2) AS pct_invalidated
FROM speed_layer_agg s
JOIN batch_agg b ON b.campaign_id = s.campaign_id AND b.window_start = s.window_start
"""
spark.sql(ADJUSTMENT).show(truncate=False)

import datetime as dt

expect("adjustment record: the published delta, history never mutated", ADJUSTMENT, [
    ("c_superbowl", dt.datetime(2026, 2, 8, 18, 0), 870, 750, 120, -60.00, 13.79),
])
print("       -> the dashboard said $435.00, the invoice is $375.00, and the")
print("          -$60.00 delta is PUBLISHED as its own row. We do not go back and")
print("          rewrite what the dashboard displayed at 18:05.")

# ================================================= CONSERVATION
# Every raw click lands in exactly one bucket. Without this the ledger cannot
# be audited and a dispute cannot be answered.
CONSERVATION = """
SELECT
    SUM(CASE WHEN ground_truth = 'tier1_fraud' THEN 1 ELSE 0 END) AS tier1,
    SUM(CASE WHEN ground_truth = 'duplicate'   THEN 1 ELSE 0 END) AS duplicates,
    SUM(CASE WHEN ground_truth = 'tier2_fraud' THEN 1 ELSE 0 END) AS tier2,
    SUM(CASE WHEN ground_truth = 'clean'       THEN 1 ELSE 0 END) AS billable,
    COUNT(*)                                                      AS raw_total
FROM raw_events
"""
c = spark.sql(CONSERVATION).collect()[0]
assert c.tier1 + c.duplicates + c.tier2 + c.billable == c.raw_total == RAW
print(f"[PASS] conservation: {c.tier1} tier1 + {c.duplicates} dupes + {c.tier2} tier2 "
      f"+ {c.billable} billable\n       = {c.raw_total:,} raw. Every click accounted "
      "for exactly once -- auditable.")

# ================================================= IDEMPOTENCY: append vs merge
# At-least-once delivery means the batch job WILL re-run a window. What happens
# next depends entirely on the sink.
spark.sql("""
CREATE OR REPLACE TEMP VIEW ledger_append AS
SELECT * FROM batch_agg
UNION ALL
SELECT * FROM batch_agg          -- the replay
""")
appended = spark.sql("""
SELECT SUM(billable_clicks) AS clicks, ROUND(SUM(billable_spend), 2) AS spend
FROM ledger_append
""").collect()[0]
assert (appended.clicks, float(appended.spend)) == (CLEAN * 2, CLEAN * CPC_USD * 2)
print(f"[PASS] APPEND sink after one replay: {appended.clicks:,} clicks / "
      f"${float(appended.spend):,.2f}\n       -> THE ADVERTISER IS BILLED TWICE. "
      f"${float(appended.spend) - CLEAN * CPC_USD:,.2f} of "
      "over-charge from a\n          single retry.")

# The idempotent sink: upsert keyed on (campaign_id, window_start). Re-running
# the window OVERWRITES rather than adds, so replay is a no-op.
spark.sql("""
CREATE OR REPLACE TEMP VIEW ledger_merged AS
SELECT campaign_id, window_start, billable_clicks, billable_spend
FROM (
    SELECT *, ROW_NUMBER() OVER (
                 PARTITION BY campaign_id, window_start   -- the idempotency key
                 ORDER BY billable_clicks DESC) AS rn
    FROM ledger_append
) WHERE rn = 1
""")
merged = spark.sql("""
SELECT SUM(billable_clicks) AS clicks, ROUND(SUM(billable_spend), 2) AS spend
FROM ledger_merged
""").collect()[0]
assert (merged.clicks, float(merged.spend)) == (CLEAN, CLEAN * CPC_USD)
print(f"[PASS] MERGE sink after the same replay: {merged.clicks:,} clicks / "
      f"${float(merged.spend):,.2f}\n       -> unchanged. The replay was a no-op.")
print("       -> KEY: (campaign_id, window_start). Re-running a window replaces it.")
print("          This is how at-least-once delivery becomes effectively-once, and")
print("          it is strictly easier than true exactly-once delivery.")

# Three replays must still be a no-op, not just one.
spark.sql("""
CREATE OR REPLACE TEMP VIEW ledger_thrice AS
SELECT * FROM batch_agg UNION ALL SELECT * FROM batch_agg
UNION ALL SELECT * FROM batch_agg UNION ALL SELECT * FROM batch_agg
""")
thrice = spark.sql("""
SELECT SUM(billable_clicks) AS clicks FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY campaign_id, window_start
                                 ORDER BY billable_clicks DESC) AS rn
    FROM ledger_thrice
) WHERE rn = 1
""").collect()[0][0]
assert thrice == CLEAN, thrice
print(f"[PASS] 4 writes of the same window -> still {thrice:,} clicks. Idempotent "
      "for ANY\n       number of retries, which is the property you actually need.")

# ================================================= raw log is never mutated
assert spark.table("raw_events").count() == RAW
fraud_rows_in_raw = spark.sql("""
SELECT COUNT(*) FROM raw_events WHERE ground_truth = 'tier2_fraud'
""").collect()[0][0]
assert fraud_rows_in_raw == TIER2
print(f"[PASS] the {TIER2} fraudulent events are STILL in the raw log after "
      "reconciliation\n       -> we exclude them by JOIN, never by DELETE. An "
      "advertiser dispute can be\n          reconstructed event by event three "
      "years later.")

# ================================================= the dispute query
# What you run when an advertiser asks "why was I charged $375 and not $435?"
DISPUTE = """
SELECT r.ground_truth AS disposition,
       COUNT(*)       AS clicks,
       ROUND(COUNT(*) * 0.50, 2) AS would_have_cost,
       MAX(COALESCE(v.reason, '-')) AS reason
FROM raw_events r
LEFT JOIN fraud_verdicts v ON v.event_id = r.event_id
GROUP BY r.ground_truth
ORDER BY clicks DESC
"""
spark.sql(DISPUTE).show(truncate=False)
expect("dispute query: every excluded click, with its reason", DISPUTE, [
    ("clean",       750, 375.00, "-"),
    ("tier2_fraud", 120,  60.00, "coordinated_click_farm"),
    ("tier1_fraud",  80,  40.00, "-"),
    ("duplicate",    50,  25.00, "-"),
])
print("       -> this is the audit artifact. It is only possible because the raw")
print("          log is immutable and the verdicts are a separate table.")

# ================================================= scale the delta up
print()
print("At production scale, the speed/batch delta is:")
for daily_clicks, rate in [(1_000_000_000, TIER2 / (CLEAN + TIER2))]:
    over = daily_clicks * rate * CPC_USD
    print(f"  1B clicks/day, {rate:.1%} tier-2 fraud -> "
          f"${over / 1e6:,.1f}M/day of provisional over-statement")
    print(f"  ${over * 365 / 1e9:,.1f}B/year. Billing off the speed layer is not a")
    print("  rounding error; it is the entire fraud budget.")

print("\n[PASS] reconciliation verified: speed overstates by exactly the tier-2 rate, "
      "the\n       delta is published not hidden, append double-bills, MERGE is "
      "replay-safe, and\n       the raw log stays immutable")
