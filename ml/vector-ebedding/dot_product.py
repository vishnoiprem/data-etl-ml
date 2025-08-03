import numpy as np

# Two similar vectors pointing in the same direction
vector_a = np.array([3, 4])
vector_b = np.array([6, 8])

dot_product = np.dot(vector_a, vector_b)
print(f"Dot product: {dot_product}")  # Output: 50

# Normalized versions for comparison
norm_a = vector_a / np.linalg.norm(vector_a)
norm_b = vector_b / np.linalg.norm(vector_b)
print(norm_a,norm_b)
cosine_sim = np.dot(norm_a, norm_b)
print(f"Cosine similarity: {cosine_sim}")  # Output: 1.0