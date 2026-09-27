"""
Problem 01: Deduplicate a CDC feed to one row per key, deterministically.

Meta flavor: "Upstream replays events. Give me one row per seller and make the
job reproducible."

How to Think:
- dropDuplicates(["key"]) is NOT deterministic. It keeps an arbitrary row —
  whichever arrives first in whatever partition order Spark happened to use.
  Re-run the job and you can get a different answer. That alone disqualifies it
  from a production pipeline.
- The correct pattern is ROW_NUMBER() over the key, ordered by a recency column
  PLUS a deterministic tie-breaker for rows sharing that timestamp.
- Without the tie-breaker the job is only *usually* reproducible, which is the
  worst kind of bug: it passes every test and drifts in production.

How to Remember:
- "row_number over key, order by recency THEN a unique tie-break, keep rn = 1."

Spark note:
- One shuffle by key. For very wide rows, select the key + ordering columns
  first, dedup, then join back — you shuffle far less data.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import spark, expect
from pyspark.sql import functions as F, Window

# Simulate a replayed feed: every row duplicated, plus a same-timestamp collision
# for seller 501 that only the tie-breaker can resolve deterministically.
spark.sql("""
SELECT * FROM seller_changes
UNION ALL SELECT * FROM seller_changes
UNION ALL SELECT 501 AS seller_id, 'business' AS tier, 'Chiang Mai' AS city,
                 '2026-01-20' AS changed_on
""").createOrReplaceTempView("cdc_raw")

expect("replayed feed has duplicates", "SELECT COUNT(*) FROM cdc_raw", [(11,)])

SQL = """
WITH ranked AS (
    SELECT seller_id, tier, city, changed_on,
           ROW_NUMBER() OVER (PARTITION BY seller_id
                              ORDER BY changed_on DESC, tier ASC) AS rn
    FROM cdc_raw
)
SELECT seller_id, tier, city, changed_on FROM ranked WHERE rn = 1
ORDER BY seller_id
"""
# Tie on 2026-01-20 for seller 501 between 'power' and 'business';
# `tier ASC` resolves it to 'business' every single run.
expect("deterministic dedup", SQL, [
    (501, "business", "Chiang Mai", "2026-01-20"),
    (502, "business", "Singapore",  "2026-01-01"),
    (503, "casual",   "Hanoi",      "2026-01-03"),
])

# Run it twice and require byte-identical output. This is the property that
# makes a pipeline safely re-runnable.
r1 = [tuple(r) for r in spark.sql(SQL).collect()]
r2 = [tuple(r) for r in spark.sql(SQL).collect()]
assert r1 == r2, "dedup is not reproducible"
print("[PASS] dedup is reproducible across runs")

# DataFrame API equivalent.
w = Window.partitionBy("seller_id").orderBy(F.col("changed_on").desc(), F.col("tier").asc())
df = (spark.table("cdc_raw").withColumn("rn", F.row_number().over(w))
      .filter("rn = 1").drop("rn").orderBy("seller_id"))
assert [tuple(r) for r in df.collect()] == r1
print("[PASS] dedup — DataFrame API matches SQL")
