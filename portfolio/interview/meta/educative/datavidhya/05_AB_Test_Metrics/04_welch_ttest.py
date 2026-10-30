"""
Problem 04: Welch's t-Test for Continuous Metrics.

Meta flavor: Comparing average watch time (continuous) between treatment and control.

How to Think:
- Welch's t-test does NOT assume equal variances.
- t = (mean_t - mean_c) / sqrt(var_t/n_t + var_c/n_c)
- degrees of freedom via Welch-Satterthwaite.

How to Remember:
- "t = (mean_t - mean_c) / sqrt(var_t/n_t + var_c/n_c)."

AI Use Cases:
- Continuous metric comparison (watch time, revenue).
- ML model A/B with regression target.
"""
import math


def welch_t_test(mean_t: float, var_t: float, n_t: int, mean_c: float, var_c: float, n_c: int) -> dict:
    se = math.sqrt(var_t / n_t + var_c / n_c)
    t = (mean_t - mean_c) / se if se > 0 else 0.0
    # Welch-Satterthwaite df
    num = (var_t / n_t + var_c / n_c) ** 2
    den = (var_t / n_t) ** 2 / (n_t - 1) + (var_c / n_c) ** 2 / (n_c - 1)
    df = num / den if den > 0 else float("inf")
    # Approximate two-sided p-value via normal (large n approximation)
    from math import erf, sqrt
    p_value = 2 * (1 - 0.5 * (1 + erf(abs(t) / sqrt(2))))
    return {"t": t, "df": df, "p_value_approx": p_value}


if __name__ == "__main__":
    # Treatment: mean 12.5, var 16, n=1000
    # Control:   mean 12.0, var 16, n=1000
    res = welch_t_test(12.5, 16, 1000, 12.0, 16, 1000)
    print(res)
