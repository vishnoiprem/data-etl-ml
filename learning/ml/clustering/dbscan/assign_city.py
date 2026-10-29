import numpy as np
import pandas as pd
from geopy.distance import great_circle

# Define city center coordinates for major cities in Thailand
city_centers = {
    'Bangkok': (13.75, 100.6),
    'Chiang Mai': (18.8, 99.0),
    'Phuket': (8.0, 98.3),
    'Pattaya': (13.0, 101.0),
    'Khon Kaen': (16.5, 103.0),
    'Hat Yai': (7.0, 100.5),
}


# Helper function to find the closest city based on latitude and longitude
def find_closest_city(lat, lon):
    min_distance = float('inf')
    closest_city = None

    for city, center_coords in city_centers.items():
        city_distance = great_circle((lat, lon), center_coords).kilometers
        if city_distance < min_distance:
            min_distance = city_distance
            closest_city = city

    return closest_city


# Generate fake delivery data for Thailand
np.random.seed(42)

# Number of records
num_records = 10000

# Generate random user_ids, order_ids, and order_amounts
user_ids = np.random.randint(1000, 2000, num_records)
order_ids = np.arange(1, num_records + 1)
order_amounts = np.random.randint(100, 1000, num_records)

# Generate random latitudes and longitudes in Thailand range
latitudes = np.random.uniform(low=5.0, high=20.0, size=num_records)  # Thailand latitudes range approx 5 to 20 degrees
longitudes = np.random.uniform(low=97.0, high=105.0,
                               size=num_records)  # Thailand longitudes range approx 97 to 105 degrees

# Generate timestamps for each order
timestamps = pd.date_range(start="2024-01-01", periods=num_records, freq='H')

# Assign the closest city based on latitude and longitude
cities = [find_closest_city(lat, lon) for lat, lon in zip(latitudes, longitudes)]

# Create the DataFrame with city names
data = pd.DataFrame({
    'user_id': user_ids,
    'order_id': order_ids,
    'latitude': latitudes,
    'longitude': longitudes,
    'order_amount': order_amounts,
    'timestamp': timestamps,
    'city': cities
})

# Display the DataFrame
print(data)

# Save the data to a CSV file
data.to_csv('thailand_delivery_data.csv', index=False)
print("Data saved to 'thailand_delivery_data.csv'")
