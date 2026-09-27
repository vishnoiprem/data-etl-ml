"""
Q80: Third Highest Product Price   [Easy | Window Functions, Dense_rank, Pandas]
DataVidhya slug: third-highest-product-price

Return EVERY product in the third-highest DISTINCT price tier, ordered by name.

How to Think:
- "Tier" is the giveaway: products with equal prices SHARE a tier, so the
  ranking is over distinct price VALUES and every product at that price is
  returned. DENSE_RANK does exactly that -- ties share a rank AND there are no
  gaps, so "rank 3" always exists if there are 3 distinct prices.
- Contrast Q30 (nth-highest-salary), which is the SAME ranking logic but returns
  the VALUE as a scalar and needs a NULL row when N does not exist. Here the
  question wants the ROWS, so it is a ranking filter, not an aggregate.

The trap:
- RANK() instead of DENSE_RANK(). Prices are 1000, 800, 500, 500, 50. RANK over
  the raw rows gives 1, 2, 3, 3, 5 -- which happens to return the same two rows
  here, so the sample cannot distinguish them. Put the TIE HIGHER UP (two
  products at 1000) and RANK's gap makes rank 3 skip the intended tier
  entirely. Asserted below.
- ROW_NUMBER returns exactly ONE product, so Desk or Chair is dropped
  arbitrarily -- the opposite of "return all products at that price".
- The sort is by product_name, so Chair (id 4) precedes Desk (id 3). Ordering by
  product_id reverses them and looks fine.
- Do not pre-aggregate to distinct prices and lose the product rows -- you need
  both the tier ranking and the rows at that tier.

Spark note:
- The window has no PARTITION BY, so all rows land in one partition. Fine here;
  on a large catalogue, compute the target price first and then filter.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("80-third-highest-product-price")
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


N = 3

# ---------------------------------------------------------- sample data
# Exactly the rows DataVidhya ships with the question.
# Tiers: 1000, 800, 500 (Desk AND Chair), 50. Third tier = 500.
spark.sql("""
CREATE OR REPLACE TEMP VIEW products AS
SELECT * FROM VALUES
    (1, 'Laptop',  CAST(1000 AS DECIMAL(10,2))),
    (2, 'Monitor', CAST( 800 AS DECIMAL(10,2))),
    (3, 'Desk',    CAST( 500 AS DECIMAL(10,2))),
    (4, 'Chair',   CAST( 500 AS DECIMAL(10,2))),
    (5, 'Mouse',   CAST(  50 AS DECIMAL(10,2)))
AS t(product_id, product_name, price)
""")

from pyspark.sql import functions as F, Window as W

# DENSE_RANK: ties share a tier and no tier number is skipped.
SQL = f"""
SELECT product_id, product_name, price
FROM (
    SELECT product_id, product_name, price,
           DENSE_RANK() OVER (ORDER BY price DESC) AS price_tier
    FROM products
)
WHERE price_tier = {N}
ORDER BY product_name
"""

spark.sql(SQL).show(truncate=False)

EXPECTED = [(4, "Chair", 500.0), (3, "Desk", 500.0)]
expect("Q80 products in the third price tier", SQL, EXPECTED)

# DataFrame API equivalent.
df = (spark.table("products")
      .withColumn("price_tier", F.dense_rank().over(W.orderBy(F.col("price").desc())))
      .filter(F.col("price_tier") == N)
      .select("product_id", "product_name", "price")
      .orderBy("product_name"))
assert [(r[0], r[1], float(r[2])) for r in df.collect()] == EXPECTED
print("[PASS] Q80 DataFrame API matches SQL")

# ------------------------------------------------ the tiers, stated
tiers = spark.sql("""
SELECT product_name, price, DENSE_RANK() OVER (ORDER BY price DESC) AS tier
FROM products ORDER BY tier, product_name
""").collect()
assert [(r[0], float(r[1]), r[2]) for r in tiers] == [
    ("Laptop", 1000.0, 1), ("Monitor", 800.0, 2),
    ("Chair", 500.0, 3), ("Desk", 500.0, 3), ("Mouse", 50.0, 4),
], tiers
print("[PASS] Q80 tiers: 1000 -> 1, 800 -> 2, 500 -> 3 (both), 50 -> 4")

# ------------------------------------------------ the sort-key trap
by_name = [r[0] for r in spark.sql(SQL).collect()]
assert by_name == [4, 3], by_name
print("[PASS] Q80 ordering by product_name puts Chair (id 4) before Desk (id 3)")

# ------------------------------------------------ ROW_NUMBER drops a row
row_num = spark.sql(f"""
SELECT COUNT(*) FROM (
    SELECT ROW_NUMBER() OVER (ORDER BY price DESC, product_name) AS rn FROM products
) WHERE rn = {N}
""").collect()[0][0]
assert row_num == 1, row_num
print("[PASS] Q80 ROW_NUMBER returns 1 product; the tier has 2")

# ------------------------------------------------ the RANK trap
# On the shipped data RANK coincidentally agrees...
rank_same = spark.sql(f"""
SELECT product_name FROM (
    SELECT product_name, RANK() OVER (ORDER BY price DESC) AS r FROM products
) WHERE r = {N} ORDER BY product_name
""").collect()
assert [r[0] for r in rank_same] == ["Chair", "Desk"], rank_same
print("[PASS] Q80 on this data RANK coincidentally returns the same two rows")

# ...but move the tie to the TOP tier and RANK's gap skips the third tier.
spark.sql("""
CREATE OR REPLACE TEMP VIEW products AS
SELECT * FROM VALUES
    (1, 'Laptop',  CAST(1000 AS DECIMAL(10,2))),
    (2, 'Desktop', CAST(1000 AS DECIMAL(10,2))),
    (3, 'Monitor', CAST( 800 AS DECIMAL(10,2))),
    (4, 'Desk',    CAST( 500 AS DECIMAL(10,2))),
    (5, 'Mouse',   CAST(  50 AS DECIMAL(10,2)))
AS t(product_id, product_name, price)
""")
expect("Q80 tie in the top tier: third distinct price is 500", SQL, [
    (4, "Desk", 500.0),
])

rank_gap = spark.sql(f"""
SELECT product_name FROM (
    SELECT product_name, RANK() OVER (ORDER BY price DESC) AS r FROM products
) WHERE r = {N} ORDER BY product_name
""").collect()
assert [r[0] for r in rank_gap] == ["Monitor"], rank_gap
print("[PASS] Q80 with a top-tier tie, RANK's rank 3 is Monitor (800) -- "
      "DENSE_RANK correctly gives Desk (500)")
