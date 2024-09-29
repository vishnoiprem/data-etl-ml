from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# Create a Spark session
spark = SparkSession.builder.master("local").appName("Accumulator Example").getOrCreate()

# Create a sample DataFrame with some missing values
data = [("Alice", 34, None), ("Bob", 45, "Sales"), ("Charlie", None, "Engineering"), ("David", 29, "HR")]
columns = ["Name", "Age", "Department"]

df = spark.createDataFrame(data, columns)

df.show()
# Create an accumulator for counting rows with missing values
missing_value_count = spark.sparkContext.accumulator(0)

print(missing_value_count,'code run')


# Function to count rows with missing values
def count_missing(row):
    global missing_value_count
    # Check if any field in the row is None (missing)
    if any(field is None for field in row):
        missing_value_count += 1

# Apply the function to each row in the DataFrame
df.foreach(count_missing)

# Show the DataFrame
df.show()

# Print the result of the accumulator
print(f"Number of rows with missing values: {missing_value_count}")
print(f"Number of rows with missing values: {missing_value_count.value}")