"""Auto-generated PySpark from Glue Studio's "Job Script" tab.

This file is what Glue Studio's UI produces when the user drags a
4-node graph (Data Catalog source -> Filter -> Change Schema ->
Parquet target) onto the canvas and clicks "Job Script". In production
it runs on a Glue-managed Spark worker; offline we run it locally with
``PYTHONPATH=../glue_lib`` so ``import awsglue.*`` resolves to the shim.

The script:
  1. Reads the pre-crawled ``studio_db_local.customers_raw`` table (12
     rows, all-string ``created_at``).
  2. Filters down to ``status == 'active'`` (9 rows).
  3. Drops the ``status`` column and casts ``created_at`` to timestamp.
  4. Writes Parquet to the path passed in ``--output_path``.
"""
import sys
from awsglue.transforms import *
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import SparkSession

# ---- init GlueContext + Job (production: real Glue; offline: shim)
sc = SparkContext.getOrCreate()
spark = SparkSession.builder.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init("customer_etl_visual_q22",
         {"--input_path":  sys.argv[1],
          "--output_path": sys.argv[2]})

# Script generated for node Data Catalog source customers_raw
customers_raw = glueContext.create_dynamic_frame.from_catalog(
    database="studio_db_local", table_name="customers_raw",
    transformation_ctx="customers_raw")

# Script generated for node Filter active_customers
active_customers = Filter.apply(
    frame=customers_raw,
    f=lambda r: (r["status"] == "active"),
    transformation_ctx="active_customers")

# Script generated for node Change Schema mapped_customers
mapped_customers = ApplyMapping.apply(
    frame=active_customers,
    mappings=[
        ("customer_id", "string", "customer_id", "string"),
        ("name",        "string", "name",        "string"),
        ("email",       "string", "email",       "string"),
        ("created_at",  "string", "created_at",  "timestamp"),
    ],
    transformation_ctx="mapped_customers")

# Script generated for node S3 Parquet target curated_customers
glueContext.write_dynamic_frame.from_options(
    frame=mapped_customers,
    connection_type="s3",
    connection_options={"path": sys.argv[2]},
    format="glueparquet",
    format_options={"compression": "snappy"},
    transformation_ctx="curated_customers_sink")

job.commit()