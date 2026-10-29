from pyspark.sql import SparkSession

# Start Spark session
spark = SparkSession.builder.appName("SalesAnalysis").config("spark.executor.memory", "8g").getOrCreate()

# Load large CSV from local or s3  (partitioned across cluster)
df = spark.read.csv("huge_sales.csv", header=True, inferSchema=True)

# Filter invalid rows (e.g., negative sales)
valid_df = df.filter(df["sales_amount"] > 0)

# Cache for reuse
valid_df.cache()

# Aggregate sales by region
sales_by_region = valid_df.groupBy("region").sum("sales_amount")

# Action: Save results
sales_by_region.write.parquet("sales_by_region")

# Peek at results
sales_by_region.show()

# Clean up
spark.stop()