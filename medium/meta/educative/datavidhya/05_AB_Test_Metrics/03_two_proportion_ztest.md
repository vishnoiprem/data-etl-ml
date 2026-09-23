# Two-Proportion Z-Test

## Problem
Is the difference between two conversion rates statistically significant?

## How to Think
1. p_pool = (x_t + x_c) / (n_t + n_c).
2. SE = sqrt(p_pool*(1-p_pool)*(1/n_t + 1/n_c)).
3. z = (p_t - p_c) / SE.
4. |z| > 1.96 -> reject H0 at alpha = 0.05.

## How to Remember
- **Formula**: "z = (p_t - p_c) / sqrt(p_pool*(1-p_pool)*(1/n_t + 1/n_c))."
- Two-sided p-value = 2 * (1 - Phi(|z|)).

## Code (Python)
```python
import math

def two_prop_z_test(x_t, n_t, x_c, n_c):
    p_t, p_c = x_t / n_t, x_c / n_c
    p_pool = (x_t + x_c) / (n_t + n_c)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n_t + 1 / n_c))
    z = (p_t - p_c) / se if se > 0 else 0.0
    from math import erf, sqrt
    p_value = 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))
    return {"z": z, "p_value": p_value}
```

## Common Mistakes
- Forgetting to use p_pool (not separate variances).
- Treating two-sided p-value as one-sided.

## AI Use Cases
- Significance testing for A/B.
- Champion-challenger comparisons.
- Statistical reporting.
