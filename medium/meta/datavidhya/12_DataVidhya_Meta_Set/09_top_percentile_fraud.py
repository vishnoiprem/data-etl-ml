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
from _seeds import spark, expect

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
