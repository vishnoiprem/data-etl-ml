# CUPED Variance Reduction

## Problem
Reduce A/B test variance by adjusting outcome with a pre-experiment covariate.

## How to Think
1. theta = Cov(y, y_pre) / Var(y_pre).
2. y_cuped = y - theta * (y_pre - mean(y_pre)).
3. Variance reduction = 1 - Corr^2.

## How to Remember
- **Pattern**: "y_cuped = y - theta * (y_pre - pre_mean)."
- Pick pre-period covariate correlated with the metric.

## Code (Python)
```python
def cuped_transform(y, y_pre, pre_mean):
    n = len(y)
    cov = sum((yi - sum(y)/n) * (ypi - sum(y_pre)/n) for yi, ypi in zip(y, y_pre)) / (n - 1)
    var_pre = sum((ypi - sum(y_pre)/n) ** 2 for ypi in y_pre) / (n - 1)
    theta = cov / var_pre if var_pre > 0 else 0.0
    return [yi - theta * (ypi - pre_mean) for yi, ypi in zip(y, y_pre)], theta
```

## Common Mistakes
- Computing theta in-sample (unbiased) and then using it on the same sample — biased CI.
- Picking a weak covariate (no variance reduction).

## AI Use Cases
- A/B variance reduction.
- Sensitivity analysis with control covariates.
