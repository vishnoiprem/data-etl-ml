import numpy as np
import matplotlib.pyplot as plt
import math
# Sample embeddings for different animals
embeddings = {
    'cat': [0.2, 0.8, 0.1],
    'dog': [0.3, 0.7, 0.2],
    'lion': [0.1, 0.9, 0.0],
    'car': [0.9, 0.1, 0.8],
    'truck': [0.8, 0.2, 0.7]
}


def euclidean_distance_numpy(vector1, vector2):
    """
    Efficient Euclidean distance using NumPy
    """
    return np.linalg.norm(np.array(vector1) - np.array(vector2))


def compare_all_distances(embeddings):
    """
    Calculate distances between all pairs of embeddings
    """
    items = list(embeddings.keys())
    distances = {}

    for i, item1 in enumerate(items):
        for j, item2 in enumerate(items[i + 1:], i + 1):
            dist = euclidean_distance_numpy(embeddings[item1], embeddings[item2])
            distances[f"{item1}-{item2}"] = dist

    return distances


# Calculate and display all distances
all_distances = compare_all_distances(embeddings)
for pair, distance in sorted(all_distances.items(), key=lambda x: x[1]):
    print(f"{pair}: {distance:.3f}")
