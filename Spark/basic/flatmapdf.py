
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("flatmapdf").getOrCreate()

# Sample Data
from pyspark.sql import functions as F

# Sample DataFrame
data = [("Spark is great",), ("Map and FlatMap are useful",)]
df = spark.createDataFrame(data, ["sentence"])

# Use 'explode' function to achieve flatMap-like behavior
df_words = df.withColumn("words", F.explode(F.split(F.col("sentence"), " ")))

df_words.show()