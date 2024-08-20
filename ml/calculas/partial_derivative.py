from sympy import symbols, diff

# Define variables and function
x, y = symbols('x y')
f = x**2 + y**2 + 3*x*y

# Compute partial derivatives
partial_x = diff(f, x)
partial_y = diff(f, y)

print(f"Partial Derivative with respect to x: {partial_x}")
print(f"Partial Derivative with respect to y: {partial_y}")