"""
Problem 07: 95% Confidence Interval on the Lift.

Meta flavor: A +/- 2 SE band around the point estimate of the lift.

How to Think:
- diff = p_t - p_c.
- SE_diff = sqrt(var_t/n_t + var_c/n_c) (binary uses p_pool).
- CI = diff +/- 1.96 * SE_diff.

How to Remember:
- "CI = diff +/- 1.96 * SE. Excludes 0 -> significant."

AI Use Cases:
- A/B result dashboards.
- Risk-aware decision making.
- Stakeholder communication.
"""
import math


def ci_lift(p_t: float, n_t: int, p_c: float, n_c: int, alpha: float = 0.05) -> dict:
    """Two-proportion 95% CI on the absolute lift."""
    p_pool = (p_t * n_t + p_c * n_c) / (n_t + n_c)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n_t + 1 / n_c))
    z = 1.96
    diff = p_t - p_c
    return {
        "lift": diff,
        "ci_low":  diff - z * se,
        "ci_high": diff + z * se,
        "se": se,
    }


if __name__ == "__main__":
    print(ci_lift(0.125, 1000, 0.10, 1000))
