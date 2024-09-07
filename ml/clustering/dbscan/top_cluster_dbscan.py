import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN

# Load the CSV file (assuming you've already loaded the dataset as 'data')
file_path = 'thailand_delivery_data.csv'
data = pd.read_csv(file_path)

# Extract latitude and longitude for clustering
coords = data[['latitude', 'longitude']].values

# Apply DBSCAN with tuned parameters min_samples can be inceased
db = DBSCAN(eps=0.1, min_samples=5, metric='euclidean')
data['cluster'] = db.fit_predict(coords)

# Step 1: Get the top 5 largest clusters (excluding noise, cluster -1)
cluster_counts = data['cluster'].value_counts()
top_5_clusters = cluster_counts[cluster_counts.index != -1].index[:5]

# Step 2: Filter the data to only include the top 5 largest clusters
top_5_clustered_data = data[data['cluster'].isin(top_5_clusters)]

# Display the top 5 clusters along with their size
top_5_cluster_summary = cluster_counts.loc[top_5_clusters].reset_index()
top_5_cluster_summary.columns = ['Cluster', 'Number of Points']
print("Top 5 Largest Clusters by DBSCAN:")
print(top_5_cluster_summary)

# Step 3: Visualize the top 5 largest clusters
plt.figure(figsize=(10, 7))
scatter = plt.scatter(top_5_clustered_data['longitude'], top_5_clustered_data['latitude'],
                      c=top_5_clustered_data['cluster'], cmap='tab10', s=50)
plt.title('Top 5 Largest Clusters by DBSCAN')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.colorbar(scatter, label='Cluster Label')
plt.grid(True)
plt.show()
