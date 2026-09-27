"""
Q23: Implement SCD Type 2 in SQL (the incremental MERGE / upsert path).
Article: "50 Data Modeling Interview Questions for DEs" — SCDs & History Tracking

Meta flavor: "dim_advertiser has 40M rows. A daily CDC feed brings ~200k changed
records. Load them without rewriting the dimension and without losing history."

NOTE: `08_SCD_Types/02_scd_type2_history.py` DERIVES an SCD2 table from a full
change log using LEAD. That is the batch/rebuild path. THIS file is the other
half: the incremental EXPIRE-then-INSERT upsert you run every day against an
existing dimension. Interviewers ask for this one when they say "in SQL".

How to Think:
- The upsert is exactly two writes, and naming them in order is the answer:
    1. EXPIRE: for keys whose tracked attributes changed, close the open row
       (set effective_to, is_current = false).
    2. INSERT: add the new version, effective_from = today, effective_to = the
       open sentinel, is_current = true.
  Plus a third case people forget: brand-new keys, which only need step 2.
- Detect change with a HASH of the tracked columns, not a column-by-column
  comparison. With 30 attributes the OR-chain is unreadable and breaks silently
  when someone adds column 31; a hash is one comparison and fails loudly.
- Do both writes in ONE transaction. Delta/Iceberg MERGE gives you that; two
  independent statements leave the dimension with either zero or two current
  rows for a key if the job dies between them.

The trap:
- THE INTERVAL CONVENTION. `[effective_from, effective_to)` -- inclusive start,
  EXCLUSIVE end. If you close the old row with `effective_to = today` and open
  the new one with `effective_from = today`, then a point-in-time join using
  BETWEEN matches BOTH versions on that date and DOUBLES the fact. Either use a
  half-open join predicate (`>= from AND < to`) or close with `today - 1` and
  use BETWEEN -- never mix the two. Asserted below.
- UNCHANGED rows must not be touched. A MERGE that expires-and-reinserts every
  incoming key generates a new version per day per advertiser, so the dimension
  grows by its full size daily and `is_current` history becomes meaningless.
  The hash comparison is what prevents this.
- Only TRACKED columns trigger a new version. A change to a non-tracked column
  (say `last_login_at`) must be a Type 1 overwrite, or every login creates a
  dimension version.
- Exactly ONE row per natural key may have is_current = true. That is the
  invariant worth asserting in production.

Spark note:
- Real implementation is `MERGE INTO dim USING staging ON ... WHEN MATCHED AND
  hash <> hash THEN UPDATE SET ... WHEN NOT MATCHED THEN INSERT`, which needs
  Delta or Iceberg. Plain Spark SQL views cannot UPDATE, so this file performs
  the same two steps as explicit set operations and asserts the end state --
  the logic and the invariants are identical.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("02-scd-type2-merge")
         .master("local[2]")
         .config("spark.sql.shuffle.partitions", "2")
         .config("spark.ui.showConsoleProgress", "false")
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")


def expect_rows(title, df, expected_rows):
    """Assert a DataFrame's exact rows, in order. Decimal/float safe."""
    import decimal

    def norm(v):
        if isinstance(v, decimal.Decimal):
            return float(v)
        if isinstance(v, float):
            return round(v, 6)
        return v

    got = [tuple(norm(c) for c in r) for r in df.collect()]
    exp = [tuple(norm(c) for c in r) for r in expected_rows]
    if got != exp:
        print(f"[FAIL] {title}")
        print(f"   expected: {exp}")
        print(f"   got:      {got}")
        raise AssertionError(title)
    print(f"[PASS] {title}")
    return got


from pyspark.sql import functions as F, Window as W

TRACKED = ["country", "tier"]        # a change here opens a new version
UNTRACKED = ["last_login_at"]       # a change here is a Type 1 overwrite
OPEN_END = "9999-12-31"             # sentinel, so BETWEEN-style joins work

# ---------------------------------------------------------- current dimension
# Three advertisers, each with exactly one open (is_current) row.
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW dim_advertiser AS
SELECT * FROM VALUES
    (1, 501, 'US', 'gold',   TIMESTAMP'2026-02-01 00:00:00',
        DATE'2026-01-01', DATE'{OPEN_END}', TRUE),
    (2, 502, 'IN', 'silver', TIMESTAMP'2026-02-10 00:00:00',
        DATE'2026-01-01', DATE'{OPEN_END}', TRUE),
    (3, 503, 'BR', 'bronze', TIMESTAMP'2026-02-11 00:00:00',
        DATE'2026-01-01', DATE'{OPEN_END}', TRUE)
AS t(advertiser_sk, advertiser_id, country, tier, last_login_at,
     effective_from, effective_to, is_current)
