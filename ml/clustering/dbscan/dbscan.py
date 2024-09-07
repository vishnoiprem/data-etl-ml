from pyspark.sql import SparkSession
<<<<<<< HEAD
from sklearn.cluster import DBSCAN
import numpy as np
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType
=======
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.clustering import DBSCAN
>>>>>>> refs/remotes/origin/master

# Initialize Spark session
spark = SparkSession.builder \
    .appName("DBSCANExample") \
    .getOrCreate()

# Sample DataFrame in PySpark
data = [(1, [1.0, 2.0]), (2, [2.0, 3.0]), (3, [3.0, 4.0]), (4, [8.0, 8.0]), (5, [8.0, 7.5])]
df = spark.createDataFrame(data, ["id", "features"])

# Convert Spark DataFrame to NumPy array
features = np.array(df.select('features').rdd.map(lambda row: row['features']).collect())

# Apply DBSCAN with a suitable eps value
dbscan = DBSCAN(eps=1.5, min_samples=2).fit(features)
labels = dbscan.labels_

# Add the cluster labels as a new column in the PySpark DataFrame
# Create a Pandas DataFrame to hold the id and cluster labels
cluster_df = spark.createDataFrame([(int(row[0]), int(label)) for row, label in zip(data, labels)], ["id", "cluster"])

# Join the cluster labels back to the original DataFrame
df_with_labels = df.join(cluster_df, on="id")

# Show the DataFrame with the correct cluster assignments
df_with_labels.show(truncate=False)

# Stop the Spark session
spark.stop()