# Databricks Notebook: ODS Layer - Ingest from MySQL to Delta Lake
# Layer: ODS (Operational Data Store) - Raw ingestion with minimal transformation
# Schedule: Every 1 hour via ADF or Databricks Workflow

# ── Imports ──────────────────────────────────────────────────────────────────
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    current_timestamp, lit, col, sha2, concat_ws,
    to_timestamp, date_format
)
from pyspark.sql.types import StringType
from delta.tables import DeltaTable
import datetime

# ── Spark / Databricks Init ───────────────────────────────────────────────────
spark = SparkSession.builder \
    .appName("EComm_ODS_MySQL_Ingestion") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

spark.conf.set("spark.databricks.delta.optimizeWrite.enabled", "true")
spark.conf.set("spark.databricks.delta.autoCompact.enabled", "true")

# ── Config ────────────────────────────────────────────────────────────────────
# In production, use Databricks Secrets: dbutils.secrets.get(scope="ecomm", key="mysql_host")
MYSQL_CONFIG = {
    "host": dbutils.secrets.get(scope="ecomm-secrets", key="mysql_host"),     # noqa
    "port": "3306",
    "database": "ecommerce_db",
    "user": dbutils.secrets.get(scope="ecomm-secrets", key="mysql_user"),      # noqa
    "password": dbutils.secrets.get(scope="ecomm-secrets", key="mysql_pass"),  # noqa
}

JDBC_URL = (
    f"jdbc:mysql://{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}"
    f"/{MYSQL_CONFIG['database']}?useSSL=true&serverTimezone=UTC"
)
JDBC_DRIVER = "com.mysql.cj.jdbc.Driver"
JDBC_PROPS = {
    "user": MYSQL_CONFIG["user"],
    "password": MYSQL_CONFIG["password"],
    "driver": JDBC_DRIVER,
}

# Delta Lake paths on Azure Data Lake Storage Gen2
ADLS_ROOT = "abfss://ecommerce@yourdatalake.dfs.core.windows.net"
ODS_PATH = f"{ADLS_ROOT}/ods"

# Ingestion timestamp for audit
INGEST_TS = datetime.datetime.utcnow().isoformat()
BATCH_DATE = datetime.datetime.utcnow().strftime("%Y-%m-%d")

# Tables: (mysql_table, primary_key, incremental_column, partition_col)
TABLE_CONFIG = [
    ("users",          "user_id",      "updated_at",  "country_code"),
    ("sellers",        "seller_id",    "updated_at",  None),
    ("categories",     "category_id",  "created_at",  None),
    ("brands",         "brand_id",     "created_at",  None),
    ("products",       "product_id",   "updated_at",  "category_id"),
    ("product_skus",   "sku_id",       "updated_at",  None),
    ("warehouses",     "warehouse_id", "created_at",  None),
    ("inventory",      "inventory_id", "updated_at",  "warehouse_id"),
    ("orders",         "order_id",     "updated_at",  "status"),
    ("order_items",    "item_id",      "created_at",  None),
    ("payments",       "payment_id",   "updated_at",  "status"),
    ("shipments",      "shipment_id",  "updated_at",  "status"),
    ("reviews",        "review_id",    "created_at",  None),
    ("user_events",    "event_id",     "created_at",  "event_type"),
    ("cart_items",     "cart_item_id", "updated_at",  None),
    ("vouchers",       "voucher_id",   "created_at",  None),
]


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_watermark(table_name: str) -> str:
    """Read last watermark from control table."""
    try:
        wm = spark.sql(f"""
            SELECT MAX(watermark) FROM ecomm_ods_control.ingestion_log
            WHERE table_name = '{table_name}' AND status = 'success'
        """).collect()[0][0]
        return str(wm) if wm else "1970-01-01 00:00:00"
    except Exception:
        return "1970-01-01 00:00:00"


