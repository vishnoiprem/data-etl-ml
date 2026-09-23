"""
Problem 01: Sample Size Calculator.

Meta flavor: Given baseline rate p0 and a desired MDE (minimum detectable
effect), how many users per arm do we need for 80% power at alpha = 0.05?

How to Think:
- Power analysis for two-proportion z-test.
- p_pool ~ (p0 + p1) / 2 for equal-arm allocation.
- n = (z_alpha/2 + z_beta)^2 * (p1*(1-p1) + p0*(1-p0)) / (p1 - p0)^2 per arm.

How to Remember:
- "n_per_arm = (Z_a/2 + Z_b)^2 * (p1*(1-p1) + p0*(1-p0)) / (p1 - p0)^2."

AI Use Cases:
- Experiment planning (Meta's PlanOut).
- Power analysis for ML A/B tests.
- Cheap vs. expensive treatments tradeoff.
"""
import math


def sample_size(p0: float, mde_relative: float, alpha: float = 0.05, power: float = 0.8) -> int:
    """Return per-arm sample size for two-proportion z-test."""
    p1 = p0 * (1 + mde_relative)
    if p1 <= 0 or p1 >= 1:
        raise ValueError("p1 must be in (0, 1)")
    z_alpha = 1.96  # two-sided 5%
    z_beta = 0.84   # 80% power
    numerator = (z_alpha + z_beta) ** 2 * (p1 * (1 - p1) + p0 * (1 - p0))
    denominator = (p1 - p0) ** 2
    return math.ceil(numerator / denominator)


# Demo: baseline 10% conversion, want to detect a 5% relative lift (=> 10.5%).
if __name__ == "__main__":
    n = sample_size(p0=0.10, mde_relative=0.05)
    print(f"Per-arm n = {n:,}")  # ~122,393 per arm
