from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

data = [(1,), (2,), (3,)]
df = spark.createDataFrame(data, ["number"])

# Convert DataFrame to RDD and apply map()
rdd = df.rdd.map(lambda row: (row[0] ** 2,))
df_squared = rdd.toDF(["squared_number"])

df_squared.show()