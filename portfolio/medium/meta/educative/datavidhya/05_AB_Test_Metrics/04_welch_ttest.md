# Welch's t-Test (Unequal Variance)

## Problem
Compare two continuous means without assuming equal variances.

## How to Think
1. SE = sqrt(var_t/n_t + var_c/n_c).
2. t = (mean_t - mean_c) / SE.
3. df via Welch-Satterthwaite.

## How to Remember
- **Formula**: "t = (mean_t - mean_c) / sqrt(var_t/n_t + var_c/n_c)."
- Use Welch when sample sizes or variances differ.

## Code (Python)
```python
import math
def welch_t_test(mean_t, var_t, n_t, mean_c, var_c, n_c):
    se = math.sqrt(var_t/n_t + var_c/n_c)
    t = (mean_t - mean_c) / se if se > 0 else 0
    num = (var_t/n_t + var_c/n_c) ** 2
    den = (var_t/n_t)**2/(n_t-1) + (var_c/n_c)**2/(n_c-1)
    df = num/den if den > 0 else float("inf")
    return {"t": t, "df": df}
```

## Common Mistakes
- Using Student's t-test (assumes equal variance) when variances differ a lot.
- Using normal approximation for small n — use t-distribution.

## AI Use Cases
- Continuous metric comparison (watch time, revenue).
- ML model A/B with regression target.
