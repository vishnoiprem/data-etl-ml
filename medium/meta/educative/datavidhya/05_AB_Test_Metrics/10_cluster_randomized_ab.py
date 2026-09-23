"""
Problem 10: Cluster-Randomized A/B (Geo-Based).

Meta flavor: When user-level randomization is impossible (network effects),
randomize by region or geo.

How to Think:
- Treatment unit = cluster (e.g., region).
- Sample size formula uses design effect = 1 + (m-1)*ICC.
- m = avg cluster size; ICC = intracluster correlation.
- Effective n = n_total / design_effect.

How to Remember:
- "Effective n = n_total / (1 + (m-1)*ICC)."

AI Use Cases:
- Network-effect experiments (Reels, Groups).
- Marketplace supply/demand tests.
- Policy interventions at scale.
"""
import math


def effective_n(n_total: int, m: float, icc: float) -> float:
    """Effective sample size after design-effect adjustment."""
    design_effect = 1 + (m - 1) * icc
    return n_total / design_effect if design_effect > 0 else n_total


def cluster_sample_size(p0: float, mde: float, m: float, icc: float, alpha: float = 0.05, power: float = 0.8) -> int:
    p1 = p0 * (1 + mde)
    z_alpha, z_beta = 1.96, 0.84
    n_indiv = math.ceil(
        (z_alpha + z_beta) ** 2 * (p1 * (1 - p1) + p0 * (1 - p0)) / (p1 - p0) ** 2
    )
    n_clusters = math.ceil(effective_n(n_indiv * 2, m, icc) / m)
    return n_clusters


if __name__ == "__main__":
    # baseline 10%, 5% MDE, avg cluster m=100, ICC=0.05
    n_clusters = cluster_sample_size(0.10, 0.05, m=100, icc=0.05)
    print(f"Clusters needed = {n_clusters}")
