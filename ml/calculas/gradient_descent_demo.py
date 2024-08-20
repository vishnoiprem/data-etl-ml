import numpy as np
from sympy import symbols, diff, integrate, Matrix, hessian
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# ------------------------------
# 1. Derivatives in Machine Learning
# ------------------------------

# A. Gradient Descent
def gradient_descent_demo():
    # Simple quadratic function: f(x) = x^2
    def f(x):
        return x**2

    # Derivative of the function: f'(x) = 2x
    def derivative(x):
        return 2 * x

    # Gradient Descent Algorithm
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

gradient_descent_demo()

# ------------------------------
# 2. Higher-Order Derivatives
# ------------------------------

def higher_order_derivatives_demo():
    # Define the variable and function
    x = symbols('x')
    f = x**3 - 3*x**2 + 4*x - 1

    # Compute first and second derivatives
    first_derivative = diff(f, x)
    second_derivative = diff(first_derivative, x)

    print(f"First Derivative: {first_derivative}")
    print(f"Second Derivative: {second_derivative}")

higher_order_derivatives_demo()

# ------------------------------
# 3. Partial Derivatives
# ------------------------------

def partial_derivatives_demo():
    # Define variables and function
    x, y = symbols('x y')
    f = x**2 + y**2 + 3*x*y

    # Compute partial derivatives
    partial_x = diff(f, x)
    partial_y = diff(f, y)

    print(f"Partial Derivative with respect to x: {partial_x}")
    print(f"Partial Derivative with respect to y: {partial_y}")

partial_derivatives_demo()

# ------------------------------
# 4. Chain Rule
# ------------------------------

def chain_rule_demo():
    # Define variables and functions
    x = symbols('x')
    u = x**2 + 1
    y = 3*u

    # Compute derivatives
    du_dx = diff(u, x)
    dy_du = diff(y, u)

    # Apply the Chain Rule
    dy_dx = dy_du * du_dx
    print(f"dy/dx using chain rule: {dy_dx}")

chain_rule_demo()

# ------------------------------
# 5. Integrals in Machine Learning
# ------------------------------

def integrals_demo():
    # Define variable and function
    x = symbols('x')
    f = x**2 + 3*x + 2

    # Compute indefinite integral
    indefinite_integral = integrate(f, x)
    print(f"Indefinite Integral: {indefinite_integral}")

    # Compute definite integral from 0 to 2
    definite_integral = integrate(f, (x, 0, 2))
    print(f"Definite Integral from 0 to 2: {definite_integral}")

integrals_demo()

# ------------------------------
# 6. Multivariable Calculus
# ------------------------------

def multivariable_calculus_demo():
    # Define variables and function
    x, y = symbols('x y')
    f = x**2 + y**2 + 3*x*y

    # Compute the Jacobian matrix
    jacobian_matrix = Matrix([f]).jacobian([x, y])
    print(f"Jacobian Matrix:\n{jacobian_matrix}")

    # Compute the Hessian matrix
    hessian_matrix = hessian(f, [x, y])
    print(f"Hessian Matrix:\n{hessian_matrix}")

multivariable_calculus_demo()

# ------------------------------
# 7. Advanced Application: Gradient Descent in Multiple Variables
# ------------------------------

def multivariable_gradient_descent_demo():
    # Function: f(x, y) = x^2 + y^2
    def f(x, y):
        return x**2 + y**2

    # Partial derivatives: df/dx = 2x, df/dy = 2y
    def gradient(x, y):
        return np.array([2*x, 2*y])

    # Gradient Descent Algorithm
    def gradient_descent(starting_point, learning_rate, iterations):
        point = np.array(starting_point)
        for _ in range(iterations):
            grad = gradient(*point)
            point = point - learning_rate * grad
            print(f"Point: {point}, f(x, y): {f(*point)}")
        return point

    # Example usage
    minimum = gradient_descent(starting_point=[10, 10], learning_rate=0.1, iterations=100)
    print(f"Minimum occurs at: {minimum}")

multivariable_gradient_descent_demo()

# ------------------------------
# 8. Regression Analysis Example
# ------------------------------

def regression_analysis_demo():
    # Example data: Simple linear relationship
    X = np.array([[1], [2], [3], [4], [5]])
    y = np.array([1, 2, 1.5, 3.5, 2])

    # Fit a linear regression model
    model = LinearRegression()
    model.fit(X, y)
    predictions = model.predict(X)

    print(f"Coefficients: {model.coef_}, Intercept: {model.intercept_}")
    print(f"Predictions: {predictions}")

regression_analysis_demo()