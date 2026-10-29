# Cluster-Randomized A/B (Geo-Based)

## Problem
Design an A/B test with cluster-level randomization (e.g., by region) to handle network effects.

## How to Think
1. Effective n = n_total / design_effect.
2. Design effect = 1 + (m - 1) * ICC.
3. m = avg users per cluster; ICC = intracluster correlation.
4. Pick cluster size to balance power and operational cost.

## How to Remember
- **Formula**: "n_effective = n_total / (1 + (m-1)*ICC)."
- ICC estimated from prior experiments in the same product.

## Code (Python)
```python
def effective_n(n_total, m, icc):
    return n_total / (1 + (m - 1) * icc)
```

## Common Mistakes
- Ignoring ICC entirely — overstates power.
- Cluster sizes too small — variance inflates.

## AI Use Cases
- Network-effect experiments (Reels, Groups).
- Marketplace supply/demand tests.
- Policy interventions at scale.