""")

# ---------------------------------------------------------- today's CDC batch
# 501 -> tier changed        (tracked   -> NEW VERSION)
# 502 -> only last_login_at  (untracked -> Type 1 overwrite, no version)
# 503 -> byte-identical      (unchanged -> must not be touched)
# 504 -> brand new           (insert only, no expire)
spark.sql("""
CREATE OR REPLACE TEMP VIEW staging_advertiser AS
SELECT * FROM VALUES
    (501, 'US', 'platinum', TIMESTAMP'2026-03-01 00:00:00'),
    (502, 'IN', 'silver',   TIMESTAMP'2026-03-01 09:30:00'),
    (503, 'BR', 'bronze',   TIMESTAMP'2026-02-11 00:00:00'),
    (504, 'DE', 'gold',     TIMESTAMP'2026-03-01 10:00:00')
AS t(advertiser_id, country, tier, last_login_at)
""")

LOAD_DATE = "2026-03-01"


def tracked_hash(alias):
    """Hash of the TRACKED columns only -- one comparison instead of an OR-chain."""
    return F.sha2(F.concat_ws("||", *[F.col(f"{alias}.{c}") for c in TRACKED]), 256)


# ---------------------------------------------------------- the MERGE, in steps
dim = spark.table("dim_advertiser").alias("d")
stg = spark.table("staging_advertiser").alias("s")

# Compare only the open rows against staging, on the tracked hash.
open_rows = dim.filter(F.col("d.is_current")).alias("d")
comparison = (open_rows.join(stg,
                             F.col("d.advertiser_id") == F.col("s.advertiser_id"),
                             "full_outer")
              .select(F.col("d.advertiser_sk").alias("existing_sk"),
                      F.col("d.advertiser_id").alias("d_id"),
                      F.col("s.advertiser_id").alias("s_id"),
                      F.col("s.country").alias("s_country"),
                      F.col("s.tier").alias("s_tier"),
                      F.col("s.last_login_at").alias("s_login"),
                      F.col("d.country").alias("d_country"),
                      F.col("d.tier").alias("d_tier"),
                      F.col("d.effective_from").alias("d_from"),
                      tracked_hash("d").alias("d_hash"),
                      tracked_hash("s").alias("s_hash"))
              .cache())

changed = comparison.filter(F.col("d_id").isNotNull() & F.col("s_id").isNotNull()
                            & (F.col("d_hash") != F.col("s_hash")))
brand_new = comparison.filter(F.col("d_id").isNull())
unchanged = comparison.filter(F.col("d_id").isNotNull() & F.col("s_id").isNotNull()
                              & (F.col("d_hash") == F.col("s_hash")))

assert [r[0] for r in changed.select("s_id").collect()] == [501]
assert [r[0] for r in brand_new.select("s_id").collect()] == [504]
assert sorted(r[0] for r in unchanged.select("s_id").collect()) == [502, 503]
print("[PASS] Q23 hash comparison classifies: 501 changed, 504 new, 502/503 unchanged")

# STEP 1 -- EXPIRE the superseded open rows. Close EXCLUSIVE at the load date.
expiring_sks = {r[0] for r in changed.select("existing_sk").collect()}
expired = (dim.withColumn(
    "effective_to",
    F.when(F.col("advertiser_sk").isin(list(expiring_sks)),
           F.lit(LOAD_DATE).cast("date")).otherwise(F.col("effective_to")))
    .withColumn("is_current",
                F.when(F.col("advertiser_sk").isin(list(expiring_sks)),
                       F.lit(False)).otherwise(F.col("is_current"))))

# Type 1 overwrite for the UNTRACKED column, applied to every matched key.
logins = stg.select(F.col("advertiser_id").alias("l_id"),
                    F.col("last_login_at").alias("l_login"))
expired = (expired.join(F.broadcast(logins),
                        F.col("advertiser_id") == F.col("l_id"), "left")
           .withColumn("last_login_at",
                       F.coalesce(F.col("l_login"), F.col("last_login_at")))
           .drop("l_id", "l_login"))

# STEP 2 -- INSERT new versions (changed keys) and first versions (new keys).
next_sk = dim.agg(F.max("advertiser_sk")).collect()[0][0]
to_insert = (changed.select("s_id", "s_country", "s_tier", "s_login")
             .unionByName(brand_new.select("s_id", "s_country", "s_tier", "s_login")))
inserted = (to_insert
            .withColumn("advertiser_sk",
                        F.lit(next_sk) + F.row_number().over(W.orderBy("s_id")))
            .select(F.col("advertiser_sk"),
                    F.col("s_id").alias("advertiser_id"),
                    F.col("s_country").alias("country"),
                    F.col("s_tier").alias("tier"),
                    F.col("s_login").alias("last_login_at"),
                    F.lit(LOAD_DATE).cast("date").alias("effective_from"),
                    F.lit(OPEN_END).cast("date").alias("effective_to"),
                    F.lit(True).alias("is_current")))

merged = expired.unionByName(inserted)
merged.createOrReplaceTempView("dim_advertiser_after")
spark.table("dim_advertiser_after").orderBy("advertiser_id", "effective_from") \
    .show(truncate=False)

import datetime as dt


def d(s):
    return dt.date(*(int(x) for x in s.split("-")))


result = spark.sql("""
SELECT advertiser_id, country, tier, effective_from, effective_to, is_current
FROM dim_advertiser_after ORDER BY advertiser_id, effective_from
""")
expect_rows("Q23 SCD2 upsert end state", result, [
    # 501: history preserved, old row closed EXCLUSIVE at the load date
    (501, "US", "gold",     d("2026-01-01"), d(LOAD_DATE), False),
    (501, "US", "platinum", d(LOAD_DATE),    d(OPEN_END),  True),
    # 502 and 503: untouched, still one open row each
    (502, "IN", "silver",   d("2026-01-01"), d(OPEN_END),  True),
    (503, "BR", "bronze",   d("2026-01-01"), d(OPEN_END),  True),
    # 504: brand new, first version only
    (504, "DE", "gold",     d(LOAD_DATE),    d(OPEN_END),  True),
])

# ---------------------------------------------------------- the invariant
# Exactly one current row per natural key. Assert this in production.
open_per_key = spark.sql("""
SELECT advertiser_id, SUM(CASE WHEN is_current THEN 1 ELSE 0 END) AS open_rows
FROM dim_advertiser_after GROUP BY advertiser_id ORDER BY advertiser_id
""").collect()
assert all(r[1] == 1 for r in open_per_key), open_per_key
print("[PASS] Q23 invariant holds: exactly one is_current row per advertiser_id")

# ---------------------------------------------------------- Type 1 on untracked
login_502 = spark.sql("""
SELECT last_login_at FROM dim_advertiser_after WHERE advertiser_id = 502
""").collect()
assert len(login_502) == 1 and str(login_502[0][0]) == "2026-03-01 09:30:00", login_502
print("[PASS] Q23 502's last_login_at was overwritten in place (Type 1) -- no new version")

# ---------------------------------------------------------- the boundary trap
# 501 has two versions. A half-open point-in-time join matches exactly ONE on
# the boundary date; an inclusive BETWEEN matches BOTH and doubles the fact.
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW fact_spend AS
SELECT * FROM VALUES
    (501, DATE'{LOAD_DATE}', CAST(1000.00 AS DECIMAL(12,2)))
AS t(advertiser_id, event_date, spend)
""")

