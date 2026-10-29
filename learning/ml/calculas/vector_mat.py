import numpy as np

# Create a vector
vector = np.array([1, 2, 3])

# Calculate the magnitude (L2 norm) of the vector
magnitude = np.linalg.norm(vector)
print(f"Vector: {vector}")
print(f"Magnitude of the vector: {magnitude}")


import numpy as np

# Define the vector
vector = np.array([3, 4])

# Calculate the magnitude (L2 norm) of the vector
magnitude = np.linalg.norm(vector)

print(f"Vector: {vector}")
print(f"Magnitude of the vector: {magnitude}")

# Dot product of two vectors
vector_a = np.array([1, 2, 3])
vector_b = np.array([4, 5, 6])
dot_product = np.dot(vector_a, vector_b)
print(f"Dot product of {vector_a} and {vector_b}: {dot_product}")


# B. Matrix Representation and Operations
print('B. Matrix Representation and Operations')

# Create a matrix
matrix = np.array([[1, 2], [3, 4]])

# Matrix multiplication
matrix_a = np.array([[1, 2], [3, 4]])
matrix_b = np.array([[5, 6], [7, 8]])
matrix_product = np.dot(matrix_a, matrix_b)
print(f"Matrix A:\n{matrix_a}")
print(f"Matrix B:\n{matrix_b}")
print(f"Matrix product of A and B:\n{matrix_product}")

# Transpose of a matrix
transpose = np.transpose(matrix)
print(f"Transpose of matrix:\n{transpose}")


print('C. Application in Linear Regression')
# Suppose we have a simple linear regression model: y = Wx + b
# Here W is the weight vector, x is the feature vector, and b is the bias term

# Feature vector (example input)
x = np.array([1, 2])

# Weight vector
W = np.array([0.5, 1.5])

# Bias term
b = 0.1

# Calculate prediction
y = np.dot(W, x) + b
print(f"Prediction (y) from linear regression model: {y}")


print('D. Application in Neural Networks')

# Example: Forward pass in a simple neural network layer

# Input vector (example input)
input_vector = np.array([0.5, 1.0])

# Weight matrix (2 inputs, 3 neurons)
weight_matrix = np.array([[0.2, 0.8, -0.5],
                          [0.5, -0.91, 0.26]])

# Bias vector (for 3 neurons)
bias_vector = np.array([0.1, -0.3, 0.4])

# Compute output (linear combination)
output = np.dot(input_vector, weight_matrix) + bias_vector
print(f"Output from neural network layer: {output}")