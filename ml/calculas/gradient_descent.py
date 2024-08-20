import numpy as np

def gradient_descent_demo():
    def f(x):
        return x**2

    def derivative(x):
        return 2 * x

    def gradient_descent(starting_point, learning_rate, iterations):
        x = starting_point
        for _ in range(iterations):
            gradient = derivative(x)
            x = x - learning_rate * gradient
            print(f"x: {x}, f(x): {f(x)}")
        return x

    minimum = gradient_descent(starting_point=10, learning_rate=0.1, iterations=100)
    print(f"Minimum occurs at: {minimum}")

gradient_descent_demo()