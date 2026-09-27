"""
Q20 / Q35: Factless fact tables — event tracking and COVERAGE analysis.
Article: "50 Data Modeling Interview Questions for DEs" — Star Schema / Advanced

Meta flavor: "We ran a Reels promotion across 3 creator tiers in 4 markets.
Which tier-market combinations were eligible but generated ZERO promoted
views?" You cannot answer that from the events table, because the answer is
rows that do not exist in it.

How to Think:
- A factless fact table has ONLY dimension keys and no numeric measure. Two
  kinds, and the second is the one worth knowing:
    EVENT TRACKING  -> records that something happened ("user X watched Reel Y").
                       The measure is the COUNT of rows.
    COVERAGE        -> records what COULD happen ("this tier-market pair was
                       eligible for the promotion"). The measure is the
                       comparison against the event table.
- Coverage exists to answer "what did NOT happen". That is impossible from
  events alone: absence leaves no row, so there is nothing to filter. You need a
  table of the universe, then an anti-join.
- The query shape is `coverage LEFT JOIN events ... WHERE events.key IS NULL`
  (or NOT EXISTS). Say "anti-join" out loud -- it names the thing.

The trap:
- Trying to answer it from the event table with a GROUP BY. Zero-activity
  combinations are simply not in the result, so they cannot appear with 0 and
  cannot be counted. Asserted below: the GROUP BY returns 3 rows out of 12, and
  no amount of HAVING recovers the missing 9.
- Building coverage as the full Cartesian product of the dimensions when the
  real eligibility rules are narrower. Coverage must be what was ACTUALLY
  eligible; a blind cross join invents combinations that were never in the
  promotion and reports them as failures.
- COUNT(*) on an outer-joined factless table returns 1 for a row with NO match
  (it counts the manufactured NULL row). Use COUNT(fact.key) -- same defect as
  Q81 in the SQL set.
- A factless fact still has a GRAIN. "One row per tier per market per promotion"
  -- state it, or the anti-join silently changes meaning.

Spark note:
- A LEFT ANTI JOIN is the direct primitive and is cheaper than LEFT + IS NULL:
  it can stop at the first match per key. Coverage tables are small and
  broadcast.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("10-factless-coverage-fact")
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


from pyspark.sql import functions as F

# ---------------------------------------------------------- coverage fact
# Grain: one row per (tier, market) eligible for promo P1. NO measures.
# Note this is NOT the full 3x4 Cartesian product -- bronze/JP was never
# eligible, so it must not be reported as a failure.
spark.sql("""
CREATE OR REPLACE TEMP VIEW factless_promo_eligibility AS
SELECT * FROM VALUES
    ('P1', 'gold',   'US'), ('P1', 'gold',   'IN'), ('P1', 'gold',   'BR'),
    ('P1', 'gold',   'JP'), ('P1', 'silver', 'US'), ('P1', 'silver', 'IN'),
    ('P1', 'silver', 'BR'), ('P1', 'silver', 'JP'), ('P1', 'bronze', 'US'),
    ('P1', 'bronze', 'IN'), ('P1', 'bronze', 'BR')
AS t(promo_id, creator_tier, market)
""")

# ---------------------------------------------------------- event-tracking fact
# Grain: one row per promoted view. Also factless -- the measure is COUNT(*).
spark.sql("""
CREATE OR REPLACE TEMP VIEW factless_promoted_view AS
SELECT * FROM VALUES
    ('P1', 'gold',   'US', 9001), ('P1', 'gold',   'US', 9002),
    ('P1', 'gold',   'IN', 9003), ('P1', 'silver', 'US', 9004),
    ('P1', 'silver', 'US', 9005), ('P1', 'silver', 'US', 9006)
AS t(promo_id, creator_tier, market, viewer_id)
""")

eligible = spark.table("factless_promo_eligibility").count()
activated = spark.sql("""
SELECT COUNT(*) FROM (
    SELECT DISTINCT promo_id, creator_tier, market FROM factless_promoted_view)
""").collect()[0][0]
assert (eligible, activated) == (11, 3), (eligible, activated)
print(f"[PASS] Q35 {eligible} eligible combinations, {activated} with any activity "
      f"-- {eligible - activated} silent failures to find")

# ---------------------------------------------------------- event tracking works
EVENTS = """
SELECT creator_tier, market, COUNT(*) AS promoted_views
FROM factless_promoted_view
GROUP BY creator_tier, market
ORDER BY promoted_views DESC, creator_tier, market
"""
expect("Q20 event-tracking factless fact: the measure is COUNT(*)", EVENTS, [
    ("silver", "US", 3),
    ("gold",   "US", 2),
    ("gold",   "IN", 1),
])

# ---------------------------------------------------------- the coverage question
# What was eligible but produced NOTHING. Only answerable via the anti-join.
ZERO_ACTIVITY = """
SELECT e.creator_tier, e.market
FROM factless_promo_eligibility e
LEFT JOIN factless_promoted_view v
       ON v.promo_id     = e.promo_id
      AND v.creator_tier = e.creator_tier
      AND v.market       = e.market
