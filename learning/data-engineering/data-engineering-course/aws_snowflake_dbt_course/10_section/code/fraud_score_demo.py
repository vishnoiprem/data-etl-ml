"""10_section / code / fraud_score_demo.py

Stand-alone Python dbt model demo. Mirrors the pattern from
dbt_project/models/marts/fraud_score.py.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""
import snowflake.snowpark.functions as F


def model(dbt, session):
    """Compute a fraud risk score per address."""
    tx = dbt.ref("transactions")

    per_address = (
        tx.group_by("from_address")
        .agg(
            F.count_distinct(F.col("to_address")).alias("distinct_counterparties"),
            F.count(F.col("tx_hash")).alias("tx_count"),
            F.sum(F.col("value_eth")).alias("total_value_eth"),
        )
    )

    scored = per_address.with_column(
        "fraud_risk_score",
        F.col("distinct_counterparties") * 0.6 + F.col("tx_count") * 0.4,
    )

    return scored
