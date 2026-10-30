"""
Q09: Top 5th Percentile Fraud Score Per State   [Hard | Window Functions]

Find records in the top 5th percentile of fraud_score within each state.

How to Think:
- "Top 5th percentile" = the highest-scoring 5%. Order DESC and take
  PERCENT_RANK() < 0.05.
- Know the three ranking windows and why PERCENT_RANK is right here:
    PERCENT_RANK() = (rank - 1) / (rows - 1)  -> 0.0 for the top row always
    CUME_DIST()    = rows <= current / rows   -> never 0
    NTILE(20)      = bucket 1 of 20            -> needs >= 20 rows per state
- NTILE is the wrong tool on small partitions: with 4 rows, NTILE(20) puts one
  row in each of buckets 1-4 and the "top 5%" becomes the top 25%.

The trap:
- PERCENT_RANK is always exactly 0.0 for the first row of a partition, so
  `< 0.05` returns the single top row even when the partition has one row
  (Texas). Whether that is desired is a question worth asking aloud.

Spark note:
- One window shuffle partitioned by state. Skewed states would need salting.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("09-top-percentile-fraud")
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
    (1, "CA", 10.0), (2, "CA", 20.0), (3, "CA", 30.0), (4, "CA", 90.0),
    (5, "NY", 40.0), (6, "NY", 95.0),
    (7, "TX", 50.0),
],
    ["record_id", "state", "fraud_score"]
).createOrReplaceTempView("fraud_scores")


SQL = """
WITH ranked AS (
    SELECT record_id, state, fraud_score,
           PERCENT_RANK() OVER (PARTITION BY state ORDER BY fraud_score DESC) AS pr
    FROM fraud_scores
)
SELECT record_id, state, fraud_score
FROM ranked
WHERE pr < 0.05
ORDER BY state, fraud_score DESC
"""

expect("Q09 top 5th percentile fraud per state", SQL, [
    (4, "CA", 90.0), (6, "NY", 95.0), (7, "TX", 50.0),
])

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports PERCENT_RANK as a window function. PERCENT_RANK() = 0
# for the first row of every partition by construction, so a `< 0.05` filter
# returns the single top row per state -- including single-row states (Texas).
# NTILE(20) would be wrong on small partitions: with 4 rows, NTILE puts one
# row in each of buckets 1-4 and "top 5%" becomes the top 25%.
#
# CREATE TABLE fraud_scores (
#     record_id   INT         NOT NULL,
#     state       VARCHAR(8)  NOT NULL,
#     fraud_score DECIMAL(6,2) NOT NULL,
#     PRIMARY KEY (record_id),
#     KEY ix_fs_state_score (state, fraud_score DESC)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO fraud_scores (record_id, state, fraud_score) VALUES
#     (1, 'CA', 10.0), (2, 'CA', 20.0), (3, 'CA', 30.0), (4, 'CA', 90.0),
#     (5, 'NY', 40.0), (6, 'NY', 95.0),
#     (7, 'TX', 50.0);
#
# WITH ranked AS (
#     SELECT record_id, state, fraud_score,
#            PERCENT_RANK() OVER (PARTITION BY state ORDER BY fraud_score DESC) AS pr
#     FROM fraud_scores
# )
# SELECT record_id, state, fraud_score
# FROM ranked
# WHERE pr < 0.05
# ORDER BY state, fraud_score DESC;
#
# -- Expected: (4, 'CA', 90.0), (6, 'NY', 95.0), (7, 'TX', 50.0).
