"""
Q35: Top 5 Products with Promotion Analysis   [Hard | Inner Joins, CASE WHEN, Aggregate Functions]
DataVidhya slug: aggregation-top5-products-promo-analysis

Take the 5 products with the greatest total sales revenue and split each one's
revenue into promotional (sale_date inside one of that product's promotion
windows) and non-promotional.

How to Think:
- Three tables, three distinct jobs. Name them before writing SQL:
    products    -> the label, and an INNER JOIN filter (drop orphan sales)
    promotions  -> a date-range PREDICATE, not a source of rows
    sales       -> the fact, and the only thing that gets summed
- Once promotions is a predicate rather than a join, the query is a plain
  conditional aggregate: SUM(CASE WHEN is_promo THEN revenue END).
- total_revenue = promo + non_promo by construction, so the CASE arms must
  partition the rows -- no row in both, no row in neither.

The trap (this is the question):
- A product can have MULTIPLE promotions, and windows can overlap. Joining
  sales to promotions FANS OUT the sale: one sale inside two overlapping
  promotions becomes two rows and its revenue is counted TWICE, so
  total_revenue silently exceeds the real total. Use EXISTS (a semi-join) or
  pre-aggregate promotions to a distinct product/date set. The shipped sample
  has exactly one promotion per product, so it does NOT catch this -- the
  overlap case is asserted separately below.
- Boundaries are INCLUSIVE. The Jan-01 sale falls on start_date and is
  promotional. `> start_date` loses it.
- "Include only sales whose product_id exists in products" -- INNER JOIN, not
  LEFT. Orphan sales are excluded entirely, not bucketed as non-promo.
- Round to ONE decimal place, not two.
- LIMIT applies AFTER the aggregate and AFTER the sort. Filtering to the top 5
  products before summing gives a different (wrong) answer.

Spark note:
- `promotions` is small, so the EXISTS becomes a broadcast left-semi join -- no
  shuffle on the fact side. On real data, range predicates cannot hash-join, so
  broadcasting the promo side is what keeps this cheap.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("35-top5-products-promo")
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
spark.sql("""
CREATE OR REPLACE TEMP VIEW products AS
SELECT * FROM VALUES (1, 'Product A', 'Electronics') AS t(product_id, product_name, category)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW promotions AS
SELECT * FROM VALUES
    (1, 1, DATE'2024-01-01', DATE'2024-01-05', 10)
AS t(promo_id, product_id, start_date, end_date, discount_pct)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW sales AS
SELECT * FROM VALUES
    (1, 1, 10, DATE'2024-01-01', 500),
    (2, 1,  5, DATE'2024-01-10', 250)
AS t(sale_id, product_id, quantity, sale_date, revenue)
""")

from pyspark.sql import functions as F

# EXISTS, not JOIN -- a sale inside two overlapping promotions must stay one row.
SQL = """
WITH tagged AS (
    SELECT p.product_name,
           s.revenue,
           CASE WHEN EXISTS (
                    SELECT 1 FROM promotions pr
                    WHERE pr.product_id = s.product_id
                      AND s.sale_date BETWEEN pr.start_date AND pr.end_date
                ) THEN 1 ELSE 0 END AS is_promo
    FROM sales s
    JOIN products p ON s.product_id = p.product_id
)
SELECT product_name,
       ROUND(CAST(SUM(revenue) AS DOUBLE), 1) AS total_revenue,
       ROUND(CAST(SUM(CASE WHEN is_promo = 1 THEN revenue ELSE 0 END) AS DOUBLE), 1) AS promo_revenue,
       ROUND(CAST(SUM(CASE WHEN is_promo = 0 THEN revenue ELSE 0 END) AS DOUBLE), 1) AS non_promo_revenue
