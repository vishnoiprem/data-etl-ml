from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType

# Define the Kafka topic schema for CDC
schema = StructType() \
    .add("op", StringType()) \
    .add("before", StringType()) \
    .add("after", StringType())

# Initialize Spark session with Delta Lake support
spark = SparkSession.builder \
    .appName("KafkaToDelta") \
    .config("spark.jars.packages", "io.delta:delta-core_2.12:1.0.0") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Read Kafka stream from topic
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "dbserver1.public.my_table") \
    .load()

# Convert Kafka value to string and parse it as JSON using the defined schema
value_df = kafka_df.selectExpr("CAST(value AS STRING) as value")
parsed_df = value_df.select(from_json(col("value"), schema).alias("data"))

# Write the parsed data to Delta Lake
parsed_df.writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", "/tmp/delta/checkpoints") \
    .start("/tmp/delta/tmp_retail")

# Keep the stream running
spark.streams.awaitAnyTermination()