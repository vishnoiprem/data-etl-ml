import sys

from pyspark.sql import SparkSession
from pyspark.sql.functions import  col , sum as _sum , avg as _avg, count as _count


spark = SparkSession.builder.appName("txn_sum").getOrCreate()
input_path = "transaction_logs.csv"

transaction_df = spark.read.csv(input_path, header=True, inferSchema=True)
print(transaction_df.show())

transaction_filter_df = transaction_df.filter(col("amount")>10)
print(transaction_filter_df.show())

txn_avg_df = transaction_filter_df.groupBy("transaction_id").agg(_avg("amount"))
total_revenue = transaction_filter_df.agg(_sum("amount").alias("TotalRevenue")).collect()[0]["TotalRevenue"]

print(txn_avg_df.show())
print(total_revenue)


# Average Transaction Value
average_transaction_value = transaction_filter_df.agg(_avg("amount").alias("AverageTransactionValue")).collect()[0]["AverageTransactionValue"]

# Total Number of Transactions
total_transactions = transaction_filter_df.agg(_count("transaction_id").alias("TotalTransactions")).collect()[0]["TotalTransactions"]

# Display Results
print(f"Total Revenue: ${total_revenue}")
print(f"Average Transaction Value: ${average_transaction_value}")
print(f"Total Transactions: {total_transactions}")


