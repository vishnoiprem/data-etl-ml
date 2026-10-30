# Sample Size Calculator

## Problem
For a two-proportion z-test, given baseline p0, MDE, alpha, power — compute per-arm n.

## How to Think
1. Convert MDE-relative to p1 = p0 * (1 + mde).
2. Plug into the closed-form formula:
   n = (Z_{a/2} + Z_b)^2 * (p1*(1-p1) + p0*(1-p0)) / (p1 - p0)^2
3. Round up.

## How to Remember
- **Formula**: "n_per_arm = (Z_a/2 + Z_b)^2 * (p1*(1-p1) + p0*(1-p0)) / (p1 - p0)^2."
- Z_a/2 = 1.96 (5% two-sided), Z_b = 0.84 (80% power).

## Code (Python)
```python
import math

def sample_size(p0, mde_relative, alpha=0.05, power=0.8):
    p1 = p0 * (1 + mde_relative)
    z_alpha, z_beta = 1.96, 0.84
    numerator = (z_alpha + z_beta) ** 2 * (p1 * (1 - p1) + p0 * (1 - p0))
    denominator = (p1 - p0) ** 2
    return math.ceil(numerator / denominator)
```

## Common Mistakes
- Using one-sided Z_a (should be Z_{a/2} for two-sided).
- Forgetting power = 0.8 by default.
- Using p0 alone (not pooled).

## AI Use Cases
- Experiment planning (Meta's PlanOut).
- Power analysis for ML A/B tests.
- Cheap vs. expensive treatments tradeoff.
