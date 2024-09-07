from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from sklearn.cluster import DBSCAN
import numpy as np

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

# Create DataFrame for x and y ID
columns = ["id", "x", "y"]
df = spark.createDataFrame(data, columns)

# Assemble features into a vector
assembler = VectorAssembler(inputCols=["x", "y"], outputCol="features")
df = assembler.transform(df)

# Convert Spark DataFrame to Pandas for DBSCAN
pandas_df = df.select("x", "y").toPandas()

# Apply DBSCAN from scikit-learn
dbscan_model = DBSCAN(eps=1.5, min_samples=2)
clusters = dbscan_model.fit_predict(pandas_df)

# Convert the cluster labels into a Spark DataFrame
cluster_df = spark.createDataFrame([(int(c),) for c in clusters], ["cluster"])

# Add cluster labels to the original DataFrame
df_with_cluster = df.withColumn("id", df["id"]).join(cluster_df)

# Show results
df_with_cluster.select("id", "features", "cluster").show()