def save_watermark(table_name: str, watermark: str, row_count: int, status: str):
    """Write watermark to control table."""
    spark.sql(f"""
        INSERT INTO ecomm_ods_control.ingestion_log
            (table_name, watermark, row_count, batch_date, status, ingested_at)
        VALUES ('{table_name}', '{watermark}', {row_count}, '{BATCH_DATE}', '{status}', current_timestamp())
    """)


def ingest_table(table: str, pk: str, ts_col: str, partition_col: str):
    """Incremental ingest from MySQL to ODS Delta table via UPSERT (MERGE)."""
    print(f"\n{'='*60}\nIngesting: {table}")

    watermark = get_watermark(table)
    print(f"  Watermark: {watermark}")

    # Read from MySQL with pushdown predicate
    query = f"(SELECT * FROM {table} WHERE {ts_col} > '{watermark}') t"
    df = spark.read.jdbc(
        url=JDBC_URL,
        table=query,
        properties=JDBC_PROPS,
        numPartitions=4,
        column=pk if table not in ["categories", "brands", "warehouses"] else None,
        lowerBound=1 if table not in ["categories", "brands", "warehouses"] else None,
        upperBound=999999999 if table not in ["categories", "brands", "warehouses"] else None,
    ) if table not in ["categories", "brands", "warehouses"] else \
        spark.read.jdbc(url=JDBC_URL, table=query, properties=JDBC_PROPS)

    row_count = df.count()
    print(f"  New/updated rows: {row_count}")

    if row_count == 0:
        save_watermark(table, watermark, 0, "success_no_data")
        return

    # Add ODS metadata columns
    df_ods = df \
        .withColumn("_ods_ingest_ts", lit(INGEST_TS).cast("timestamp")) \
        .withColumn("_ods_batch_date", lit(BATCH_DATE)) \
        .withColumn("_ods_source", lit("mysql_ecommerce_db")) \
        .withColumn("_row_hash", sha2(concat_ws("|", *[col(c).cast(StringType()) for c in df.columns]), 256))

    delta_path = f"{ODS_PATH}/{table}"

    # MERGE (upsert) into Delta
    if DeltaTable.isDeltaTable(spark, delta_path):
        dt = DeltaTable.forPath(spark, delta_path)
        dt.alias("target").merge(
            df_ods.alias("source"),
            f"target.{pk} = source.{pk}"
        ).whenMatchedUpdateAll(
        ).whenNotMatchedInsertAll(
        ).execute()
    else:
        # First run - full write
        writer = df_ods.write.format("delta").mode("overwrite")
        if partition_col and partition_col in df_ods.columns:
            writer = writer.partitionBy(partition_col)
        writer.save(delta_path)
        # Register in metastore
        spark.sql(f"""
            CREATE TABLE IF NOT EXISTS ecomm_ods.{table}
            USING DELTA LOCATION '{delta_path}'
        """)

    # Update watermark
    max_ts = df.agg({ts_col: "max"}).collect()[0][0]
    save_watermark(table, str(max_ts), row_count, "success")
    print(f"  Done. New watermark: {max_ts}")


# ── Create Control Schema ─────────────────────────────────────────────────────
spark.sql("CREATE DATABASE IF NOT EXISTS ecomm_ods_control")
spark.sql("""
    CREATE TABLE IF NOT EXISTS ecomm_ods_control.ingestion_log (
        log_id        BIGINT GENERATED ALWAYS AS IDENTITY,
        table_name    STRING,
        watermark     STRING,
        row_count     BIGINT,
        batch_date    DATE,
        status        STRING,
        ingested_at   TIMESTAMP
    ) USING DELTA
""")

spark.sql("CREATE DATABASE IF NOT EXISTS ecomm_ods")

# ── Run Ingestion ─────────────────────────────────────────────────────────────
failed = []
for table_name, pk_col, ts_column, part_col in TABLE_CONFIG:
    try:
        ingest_table(table_name, pk_col, ts_column, part_col)
    except Exception as e:
        print(f"ERROR on {table_name}: {e}")
        failed.append(table_name)

if failed:
    raise Exception(f"Ingestion failed for: {failed}")

print("\n✅ ODS Ingestion complete!")
