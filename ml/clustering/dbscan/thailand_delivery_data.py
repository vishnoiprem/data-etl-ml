import pandas as pd
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt

file_path = 'thailand_delivery_data.csv'
data = pd.read_csv(file_path)

# Extract latitude and longitude for clustering
coords = data[['latitude', 'longitude']].values


# Function to run DBSCAN and plot clusters
def run_dbscan_and_plot(eps_value, min_samples_value):
    # Apply DBSCAN with the given eps and min_samples
    db = DBSCAN(eps=eps_value, min_samples=min_samples_value, metric='euclidean')
    data['cluster'] = db.fit_predict(coords)

    # Display the cluster counts
    cluster_counts = data['cluster'].value_counts()
    print(f"DBSCAN Results (eps={eps_value}, min_samples={min_samples_value}):")
    print(cluster_counts)

    # Visualize the clusters
    plt.figure(figsize=(10, 7))
    scatter = plt.scatter(data['longitude'], data['latitude'], c=data['cluster'], cmap='tab10', s=50)
    plt.title(f'DBSCAN Clustering of Delivery Locations (eps={eps_value}, min_samples={min_samples_value})')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.colorbar(scatter, label='Cluster Label')
    plt.grid(True)
    plt.show()


# Test smaller eps values for DBSCAN (better suited for dense data)
run_dbscan_and_plot(eps_value=0.05, min_samples_value=100)
run_dbscan_and_plot(eps_value=0.01, min_samples_value=200)
run_dbscan_and_plot(eps_value=0.001, min_samples_value=300)
