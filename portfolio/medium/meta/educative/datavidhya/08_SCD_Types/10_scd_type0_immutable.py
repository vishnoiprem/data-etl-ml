"""
Problem 10: SCD Type 0 (Immutable / No Changes Allowed).

Meta flavor: Regulatory dimensions where the value at the time of event must
never be modified (e.g., transaction currency, KYC classification).

How to Think:
- Once inserted, rows never change.
- New "corrections" are new rows (Type 2 semantics, but corrections are forbidden).
- Audit-friendly.

How to Remember:
- "Type 0: append-only. No UPDATE."

AI Use Cases:
- Regulatory reporting (SOX, GDPR).
- Audit logs.
- Immutable event streams.
"""
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# Type 0: insert only. Corrections are new rows.
dim = spark.createDataFrame(
    [(1, "USD", "2025-01-01")],
    ["transaction_id", "currency", "event_date"]
)

# A "correction" would be a new row, not an UPDATE
correction = spark.createDataFrame(
    [(1, "EUR", "2025-01-02")],   # same transaction, new currency correction
    ["transaction_id", "currency", "event_date"]
)

# Append-only: no UPDATE statement issued
result = dim.union(correction)
result.show()

SQL = """
-- Insert only; no UPDATE statements ever issued.
INSERT INTO dim_transaction (transaction_id, currency, event_date)
VALUES (1, 'EUR', '2025-01-02');
"""
