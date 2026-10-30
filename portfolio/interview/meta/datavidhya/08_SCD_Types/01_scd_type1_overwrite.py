"""
Problem 01: SCD Type 1 — overwrite, keep only the current value.

Meta flavor: "The dim just needs the seller's current tier."

How to Think:
- Type 1 keeps ONE row per natural key: the latest. History is destroyed.
- The correct pattern is ROW_NUMBER() over the key ordered by the change
  timestamp DESC, then keep rn = 1. Do NOT use MAX() per column:
  MAX(tier), MAX(city) independently can splice values from DIFFERENT versions
  and invent a row that never existed. That is the classic Type 1 bug.
- Always add a deterministic tie-break to the ORDER BY. Two changes on the same
  timestamp otherwise resolve arbitrarily and the job is non-reproducible.

When Type 1 is right:
- Corrections to bad data, and attributes nobody reports history on.
- If anyone might ask "what was their tier when they made that sale?", you need
  Type 2 instead. Meta's guide flags defaulting to Type 1 as a top mistake.

Spark note:
- One window shuffle by key. This is also the exact dedup pattern in 09/.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("01-scd-type1-overwrite")
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
spark.createDataFrame(
    [
    (501, "casual",   "Bangkok", "2026-01-01"),
    (501, "power",    "Bangkok", "2026-01-05"),
    (501, "power",    "Chiang Mai", "2026-01-20"),
    (502, "business", "Singapore", "2026-01-01"),
    (503, "casual",   "Hanoi",  "2026-01-03"),
],
    ["seller_id", "tier", "city", "changed_on"]
).createOrReplaceTempView("seller_changes")


SQL = """
WITH ranked AS (
    SELECT seller_id, tier, city, changed_on,
           ROW_NUMBER() OVER (PARTITION BY seller_id
                              ORDER BY changed_on DESC, tier DESC) AS rn
    FROM seller_changes
)
SELECT seller_id, tier, city, changed_on
FROM ranked WHERE rn = 1
ORDER BY seller_id
"""
expect("SCD1 current row per seller", SQL, [
    (501, "power",    "Chiang Mai", "2026-01-20"),
    (502, "business", "Singapore",  "2026-01-01"),
    (503, "casual",   "Hanoi",      "2026-01-03"),
])

# The WRONG approach, asserted so the failure mode is documented. Here the
# spliced row happens to look plausible, which is exactly why it is dangerous:
# MAX(tier) is lexicographic ('power' > 'casual'), unrelated to recency.
expect("SCD1 WRONG: independent MAX() splices versions", """
SELECT seller_id, MAX(tier) AS tier, MAX(city) AS city
FROM seller_changes GROUP BY seller_id ORDER BY seller_id
""", [
    (501, "power",    "Chiang Mai"),
    (502, "business", "Singapore"),
    (503, "casual",   "Hanoi"),
])

# ---- MySQL way ----------------------------------------------------------
# CREATE TABLE + sample data:
#   CREATE TABLE seller_changes (
#       seller_id  INT NOT NULL,
#       tier       VARCHAR(16) NOT NULL,
#       city       VARCHAR(60) NOT NULL,
#       changed_on DATE NOT NULL,
#       KEY idx_seller_changed (seller_id, changed_on)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO seller_changes (seller_id, tier, city, changed_on) VALUES
#       (501, 'casual',   'Bangkok',    '2026-01-01'),
#       (501, 'power',    'Bangkok',    '2026-01-05'),
#       (501, 'power',    'Chiang Mai', '2026-01-20'),
#       (502, 'business', 'Singapore',  '2026-01-01'),
#       (503, 'casual',   'Hanoi',      '2026-01-03');
#
# SCD1 current row per seller (MySQL 8.0+ windows):
#   WITH ranked AS (
#       SELECT seller_id, tier, city, changed_on,
#              ROW_NUMBER() OVER (PARTITION BY seller_id
#                                 ORDER BY changed_on DESC, tier DESC) AS rn
#       FROM seller_changes
#   )
#   SELECT seller_id, tier, city, changed_on
#   FROM ranked WHERE rn = 1
#   ORDER BY seller_id;
#
# WRONG (independent MAX() splices versions):
#   SELECT seller_id, MAX(tier) AS tier, MAX(city) AS city
#   FROM seller_changes GROUP BY seller_id ORDER BY seller_id;
# Trap: MAX(tier) is lexicographic ('power' > 'casual'), unrelated to recency.
# On real data where the spliced values come from DIFFERENT versions, you
# invent a row that never existed. Always use ROW_NUMBER(), never MAX().
