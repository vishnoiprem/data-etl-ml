"""Glue Job 2 — Aggregate city_temperature.csv by country and write Parquet.

Part of the AWS Glue - The Complete Masterclass course (Section 7 lab —
First AWS Glue Pipeline). Reads a CSV from the source S3 bucket, computes
average / min / max / distinct-city counts per (country, year, month),
and writes partitioned Parquet to the target S3 bucket.

The job is invoked by AWS Glue with the following --job arguments (passed
as `--key value` pairs in `sys.argv` and read via `getResolvedOptions`,
the canonical Glue 4.0 helper):

  --source_bucket   source S3 bucket (e.g. awsglueudemycourse-datasoup-gluejob2-source)
  --target_bucket   target S3 bucket (e.g. awsglueudemycourse-datasoup-gluejob1-target)
  --source_key      key within the source bucket (default: input/city_temperature.csv)

The script is Glue-version 4.0 (Spark 3.3, Python 3.10).
"""

import sys
from awsglue.transforms import *
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

# ---------------------------------------------------------------------
# Glue / Spark boilerplate.
# ---------------------------------------------------------------------

sc = SparkContext.getOrCreate()
glue_context = GlueContext(sc)
spark = glue_context.spark_session
job = Job(glue_context)

# ---------------------------------------------------------------------
# Job arguments — canonical Glue 4.0 pattern via getResolvedOptions.
# Arg names use underscores (Glue job-arg convention) and must match the
# `DefaultArguments` keys in glue_pipeline_stack.yaml.
# ---------------------------------------------------------------------

DEFAULT_SOURCE_KEY = "input/city_temperature.csv"
try:
    args = getResolvedOptions(
        sys.argv,
        ["source_bucket", "target_bucket", "source_key"],
    )
    SOURCE_BUCKET = args["source_bucket"]
    TARGET_BUCKET = args["target_bucket"]
    SOURCE_KEY = args.get("source_key", DEFAULT_SOURCE_KEY)
except Exception as exc:  # missing required arg
    raise SystemExit(
        f"missing required job argument: {exc}. "
        "Expected: --source_bucket <bucket> --target_bucket <bucket> "
        "[--source_key <key>]"
    ) from exc

assert SOURCE_BUCKET, "SOURCE_BUCKET resolved to empty string"
assert TARGET_BUCKET, "TARGET_BUCKET resolved to empty string"

job.init(sys.argv[0], {"source_bucket": SOURCE_BUCKET, "target_bucket": TARGET_BUCKET})

# ---------------------------------------------------------------------
# Schema: matches city_temperature.csv columns exactly.
# ---------------------------------------------------------------------

SCHEMA = StructType([
    StructField("region", StringType(), nullable=True),
    StructField("country", StringType(), nullable=True),
    StructField("city", StringType(), nullable=True),
    StructField("latitude", DoubleType(), nullable=True),
    StructField("longitude", DoubleType(), nullable=True),
    StructField("year", IntegerType(), nullable=True),
    StructField("month", IntegerType(), nullable=True),
    StructField("day", IntegerType(), nullable=True),
    StructField("avg_temperature", DoubleType(), nullable=True),
    StructField("avg_temperature_uncertainty", DoubleType(), nullable=True),
])

# ---------------------------------------------------------------------
# Read CSV, aggregate, write Parquet (partitioned by year and month).
# ---------------------------------------------------------------------

source_path = f"s3://{SOURCE_BUCKET}/{SOURCE_KEY}"
df = (
    spark.read
    .option("header", "true")
    .schema(SCHEMA)
    .csv(source_path)
)

# Drop rows with null avg_temperature so the avg aggregate is well-defined.
clean = df.filter(F.col("avg_temperature").isNotNull())

agg = (
    clean.groupBy("country", "year", "month")
    .agg(
        F.round(F.avg("avg_temperature"), 2).alias("mean_avg_temperature"),
        F.min("avg_temperature").alias("min_avg_temperature"),
        F.max("avg_temperature").alias("max_avg_temperature"),
        F.countDistinct("city").alias("n_cities"),
    )
    .orderBy("country", "year", "month")
)

target_path = f"s3://{TARGET_BUCKET}/output/by_country_year_month/"
(
    agg.write
    .mode("overwrite")
    .partitionBy("year", "month")
    .parquet(target_path)
)

job.commit()
