"""
Q53: Get Top N Records per Group   [Medium | Window Functions, Aggregate Functions]
DataVidhya slug: top-n-records-per-group

Sum revenue by region+product, rank within region with TIES SHARING A RANK AND
NO GAPS, keep ranks 1-3.

How to Think:
- Two stages and they must be in this order: AGGREGATE first (revenue per
  region+product), THEN rank the aggregates. Ranking raw sale rows ranks
  individual sales, and North/Laptop's two rows would never combine into 1500.
- "Assign equal totals the same rank" + "keep ranks 1 through 3" together force
  DENSE_RANK. Work out why on the data before writing it: North has totals
  1500, 800, 800, 200. DENSE_RANK gives 1, 2, 2, 3 -- four rows survive.
  RANK gives 1, 2, 2, 4 -- Mouse is excluded. The expected output keeps Mouse,
  so DENSE_RANK is the only function that fits.
- "Top 3" here means top 3 RANKS, not top 3 ROWS. North legitimately returns 4.

The trap:
- RANK vs DENSE_RANK vs ROW_NUMBER, and this question is engineered so all three
  differ. ROW_NUMBER would give Monitor 2 and Tablet 3 (breaking the tie
  arbitrarily and dropping Mouse); RANK drops Mouse via the gap; only
  DENSE_RANK matches.
- Ranking before aggregating: North/Laptop's 1000 and 500 must sum to 1500,
  which outranks Monitor's 800. Rank the raw rows and Laptop's 1000 is still
  first but its 500 row lands near the bottom.
- The two tied rows (Monitor, Tablet at rank 2) need a third sort key or their
  order is non-deterministic; the expected output has them alphabetical.

Spark note:
- Shuffle once for the GROUP BY, then again for the window (different key:
  region only). Partitioning the aggregate by region would avoid the second.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("53-top-n-per-group")
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


TOP_N = 3

# ---------------------------------------------------------- sample data
# Exactly the rows DataVidhya ships with the question.
# North/Laptop spans two sales (1000 + 500); Monitor and Tablet tie at 800.
spark.sql("""
CREATE OR REPLACE TEMP VIEW sales AS
SELECT * FROM VALUES
    (1, 'North', 'Laptop',  DATE'2024-01-01', 1000),
    (2, 'North', 'Laptop',  DATE'2024-01-02',  500),
    (3, 'North', 'Monitor', DATE'2024-01-01',  800),
    (4, 'North', 'Tablet',  DATE'2024-01-01',  800),
    (5, 'North', 'Mouse',   DATE'2024-01-01',  200),
    (6, 'South', 'Phone',   DATE'2024-01-01',  900),
    (7, 'South', 'Tablet',  DATE'2024-01-01',  700),
    (8, 'South', 'Watch',   DATE'2024-01-01',  600)
AS t(sale_id, region, product_name, sale_date, revenue)
""")

from pyspark.sql import functions as F, Window as W

SQL = f"""
WITH totals AS (
    -- aggregate BEFORE ranking
    SELECT region, product_name, SUM(revenue) AS total_revenue
    FROM sales
    GROUP BY region, product_name
),
ranked AS (
    SELECT region, product_name, total_revenue,
           DENSE_RANK() OVER (PARTITION BY region
                              ORDER BY total_revenue DESC) AS region_rank
    FROM totals
)
SELECT region, product_name, total_revenue, region_rank
FROM ranked
WHERE region_rank <= {TOP_N}
ORDER BY region, region_rank, product_name
"""

spark.sql(SQL).show(truncate=False)

EXPECTED = [
    ("North", "Laptop",  1500, 1),
    ("North", "Monitor",  800, 2),
    ("North", "Tablet",   800, 2),
    ("North", "Mouse",    200, 3),
    ("South", "Phone",    900, 1),
    ("South", "Tablet",   700, 2),
    ("South", "Watch",    600, 3),
]
expect("Q53 top 3 revenue ranks per region", SQL, EXPECTED)

# DataFrame API equivalent.
w = W.partitionBy("region").orderBy(F.col("total_revenue").desc())
df = (spark.table("sales")
      .groupBy("region", "product_name")
      .agg(F.sum("revenue").alias("total_revenue"))
      .withColumn("region_rank", F.dense_rank().over(w))
      .filter(F.col("region_rank") <= TOP_N)
      .orderBy("region", "region_rank", "product_name"))
assert [tuple(r) for r in df.collect()] == EXPECTED
print("[PASS] Q53 DataFrame API matches SQL")

# ------------------------------------------------ all three rank functions differ
compare = spark.sql("""
WITH totals AS (
    SELECT region, product_name, SUM(revenue) AS total_revenue
    FROM sales GROUP BY region, product_name
)
SELECT product_name, total_revenue,
       DENSE_RANK() OVER (PARTITION BY region ORDER BY total_revenue DESC) AS dense,
       RANK()       OVER (PARTITION BY region ORDER BY total_revenue DESC) AS rnk,
       ROW_NUMBER() OVER (PARTITION BY region ORDER BY total_revenue DESC, product_name) AS rn
