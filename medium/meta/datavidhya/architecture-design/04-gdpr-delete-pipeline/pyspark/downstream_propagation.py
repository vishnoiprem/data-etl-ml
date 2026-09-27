"""
Spark Batch: Find all derived tables that may contain re-identifiable data.

Walks the lineage graph from a set of source tables and emits a deletion plan
for downstream tables (aggregates, joins, ML features).
"""

import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit


def build_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("downstream_propagation")
        .getOrCreate()
    )


# Source: lineage graph export from DataHub / OpenLineage
LINEAGE_EDGES = [
    ("local.bronze.events",               "local.silver.events"),
    ("local.silver.events",               "local.gold.user_features_daily"),
    ("local.silver.events",               "local.gold.session_metrics"),
    ("local.gold.user_features_daily",    "local.ml.training_set"),
    ("local.gold.user_features_daily",    "local.ml.feast_features"),
    ("local.gold.user_features_daily",    "snowflake.analytics.dwd"),
    ("local.gold.session_metrics",        "elasticsearch.events-2026"),
    ("local.gold.session_metrics",        "redis.session_cache"),
]


def propagate_deletions(source_tables: list[str], user_id: str) -> list[dict]:
    """BFS through the lineage graph to find all tables needing a delete."""
    spark = build_spark()
    edges = spark.createDataFrame(
        [(u, d) for u, d in LINEAGE_EDGES], "upstream STRING, downstream STRING"
    )

    visited = set()
    frontier = set(source_tables)
    plan = []

    while frontier:
        visited |= frontier
        next_frontier = set()
        for src in frontier:
            children = [r.downstream for r in edges.filter(col("upstream") == src).collect()]
            for child in children:
                if child not in visited:
                    plan.append({
                        "table": child,
                        "depth_from_source": 1,    # simplified
                        "delete_method": "direct" if "ml" not in child and "redis" not in child else "soft_delete",
                    })
                    next_frontier.add(child)
        frontier = next_frontier
    return plan


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source-tables", nargs="+", required=True)
    p.add_argument("--user-id", required=True)
    args = p.parse_args()
    plan = propagate_deletions(args.source_tables, args.user_id)
    print(f"\nDeletion plan for {args.user_id}:")
    for step in plan:
        print(f"  {step['table']:40s} method={step['delete_method']}")
