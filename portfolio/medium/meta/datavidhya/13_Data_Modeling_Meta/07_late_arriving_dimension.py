"""
Q27: How do you handle late-arriving dimensions?
Article: "50 Data Modeling Interview Questions for DEs" — SCDs & History Tracking

Meta flavor: "The ads events stream is real-time; the advertiser master data
lands on a nightly batch. Every night ~0.3% of impressions reference an
advertiser_id the dimension has never seen. Do not drop the spend."

How to Think:
- Three options, and the interviewer wants you to reject two of them out loud:
    1. DROP the fact row -> you lose revenue. Never.
    2. NULL the foreign key -> the row survives the load but vanishes from every
       dimension join, which is the same data loss one step later.
    3. INFERRED MEMBER (the answer): insert a placeholder dimension row keyed on
       the real natural key, with attributes marked unknown and a flag saying
       "inferred". The fact joins cleanly TODAY, and when the real attributes
       arrive tonight you UPDATE the placeholder in place.
- An inferred member is NOT the same thing as the Unknown member from
  `08_null_fk_unknown_member.py`. Unknown (-1) is a single shared row meaning
  "no key at all". An inferred member is one row PER unseen natural key,
  meaning "this entity is real, we just do not know about it yet". Conflating
  them is the most common mistake: -1 cannot be backfilled, because you no
  longer know which advertiser each fact meant.

The trap (this is the real question):
- BACKDATING THE SCD2 INTERVAL. When the real attributes arrive, the placeholder
  must be resolved with `effective_from` set to the date the FACT first
  appeared, not today. Resolve it with today's date and every impression between
  arrival and resolution falls into a gap where no dimension version covers it
  -- so a point-in-time join drops exactly the rows you were trying to save.
  Asserted below; this is the subtle failure interviewers probe for.
- The placeholder must carry the NATURAL key. That is what lets tonight's batch
  find it. A generated surrogate with no natural key is unresolvable.
- Resolution is an UPDATE of the existing surrogate key, not an insert of a new
  one. Insert a second row and historical facts still point at the placeholder,
  so they keep reporting 'Unknown' forever.
- Mark inferred rows with a flag (`is_inferred`) and monitor the count. A slow
  rise means the dimension feed is degrading; without the flag it is invisible.

Spark note:
- Real implementation is a Delta/Iceberg MERGE: `WHEN MATCHED AND
  target.is_inferred THEN UPDATE SET <real attributes>, is_inferred = false`.
  This file performs the same steps as set operations and asserts the end state.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("07-late-arriving-dimension")
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
FACT_DATE = "2026-03-01"      # when the impressions arrived
RESOLVE_DATE = "2026-03-02"   # when the nightly master batch caught up

from pyspark.sql import functions as F

# ---------------------------------------------------------- day 1: the arrival
# Advertiser 601 is known. 602 is NOT in the dimension yet.
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW dim_advertiser AS
SELECT * FROM VALUES
    (1, 601, 'Acme Corp', 'US', 'gold', FALSE,
        DATE'2026-01-01', DATE'{OPEN_END}', TRUE)
AS t(advertiser_sk, advertiser_id, name, country, tier, is_inferred,
     effective_from, effective_to, is_current)
""")
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW fact_impression AS
SELECT * FROM VALUES
    (1, 601, DATE'{FACT_DATE}', CAST(100.00 AS DECIMAL(12,2))),
    (2, 602, DATE'{FACT_DATE}', CAST(250.00 AS DECIMAL(12,2))),
    (3, 602, DATE'{FACT_DATE}', CAST(150.00 AS DECIMAL(12,2)))