half_open = spark.sql("""
SELECT COUNT(*) AS matched, ROUND(SUM(f.spend), 2) AS attributed
FROM fact_spend f
JOIN dim_advertiser_after d
  ON d.advertiser_id = f.advertiser_id
 AND f.event_date >= d.effective_from
 AND f.event_date <  d.effective_to        -- EXCLUSIVE end
""").collect()[0]
assert (half_open[0], float(half_open[1])) == (1, 1000.00), half_open
print("[PASS] Q23 half-open join on the boundary date matches 1 version -> 1000.00")

inclusive = spark.sql("""
SELECT COUNT(*) AS matched, ROUND(SUM(f.spend), 2) AS attributed
FROM fact_spend f
JOIN dim_advertiser_after d
  ON d.advertiser_id = f.advertiser_id
 AND f.event_date BETWEEN d.effective_from AND d.effective_to   -- INCLUSIVE
""").collect()[0]
assert (inclusive[0], float(inclusive[1])) == (2, 2000.00), inclusive
print("[PASS] Q23 inclusive BETWEEN matches 2 versions -> 2000.00, double-counted")

# ---------------------------------------------------------- point-in-time works
# The whole reason for Type 2: attribute March spend to the tier held in March,
# and January spend to the tier held in January.
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW fact_spend AS
SELECT * FROM VALUES
    (501, DATE'2026-01-15', CAST( 400.00 AS DECIMAL(12,2))),
    (501, DATE'2026-03-05', CAST( 600.00 AS DECIMAL(12,2)))
AS t(advertiser_id, event_date, spend)
""")
pit = spark.sql("""
SELECT f.event_date, d.tier, ROUND(f.spend, 2) AS spend
FROM fact_spend f
JOIN dim_advertiser_after d
  ON d.advertiser_id = f.advertiser_id
 AND f.event_date >= d.effective_from AND f.event_date < d.effective_to
ORDER BY f.event_date
""")
expect_rows("Q23 point-in-time attribution uses the tier held at the time", pit, [
    (d("2026-01-15"), "gold",     400.00),
    (d("2026-03-05"), "platinum", 600.00),
])

# ---------------------------------------------------------- the every-row-reinsert trap
# A MERGE without the hash guard expires and reinserts all 4 keys, so the
# dimension would gain a version per key per day.
naive_versions = comparison.filter(F.col("s_id").isNotNull()).count()
guarded_versions = changed.count() + brand_new.count()
assert (naive_versions, guarded_versions) == (4, 2), (naive_versions, guarded_versions)
print("[PASS] Q23 no-hash MERGE would write 4 new versions/day; the guard writes 2")
