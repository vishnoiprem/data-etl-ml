from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col

# Step 1: Set Up the Spark Session with Hive support
spark = SparkSession.builder \
    .appName("HiveKafkaJoinExample") \
    .enableHiveSupport() \
    .getOrCreate()

# Step 2: Read Data from Hive Table
# Replace "your_hive_table" with the actual Hive table name
hive_df = spark.sql("SELECT * FROM your_hive_table")

# Step 3: Read Data from Kafka Stream
# Replace "localhost:9092" with your Kafka broker address
# Replace "your_kafka_topic" with your Kafka topic name
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "your_kafka_topic") \
    .load()

# Assuming the Kafka data is in JSON format, define the schema
schema = "id INT, transaction_type STRING, timestamp STRING"

# Parse the JSON data in the Kafka stream
kafka_df = kafka_df.selectExpr("CAST(value AS STRING) as json") \
    .select(from_json(col("json"), schema).alias("data")) \
    .select("data.*")

# Step 4: Perform the Join Operation between Hive and Kafka DataFrames
# Assuming both Hive and Kafka data have a common "id" field for joining
joined_df = hive_df.join(kafka_df, "id")

# Step 5: Write the Joined Data to the Target Database
# In this example, we're writing to Parquet format in HDFS or local storage
# Replace "/path/to/output" with your desired output path
query = joined_df.writeStream \
    .outputMode("append") \
    .format("parquet") \
    .option("path", "/path/to/output") \
    .option("checkpointLocation", "/path/to/checkpoint") \
    .start()

# Wait for the streaming query to finish
query.awaitTermination()