AS t(impression_id, advertiser_id, event_date, spend)
""")

orphans = spark.sql("""
SELECT DISTINCT f.advertiser_id FROM fact_impression f
WHERE NOT EXISTS (SELECT 1 FROM dim_advertiser d WHERE d.advertiser_id = f.advertiser_id)
""").collect()
assert [r[0] for r in orphans] == [602], orphans
orphan_spend = spark.sql("""
SELECT ROUND(SUM(spend), 2) FROM fact_impression WHERE advertiser_id = 602
""").collect()[0][0]
print(f"[PASS] Q27 advertiser 602 is unknown, carrying {orphan_spend} of spend at risk")

# ---------------------------------------------------------- reject option 1: drop
dropped = spark.sql("""
SELECT ROUND(SUM(f.spend), 2) FROM fact_impression f
JOIN dim_advertiser d ON d.advertiser_id = f.advertiser_id
""").collect()[0][0]
assert float(dropped) == 100.00, dropped
print("[PASS] Q27 an inner join reports 100.00 of 500.00 -- 80% of spend dropped")

# ---------------------------------------------------------- insert inferred members
# One row PER unseen natural key, effective from the date the FACT appeared.
# Stage names are explicit: a temp view cannot be redefined in terms of itself.
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW dim_day1 AS
SELECT * FROM dim_advertiser
UNION ALL
SELECT 2, 602, '(inferred)', '(unknown)', '(unknown)', TRUE,
       DATE'{FACT_DATE}', DATE'{OPEN_END}', TRUE
""")
spark.table("dim_day1").orderBy("advertiser_sk").show(truncate=False)

import datetime as dt


def d(s):
    return dt.date(*(int(x) for x in s.split("-")))


def DIM(view="dim_advertiser"):
    """The dimension's shape, readable against any load stage."""
    return f"""
    SELECT advertiser_sk, advertiser_id, name, tier, is_inferred,
           effective_from, effective_to, is_current
    FROM {view} ORDER BY advertiser_sk
    """


expect("Q27 inferred member inserted, keyed on the real natural key", DIM("dim_day1"), [
    (1, 601, "Acme Corp",  "gold",      False, d("2026-01-01"), d(OPEN_END), True),
    (2, 602, "(inferred)", "(unknown)", True,  d(FACT_DATE),    d(OPEN_END), True),
])

# Now no spend is lost.
kept = spark.sql("""
SELECT ROUND(SUM(f.spend), 2) FROM fact_impression f
JOIN dim_day1 d ON d.advertiser_id = f.advertiser_id
 AND f.event_date >= d.effective_from AND f.event_date < d.effective_to
""").collect()[0][0]
assert float(kept) == 500.00, kept
print(f"[PASS] Q27 all {kept} of spend now joins -- nothing dropped, nothing NULL")

# The flag makes the gap measurable.
inferred_count = spark.sql(
    "SELECT COUNT(*) FROM dim_day1 WHERE is_inferred").collect()[0][0]
assert inferred_count == 1
print("[PASS] Q27 is_inferred flag makes the dimension-feed gap monitorable")

# ---------------------------------------------------------- day 2: resolution
# The nightly batch brings 602's real attributes. UPDATE the placeholder in
# place -- same surrogate key, same effective_from. Do NOT insert a new row.
spark.sql("""
CREATE OR REPLACE TEMP VIEW staging_advertiser AS
SELECT * FROM VALUES
    (602, 'Globex Ltd', 'DE', 'silver')
AS t(advertiser_id, name, country, tier)
""")

spark.sql("""
CREATE OR REPLACE TEMP VIEW dim_resolved AS
SELECT d.advertiser_sk,
       d.advertiser_id,
       COALESCE(s.name, d.name)       AS name,
       COALESCE(s.country, d.country) AS country,
       COALESCE(s.tier, d.tier)       AS tier,
       CASE WHEN s.advertiser_id IS NOT NULL AND d.is_inferred
            THEN FALSE ELSE d.is_inferred END AS is_inferred,
       d.effective_from,              -- BACKDATED: unchanged, not today
       d.effective_to,
       d.is_current
FROM dim_day1 d
LEFT JOIN staging_advertiser s
       ON s.advertiser_id = d.advertiser_id AND d.is_inferred
""")
spark.table("dim_resolved").orderBy("advertiser_sk").show(truncate=False)

expect("Q27 placeholder resolved IN PLACE, effective_from still the fact date", DIM("dim_resolved"), [
    (1, 601, "Acme Corp",  "gold",   False, d("2026-01-01"), d(OPEN_END), True),
    (2, 602, "Globex Ltd", "silver", False, d(FACT_DATE),    d(OPEN_END), True),
])

