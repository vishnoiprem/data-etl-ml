from sympy import diff, symbols

# Define the variable and function
x = symbols('x')
f = x**3 - 3*x**2 + 4*x - 1

# Compute first and second derivatives
first_derivative = diff(f, x)
second_derivative = diff(first_derivative, x)

print(f"First Derivative: {first_derivative}")
print(f"Second Derivative: {second_derivative}")