WHERE v.promo_id IS NULL
ORDER BY e.creator_tier, e.market
"""
spark.sql(ZERO_ACTIVITY).show(truncate=False)
expect("Q35 coverage anti-join finds the 8 combinations with zero views", ZERO_ACTIVITY, [
    ("bronze", "BR"), ("bronze", "IN"), ("bronze", "US"),
    ("gold",   "BR"), ("gold",   "JP"),
    ("silver", "BR"), ("silver", "IN"), ("silver", "JP"),
])

# DataFrame API -- LEFT ANTI JOIN is the direct primitive.
df = (spark.table("factless_promo_eligibility").alias("e")
      .join(F.broadcast(spark.table("factless_promoted_view").alias("v")),
            ["promo_id", "creator_tier", "market"], "left_anti")
      .select("creator_tier", "market")
      .orderBy("creator_tier", "market"))
assert [tuple(r) for r in df.collect()] == [
    ("bronze", "BR"), ("bronze", "IN"), ("bronze", "US"),
    ("gold", "BR"), ("gold", "JP"),
    ("silver", "BR"), ("silver", "IN"), ("silver", "JP"),
]
print("[PASS] Q35 LEFT ANTI JOIN matches the LEFT JOIN + IS NULL formulation")

# ---------------------------------------------------------- events alone cannot answer
# The GROUP BY sees only what happened: 3 of 11 combinations.
events_only = spark.sql(f"SELECT COUNT(*) FROM ({EVENTS})").collect()[0][0]
assert events_only == 3, events_only
print(f"[PASS] Q35 a GROUP BY over events returns {events_only} of {eligible} "
      "combinations -- the zeros are absent, not zero")

# No HAVING can recover them: there is no row to apply it to.
having = spark.sql("""
SELECT COUNT(*) FROM (
    SELECT creator_tier, market, COUNT(*) AS n
    FROM factless_promoted_view GROUP BY creator_tier, market HAVING COUNT(*) = 0
)
""").collect()[0][0]
assert having == 0
print("[PASS] Q35 `HAVING COUNT(*) = 0` returns nothing -- absence leaves no row to filter")

# ---------------------------------------------------------- full coverage report
COVERAGE = """
SELECT e.creator_tier,
       e.market,
       COUNT(v.viewer_id)                                     AS promoted_views,
       CASE WHEN COUNT(v.viewer_id) = 0 THEN 'no activity'
            ELSE 'active' END                                  AS status
FROM factless_promo_eligibility e
LEFT JOIN factless_promoted_view v
       ON v.promo_id = e.promo_id AND v.creator_tier = e.creator_tier
      AND v.market = e.market
GROUP BY e.creator_tier, e.market
ORDER BY promoted_views DESC, e.creator_tier, e.market
"""
spark.sql(COVERAGE).show(truncate=False)
rows = spark.sql(COVERAGE).collect()
assert len(rows) == eligible, len(rows)
assert sum(1 for r in rows if r.status == "no activity") == 8
print(f"[PASS] Q35 coverage report covers all {len(rows)} eligible combinations, "
      "8 flagged 'no activity'")

# ---------------------------------------------------------- COUNT(*) vs COUNT(key)
star_vs_key = spark.sql("""
SELECT e.creator_tier, e.market, COUNT(*) AS star, COUNT(v.viewer_id) AS keyed
FROM factless_promo_eligibility e
LEFT JOIN factless_promoted_view v
       ON v.promo_id = e.promo_id AND v.creator_tier = e.creator_tier
      AND v.market = e.market
WHERE e.creator_tier = 'bronze' AND e.market = 'US'
GROUP BY e.creator_tier, e.market
""").collect()[0]
assert (star_vs_key[2], star_vs_key[3]) == (1, 0), star_vs_key
print("[PASS] Q35 COUNT(*) reports 1 promoted view for bronze/US which had none; "
      "COUNT(viewer_id) correctly reports 0")

# ---------------------------------------------------------- the Cartesian trap
# A blind cross join invents bronze/JP, which was never eligible.
cartesian = spark.sql("""
WITH tiers AS (SELECT DISTINCT creator_tier FROM factless_promo_eligibility),
     mkts  AS (SELECT DISTINCT market       FROM factless_promo_eligibility)
SELECT COUNT(*) FROM tiers CROSS JOIN mkts
""").collect()[0][0]
assert (cartesian, eligible) == (12, 11), (cartesian, eligible)

invented = spark.sql("""
WITH tiers AS (SELECT DISTINCT creator_tier FROM factless_promo_eligibility),
     mkts  AS (SELECT DISTINCT market       FROM factless_promo_eligibility),
     grid  AS (SELECT t.creator_tier, m.market FROM tiers t CROSS JOIN mkts m)
SELECT g.creator_tier, g.market FROM grid g
LEFT ANTI JOIN factless_promo_eligibility e
       ON e.creator_tier = g.creator_tier AND e.market = g.market
""").collect()
assert [(r[0], r[1]) for r in invented] == [("bronze", "JP")], invented
print(f"[PASS] Q35 a Cartesian grid has {cartesian} cells vs {eligible} truly eligible "
      "-- it would report bronze/JP as a failure though it was never in the promo")
