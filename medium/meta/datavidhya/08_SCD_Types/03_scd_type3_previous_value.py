"""
Problem 03: SCD Type 3 — current value plus previous value in the same row.

Meta flavor: "Show me sellers who moved city, with where they came from."

How to Think:
- Type 3 adds columns, not rows: current_city + previous_city. One row per key,
  so it stays cheap to join, but it remembers exactly ONE step of history.
- Built with LAG over the change sequence, then keep the latest row.
- Type 3 is the right choice only when the business question is literally
  "what changed most recently" — e.g. tier upgrades, country moves for
  compliance. The moment someone asks for a value 3 changes ago, or for
  point-in-time correctness, Type 3 cannot answer and you need Type 2.

How to Remember:
- "Type 1 forgets. Type 2 remembers everything (new rows). Type 3 remembers one
  step (new columns)."

The trap:
- Sellers who never changed must still appear, with previous_city NULL — not
  filtered out, and not defaulted to the current value. Both mistakes destroy
  the "did they move?" signal this table exists to answer.

Spark note:
- LAG + ROW_NUMBER in one window pass per key.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("03-scd-type3-previous-value")
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
WITH stepped AS (
    SELECT seller_id, city, tier, changed_on,
           LAG(city) OVER (PARTITION BY seller_id ORDER BY changed_on) AS prev_city,
           ROW_NUMBER() OVER (PARTITION BY seller_id ORDER BY changed_on DESC) AS rn
    FROM seller_changes
)
SELECT seller_id,
       city AS current_city,
       prev_city AS previous_city,
       CASE WHEN prev_city IS NOT NULL AND prev_city <> city THEN true ELSE false END AS moved
FROM stepped
WHERE rn = 1
ORDER BY seller_id
"""
expect("SCD3 current + previous city", SQL, [
    (501, "Chiang Mai", "Bangkok", True),
    (502, "Singapore",  None,      False),
    (503, "Hanoi",      None,      False),
])
