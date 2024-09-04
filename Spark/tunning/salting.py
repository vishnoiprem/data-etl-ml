from pyspark.sql import SparkSession
from pyspark.sql.functions import col, expr, concat, lit, rand, count

# Initialize SparkSession
spark = SparkSession.builder.appName("SaltingExample").getOrCreate()

# Sample user data (skewed towards user_id=1)
user_data = [
    (1, 'ProductA', '2023-01-01 10:00:00'),
    (1, 'ProductB', '2023-01-01 10:05:00'),
    (1, 'ProductC', '2023-01-01 10:10:00'),
    (1, 'ProductD', '2023-01-01 10:15:00'),
    (2, 'ProductE', '2023-01-01 10:20:00'),
    (2, 'ProductF', '2023-01-01 10:25:00'),
    (3, 'ProductG', '2023-01-01 10:30:00')
]

user_df = spark.createDataFrame(user_data, ["user_id", "product_name", "timestamp"])

# Add random salt to spread the data across different partitions
num_salts = 5  # Let's assume we use 5 salts to spread the load
salted_user_df = user_df.withColumn("salt", expr(f"CAST(rand() * {num_salts} AS INT)"))

# Concatenate user_id with salt to create a salted user_id
salted_user_df = salted_user_df.withColumn("salted_user_id", concat(col("user_id"), lit("_"), col("salt")))

# Perform the counting within each salted bucket
salted_counts_df = salted_user_df.groupBy("salted_user_id", "user_id").agg(count("*").alias("user_action_count"))

# Aggregate back by user_id to get the final user-wise count
final_counts_df = salted_counts_df.groupBy("user_id").agg(expr("SUM(user_action_count) AS total_actions"))

# Show the final result
final_counts_df.show()

# Stop the SparkSession
spark.stop()