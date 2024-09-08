from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("ClusterManagerExample") \
    .master("local[*]") \
    .getOrCreate()
# .master("yarn") \

df = spark.read.csv("large-dataset.csv", header=True, inferSchema=True)

# Example: Filter and group by a column
result = df.filter(df['age'] > 30) \
    .groupBy('Name') \
    .count()

# Collect the result
result.show()

# Stop the Spark session
spark.stop()