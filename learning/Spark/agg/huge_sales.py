import csv
import random
from datetime import datetime, timedelta
import os

# Define possible values
regions = ["US", "EU", "APAC", "LATAM", "Africa"]
products = ["Laptop", "Phone", "Tablet", "Monitor", "Keyboard"]
start_date = datetime(2025, 1, 1)

# Function to generate a random timestamp
def random_timestamp():
    days_offset = random.randint(0, 60)  # Up to 2 months from Jan 1, 2025
    hours_offset = random.randint(0, 23)
    minutes_offset = random.randint(0, 59)
    seconds_offset = random.randint(0, 59)
    return start_date + timedelta(days=days_offset, hours=hours_offset, minutes=minutes_offset, seconds=seconds_offset)

# Generate 10,000 records
records = []
for _ in range(100):
    timestamp = random_timestamp().strftime("%Y-%m-%d %H:%M:%S")
    region = random.choice(regions)
    sales_amount = round(random.uniform(-10, 1000), 2)  # Some negative values for filtering demos
    product = random.choice(products)
    records.append([timestamp, region, sales_amount, product])

# Write to CSV
file_name = "huge_sales.csv"
with open(file_name, mode="w", newline="") as file:
    writer = csv.writer(file)
    # Write header
    writer.writerow(["timestamp", "region", "sales_amount", "product"])
    # Write data
    writer.writerows(records)

print(f"Generated {file_name} with 10,000 records in {os.getcwd()}")