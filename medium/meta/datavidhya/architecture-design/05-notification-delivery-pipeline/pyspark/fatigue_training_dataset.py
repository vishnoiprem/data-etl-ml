"""
Spark Batch: Build labeled dataset for fatigue model retraining.

Features:
  - notifs_sent_24h, _7d, _30d
  - open_rate_7d, dismiss_rate_7d
  - channel mix (push/email/sms/in-app counts)

Label:
  - 1 if user unsubscribed from any channel in next 7 days
  - 0 otherwise
"""

import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, countDistinct, sum as sum_, when, lit, datediff


def build_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("notification_fatigue_dataset")
        .getOrCreate()
    )


def build_dataset(facts_table: str, unsubs_table: str, out_path: str,
                  feature_date: str):
    spark = build_spark()

    facts = (spark.read.format("iceberg").load(facts_table)
                       .filter(col("dt") == feature_date))

    # Per-user aggregates
    features = (facts.groupBy("user_id")
                      .agg(
                          count("*").alias("notifs_sent"),
                          countDistinct("notification_group_id").alias("unique_notifs"),
                          sum_(when(col("channel").isin(["push"]), 1).otherwise(0))
                              .alias("push_count"),
                          sum_(when(col("channel").isin(["email"]), 1).otherwise(0))
                              .alias("email_count"),
                          sum_(when(col("channel").isin(["sms"]), 1).otherwise(0))
                              .alias("sms_count"),
                          sum_(when(col("opened_ts").isNotNull(), 1).otherwise(0))
                              .alias("opens"),
                          sum_(when(col("clicked_ts").isNotNull(), 1).otherwise(0))
                              .alias("clicks"),
                      )
                      .withColumn("open_rate",
                                  col("opens") / col("notifs_sent"))
                      .withColumn("ctr",
                                  col("clicks") / col("notifs_sent")))

    # Label: user unsubscribed in 7 days after feature_date
    labels = (spark.read.format("iceberg").load(unsubs_table)
                        .filter((col("event_ts") >= feature_date) &
                                (col("event_ts") <  feature_date + lit("interval 7 days")))
                        .select("user_id")
                        .distinct()
                        .withColumn("label", lit(1)))

    train = (features.join(labels, "user_id", "left")
                    .fillna(0, subset=["label"])
                    .drop("user_id"))

    (train.write
          .mode("overwrite")
          .format("parquet")
          .save(out_path))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--facts",   default="local.gold.notification_facts")
    p.add_argument("--unsubs",  default="local.bronze.notification_events")
    p.add_argument("--out",     required=True)
    p.add_argument("--feature-date", required=True)
    args = p.parse_args()
    build_dataset(args.facts, args.unsubs, args.out, args.feature_date)
