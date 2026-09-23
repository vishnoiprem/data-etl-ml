# 95% Confidence Interval on Lift

## Problem
Compute the two-sided CI for the absolute difference in conversion rates.

## How to Think
1. SE_diff = sqrt(p_pool*(1-p_pool)*(1/n_t + 1/n_c)).
2. CI = diff +/- 1.96 * SE_diff.

## How to Remember
- **Pattern**: "CI = diff +/- 1.96 * SE. Excludes 0 -> significant."
- For continuous: use sqrt(var_t/n_t + var_c/n_c) for SE.

## Code (Python)
```python
import math
def ci_lift(p_t, n_t, p_c, n_c, alpha=0.05):
    p_pool = (p_t*n_t + p_c*n_c) / (n_t + n_c)
    se = math.sqrt(p_pool*(1-p_pool)*(1/n_t + 1/n_c))
    diff = p_t - p_c
    return {"lift": diff, "ci_low": diff - 1.96*se, "ci_high": diff + 1.96*se}
```

## Common Mistakes
- Forgetting to use p_pool (not separate variances).
- Reporting CI on relative lift without bootstrapping — math is non-trivial.

## AI Use Cases
- A/B result dashboards.
- Risk-aware decision making.
- Stakeholder communication.
