import numpy as np
import torch

# ================================
# 1. Scalars (0D Tensor)
# ================================
scalar_np = np.array(5)
scalar_torch = torch.tensor(5)

print("\n1️⃣ Scalars (0D Tensor)")
print("NumPy Scalar:", scalar_np)
print("PyTorch Scalar:", scalar_torch)

# ================================
# 2. Vectors (1D Tensor)
# ================================
vector_np = np.array([10, 20, 30])
vector_torch = torch.tensor([10, 20, 30])

print("\n2️⃣ Vectors (1D Tensor)")
print("NumPy Vector:", vector_np)
print("PyTorch Vector:", vector_torch)

# ================================
# 3. Matrices (2D Tensor)
# ================================
matrix_np = np.array([[1, 2, 3], [4, 5, 6]])
matrix_torch = torch.tensor([[1, 2, 3], [4, 5, 6]])

print("\n3️⃣ Matrices (2D Tensor)")
print("NumPy Matrix:\n", matrix_np)
print("PyTorch Matrix:\n", matrix_torch)

# ================================
# 4. 3D Tensor (Example: RGB Image)
# ================================
tensor_3d_np = np.random.randint(0, 256, (3, 3, 3))  # Shape: (3, 3, 3) -> RGB Image
tensor_3d_torch = torch.randint(0, 256, (3, 3, 3))  # Random RGB values

print("\n4️⃣ 3D Tensor (RGB Image)")
print("NumPy 3D Tensor:\n", tensor_3d_np)
print("PyTorch 3D Tensor:\n", tensor_3d_torch)

# ================================
# 5. Basic Tensor Operations
# ================================
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])

print("\n5️⃣ Matrix Operations")
print("Matrix Addition:\n", A + B)
print("Matrix Subtraction:\n", A - B)

# ================================
# 6. Matrix Multiplication
# ================================
elementwise_product = A * B  # Element-wise Multiplication
dot_product = np.dot(A, B)  # Matrix Multiplication (Dot Product)

print("\n6️⃣ Matrix Multiplication")
print("Element-wise Multiplication:\n", elementwise_product)
print("Matrix Multiplication (Dot Product):\n", dot_product)

# ================================
# 7. Transpose of a Matrix
# ================================
A_transpose = A.T
print("\n7️⃣ Transpose of A:\n", A_transpose)

# ================================
# 8. Reshaping a Tensor
# ================================
A_reshaped = A.reshape(4, 1)  # Convert 2x2 matrix into a 4x1 matrix
print("\n8️⃣ Reshaped Matrix:\n", A_reshaped)

# ================================
# 9. Converting Between NumPy and PyTorch
# ================================
numpy_array = np.array([1, 2, 3])
torch_tensor = torch.tensor(numpy_array)
converted_numpy_array = torch_tensor.numpy()

print("\n9️⃣ NumPy ↔ PyTorch Conversion")
print("Converted to PyTorch Tensor:", torch_tensor)
print("Converted back to NumPy Array:", converted_numpy_array)