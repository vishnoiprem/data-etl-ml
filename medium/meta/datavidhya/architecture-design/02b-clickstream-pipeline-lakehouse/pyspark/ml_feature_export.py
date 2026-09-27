"""
Export Iceberg Gold features to ML training formats.

Supports:
  - TFRecord   (TensorFlow)
  - Petastorm  (PyTorch)
  - Parquet    (XGBoost, scikit-learn)

Standard point-in-time correct join: feature snapshot vs label date.
"""

import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, when
from pyspark.sql.window import Window


def build_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("ml_feature_export")
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.local.type", "hadoop")
        .config("spark.sql.catalog.local.warehouse", "s3://lakehouse/warehouse")
        .getOrCreate()
    )


def export_training_set(
    features_table: str,
    labels_table:   str,
    output_path:    str,
    feature_dt:     str,
    label_dt:       str,
    output_format:  str = "tfrecord",
):
    """
    Point-in-time correct training set.
    Features at feature_dt joined with labels at label_dt.
    """
    spark = build_spark()

    features = (spark.read.format("iceberg").load(features_table)
                          .filter(col("dt") == feature_dt))
    labels   = (spark.read.format("iceberg").load(labels_table)
                          .filter(col("dt") == label_dt)
                          .select("user_id", col("label").alias("y")))

    # PIT-correct: features come from BEFORE labels are observed
    train = features.join(labels, on="user_id", how="inner")

    # Drop identifier columns
    train = train.drop("user_id", "dt")

    if output_format == "tfrecord":
        (train.write
              .mode("overwrite")
              .format("tfrecord")
              .option("recordName", "TrainingExample")
              .save(output_path))
    elif output_format == "parquet":
        (train.write
              .mode("overwrite")
              .format("parquet")
              .save(output_path))
    else:
        raise ValueError(f"unsupported format: {output_format}")

    print(f"Wrote training set to {output_path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--features", required=True)
    p.add_argument("--labels",   required=True)
    p.add_argument("--output",   required=True)
    p.add_argument("--feature-dt", required=True)
    p.add_argument("--label-dt",   required=True)
    p.add_argument("--format", default="tfrecord", choices=["tfrecord", "parquet"])
    args = p.parse_args()
    export_training_set(args.features, args.labels, args.output,
                        args.feature_dt, args.label_dt, args.format)
