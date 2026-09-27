"""
Q48: Coverage Analysis: Data Quality Check   [Medium | Inner Joins, Aggregate Functions, Data Quality]
DataVidhya slug: coverage-analysis-data-quality

Per EXPECTED category: expected_count, actual_count (0 if none loaded),
missing_count, coverage_pct. Categories only in the actual set are ignored.

How to Think:
- AGGREGATE BOTH SIDES FIRST, then join the two one-row-per-category summaries.
  This is the whole question. Joining the raw record tables and counting
  afterwards fans out: category A has 4 expected x 3 actual = 12 rows, and both
  counts come out 12.
- Direction matters: `expected LEFT JOIN actual`. `expected` is the driving set
  (it is the requirement), so a category with nothing loaded survives, and a
  category that was never expected cannot enter.
- Grain, out loud: "one row per expected category."

The trap:
- The fan-out above. It is silent -- 12/12 = 100% coverage, which is exactly the
  answer a broken pipeline would love to report. This is a data-QUALITY check,
  so a query that cannot detect missing data is worse than no query.
- Category C has zero actual records, so the LEFT JOIN yields NULL and it must
  be COALESCEd to 0 -- for actual_count, for missing_count, and inside
  coverage_pct. A bare NULL propagates through the arithmetic and C reports NULL
  instead of 0.00.
- Category Z exists only in `actual_records` (an unexpected extra) and must be
  dropped. A FULL OUTER JOIN or `actual LEFT JOIN expected` would keep it.
- Integer division: use 100.0.
- missing_count can in principle go negative if more loaded than expected --
  worth flagging aloud as a separate alert, not clamping silently.

Spark note:
- Two small pre-aggregations then a broadcast join. This shape also keeps the
  join keyed on category (low cardinality) rather than record_id.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("48-coverage-data-quality")
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
# A: 4 expected / 3 loaded. B: 3 / 3. C: 2 / 0. Z: loaded but never expected.
spark.sql("""
CREATE OR REPLACE TEMP VIEW actual_records AS
SELECT * FROM VALUES
    (70001, 'A', DATE'2024-06-04', CAST(4606.98 AS DECIMAL(10,2))),
    (70002, 'A', DATE'2024-03-19', CAST(1680.69 AS DECIMAL(10,2))),
    (70003, 'A', DATE'2024-05-07', CAST(2394.83 AS DECIMAL(10,2))),
    (70014, 'B', DATE'2024-04-20', CAST(2609.24 AS DECIMAL(10,2))),
    (70015, 'B', DATE'2024-07-28', CAST(3677.63 AS DECIMAL(10,2))),
    (70016, 'B', DATE'2024-03-27', CAST(4546.52 AS DECIMAL(10,2))),
    (70099, 'Z', DATE'2024-08-01', CAST( 999.99 AS DECIMAL(10,2)))
AS t(record_id, category, actual_date, value)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW expected_records AS
SELECT * FROM VALUES
    (70001, 'A', DATE'2024-02-02'),
    (70002, 'A', DATE'2024-04-05'),
    (70003, 'A', DATE'2024-08-01'),
    (70004, 'A', DATE'2024-06-12'),
    (70014, 'B', DATE'2024-01-25'),
    (70015, 'B', DATE'2024-09-25'),
    (70016, 'B', DATE'2024-01-18'),
    (70029, 'C', DATE'2024-01-07'),
    (70030, 'C', DATE'2024-12-30')
AS t(record_id, category, expected_date)
""")

from pyspark.sql import functions as F

# Aggregate each side to one row per category BEFORE joining.
SQL = """
WITH exp AS (
    SELECT category, COUNT(*) AS expected_count
    FROM expected_records
    GROUP BY category
),
act AS (
    SELECT category, COUNT(*) AS actual_count
    FROM actual_records
    GROUP BY category
)
SELECT e.category,
       e.expected_count,
       COALESCE(a.actual_count, 0)                      AS actual_count,
       e.expected_count - COALESCE(a.actual_count, 0)   AS missing_count,
       ROUND(COALESCE(a.actual_count, 0) * 100.0 / e.expected_count, 2) AS coverage_pct
