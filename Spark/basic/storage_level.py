from pyspark.sql import SparkSession
from pyspark import StorageLevel

# Initialize Spark session
spark = SparkSession.builder.appName("Storage Level Example").getOrCreate()

# Create a sample DataFrame
data = [(1, "Alice", 5000), (2, "Bob", 4000), (3, "Charlie", 7000), (4, "David", 3000)]
columns = ["id", "name", "salary"]
df = spark.createDataFrame(data, schema=columns)

# Show initial data
print("Initial DataFrame:")
df.show()

# Cache DataFrame using MEMORY_ONLY storage level
print("\nCaching DataFrame using MEMORY_ONLY:")
df.cache()  # Equivalent to df.persist(StorageLevel.MEMORY_ONLY)
df.show()

# Unpersist the DataFrame
df.unpersist()
print("\nUnpersisted DataFrame (MEMORY_ONLY)")

# Persist DataFrame using MEMORY_AND_DISK storage level
print("\nPersisting DataFrame using MEMORY_AND_DISK:")
df.persist(StorageLevel.MEMORY_AND_DISK)
df.show()

# Unpersist the DataFrame
df.unpersist()
print("\nUnpersisted DataFrame (MEMORY_AND_DISK)")

# Persist DataFrame using custom storage level for MEMORY_ONLY_SER
# If MEMORY_ONLY_SER is not available, create a custom level: (useDisk=False, useMemory=True, useOffHeap=False, deserialized=False, replication=1)
print("\nPersisting DataFrame using custom StorageLevel (similar to MEMORY_ONLY_SER):")
memory_only_ser_level = StorageLevel(useDisk=False, useMemory=True, useOffHeap=False, deserialized=False, replication=1)
df.persist(memory_only_ser_level)
df.show()

# Unpersist the DataFrame
df.unpersist()
print("\nUnpersisted DataFrame (Custom MEMORY_ONLY_SER)")

# Persist DataFrame using DISK_ONLY storage level (data only on disk)
print("\nPersisting DataFrame using DISK_ONLY:")
df.persist(StorageLevel.DISK_ONLY)
df.show()

# Unpersist the DataFrame
df.unpersist()
print("\nUnpersisted DataFrame (DISK_ONLY)")


print("\nPersisting DataFrame using OFF_HEAP:")
df.persist(StorageLevel.OFF_HEAP)
df.show()

# Unpersist the DataFrame
df.unpersist()
print("\nUnpersisted DataFrame (OFF_HEAP)")

# Stop the Spark session
spark.stop()
# Stop the Spark session
spark.stop()