FROM tagged
GROUP BY product_name
ORDER BY total_revenue DESC, product_name
LIMIT 5
"""

spark.sql(SQL).show(truncate=False)

expect("Q35 top-5 products promo split", SQL, [("Product A", 750.0, 500.0, 250.0)])

# DataFrame API equivalent -- left-semi join is the EXISTS.
sales, products, promos = (spark.table("sales").alias("s"),
                           spark.table("products").alias("p"),
                           spark.table("promotions").alias("pr"))
promo_sales = (sales.join(
    F.broadcast(promos),
    (F.col("s.product_id") == F.col("pr.product_id")) &
    (F.col("s.sale_date") >= F.col("pr.start_date")) &
    (F.col("s.sale_date") <= F.col("pr.end_date")),
    "left_semi").select(F.col("sale_id").alias("promo_sale_id")))

df = (sales.join(products, F.col("s.product_id") == F.col("p.product_id"))
      .join(promo_sales, F.col("s.sale_id") == F.col("promo_sale_id"), "left")
      .withColumn("is_promo", F.col("promo_sale_id").isNotNull())
      .groupBy("product_name")
      .agg(F.round(F.sum("revenue").cast("double"), 1).alias("total_revenue"),
           F.round(F.sum(F.when(F.col("is_promo"), F.col("revenue")).otherwise(0))
                   .cast("double"), 1).alias("promo_revenue"),
           F.round(F.sum(F.when(~F.col("is_promo"), F.col("revenue")).otherwise(0))
                   .cast("double"), 1).alias("non_promo_revenue"))
      .orderBy(F.col("total_revenue").desc(), F.col("product_name"))
      .limit(5))
assert [tuple(r) for r in df.collect()] == [("Product A", 750.0, 500.0, 250.0)]
print("[PASS] Q35 DataFrame API matches SQL")

# ------------------------------------------------ the overlapping-promotion trap
# Two promotions both cover 2024-01-01. EXISTS keeps the sale once; a plain
# JOIN would double-count its 500 and report total_revenue = 1250.
spark.sql("""
CREATE OR REPLACE TEMP VIEW promotions AS
SELECT * FROM VALUES
    (1, 1, DATE'2024-01-01', DATE'2024-01-05', 10),
    (2, 1, DATE'2023-12-28', DATE'2024-01-03', 20)
AS t(promo_id, product_id, start_date, end_date, discount_pct)
""")

expect("Q35 overlapping promotions do not double-count", SQL,
       [("Product A", 750.0, 500.0, 250.0)])

fanned = spark.sql("""
SELECT ROUND(CAST(SUM(s.revenue) AS DOUBLE), 1) AS inflated_total
FROM sales s
JOIN products p  ON s.product_id = p.product_id
LEFT JOIN promotions pr
       ON pr.product_id = s.product_id
      AND s.sale_date BETWEEN pr.start_date AND pr.end_date
""").collect()[0][0]
assert fanned == 1250.0, fanned
print("[PASS] Q35 joining promotions inflates total to 1250.0 -- EXISTS keeps it at 750.0")

# ------------------------------------------------ the inclusive-boundary trap
# The Jan-01 sale sits exactly on start_date and must be promotional.
spark.sql("""
CREATE OR REPLACE TEMP VIEW promotions AS
SELECT * FROM VALUES
    (1, 1, DATE'2024-01-01', DATE'2024-01-05', 10)
AS t(promo_id, product_id, start_date, end_date, discount_pct)
""")
exclusive = spark.sql("""
SELECT ROUND(CAST(SUM(CASE WHEN EXISTS (
            SELECT 1 FROM promotions pr
            WHERE pr.product_id = s.product_id
              AND s.sale_date > pr.start_date AND s.sale_date < pr.end_date
       ) THEN s.revenue ELSE 0 END) AS DOUBLE), 1) AS promo_revenue
FROM sales s
""").collect()[0][0]
assert exclusive == 0.0, exclusive
print("[PASS] Q35 exclusive bounds lose the boundary sale (0.0 vs 500.0)")

# ------------------------------------------------ the orphan-sale trap
# A sale for a product that is not in `products` is excluded entirely --
# it must not appear as non-promo revenue.
spark.sql("""
CREATE OR REPLACE TEMP VIEW sales AS
SELECT * FROM VALUES
    (1, 1, 10, DATE'2024-01-01', 500),
    (2, 1,  5, DATE'2024-01-10', 250),
    (3, 99, 1, DATE'2024-01-11', 9999)
AS t(sale_id, product_id, quantity, sale_date, revenue)
""")
expect("Q35 orphan sale (product 99) excluded entirely", SQL,
       [("Product A", 750.0, 500.0, 250.0)])
