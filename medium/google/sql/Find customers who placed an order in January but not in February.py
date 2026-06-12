from pyspark.sql import SparkSession
from pyspark.sql.functions import to_date

data = [
    (1, "C001", "2026-01-05", 100),
    (2, "C002", "2026-01-10", 200),
    (3, "C003", "2026-01-15", 150),
    (4, "C004", "2026-01-20", 300),
    (5, "C001", "2026-02-03", 120),
    (6, "C003", "2026-02-12", 180),
    (7, "C005", "2026-02-18", 220),
    (8, "C006", "2026-03-01", 500)
]

columns = ["order_id", "customer_id", "order_date", "amount"]

orders_df = SparkSession.createDataFrame(data, columns)

orders_df = orders_df.withColumn("order_date", to_date("order_date"))

orders_df.createOrReplaceTempView("orders")

# display(orders_df)

print(orders_df)