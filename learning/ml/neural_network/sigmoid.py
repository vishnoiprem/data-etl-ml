import numpy as np

# Simple XOR dataset
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
y = np.array([[0], [1], [1], [0]])

# Network architecture: 2 -> 2 -> 1
# Initialize weights (simplified for demonstration)
W1 = np.array([[0.5, -0.3], [0.2, 0.8]])  # 2x2 matrix
b1 = np.array([[0.1], [0.2]])  # 2x1 vector
W2 = np.array([[0.9, -0.7]])  # 1x2 matrix
b2 = np.array([[0.3]])  # 1x1 vector


def sigmoid(x):
    return 1 / (1 + np.exp(-np.clip(x, -500, 500)))  # Clipped for stability


def forward_pass(x):
    # Layer 1
    z1 = np.dot(W1, x.T) + b1
    a1 = sigmoid(z1)

    # Layer 2 (output)
    z2 = np.dot(W2, a1) + b2
    a2 = sigmoid(z2)

    return z1, a1, z2, a2


# Example forward pass for input [1, 0]
input_sample = np.array([[1, 0]])
z1, a1, z2, output = forward_pass(input_sample)
print(f"Input: {input_sample[0]}")
print(f"Hidden layer output: {a1.flatten()}")
print(f"Final output: {output[0][0]:.4f}")