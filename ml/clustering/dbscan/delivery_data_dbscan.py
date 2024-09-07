import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from geopy.distance import great_circle

# 1. Generate fake delivery data for Thailand
np.random.seed(42)

# Number of records
num_records = 200

# Generate random user_ids, order_ids, and order_amounts
user_ids = np.random.randint(1000, 2000, num_records)
order_ids = np.arange(1, num_records + 1)
order_amounts = np.random.randint(100, 1000, num_records)

# Generate random latitudes and longitudes in Thailand range
latitudes = np.random.uniform(low=5.0, high=20.0, size=num_records)  # Thailand latitudes range approx 5 to 20 degrees
longitudes = np.random.uniform(low=97.0, high=105.0, size=num_records)  # Thailand longitudes range approx 97 to 105 degrees

# Generate timestamps for each order
timestamps = pd.date_range(start="2023-01-01", periods=num_records, freq='H')

# Create the DataFrame
data = pd.DataFrame({
    'user_id': user_ids,
    'order_id': order_ids,
    'latitude': latitudes,
    'longitude': longitudes,
    'order_amount': order_amounts,
    'timestamp': timestamps
})

# 2. Apply DBSCAN based on latitude and longitude for delivery clustering

# DBSCAN works better with distances, so we need to scale the latitude and longitude data.
# We will use a custom distance metric for geographical distances.
coords = data[['latitude', 'longitude']].values

# Define a custom function to calculate distance between two geo-coordinates
def haversine_dist(coords1, coords2):
    return great_circle(coords1, coords2).meters

# Run DBSCAN
db = DBSCAN(eps=100000, min_samples=3, metric=lambda x, y: haversine_dist(x, y))  # eps = 100 km
clusters = db.fit_predict(coords)

# Add cluster labels to the DataFrame
data['cluster'] = clusters

# 3. Visualize the clusters
plt.figure(figsize=(10, 7))
scatter = plt.scatter(data['longitude'], data['latitude'], c=data['cluster'], cmap='tab10', s=50)
plt.title('DBSCAN Clustering for Delivery Locations in Thailand')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.colorbar(scatter, label='Cluster Label')
plt.grid(True)
plt.show()

# Output data
print(data.head())