"""
Spark Batch: Build long-term audit table of moderation decisions.

Joins content + scores + decisions + human_review_actions into a single
wide audit table for legal/regulatory reporting.
"""

import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit


def build_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("moderation_audit")
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.local.type", "hadoop")
        .getOrCreate()
    )


def build_audit_table(
    content_table: str,
    scores_table: str,
    decisions_table: str,
    human_actions_table: str,
    out_table: str,
    since_days: int = 30,
):
    spark = build_spark()

    content = spark.read.format("iceberg").load(content_table)
    scores  = spark.read.format("iceberg").load(scores_table)
    dec     = spark.read.format("iceberg").load(decisions_table)
    human   = spark.read.format("iceberg").load(human_actions_table)

    # Pivot scores: one row per content × class_label with text/image/video cols
    scores_pivot = (scores.groupBy("content_id", "class_label")
                          .pivot("modality", ["text", "image", "video_frame"])
                          .agg({"score": "max"})
                          .fillna(0.0))

    audit = (content
             .join(dec, "content_id", "left")
             .join(scores_pivot, "content_id", "left")
             .join(human.groupBy("content_id")
                          .agg({"decision": "first"})
                          .withColumnRenamed("first(decision)", "human_decision"),
                   "content_id", "left")
             .select(
                 "content_id", "user_id", "content_type",
                 "class_label",
                 col("text").alias("score_text"),
                 col("image").alias("score_image"),
                 col("video_frame").alias("score_video"),
                 "severity_class", "decision AS auto_decision", "confidence",
                 "threshold_used", "model_versions",
                 "human_decision",
                 "decided_ts",
             ))

    (audit.write
          .format("iceberg")
          .mode("append")
          .partitionedBy("days(decided_ts)")
          .saveAsTable(out_table))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--content",   default="local.dim.content")
    p.add_argument("--scores",    default="local.gold.content_scores")
    p.add_argument("--decisions", default="local.gold.moderation_decisions")
    p.add_argument("--human",     default="local.gold.human_review_actions")
    p.add_argument("--out",       default="local.gold.audit_full")
    args = p.parse_args()
    build_audit_table(args.content, args.scores, args.decisions, args.human, args.out)
