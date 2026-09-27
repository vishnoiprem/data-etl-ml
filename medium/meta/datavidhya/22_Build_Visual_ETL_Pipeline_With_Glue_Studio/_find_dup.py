import sys
sys.path.insert(0, '/Users/pvishnoi/PycharmProjects/data-etl-ml/medium/meta/datavidhya/22_Build_Visual_ETL_Pipeline_With_Glue_Studio')
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()
df = spark.read.parquet('/tmp/q22_out2')
df.groupBy('customer_id').count().filter('count > 1').show()
df.orderBy('customer_id').show(20, False)
