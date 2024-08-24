from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("SaltingExample").getOrCreate()

# Sample data with a skewed key
data1 = [("key1", 1), ("key1", 2), ("key1", 3), ("key2", 4)]
data2 = [("key1", "A"), ("key1", "B"), ("key2", "C")]

rdd1 = spark.sparkContext.parallelize(data1)
rdd2 = spark.sparkContext.parallelize(data2)

# Salting keys in rdd1
salted_rdd1 = rdd1.flatMap(lambda x: [(x[0] + "_" + str(i), x[1]) for i in range(3)])
# Salting keys in rdd2
salted_rdd2 = rdd2.flatMap(lambda x: [(x[0] + "_" + str(i), x[1]) for i in range(3)])

# Perform the join on the salted keys
joined_rdd = salted_rdd1.join(salted_rdd2)

# Remove salt after join (if needed)
result_rdd = joined_rdd.map(lambda x: (x[0].split("_")[0], x[1]))

result = result_rdd.collect()
print(result)
