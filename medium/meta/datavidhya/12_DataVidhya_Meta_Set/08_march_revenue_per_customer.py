"""
Q08: Customer Revenue in March   [Medium | Date Functions, Aggregation]

Revenue per customer for orders placed in March, revenue = quantity * unit_cost,
sorted descending.

How to Think:
- Revenue is computed PER ROW then summed: SUM(quantity * unit_cost).
  SUM(quantity) * SUM(unit_cost) is a different (wrong) number — a classic slip.
- Filter the month with a half-open range on the date, not by extracting MONTH,
  so the predicate stays partition-prunable and the year is not ignored.
  EXTRACT(MONTH ...) = 3 would also match March of every other year.

The trap:
- The seed data has a February and an April order to catch a missing or
  too-wide date filter.

Spark note:
- On a partitioned table, `order_date >= '2026-03-01' AND < '2026-04-01'`
  prunes partitions. `MONTH(order_date) = 3` forces a full scan — this is the
  "would this scan the whole table?" reasoning Meta rewards.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("08-march-revenue-per-customer")
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
    (1, 10, "2026-03-02", 2, 25.00),
    (2, 10, "2026-03-15", 1, 10.00),
    (3, 11, "2026-03-20", 3, 30.00),
    (4, 12, "2026-02-28", 5, 100.00),   # February - excluded
    (5, 11, "2026-04-01", 1, 99.00),    # April - excluded
],
    ["order_id", "customer_id", "order_date", "quantity", "unit_cost"]
).createOrReplaceTempView("cust_orders")


SQL = """
SELECT customer_id,
       ROUND(SUM(quantity * unit_cost), 2) AS revenue
FROM cust_orders
WHERE order_date >= DATE '2026-03-01'
  AND order_date <  DATE '2026-04-01'
GROUP BY customer_id
ORDER BY revenue DESC, customer_id
"""

expect("Q08 March revenue per customer", SQL, [(11, 90.0), (10, 60.0)])

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports the same GROUP BY + SUM(quantity * unit_cost) pattern.
# Revenue is computed per row first, then summed -- SUM(quantity) * SUM(unit_cost)
# would be wrong (cross-product). The date range is half-open so the partition
# stays prunable on a date-partitioned table, and the year is implicit (no
# EXTRACT(MONTH ...) = 3 that would also match March of other years).
#
# CREATE TABLE cust_orders (
#     order_id    INT            NOT NULL,
#     customer_id INT            NOT NULL,
#     order_date  DATE           NOT NULL,
#     quantity    INT            NOT NULL,
#     unit_cost   DECIMAL(10, 2) NOT NULL,
#     PRIMARY KEY (order_id),
#     KEY ix_co_customer_date (customer_id, order_date)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO cust_orders (order_id, customer_id, order_date, quantity, unit_cost) VALUES
#     (1, 10, '2026-03-02', 2, 25.00),
#     (2, 10, '2026-03-15', 1, 10.00),
#     (3, 11, '2026-03-20', 3, 30.00),
#     (4, 12, '2026-02-28', 5, 100.00),
#     (5, 11, '2026-04-01', 1, 99.00);
#
# SELECT customer_id,
#        ROUND(SUM(quantity * unit_cost), 2) AS revenue
# FROM cust_orders
# WHERE order_date >= '2026-03-01'
#   AND order_date <  '2026-04-01'
# GROUP BY customer_id
# ORDER BY revenue DESC, customer_id;
#
# -- Expected:
# -- 11  90.00
# -- 10  60.00
