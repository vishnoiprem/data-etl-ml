import numpy as np

# Objective function: f(x) = x^2
def objective_function(x):
    return x**2

# Gradient of the objective function: f'(x) = 2x
def gradient(x):
    return 2 * x

# Gradient Descent algorithm
def gradient_descent(learning_rate=0.1, epochs=10):
    x = 10  # Initial value
    for i in range(epochs):
        grad = gradient(x)
        x = x - learning_rate * grad  # Update step
        print(f'Epoch {i+1}: x = {x}, f(x) = {objective_function(x)}')
    return x

# Running gradient descent
minimized_x = gradient_descent()
print(f'Optimized value of x: {minimized_x}')