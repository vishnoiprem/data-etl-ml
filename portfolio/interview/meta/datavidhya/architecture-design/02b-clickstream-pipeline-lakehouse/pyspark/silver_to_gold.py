"""
Spark Batch: Silver → Gold (user_features_daily + session_metrics).

- user_features_daily: per-user-per-day aggregations for ML training
- session_metrics: per-session funnel/engagement metrics
"""

import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, countDistinct, sum as sum_, max as max_, min as min_,
    first, last, when, expr, unix_timestamp, lit, to_date
)
from pyspark.sql.window import Window


def build_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("clickstream_silver_to_gold")
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.local.type", "hadoop")
        .config("spark.sql.catalog.local.warehouse", "s3://lakehouse/warehouse")
        .getOrCreate()
    )


def user_features_daily(silver_table: str, out_table: str, run_date: str):
    spark = build_spark()

    s = (spark.read.format("iceberg").load(silver_table)
                .filter(col("dt") == run_date))

    user_day = (
        s.groupBy("user_id", "dt")
         .agg(
             count("*").alias("event_count"),
             sum_(when(col("event_name") == "page_view", 1).otherwise(0)).alias("page_views"),
             sum_(when(col("event_name") == "click",     1).otherwise(0)).alias("clicks"),
             sum_(when(col("event_name") == "scroll",    1).otherwise(0)).alias("scrolls"),
             sum_(when(col("event_name") == "purchase",  1).otherwise(0)).alias("purchases"),
             sum_(when(col("event_name") == "form_submit", 1).otherwise(0)).alias("form_submits"),
             sum_(when(col("event_name") == "purchase",
                       col("properties").getItem("revenue_usd").cast("double"))
                  .otherwise(0.0)).alias("purchase_revenue"),
             countDistinct(when(col("event_name") == "page_view",
                                col("properties").getItem("page"))).alias("distinct_pages"),
             countDistinct("session_id").alias("session_count"),
             first("platform").alias("platform_top"),
             first("country").alias("country"),
         )
    )

    (user_day.write
              .format("iceberg")
              .mode("overwrite")
              .partitionedBy("dt")
              .option("write.distribution-mode", "hash")
              .saveAsTable(out_table))


def session_metrics(silver_table: str, out_table: str, run_date: str):
    spark = build_spark()

    s = (spark.read.format("iceberg").load(silver_table)
                .filter(col("dt") == run_date))

    # Session boundary: 30 min inactivity
    w = Window.partitionBy("user_id").orderBy(col("event_ts").cast("long"))
    prev_ts = lag(col("event_ts").cast("long")).over(w)
    is_new = when(prev_ts.isNull() | ((col("event_ts").cast("long") - prev_ts) > 1800), 1).otherwise(0)
    session_n = sum_(is_new).over(w)

    with_session = s.withColumn("session_n", session_n) \
                   .withColumn("session_id_full",
                               concat_ws(":", col("user_id"), col("session_n")))

    sess = (
        with_session.groupBy("session_id_full", "user_id", "dt")
            .agg(
                min_("event_ts").alias("started_ts"),
                max_("event_ts").alias("ended_ts"),
                count("*").alias("event_count"),
                sum_(when(col("event_name") == "page_view", 1).otherwise(0)).alias("page_view_count"),
                sum_(when(col("event_name") == "click",     1).otherwise(0)).alias("click_count"),
                max_(when(col("event_name") == "purchase", 1).otherwise(0)).alias("conversion_flag"),
                first(when(col("event_name") == "page_view",
                           col("properties").getItem("page")), ignorenulls=True)
                    .alias("entry_page"),
                last(when(col("event_name") == "page_view",
                          col("properties").getItem("page")), ignorenulls=True)
                    .alias("exit_page"),
            )
            .withColumn("duration_s", unix_timestamp("ended_ts") - unix_timestamp("started_ts"))
            .withColumnRenamed("session_id_full", "session_id")
    )

    (sess.write
         .format("iceberg")
         .mode("overwrite")
         .partitionedBy("dt")
         .saveAsTable(out_table))


from pyspark.sql.functions import lag, sum as sum_, concat_ws


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--silver", default="local.silver.events")
    p.add_argument("--user_features", default="local.gold.user_features_daily")
    p.add_argument("--sessions",      default="local.gold.session_metrics")
    p.add_argument("--dt", required=True)
    args = p.parse_args()

    user_features_daily(args.silver, args.user_features, args.dt)
    session_metrics(args.silver, args.sessions, args.dt)
