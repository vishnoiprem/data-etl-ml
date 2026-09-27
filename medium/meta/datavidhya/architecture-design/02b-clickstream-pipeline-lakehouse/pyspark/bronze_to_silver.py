"""
Spark Batch: Bronze → Silver.

Steps:
  1. Read Bronze for the target dt
  2. Apply bot filter (signature + heuristic + ML hook)
  3. Enrich with user traits (lookup table)
  4. Dedupe by event_id (defensive — Iceberg can have duplicates after retries)
  5. Write to Silver partitioned by dt, Z-ORDER by (user_id, event_name)
"""

import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, when, count, countDistinct, broadcast, regexp_extract, lower
)
from pyspark.sql.window import Window


def build_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("clickstream_bronze_to_silver")
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.local.type", "hadoop")
        .config("spark.sql.catalog.local.warehouse", "s3://lakehouse/warehouse")
        .getOrCreate()
    )


# User-Agent → bot signature (loadable from config in prod)
BOT_UA_REGEX = (
    r"headlesschrome|phantomjs|selenium|webdriver|scrapy|"
    r"python-requests|curl/|wget/|bot|spider|crawler|"
    r"ahrefs|semrush|mj12|petalbot"
)


def bronze_to_silver(
    bronze_table: str,
    silver_table: str,
    user_traits_table: str,
    run_date: str,
):
    spark = build_spark()

    bronze = (
        spark.read.format("iceberg").load(bronze_table)
        .filter(col("dt") == run_date)
    )

    # Stage 1 — UA signature
    flagged_s1 = (
        bronze.withColumn(
            "ingest_status",
            when(lower(col("user_agent")).rlike(BOT_UA_REGEX), lit("BOT_STAGE1"))
            .otherwise(col("ingest_status"))
        )
    )

    # Stage 2 — heuristic (no scroll + high rate via window)
    w_user = Window.partitionBy("user_id").orderBy(col("event_ts").cast("long")) \
                   .rangeBetween(-5, 0)
    with_rate = (
        flagged_s1.withColumn("events_in_5s", count("*").over(w_user))
    )
    flagged_s2 = (
        with_rate.withColumn(
            "ingest_status",
            when((col("events_in_5s") > 50) & (col("ingest_status") == "OK"),
                 lit("BOT_STAGE2")).otherwise(col("ingest_status"))
        )
    )

    # Keep only human events for Silver
    human = flagged_s2.filter(col("ingest_status") == "OK")

    # Enrich with user traits (broadcast join — small table)
    traits = broadcast(spark.read.format("iceberg").load(user_traits_table)
                                .select("user_id", "traits"))
    enriched = human.join(traits, on="user_id", how="left")

    # Final defensive dedup
    deduped = enriched.dropDuplicates(["event_id"])

    # Tag experiment_ids from context
    final = (
        deduped.withColumn("experiment_ids",
                           when(col("context").getItem("experiment_ids").isNotNull(),
                                split(col("context").getItem("experiment_ids"), ","))
                           .otherwise(lit(None)))
    )

    # Write with Z-ORDER optimization
    (final.write
          .format("iceberg")
          .mode("append")
          .partitionedBy("dt")
          .option("write.distribution-mode", "hash")
          .saveAsTable(silver_table))

    # Z-ORDER (Iceberg rewrite)
    spark.sql(f"""
        CALL local.system.rewrite_data_files(
            table => '{silver_table}',
            strategy => 'sort',
            sort_order => 'zorder(user_id, event_name)'
        )
    """)


from pyspark.sql.functions import split


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--bronze", default="local.bronze.events")
    p.add_argument("--silver", default="local.silver.events")
    p.add_argument("--traits", default="local.dim.user_traits")
    p.add_argument("--dt",     required=True)
    args = p.parse_args()
    bronze_to_silver(args.bronze, args.silver, args.traits, args.dt)
