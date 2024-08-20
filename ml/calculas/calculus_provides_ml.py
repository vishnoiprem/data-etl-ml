import numpy as np

# Simple quadratic function: f(x) = x^2
def f(x):
    return x**2

# Derivative of the function: f'(x) = 2x
def derivative(x):
    return 2 * x

# Gradient Descent to find the minimum of the function
def gradient_descent(starting_point, learning_rate, iterations):
    x = starting_point
    for _ in range(iterations):
        gradient = derivative(x)
        x = x - learning_rate * gradient
        print(f"x: {x}, f(x): {f(x)}")
    return x

# Example usage
minimum = gradient_descent(starting_point=10, learning_rate=0.1, iterations=100)
print(f"Minimum occurs at: {minimum}")