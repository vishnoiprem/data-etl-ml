from pyspark.sql import SparkSession

# Create a Spark session
spark = SparkSession.builder.appName("PartitionExample").getOrCreate()

# Sample DataFrame
data = [("user1", "click", "2023-08-16T10:00:00.000Z"),
        ("user1", "click", "2023-08-16T10:05:00.000Z"),
        ("user2", "purchase", "2023-08-16T10:10:00.000Z")]

columns = ["user_id", "event_type", "event_time"]
df = spark.createDataFrame(data, columns)

# Writing DataFrame partitioned by 'user_id'
df.write.partitionBy("user_id").parquet("output_directory")