from pyspark.sql import SparkSession
from pyspark.sql.functions import col, window, rand, split, to_timestamp, from_json
import pyspark.sql.functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

# Start Spark session with local configuration
spark = SparkSession.builder \
    .appName("SalesWithSkewAndStream") \
    .config("spark.master", "local[*]") \
    .config("spark.driver.memory", "4g") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()

# Set log level to WARN to reduce verbosity
# spark.sparkContext.setLogLevel("WARN")
spark.sparkContext.setLogLevel("DEBUG")
# Batch: Load sales data from a local CSV file
batch_df = spark.read.csv("huge_sales.csv", header=True, inferSchema=True)

# Handle skew in 'region' by salting keys
batch_df = batch_df.withColumn("salted_region", F.concat(F.floor(rand() * 10).cast("string"), F.lit("-"), col("region"))) \
                   .filter(col("sales_amount") > 0)

# Aggregate with salted keys, then clean up
sales_by_region = batch_df.groupBy("salted_region").agg(F.sum("sales_amount").alias("total_sales")) \
                          .withColumn("region", split(col("salted_region"), "-")[1]) \
                          .groupBy("region").agg(F.sum("total_sales").alias("total_sales"))

# Save batch results to a local directory
output_dir = "output/batch_sales_by_region"
sales_by_region.write.mode("overwrite").parquet(output_dir)
print(f"Batch results saved to: {output_dir}")

# Define schema for streaming data
schema = StructType([
    StructField("timestamp", StringType(), True),
    StructField("region", StringType(), True),
    StructField("sales_amount", DoubleType(), True)
])

# Simulate streaming data using a local socket (for demonstration purposes)
# To test this, run `nc -lk 9999` in a terminal and send JSON messages like:
# {"timestamp": "2023-10-01T12:00:00", "region": "North", "sales_amount": 150.5}
stream_df = spark.readStream \
    .format("socket") \
    .option("host", "localhost") \
    .option("port", 9999) \
    .load() \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*") \
    .filter(col("sales_amount") > 0) \
    .withColumn("timestamp", to_timestamp(col("timestamp")))

# Windowed aggregation (hourly sales)
hourly_sales = stream_df.groupBy(
    "region",
    window(col("timestamp"), "1 hour")
).agg(F.sum("sales_amount").alias("total_sales"))

# Output to console (for local testing)
query = hourly_sales.writeStream \
    .outputMode("complete") \
    .format("console") \
    .trigger(processingTime="10 seconds") \
    .start()

# Wait for the streaming query to terminate
query.awaitTermination()

# Clean up
spark.stop()