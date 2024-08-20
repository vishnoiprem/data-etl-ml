from sympy import symbols, diff

# Define variables and functions
x = symbols('x')
u = x**2 + 1
y = 3*u

# Compute derivatives
du_dx = diff(u, x)
dy_du = diff(y, u)

# Chain rule
dy_dx = dy_du * du_dx
print(f"dy/dx using chain rule: {dy_dx}")