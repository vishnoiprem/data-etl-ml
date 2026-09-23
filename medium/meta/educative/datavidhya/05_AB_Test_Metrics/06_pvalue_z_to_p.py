"""
Problem 06: Convert z/t statistic to p-value.

Meta flavor: Many SQL pipelines emit just the z-score; downstream
visualizations convert to p-value.

How to Think:
- Use the normal CDF: Phi(z) = 0.5 * (1 + erf(z / sqrt(2))).
- Two-sided p = 2 * (1 - Phi(|z|)).

How to Remember:
- "p_two_sided = 2 * (1 - Phi(|z|))."

AI Use Cases:
- Statistical reporting dashboards.
- Bonferroni / BH correction downstream.
"""
import math


def z_to_p_two_sided(z: float) -> float:
    return 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))


if __name__ == "__main__":
    for z in [1.0, 1.96, 2.58, 3.0]:
        print(f"z={z:>5}  p={z_to_p_two_sided(z):.4f}")
