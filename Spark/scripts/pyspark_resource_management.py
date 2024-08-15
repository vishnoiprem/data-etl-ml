from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as _sum

# Step 1: Initialize Spark Session with Resource Management Configurations
spark = SparkSession.builder \
    .appName("ResourceManagementExample") \
    .config("spark.executor.memory", "4g") \
    .config("spark.executor.cores", "2") \
    .config("spark.dynamicAllocation.enabled", "true") \
    .config("spark.dynamicAllocation.minExecutors", "2") \
    .config("spark.dynamicAllocation.maxExecutors", "10") \
    .config("spark.sql.shuffle.partitions", "200") \
    .getOrCreate()

# Step 2: Data Ingestion
# Replace "path/to/data.csv" with the actual path to your CSV file
df = spark.read.csv("path/to/data.csv", header=True, inferSchema=True)

# Step 3: Data Processing
# Example transformation: Filter rows and aggregate data
processed_df = df.filter(col('value') > 10) \
    .groupBy("category") \
    .agg(_sum("amount").alias("total_amount"))

# Step 4: Write the Processed Data to Output
# Replace "path/to/output" with the actual path where you want to save the output
processed_df.write.mode("overwrite").parquet("path/to/output")

# Step 5: Stop the Spark Session
spark.stop()