import numpy as np
import math


def euclidean_distance(vector1, vector2):
    """
    Calculate Euclidean distance between two vectors
    """
    # Method 1: Step by step
    differences = []
    for i in range(len(vector1)):
        diff = vector1[i] - vector2[i]
        differences.append(diff ** 2)
    print(differences)

    distance = math.sqrt(sum(differences))
    return distance


# Example usage
vec_a = [1, 2, 3]
vec_b = [4, 6, 8]
distance = euclidean_distance(vec_a, vec_b)
print(f"Distance: {distance:.2f}")
# Output: Distance: 7.07
