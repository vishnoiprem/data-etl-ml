from sympy import symbols, integrate

# Define variable and function
x = symbols('x')
f = x**2 + 3*x + 2

# Compute indefinite integral
indefinite_integral = integrate(f, x)
print(f"Indefinite Integral: {indefinite_integral}")

# Compute definite integral from 0 to 2
definite_integral = integrate(f, (x, 0, 2))
print(f"Definite Integral from 0 to 2: {definite_integral}")