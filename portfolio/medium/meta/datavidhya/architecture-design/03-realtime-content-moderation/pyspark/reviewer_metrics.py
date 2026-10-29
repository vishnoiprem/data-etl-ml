"""
Spark Batch: Per-reviewer throughput + agreement metrics.

Inputs:
  - human_review_actions table

Outputs:
  - Per-reviewer stats: items reviewed, avg decision time, agreement rate
"""

import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg, unix_timestamp, sum as sum_, when


def build_spark() -> SparkSession:
    return SparkSession.builder.appName("reviewer_metrics").getOrCreate()


def compute_metrics(actions_table: str, out_table: str, since_days: int = 7):
    spark = build_spark()

    actions = spark.read.format("iceberg").load(actions_table)

    per_reviewer = (actions
        .groupBy("reviewer_id")
        .agg(
            count("*").alias("items_reviewed"),
            avg(unix_timestamp("decided_ts") - unix_timestamp(col("enqueued_ts"))).alias("avg_decision_sec"),
            sum_(when(col("decision") == "REMOVE", 1).otherwise(0)).alias("removes"),
            sum_(when(col("decision") == "APPROVE", 1).otherwise(0)).alias("approves"),
            sum_(when(col("decision") == "ESCALATE", 1).otherwise(0)).alias("escalates"),
        ))

    (per_reviewer.write
                  .format("iceberg")
                  .mode("overwrite")
                  .saveAsTable(out_table))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--actions", default="local.gold.human_review_actions")
    p.add_argument("--out",     default="local.gold.reviewer_metrics")
    args = p.parse_args()
    compute_metrics(args.actions, args.out)