FROM totals WHERE region = 'North'
ORDER BY total_revenue DESC, product_name
""").collect()
rows = [(r[0], r[1], r[2], r[3], r[4]) for r in compare]
assert rows == [
    ("Laptop", 1500, 1, 1, 1),
    ("Monitor", 800, 2, 2, 2),
    ("Tablet",  800, 2, 2, 3),
    ("Mouse",   200, 3, 4, 4),
], rows
print("[PASS] Q53 Mouse is dense 3 / rank 4 / row_number 4 -- only DENSE_RANK keeps it")

rank_based = spark.sql("""
WITH totals AS (
    SELECT region, product_name, SUM(revenue) AS total_revenue
    FROM sales GROUP BY region, product_name
)
SELECT product_name FROM (
    SELECT region, product_name,
           RANK() OVER (PARTITION BY region ORDER BY total_revenue DESC) AS r
    FROM totals
) WHERE region = 'North' AND r <= 3 ORDER BY product_name
""").collect()
assert [r[0] for r in rank_based] == ["Laptop", "Monitor", "Tablet"], rank_based
print("[PASS] Q53 RANK() drops Mouse from North (3 rows, not 4)")

# ------------------------------------------------ the rank-before-aggregate trap
# Ranking raw sales never combines Laptop's 1000 + 500 into 1500.
raw_ranked = spark.sql("""
SELECT product_name, revenue, r FROM (
    SELECT product_name, revenue, region,
           DENSE_RANK() OVER (PARTITION BY region ORDER BY revenue DESC) AS r
    FROM sales
) WHERE region = 'North' ORDER BY r, product_name
""").collect()
assert [(r[0], r[1], r[2]) for r in raw_ranked] == [
    ("Laptop", 1000, 1), ("Monitor", 800, 2), ("Tablet", 800, 2),
    ("Laptop", 500, 3), ("Mouse", 200, 4),
], raw_ranked
print("[PASS] Q53 ranking raw sales splits Laptop into 1000@1 and 500@3 -- never reaches 1500")

# ------------------------------------------------ top 3 RANKS, not top 3 ROWS
north_rows = [r for r in spark.sql(SQL).collect() if r[0] == "North"]
assert len(north_rows) == 4, north_rows
print("[PASS] Q53 North returns 4 rows for 3 ranks -- 'top 3' means ranks, not rows")

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports the same aggregate-first / DENSE_RANK second pattern.
# DENSE_RANK keeps ties and leaves no gap, so rank 3 still exists when
# rank 2 is shared between Monitor and Tablet.
#
# CREATE TABLE sales (
#     sale_id      INT       NOT NULL,
#     region       VARCHAR(16) NOT NULL,
#     product_name VARCHAR(64) NOT NULL,
#     sale_date    DATE      NOT NULL,
#     revenue      INT       NOT NULL,
#     PRIMARY KEY (sale_id),
#     KEY ix_sales_region_product (region, product_name)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO sales (sale_id, region, product_name, sale_date, revenue) VALUES
#     (1, 'North', 'Laptop',  '2024-01-01', 1000),
#     (2, 'North', 'Laptop',  '2024-01-02',  500),
#     (3, 'North', 'Monitor', '2024-01-01',  800),
#     (4, 'North', 'Tablet',  '2024-01-01',  800),
#     (5, 'North', 'Mouse',   '2024-01-01',  200),
#     (6, 'South', 'Phone',   '2024-01-01',  900),
#     (7, 'South', 'Tablet',  '2024-01-01',  700),
#     (8, 'South', 'Watch',   '2024-01-01',  600);
#
# WITH totals AS (
#     SELECT region, product_name, SUM(revenue) AS total_revenue
#     FROM sales GROUP BY region, product_name
# ),
# ranked AS (
#     SELECT region, product_name, total_revenue,
#            DENSE_RANK() OVER (PARTITION BY region
#                               ORDER BY total_revenue DESC) AS region_rank
#     FROM totals
# )
# SELECT region, product_name, total_revenue, region_rank
# FROM ranked
# WHERE region_rank <= 3
# ORDER BY region, region_rank, product_name;
#
# -- Expected:
# -- North Laptop  1500 1
# -- North Monitor  800 2
# -- North Tablet   800 2
# -- North Mouse    200 3
# -- South Phone    900 1
# -- South Tablet   700 2
# -- South Watch    600 3
