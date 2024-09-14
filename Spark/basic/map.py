from pyspark.sql import SparkSession

# Create Spark session
spark = SparkSession.builder.appName("map_example").getOrCreate()

# Sample Data
data = [1, 2, 3, 4, 5]

# Parallelize the data into an RDD
rdd = spark.sparkContext.parallelize(data)

# Apply the map() transformation
squared_rdd = rdd.map(lambda x: x ** 2)

# Collect the result
print(squared_rdd.collect())