# Same surrogate key, so historical facts now read the real attributes.
RESOLVED = """
SELECT f.impression_id, d.name, d.tier, ROUND(f.spend, 2) AS spend
FROM fact_impression f
JOIN dim_resolved d ON d.advertiser_id = f.advertiser_id
 AND f.event_date >= d.effective_from AND f.event_date < d.effective_to
ORDER BY f.impression_id
"""
expect("Q27 day-1 impressions retroactively pick up the real attributes", RESOLVED, [
    (1, "Acme Corp",  "gold",   100.00),
    (2, "Globex Ltd", "silver", 250.00),
    (3, "Globex Ltd", "silver", 150.00),
])

assert spark.sql("SELECT COUNT(*) FROM dim_resolved WHERE is_inferred") \
    .collect()[0][0] == 0
print("[PASS] Q27 no inferred rows remain -- the placeholder was resolved, not duplicated")

# ---------------------------------------------------------- THE BACKDATING TRAP
# Resolve with effective_from = TODAY instead of the fact date, and day-1
# impressions fall into a coverage gap.
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW dim_badly_resolved AS
SELECT * FROM VALUES
    (1, 601, 'Acme Corp',  'gold',   DATE'2026-01-01', DATE'{OPEN_END}'),
    (2, 602, 'Globex Ltd', 'silver', DATE'{RESOLVE_DATE}', DATE'{OPEN_END}')
AS t(advertiser_sk, advertiser_id, name, tier, effective_from, effective_to)
""")
gap = spark.sql("""
SELECT ROUND(COALESCE(SUM(f.spend), 0), 2) AS attributed
FROM fact_impression f
JOIN dim_badly_resolved d ON d.advertiser_id = f.advertiser_id
 AND f.event_date >= d.effective_from AND f.event_date < d.effective_to
""").collect()[0][0]
assert float(gap) == 100.00, gap
print(f"[PASS] Q27 resolving with today's date attributes only {gap} of 500.00 -- "
      "the 400.00 of day-1 spend falls into a coverage gap")

# ---------------------------------------------------------- why -1 cannot be used
# Route both unknown advertisers to a shared Unknown member and they become
# indistinguishable, so tonight's batch has nothing to resolve against.
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW fact_with_unknown AS
SELECT * FROM VALUES
    (2, -1, 602, DATE'{FACT_DATE}', CAST(250.00 AS DECIMAL(12,2))),
    (4, -1, 603, DATE'{FACT_DATE}', CAST( 75.00 AS DECIMAL(12,2)))
AS t(impression_id, advertiser_sk, true_advertiser_id, event_date, spend)
""")
collapsed = spark.sql("""
SELECT advertiser_sk, COUNT(DISTINCT true_advertiser_id) AS distinct_advertisers
FROM fact_with_unknown GROUP BY advertiser_sk
""").collect()[0]
assert (collapsed[0], collapsed[1]) == (-1, 2), collapsed
print("[PASS] Q27 a shared Unknown key collapses 2 distinct advertisers into one "
      "bucket -- unresolvable; an inferred member keeps them separate")

