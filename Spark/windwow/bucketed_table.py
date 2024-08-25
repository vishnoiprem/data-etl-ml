from pyspark.sql import SparkSession

# Create a Spark session
spark = SparkSession.builder.appName("BucketingExample").getOrCreate()

# Sample data for demonstration
data = [("Alice", 34, "HR"),
        ("Bob", 45, "IT"),
        ("Charlie", 23, "Finance"),
        ("David", 45, "HR"),
        ("Eve", 29, "IT"),
        ("Frank", 31, "Finance")]

# Create a DataFrame
df = spark.createDataFrame(data, ["Name", "Age", "Department"])

# Save the DataFrame as a bucketed table
# We bucket the table by the "Age" column into 3 buckets
df.write.bucketBy(3, "Age").sortBy("Age").saveAsTable("bucketed_table")

# To read the bucketed table
bucketed_df = spark.table("bucketed_table")

bucketed_df.show()

# Stop the Spark session
spark.stop()
