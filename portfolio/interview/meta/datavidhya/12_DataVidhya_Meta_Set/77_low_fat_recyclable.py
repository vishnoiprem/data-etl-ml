"""
Q77: Low-Fat Recyclable Products   [Easy | Filter]
DataVidhya slug: filtering-low-fat-recyclable-products

Products that are BOTH 'Low Fat' and recyclable ('Y').

How to Think:
- Two exact-equality predicates ANDed together. That is the whole query.
- "Both" = AND. Worth pausing on for one second anyway: OR would return
  products 1, 2, 3, 5 and 7 -- five rows instead of three -- and is the single
  way to get this wrong.

The trap:
- Both flags are VARCHAR, not booleans, and both must match EXACTLY. `is_recyclable
  = 'Y'`, not truthiness, not 'Yes', not 1. On real data you would ask whether
  'y'/'yes'/'TRUE' also occur and normalise with UPPER/TRIM -- the asking is the
  signal here, since a silent case mismatch drops rows without error.
- 'Low Fat' has a SPACE and a capital F. 'low fat' and 'LowFat' both fail an
  equality test.
- Product 5 (Low Fat, not recyclable) and product 2 (recyclable, Regular) are
  the two planted near-misses -- one for each predicate.
- product_id is not contiguous (there is no 6), so do not assume row position.

Spark note:
- Two equality predicates on a scan: both push down to the file source, and on
  a partitioned table either could prune.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("77-low-fat-recyclable")
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
# Exactly the rows DataVidhya ships with the question.
# Product 2 fails on fat, product 5 fails on recyclable -- one near-miss each.
spark.sql("""
CREATE OR REPLACE TEMP VIEW products AS
SELECT * FROM VALUES
    (1, 'Organic Cereal', 'Low Fat', 'Y'),
    (2, 'Whole Milk',     'Regular', 'Y'),
    (3, 'Greek Yogurt',   'Low Fat', 'Y'),
    (4, 'Butter',         'Regular', 'N'),
    (5, 'Almond Milk',    'Low Fat', 'N'),
    (7, 'Skim Yogurt',    'Low Fat', 'Y')
AS t(product_id, product_name, fat_content, is_recyclable)
""")

from pyspark.sql import functions as F

SQL = """
SELECT product_id, product_name
FROM products
WHERE fat_content   = 'Low Fat'      -- exact string, space and capital F
  AND is_recyclable = 'Y'            -- exact string, not truthiness
ORDER BY product_id
"""

spark.sql(SQL).show(truncate=False)

EXPECTED = [(1, "Organic Cereal"), (3, "Greek Yogurt"), (7, "Skim Yogurt")]
expect("Q77 low-fat recyclable products", SQL, EXPECTED)

# DataFrame API equivalent.
df = (spark.table("products")
      .filter((F.col("fat_content") == "Low Fat") & (F.col("is_recyclable") == "Y"))
      .select("product_id", "product_name")
      .orderBy("product_id"))
assert [tuple(r) for r in df.collect()] == EXPECTED
print("[PASS] Q77 DataFrame API matches SQL")

# ------------------------------------------------ AND, not OR
or_version = spark.sql("""
SELECT product_id FROM products
WHERE fat_content = 'Low Fat' OR is_recyclable = 'Y'
ORDER BY product_id
""").collect()
assert [r[0] for r in or_version] == [1, 2, 3, 5, 7], or_version
print("[PASS] Q77 OR returns 5 products (1,2,3,5,7); AND returns the correct 3")

# ------------------------------------------------ each predicate alone
fat_only = [r[0] for r in spark.sql("""
SELECT product_id FROM products WHERE fat_content = 'Low Fat' ORDER BY product_id
""").collect()]
rec_only = [r[0] for r in spark.sql("""
SELECT product_id FROM products WHERE is_recyclable = 'Y' ORDER BY product_id
""").collect()]
assert fat_only == [1, 3, 5, 7] and rec_only == [1, 2, 3, 7]
print("[PASS] Q77 Low Fat alone gives 1,3,5,7; recyclable alone gives 1,2,3,7")

# ------------------------------------------------ the case/format trap
# Mixed-case and no-space variants fail exact equality and vanish silently.
spark.sql("""
CREATE OR REPLACE TEMP VIEW products AS
SELECT * FROM VALUES
    (1, 'Exact',     'Low Fat', 'Y'),
    (2, 'Lowercase', 'low fat', 'y'),
    (3, 'NoSpace',   'LowFat',  'Y'),
    (4, 'Yes',       'Low Fat', 'Yes')
AS t(product_id, product_name, fat_content, is_recyclable)
""")
expect("Q77 only the exactly-formatted row survives", SQL, [(1, "Exact")])

normalised = spark.sql("""
SELECT product_id FROM products
WHERE UPPER(TRIM(fat_content)) = 'LOW FAT'
  AND UPPER(TRIM(is_recyclable)) LIKE 'Y%'
ORDER BY product_id
""").collect()
assert [r[0] for r in normalised] == [1, 2, 4], normalised
print("[PASS] Q77 normalising with UPPER/TRIM would admit 1,2,4 -- "
      "worth asking which the business means")

# ---- MySQL way ----------------------------------------------------------
# Two exact-equality predicates; MySQL handles VARCHAR='literal' the same
# way as Spark, including trailing-space padding rules under the default
# sql_mode. An index on (fat_content, is_recyclable) makes this a covering
# seek on the typical small catalogue.
#
# CREATE TABLE products (
#     product_id     INT          NOT NULL,
#     product_name   VARCHAR(128) NOT NULL,
#     fat_content    VARCHAR(16)  NOT NULL,
#     is_recyclable  CHAR(1)      NOT NULL,
#     PRIMARY KEY (product_id),
#     KEY ix_products_fat_rec (fat_content, is_recyclable)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO products (product_id, product_name, fat_content, is_recyclable) VALUES
#     (1, 'Organic Cereal', 'Low Fat', 'Y'),
#     (2, 'Whole Milk',     'Regular', 'Y'),
#     (3, 'Greek Yogurt',   'Low Fat', 'Y'),
#     (4, 'Butter',         'Regular', 'N'),
#     (5, 'Almond Milk',    'Low Fat', 'N'),
#     (7, 'Skim Yogurt',    'Low Fat', 'Y');
#
# SELECT product_id, product_name
# FROM products
# WHERE fat_content = 'Low Fat'
#   AND is_recyclable = 'Y'
# ORDER BY product_id;
#
# -- Expected rows: (1, 'Organic Cereal'), (3, 'Greek Yogurt'),
# --                (7, 'Skim Yogurt').
