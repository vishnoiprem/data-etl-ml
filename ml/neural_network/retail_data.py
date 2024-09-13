import numpy as np
import pandas as pd

# Set the random seed for reproducibility
np.random.seed(42)

# Number of data points
num_rows = 1000

# Generate synthetic data
foot_traffic = np.random.randint(50, 1000, size=num_rows)  # Foot traffic between 50 and 1000
promotion = np.random.choice([0, 1], size=num_rows, p=[0.7, 0.3])  # 30% chance of promotion (1), 70% no promotion (0)
weather = np.random.choice(['Sunny', 'Rainy', 'Cloudy'], size=num_rows)  # Random weather conditions
day_of_week = np.random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], size=num_rows)

# Generate sales data with some relation to foot_traffic and promotion
# The idea is that more foot_traffic and promotion would likely lead to higher sales
sales = (foot_traffic * np.random.uniform(0.5, 1.5, size=num_rows)) + (promotion * np.random.uniform(100, 500, size=num_rows)) + np.random.normal(50, 25, size=num_rows)

# Create a DataFrame
retail_data = pd.DataFrame({
    'foot_traffic': foot_traffic,
    'promotion': promotion,
    'weather': weather,
    'day_of_week': day_of_week,
    'sales': sales
})

# Check the first few rows
print(retail_data.head())

# Save the data to a CSV file
retail_data.to_csv('retail_data.csv', index=False)
