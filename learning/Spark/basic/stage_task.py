from pyspark.sql import SparkSession

# Initialize a Spark session
spark = SparkSession.builder.appName("SparkStageAndTaskExample").getOrCreate()

# Sample data
data = [("Alice", 34), ("Bob", 45), ("Cathy", 29), ("David", 23)]
rdd = spark.sparkContext.parallelize(data)

# Stage 1: map transformation
# This operation runs on each partition independently and does not involve shuffling
mapped_rdd = rdd.map(lambda x: (x[0], x[1] * 2))

# Stage 2: reduceByKey involves shuffling, and thus it's a boundary of stages
# Reduce operation aggregates the data, leading to a new stage
reduced_rdd = mapped_rdd.reduceByKey(lambda a, b: a + b)

# Collect the result
result = reduced_rdd.collect()

# Show result
print(result)

# Stop the Spark session
spark.stop()