# ---- MySQL way ----------------------------------------------------------
# CREATE TABLE + sample data:
#   CREATE TABLE dim_advertiser (
#       advertiser_sk   INT             NOT NULL,
#       advertiser_id   INT             NOT NULL,
#       name            VARCHAR(64)     NOT NULL,
#       country         VARCHAR(8)      NOT NULL,
#       tier            VARCHAR(16)     NOT NULL,
#       is_inferred     TINYINT(1)      NOT NULL,
#       effective_from  DATE            NOT NULL,
#       effective_to    DATE            NOT NULL,
#       is_current      TINYINT(1)      NOT NULL,
#       PRIMARY KEY (advertiser_sk),
#       KEY idx_dim_adv_id (advertiser_id),
#       KEY idx_dim_adv_pit (advertiser_id, effective_from, effective_to),
#       KEY idx_dim_adv_inferred (is_inferred)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO dim_advertiser
#       (advertiser_sk, advertiser_id, name, country, tier, is_inferred,
#        effective_from, effective_to, is_current) VALUES
#       (1, 601, 'Acme Corp',  'US', 'gold',   0, '2026-01-01', '9999-12-31', 1);
#
#   CREATE TABLE fact_impression (
#       impression_id  INT             NOT NULL,
#       advertiser_id  INT             NOT NULL,
#       event_date     DATE            NOT NULL,
#       spend          DECIMAL(12,2)   NOT NULL,
#       PRIMARY KEY (impression_id),
#       KEY idx_fact_imp_adv_date (advertiser_id, event_date)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO fact_impression (impression_id, advertiser_id, event_date, spend) VALUES
#       (1, 601, '2026-03-01', 100.00),
#       (2, 602, '2026-03-01', 250.00),
#       (3, 602, '2026-03-01', 150.00);
#
#   -- Q27 inferred member inserted, keyed on the real natural key (expect block).
#   -- Step 1: detect orphans
#   SELECT DISTINCT f.advertiser_id
#   FROM fact_impression f
#   WHERE NOT EXISTS (SELECT 1 FROM dim_advertiser d WHERE d.advertiser_id = f.advertiser_id);
#
#   -- Step 2: insert one inferred row PER unseen natural key, effective_from = fact date.
#   INSERT INTO dim_advertiser
#       (advertiser_sk, advertiser_id, name, country, tier, is_inferred,
#        effective_from, effective_to, is_current)
#   SELECT (SELECT COALESCE(MAX(advertiser_sk), 0) FROM dim_advertiser) +
#              ROW_NUMBER() OVER (ORDER BY f.advertiser_id) AS advertiser_sk,
#          f.advertiser_id,
#          '(inferred)', '(unknown)', '(unknown)', 1,
#          '2026-03-01', '9999-12-31', 1
#   FROM fact_impression f
#   LEFT JOIN dim_advertiser d ON d.advertiser_id = f.advertiser_id
#   WHERE d.advertiser_id IS NULL;
#
#   SELECT advertiser_sk, advertiser_id, name, tier, is_inferred,
#          effective_from, effective_to, is_current
#   FROM dim_advertiser ORDER BY advertiser_sk;
#
#   -- Q27 day-1 impressions retroactively pick up the real attributes (expect block)
#   CREATE TABLE staging_advertiser (
#       advertiser_id  INT         NOT NULL,
#       name           VARCHAR(64) NOT NULL,
#       country        VARCHAR(8)  NOT NULL,
#       tier           VARCHAR(16) NOT NULL
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO staging_advertiser (advertiser_id, name, country, tier) VALUES
#       (602, 'Globex Ltd', 'DE', 'silver');
#
#   -- Resolution: UPDATE the placeholder IN PLACE, effective_from UNCHANGED.
#   UPDATE dim_advertiser d
#   JOIN staging_advertiser s ON s.advertiser_id = d.advertiser_id
#   SET d.name        = s.name,
#       d.country     = s.country,
#       d.tier        = s.tier,
#       d.is_inferred = 0
#   WHERE d.is_inferred = 1;
#
#   SELECT f.impression_id, d.name, d.tier, ROUND(f.spend, 2) AS spend
#   FROM fact_impression f
#   JOIN dim_advertiser d ON d.advertiser_id = f.advertiser_id
#    AND f.event_date >= d.effective_from AND f.event_date < d.effective_to
#   ORDER BY f.impression_id;
#
#   -- THE BACKDATING TRAP: resolving with effective_from = today leaves a gap.
#   INSERT INTO dim_advertiser
#       (advertiser_sk, advertiser_id, name, tier, effective_from, effective_to) VALUES
#       (3, 602, 'Globex Ltd', 'silver', '2026-03-02', '9999-12-31');
#   -- The day-1 spend falls into a coverage gap.
#
# MySQL 8.0+ notes: NOT EXISTS / LEFT JOIN ... IS NULL is the MySQL-idiomatic
# anti-join. Resolution is a single UPDATE ... JOIN that mutates the inferred
# row in place -- inserting a second row leaves historical facts pointing at
# the placeholder forever. The is_inferred TINYINT(1) flag is what makes the
# dimension-feed gap MONITORABLE; without it the backdating trap is invisible
# until the next reconciliation fails. The (idx_dim_adv_pit) covering index
# keeps the half-open point-in-time join a single range scan at Meta volume.
