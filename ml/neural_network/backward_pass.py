import numpy as np

# Sigmoid activation
def sigmoid(x):
    return 1 / (1 + np.exp(-x))

# Derivative of sigmoid
def sigmoid_derivative(x):
    return x * (1 - x)

# Forward pass
def forward_pass(x):
    z1 = np.dot(W1, x) + b1
    a1 = sigmoid(z1)
    z2 = np.dot(W2, a1) + b2
    a2 = sigmoid(z2)
    return z1, a1, z2, a2

# Backward pass
def backward_pass(x, y_true, z1, a1, z2, a2, learning_rate=0.1):
    global W1, b1, W2, b2

    # Output layer error
    loss = 0.5 * (y_true - a2) ** 2

    dL_da2 = -(y_true - a2)
    da2_dz2 = sigmoid_derivative(a2)
    dL_dz2 = dL_da2 * da2_dz2

    dL_dW2 = np.dot(dL_dz2, a1.T)
    dL_db2 = dL_dz2

    dL_da1 = np.dot(W2.T, dL_dz2)
    da1_dz1 = sigmoid_derivative(a1)
    dL_dz1 = dL_da1 * da1_dz1

    dL_dW1 = np.dot(dL_dz1, x.T)
    dL_db1 = dL_dz1

    # Update weights and biases
    W2 -= learning_rate * dL_dW2
    b2 -= learning_rate * dL_db2
    W1 -= learning_rate * dL_dW1
    b1 -= learning_rate * dL_db1

    return loss[0][0]

# Example data (XOR problem)
X = np.array([[0,0], [0,1], [1,0], [1,1]]).T  # Shape: (2, 4)
y = np.array([[0, 1, 1, 0]])  # Shape: (1, 4)

# Network size
input_size = 2
hidden_size = 2
output_size = 1

# Initialize weights and biases
np.random.seed(42)
W1 = np.random.randn(hidden_size, input_size)
b1 = np.random.randn(hidden_size, 1)
W2 = np.random.randn(output_size, hidden_size)
b2 = np.random.randn(output_size, 1)

# Training loop
for epoch in range(10000):
    total_loss = 0
    for i in range(X.shape[1]):
        x_sample = X[:, i:i+1]  # Shape: (2,1)
        y_sample = y[:, i:i+1]  # Shape: (1,1)

        z1, a1, z2, a2 = forward_pass(x_sample)
        loss = backward_pass(x_sample, y_sample, z1, a1, z2, a2)
        total_loss += loss

    if epoch % 1000 == 0:
        print(f"Epoch {epoch}, Loss: {total_loss:.4f}")

# Test
for i in range(X.shape[1]):
    x_sample = X[:, i:i+1]
    _, _, _, a2 = forward_pass(x_sample)
    print(f"Input: {X[:,i]} => Predicted: {a2[0][0]:.4f}")