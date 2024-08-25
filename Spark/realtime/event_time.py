from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_unixtime, window, sum as _sum, count
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, DoubleType


from pyspark.sql import SparkSession
from pyspark.sql.types import TimestampType


spark = SparkSession.builder \
    .appName("EventTimeProcessingExample") \
    .getOrCreate()


schema = StructType([
    StructField("order_id", StringType(), True),
    StructField("user_id", StringType(), True),
    StructField("order_time", StringType(), True),
    StructField("amount", DoubleType(), True)
])

# Example raw data
data = [
    ("order1", "user1", "2023-08-16 10:00:00", 100.0),
    ("order2", "user1", "2023-08-16 10:01:00", 150.0),
    ("order3", "user2", "2023-08-16 10:05:00", 200.0),
    ("order4", "user1", "2023-08-16 10:15:00", 250.0),
    ("order5", "user3", "2023-08-16 10:20:00", 300.0)
]

df = spark.createDataFrame(data, schema=schema)
df = df.withColumn("order_time_new", from_unixtime(col("order_time").cast("long")))

df.printSchema()
df.show(truncate=False)

# Step 4: Tumbling Window

tumbling_window = df \
    .groupBy(window(col("order_time"), "10 minutes")) \
    .agg(
        count("order_id").alias("total_orders"),
        _sum("amount").alias("total_amount")
    ) \
    .orderBy("window")

tumbling_window.show(truncate=False)

# Step 5: Sliding Window



sliding_window = df \
    .groupBy(window(col("order_time"), "5 minutes", "1 minute")) \
    .agg(
        count("order_id").alias("total_orders"),
        _sum("amount").alias("total_amount")
    ) \
    .orderBy("window")

sliding_window.show(truncate=False)

# Step 6: Session Window
# Perform aggregation using a session window with a session gap duration of 10 minutes.

session_window = df \
    .groupBy(window(col("order_time"), "10 minutes")) \
    .agg(
        count("order_id").alias("total_orders"),
        _sum("amount").alias("total_amount")
    ) \
    .orderBy("window")

session_window.show(truncate=False)
