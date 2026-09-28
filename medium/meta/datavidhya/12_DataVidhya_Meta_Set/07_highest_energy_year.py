"""
Q07: Highest Energy Consumption Year   [Medium | UNION ALL, Aggregation]

Combine three regional tables, aggregate by year, return the highest year.

How to Think:
- UNION ALL, never UNION. UNION deduplicates, which would silently collapse
  two regions that happen to report the same (year, consumption) pair. That is
  a real data-loss bug, and saying why you chose ALL is the signal here.
- Aggregate AFTER the union, not before, so the grain is consistent.
- "The highest year" — use RANK(), not LIMIT 1, so ties surface.

The trap:
- 2024 and 2025 both total 350.0. LIMIT 1 would report one arbitrarily and hide
  the tie. RANK() = 1 returns both, which is the correct answer to "which year".

Spark note:
- UNION ALL is a cheap, shuffle-free append. UNION adds a full distinct shuffle.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("07-highest-energy-year")
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
    [(2024, 100.0), (2025, 150.0)],
    ["year", "consumption"]
).createOrReplaceTempView("energy_asia")

spark.createDataFrame(
    [(2024, 200.0), (2025, 120.0)],
    ["year", "consumption"]
).createOrReplaceTempView("energy_europe")

spark.createDataFrame(
    [(2024,  50.0), (2025,  80.0)],
    ["year", "consumption"]
).createOrReplaceTempView("energy_africa")


SQL = """
WITH all_regions AS (
    SELECT year, consumption FROM energy_asia
    UNION ALL
    SELECT year, consumption FROM energy_europe
    UNION ALL
    SELECT year, consumption FROM energy_africa
),
totals AS (
    SELECT year, SUM(consumption) AS total_consumption
    FROM all_regions
    GROUP BY year
),
ranked AS (
    SELECT year, total_consumption,
           RANK() OVER (ORDER BY total_consumption DESC) AS rnk
    FROM totals
)
SELECT year, total_consumption
FROM ranked
WHERE rnk = 1
ORDER BY year
"""

expect("Q07 highest energy year (tie)", SQL, [(2024, 350.0), (2025, 350.0)])

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports UNION ALL, CTEs, and RANK(). UNION ALL preserves all
# rows -- UNION would silently collapse two regions that happen to report
# the same (year, consumption) pair. Aggregate after the union, not before,
# so the year grain is preserved. RANK() = 1 returns ties; LIMIT 1 would
# hide the 2024/2025 tie at 350.0.
#
# CREATE TABLE energy_asia (
#     year        INT NOT NULL,
#     consumption DECIMAL(10, 2) NOT NULL,
#     PRIMARY KEY (year)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE energy_europe (
#     year        INT NOT NULL,
#     consumption DECIMAL(10, 2) NOT NULL,
#     PRIMARY KEY (year)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE energy_africa (
#     year        INT NOT NULL,
#     consumption DECIMAL(10, 2) NOT NULL,
#     PRIMARY KEY (year)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO energy_asia (year, consumption) VALUES (2024, 100.0), (2025, 150.0);
# INSERT INTO energy_europe (year, consumption) VALUES (2024, 200.0), (2025, 120.0);
# INSERT INTO energy_africa (year, consumption) VALUES (2024,  50.0), (2025,  80.0);
#
# WITH all_regions AS (
#     SELECT year, consumption FROM energy_asia
#     UNION ALL
#     SELECT year, consumption FROM energy_europe
#     UNION ALL
#     SELECT year, consumption FROM energy_africa
# ),
# totals AS (
#     SELECT year, SUM(consumption) AS total_consumption
#     FROM all_regions
#     GROUP BY year
# ),
# ranked AS (
#     SELECT year, total_consumption,
#            RANK() OVER (ORDER BY total_consumption DESC) AS rnk
#     FROM totals
# )
# SELECT year, total_consumption
# FROM ranked
# WHERE rnk = 1
# ORDER BY year;
#
# -- Expected: 2024 350.0, 2025 350.0.
