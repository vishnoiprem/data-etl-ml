"""
Spark Batch: Build labeled training dataset for model retraining.

Joins human_review_actions with content_scores + content_features.
Outputs a balanced labeled dataset (per class) for offline training.
"""

import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, lit, rand


def build_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("moderation_training_dataset")
        .getOrCreate()
    )


def build(
    actions_table: str,
    content_table: str,
    scores_table: str,
    out_path: str,
    sample_per_class: int = 50_000,
):
    spark = build_spark()

    actions = (spark.read.format("iceberg").load(actions_table)
                          .select("content_id", "reviewer_id",
                                  "decision", col("decided_ts").alias("label_ts")))

    scores = (spark.read.format("iceberg").load(scores_table)
                         .groupBy("content_id")
                         .pivot("modality", ["text", "image", "video_frame"])
                         .agg({"score": "max"}))

    content = (spark.read.format("iceberg").load(content_table)
                          .select("content_id", "content_type", "language"))

    # Label: REMOVE → 1, else 0
    labeled = (actions
               .withColumn("label", when(col("decision") == "REMOVE", 1).otherwise(0))
               .join(content, "content_id")
               .join(scores,  "content_id")
               .withColumn("text_present",  when(col("text").isNotNull(),  1).otherwise(0))
               .withColumn("image_present", when(col("image").isNotNull(), 1).otherwise(0)))

    # Balance classes by random sampling
    balanced = (labeled
                .withColumn("rand_key", rand())
                .orderBy("label", "rand_key")
                .limit(sample_per_class * 2))

    (balanced.write
              .mode("overwrite")
              .format("parquet")
              .save(out_path))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--actions", default="local.gold.human_review_actions")
    p.add_argument("--content", default="local.dim.content")
    p.add_argument("--scores",  default="local.gold.content_scores")
    p.add_argument("--out",     required=True)
    args = p.parse_args()
    build(args.actions, args.content, args.scores, args.out)
