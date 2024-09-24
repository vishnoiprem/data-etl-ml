from pyspark.sql import SparkSession
from pyspark.sql.functions import window, col, sum as _sum, count, from_unixtime, unix_timestamp

# Create a Spark session
spark = SparkSession.builder \
    .appName("Retail Sales Streaming with Late Data Handling") \
    .config("spark.sql.streaming.schemaInference", "true") \
    .getOrCreate()

# Set up the streaming read from the CSV files in a folder
sales_df = spark.readStream \
    .option("header", "true") \
    .option("maxFilesPerTrigger", 1) \
    .csv("/Users/prem/PycharmProjects/data-etl-ml/Spark/realtime/stream/csv/")
# Cast the timestamp and amount columns to appropriate types
sales_df = sales_df.withColumn("timestamp", col("timestamp").cast("timestamp")) \
                   .withColumn("amount", col("amount").cast("double"))

# Watermark and window for hourly sales aggregation with late-arriving data handling
watermarked_df = sales_df \
    .withWatermark("timestamp", "1 minutes")  # Allow late data for 1 minutes

# Group by hourly window and calculate metrics like GMV and order count
hourly_sales_df = watermarked_df.groupBy(
    window(col("timestamp"), "1 hour"),  # 1-hour window
).agg(
    _sum("amount").alias("GMV"),         # Total GMV (Gross Merchandise Volume)
    count("order_id").alias("order_count")  # Number of orders
)

# Write the results to the console for demonstration
query = hourly_sales_df.writeStream \
    .outputMode("update") \
    .format("console") \
    .option("truncate", "false") \
    .start()

query.awaitTermination()