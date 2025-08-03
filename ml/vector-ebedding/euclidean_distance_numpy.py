import numpy as np

def euclidean_distance_numpy(vector1, vector2):
    """
    Efficient Euclidean distance using NumPy
    """
    return np.linalg.norm(np.array(vector1) - np.array(vector2))

# Example with word embeddings
word_cat = np.array([0.2, 0.8, 0.1, 0.5, 0.3])
word_dog = np.array([0.3, 0.7, 0.2, 0.4, 0.4])
word_car = np.array([0.9, 0.1, 0.8, 0.2, 0.1])

print(f"Cat-Dog distance: {euclidean_distance_numpy(word_cat, word_dog):.3f}")
print(f"Cat-Car distance: {euclidean_distance_numpy(word_cat, word_car):.3f}")
print(f"Dog-Car distance: {euclidean_distance_numpy(word_dog, word_car):.3f}")
