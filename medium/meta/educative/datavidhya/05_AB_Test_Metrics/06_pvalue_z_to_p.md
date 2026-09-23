# Z to p-Value

## Problem
Convert a z-statistic to a two-sided p-value.

## How to Think
1. Compute Phi(z) using the error function: `0.5 * (1 + erf(z / sqrt(2)))`.
2. Two-sided p = 2 * (1 - Phi(|z|)).

## How to Remember
- **Pattern**: "p_two_sided = 2 * (1 - Phi(|z|))."
- |z| > 1.96 -> p < 0.05.

## Code (Python)
```python
import math
def z_to_p_two_sided(z):
    return 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
```

## Common Mistakes
- Forgetting absolute value before Phi.
- Using one-sided test without specifying direction.

## AI Use Cases
- Statistical reporting dashboards.
- Bonferroni / BH correction downstream.
