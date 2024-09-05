
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.linalg import Vectors
from pyspark.ml.clustering import DBSCAN

# Create Spark session
spark = SparkSession.builder \
    .appName("DBSCAN Example") \
    .getOrCreate()

# Sample dataset
data = [
    (1, 1.0, 1.0),
    (2, 2.0, 1.0),
    (3, 3.0, 2.0),
    (4, 8.0, 7.0),
    (5, 8.0, 8.0),
    (6, 25.0, 80.0)
]

# Create DataFrame
columns = ["id", "x", "y"]
df = spark.createDataFrame(data, columns)

# Assemble features into a vector
assembler = VectorAssembler(inputCols=["x", "y"], outputCol="features")
df = assembler.transform(df)

# Define DBSCAN Model (set the eps value and minPoints)
dbscan = DBSCAN(eps=1.5, minPoints=2, inputCol="features")

# Fit model
model = dbscan.fit(df)

# Display cluster assignments
df_with_cluster = model.transform(df)
df_with_cluster.select("id", "features", "prediction").show()