FROM exp e
LEFT JOIN act a ON a.category = e.category     -- expected drives; Z cannot enter
ORDER BY e.category
"""

spark.sql(SQL).show(truncate=False)

EXPECTED = [
    ("A", 4, 3, 1,  75.00),
    ("B", 3, 3, 0, 100.00),
    ("C", 2, 0, 2,   0.00),
]
expect("Q48 coverage per expected category", SQL, EXPECTED)

# DataFrame API equivalent.
exp = (spark.table("expected_records").groupBy("category")
       .agg(F.count(F.lit(1)).alias("expected_count")))
act = (spark.table("actual_records").groupBy("category")
       .agg(F.count(F.lit(1)).alias("actual_count")))
df = (exp.join(F.broadcast(act), "category", "left")
      .withColumn("actual_count", F.coalesce("actual_count", F.lit(0)))
      .withColumn("missing_count", F.col("expected_count") - F.col("actual_count"))
      .withColumn("coverage_pct",
                  F.round(F.col("actual_count") * F.lit(100.0) / F.col("expected_count"), 2))
      .select("category", "expected_count", "actual_count", "missing_count", "coverage_pct")
      .orderBy("category"))
assert [(r[0], r[1], r[2], r[3], float(r[4])) for r in df.collect()] == [
    ("A", 4, 3, 1, 75.0), ("B", 3, 3, 0, 100.0), ("C", 2, 0, 2, 0.0),
]
print("[PASS] Q48 DataFrame API matches SQL")

# ------------------------------------------------ the fan-out trap
# Joining the raw record tables multiplies A's rows 4 x 3 and reports 100%.
fanned = spark.sql("""
SELECT e.category,
       COUNT(*) AS expected_count,
       COUNT(a.record_id) AS actual_count,
       ROUND(COUNT(a.record_id) * 100.0 / COUNT(*), 2) AS coverage_pct
FROM expected_records e
LEFT JOIN actual_records a ON a.category = e.category
GROUP BY e.category ORDER BY e.category
""").collect()
assert [(r[0], r[1], r[2], float(r[3])) for r in fanned] == [
    ("A", 12, 12, 100.0), ("B", 9, 9, 100.0), ("C", 2, 0, 0.0),
], fanned
print("[PASS] Q48 joining raw rows inflates A to 12/12 = 100% -- a QA check that cannot fail")

# ------------------------------------------------ the NULL-propagation trap
no_coalesce = spark.sql("""
WITH exp AS (SELECT category, COUNT(*) AS expected_count FROM expected_records GROUP BY category),
     act AS (SELECT category, COUNT(*) AS actual_count   FROM actual_records   GROUP BY category)
SELECT e.category, a.actual_count,
       e.expected_count - a.actual_count AS missing_count,
       ROUND(a.actual_count * 100.0 / e.expected_count, 2) AS coverage_pct
FROM exp e LEFT JOIN act a ON a.category = e.category
ORDER BY e.category
""").collect()
c_row = [r for r in no_coalesce if r[0] == "C"][0]
assert (c_row[1], c_row[2], c_row[3]) == (None, None, None), c_row
print("[PASS] Q48 without COALESCE, category C reports NULL/NULL/NULL instead of 0/2/0.00")

# ------------------------------------------------ the unexpected-category trap
cats = [r[0] for r in spark.sql(SQL).collect()]
assert "Z" not in cats, cats
full_outer = sorted({r[0] for r in spark.sql("""
WITH exp AS (SELECT category FROM expected_records GROUP BY category),
     act AS (SELECT category FROM actual_records   GROUP BY category)
SELECT COALESCE(e.category, a.category) AS category
FROM exp e FULL OUTER JOIN act a ON a.category = e.category
""").collect()})
assert full_outer == ["A", "B", "C", "Z"], full_outer
print("[PASS] Q48 FULL OUTER JOIN would admit the unexpected category Z")
