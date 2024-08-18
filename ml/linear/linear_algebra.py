scalar = 5
print(scalar)
# Output: 5

import numpy as np

# Vector example
vector = np.array([1, 2, 3])
print(vector)
# Output: [1 2 3]

v1 = np.array([1, 2, 3])
v2 = np.array([4, 5, 6])
v_add = v1 + v2
print(v_add)
# Output: [5 7 9]

v1 = np.array([1, 2, 3])
v2 = np.array([4, 5, 6])
dot_product = np.dot(v1, v2)
print(dot_product)
# Output: 32

# Matrix example
matrix = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
print(matrix)


m1 = np.array([[1, 2], [3, 4]])
m2 = np.array([[5, 6], [7, 8]])
m_add = m1 + m2
print(m_add)


m1 = np.array([[1, 2], [3, 4]])
m2 = np.array([[5, 6], [7, 8]])
m_mult = np.dot(m1, m2)
print(m_mult)  # Output: [[19 22]
               #          [43 50]]


print('tensor ')
# Tensor example (3D array)
tensor = np.array([[[1, 2], [3, 4]], [[5, 6], [7, 8]], [[9, 10], [11, 12]]])
print(tensor)

print('transpose')
matrix = np.array([[1, 2], [3, 4]])
transpose = np.transpose(matrix)
print(transpose)  # Output: [[1 3]
                  #          [2 4]]


print('np.linalg.det')

matrix = np.array([[1, 2], [3, 4]])
det = np.linalg.det(matrix)
print(det)  # Output: -2.0000000000000004


print('8. Inverse of a Matrix')

matrix = np.array([[1, 2], [3, 4]])
inverse = np.linalg.inv(matrix)
print(inverse)


print('9. Eigenvalues and Eigenvectors')

matrix = np.array([[4, -2], [1, 1]])
eigenvalues, eigenvectors = np.linalg.eig(matrix)
print("Eigenvalues:", eigenvalues)
print("Eigenvectors:\n", eigenvectors)


print('10. Singular Value Decomposition (SVD)')
matrix = np.array([[1, 2], [3, 4], [5, 6]])
U, S, Vt = np.linalg.svd(matrix)
print("U:\n", U)
print("S:\n", S)
print("Vt:\n", Vt)


print('11. Advanced Matrix Operations')

matrix = np.array([[1, 2], [2, 4]])
rank = np.linalg.matrix_rank(matrix)
print("Rank:", rank)  # Output: 1


print('12. Practical Application: Linear Regression')


import numpy as np

# Dataset
X = np.array([[1, 1], [1, 2], [2, 2], [2, 3]])
y = np.dot(X, np.array([1, 2])) + 3

# Add a column of ones to include the intercept in the model
X_b = np.c_[np.ones((4, 1)), X]

# Calculate the optimal weights using the Normal Equation
theta_best = np.linalg.inv(X_b.T.dot(X_b)).dot(X_b.T).dot(y)
print("Optimal weights:", theta_best)