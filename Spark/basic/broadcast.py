
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType
# Create a Spark session
spark = SparkSession.builder.master("local").appName("broadcast Example").getOrCreate()

lookup_table = {"HR": "Human Resources", "Sales": "Sales and Marketing", "Engineering": "Product Engineering"}

# Broadcast the lookup table to all nodes
broadcast_lookup = spark.sparkContext.broadcast(lookup_table)

# Create a sample DataFrame
data = [("Alice", "HR"), ("Bob", "Sales"), ("Charlie", "Engineering"), ("David", "HR")]
columns = ["Name", "DepartmentCode"]

df = spark.createDataFrame(data, columns)

# Use the broadcast variable in a UDF (User Defined Function)


# Create a UDF to get the full department name using the broadcasted lookup table
def get_department_name(code):
    return broadcast_lookup.value.get(code, "Unknown")

# Register the UDF
lookup_udf = udf(get_department_name, StringType())

# Apply the UDF to the DataFrame to get the full department name
df_with_dept = df.withColumn("DepartmentName", lookup_udf(col("DepartmentCode")))

# Show the updated DataFrame
df_with_dept.show()