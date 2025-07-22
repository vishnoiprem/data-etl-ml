import numpy as np
import math

# Define vectors
A = [3, 4]
B = [6, 8]

# Step 1: Calculate dot product
dot_product = sum(a * b for a, b in zip(A, B))
print(f"Dot product: {dot_product}")  # 3*6 + 4*8 = 18 + 32 = 50

# Step 2: Calculate magnitudes
magnitude_A = math.sqrt(sum(a**2 for a in A))
magnitude_B = math.sqrt(sum(b**2 for b in B))
print(f"Magnitude A: {magnitude_A}")  # √(3² + 4²) = √25 = 5
print(f"Magnitude B: {magnitude_B}")  # √(6² + 8²) = √100 = 10

# Step 3: Calculate cosine similarity
cosine_sim = dot_product / (magnitude_A * magnitude_B)
print(f"Cosine similarity: {cosine_sim}")  # 50 / (5 * 10) = 1.0