"""
Problem 08: CUPED Variance Reduction.

Meta flavor: Reduce variance by regressing on a pre-experiment covariate
(e.g., pre-period clicks).

How to Think:
- y_cuped = y - theta * (y_pre - mean(y_pre))
- theta = Cov(y, y_pre) / Var(y_pre) (estimated from pre-period data).
- Variance reduction = Var(y_cuped) / Var(y) ~ (1 - corr^2).

How to Remember:
- "y_cuped = y - theta*(y_pre - pre_mean)."

AI Use Cases:
- A/B variance reduction.
- Sensitivity analysis with control covariates.
"""
import math


def cuped_transform(y, y_pre, pre_mean):
    """Apply CUPED adjustment. y, y_pre are parallel arrays."""
    n = len(y)
    cov = sum((yi - sum(y) / n) * (ypi - sum(y_pre) / n) for yi, ypi in zip(y, y_pre)) / (n - 1)
    var_pre = sum((ypi - sum(y_pre) / n) ** 2 for ypi in y_pre) / (n - 1)
    theta = cov / var_pre if var_pre > 0 else 0.0
    return [yi - theta * (ypi - pre_mean) for yi, ypi in zip(y, y_pre)], theta


if __name__ == "__main__":
    y = [10, 12, 11, 13, 14, 9, 15]
    y_pre = [9, 11, 12, 14, 13, 8, 16]
    pre_mean = sum(y_pre) / len(y_pre)
    adjusted, theta = cuped_transform(y, y_pre, pre_mean)
    print(f"theta = {theta:.4f}, adjusted = {adjusted}")
