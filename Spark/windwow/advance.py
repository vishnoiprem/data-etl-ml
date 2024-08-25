from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import col, sum, broadcast, udf, pandas_udf, lit, concat
from pyspark.sql.types import IntegerType

# Create a Spark session
spark = SparkSession.builder.appName("SparkExamples").getOrCreate()

# Sample data for Window Functions
data_window = [("Alice", 1000), ("Bob", 1500), ("Alice", 800), ("Bob", 2000), ("Alice", 1200)]
columns_window = ["Name", "Amount"]

df_window = spark.createDataFrame(data_window, columns_window)

# Define window specification
windowSpec = Window.partitionBy("Name").orderBy("Amount").rowsBetween(Window.unboundedPreceding, Window.currentRow)

# Calculate running total using Window Function
df_with_running_total = df_window.withColumn("RunningTotal", sum("Amount").over(windowSpec))
df_with_running_total.show()

# Sample data for Broadcast Joins
data1_broadcast = [("Alice", 34), ("Bob", 45), ("Charlie", 23)]
data2_broadcast = [("Alice", "HR"), ("Bob", "IT"), ("Charlie", "Finance")]

df1_broadcast = spark.createDataFrame(data1_broadcast, ["Name", "Age"])
df2_broadcast = spark.createDataFrame(data2_broadcast, ["Name", "Department"])

# Perform Broadcast Join
df_joined_broadcast = df1_broadcast.join(broadcast(df2_broadcast), "Name")
df_joined_broadcast.show()

# Sample data for UDF and Pandas UDF
data_udf = [(1,), (2,), (3,)]
df_udf = spark.createDataFrame(data_udf, ["Value"])

# Define a regular UDF
def square(x):
    return x * x

square_udf = udf(square, IntegerType())

# Apply the UDF
df_transformed_udf = df_udf.withColumn("SquaredValue", square_udf(df_udf["Value"]))
df_transformed_udf.show()

# Define a Pandas UDF
@pandas_udf(IntegerType())
def square_pandas_udf(x):
    return x * x

# Apply the Pandas UDF
df_transformed_pandas_udf = df_udf.withColumn("SquaredValue", square_pandas_udf(df_udf["Value"]))
df_transformed_pandas_udf.show()

# Sample data for Handling Large Scale Data (Salting)
data1_salt = [("key1", "value1"), ("key1", "value2"), ("key1", "value3"), ("key2", "value4")]
data2_salt = [("key1", "valueA"), ("key2", "valueB")]

df1_salt = spark.createDataFrame(data1_salt, ["key", "value"])
df2_salt = spark.createDataFrame(data2_salt, ["key", "other_value"])

# Adding salt to the first dataframe
salted_df1 = df1_salt.withColumn("salted_key", concat(col("key"), lit("_"), lit(1)))

# Adding salt to the second dataframe
salted_df2 = df2_salt.withColumn("salted_key", concat(col("key"), lit("_"), lit(1)))

# Join on the salted key
df_joined_salted = salted_df1.join(salted_df2, "salted_key")
df_joined_salted.show()

# Stop the Spark session
spark.stop()
