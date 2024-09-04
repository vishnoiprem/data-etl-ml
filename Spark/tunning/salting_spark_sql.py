from pyspark.sql import SparkSession
from pyspark.sql.functions import expr, concat, lit, rand

# Initialize SparkSession
spark = SparkSession.builder.appName("SaltingSQLExample").getOrCreate()

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

# Create DataFrame
user_df = spark.createDataFrame(user_data, ["user_id", "product_name", "timestamp"])

# Add random salt using a random number between 0 and 4 (change the range based on your needs)
user_df = user_df.withColumn("salt", expr("CAST(rand() * 5 AS INT)"))

# Concatenate user_id with salt to create a salted user_id
salted_user_df = user_df.withColumn("salted_user_id", concat(user_df.user_id.cast("string"), lit("_"), user_df.salt.cast("string")))

# Register the DataFrame as a temporary SQL view
salted_user_df.createOrReplaceTempView("salted_user_data")

# Perform the SQL queries for salting and counting
# Step 1: Count records based on salted_user_id
salted_count_query = """
SELECT salted_user_id, user_id, COUNT(*) AS salted_count
FROM salted_user_data
GROUP BY salted_user_id, user_id
"""

# Step 2: Aggregate the counts by the original user_id
final_count_query = """
SELECT user_id, SUM(salted_count) AS total_actions
FROM (
    SELECT salted_user_id, user_id, COUNT(*) AS salted_count
    FROM salted_user_data
    GROUP BY salted_user_id, user_id
) AS salted_counts
GROUP BY user_id
"""

# Execute the final query
final_counts_df = spark.sql(final_count_query)

# Show the final result
final_counts_df.show()

# Stop the SparkSession
spark.stop()