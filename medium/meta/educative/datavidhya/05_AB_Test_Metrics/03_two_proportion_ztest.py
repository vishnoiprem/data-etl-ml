"""
Problem 03: Two-Proportion Z-Test.

Meta flavor: Is the difference between treatment and control conversion rates
statistically significant?

How to Think:
- z = (p_t - p_c) / sqrt(p_pool * (1 - p_pool) * (1/n_t + 1/n_c))
- p_pool = (x_t + x_c) / (n_t + n_c)
- Compare |z| to 1.96 for alpha = 0.05 two-sided.

How to Remember:
- "z = (p_t - p_c) / sqrt(p_pool*(1-p_pool)*(1/n_t + 1/n_c))."

AI Use Cases:
- Significance testing for A/B.
- Champion-challenger comparisons.
- Statistical reporting.
"""
import math


def two_prop_z_test(x_t: int, n_t: int, x_c: int, n_c: int) -> dict:
    """Two-proportion z-test. Returns z-stat and approximate two-sided p-value."""
    p_t = x_t / n_t
    p_c = x_c / n_c
    p_pool = (x_t + x_c) / (n_t + n_c)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n_t + 1 / n_c))
    z = (p_t - p_c) / se if se > 0 else 0.0
    # Two-sided p-value via normal CDF approximation
    # Phi(z) ≈ 0.5 * (1 + erf(z / sqrt(2)))
    from math import erf, sqrt
    p_value = 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))
    return {"z": z, "p_value": p_value, "p_t": p_t, "p_c": p_c}


if __name__ == "__main__":
    # 125 / 1000 treatment, 100 / 1000 control
    res = two_prop_z_test(125, 1000, 100, 1000)
    print(res)
