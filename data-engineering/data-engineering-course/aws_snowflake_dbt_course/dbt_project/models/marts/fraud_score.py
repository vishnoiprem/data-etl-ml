"""Python dbt model: fraud_score.

Author: Prem Vishnoi <pvishnoi@avilx.com>

Lecture reference: L62 "Python Models", L63 "Python Models - Packages
& Execution Constraints", L109 "dbt Unit Tests".

A dbt Python model is a Python file with a `model(dbt, session)`
function. dbt passes in:
- `dbt`: a wrapper around the dbt context (ref(), source(), var(),
  config(), this, is_incremental(), etc.)
- `session`: the Snowflake Snowpark session for DataFrame access.

This model computes a "fraud risk score" per Ethereum address based on
the diversity of counterparties in their transaction history.
"""
import snowflake.snowpark.functions as F


def model(dbt, session):
    """Compute a fraud risk score per address from the transactions mart."""
    # ref() inside a Python model returns a reference to the upstream
    # relation; we materialize it as a Snowpark DataFrame.
    tx = dbt.ref("transactions")

    # Per-address aggregation: distinct counterparties + tx count
    per_address = (
        tx.group_by("from_address")
        .agg(
            F.count_distinct(F.col("to_address")).alias("distinct_counterparties"),
            F.count(F.col("tx_hash")).alias("tx_count"),
            F.sum(F.col("value_eth")).alias("total_value_eth"),
        )
    )

    # Fraud score: simple heuristic — more counterparties + more txs = higher risk
    scored = per_address.with_column(
        "fraud_risk_score",
        F.col("distinct_counterparties") * 0.6 + F.col("tx_count") * 0.4,
    )

    # Always return a Snowpark DataFrame (not pandas).
    return scored
