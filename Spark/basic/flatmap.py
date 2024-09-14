from  pyspark.sql import  SparkSession
spark = SparkSession.builder.appName("flatmap").getOrCreate()


# Sample Data
sentences = ["Spark is great", "Map and FlatMap are useful", "FlatMap flattens lists"]

# Parallelize the data into an RDD
rdd = spark.sparkContext.parallelize(sentences)

# Apply the flatMap() transformation
words_rdd = rdd.flatMap(lambda sentence: sentence.split(" "))

# Collect the result
print(words_rdd.collect())