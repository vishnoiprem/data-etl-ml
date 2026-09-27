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
from _seeds import spark, expect

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
