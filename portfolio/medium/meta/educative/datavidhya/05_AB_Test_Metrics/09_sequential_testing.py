"""
Problem 09: Sequential Testing / Always-Valid p-Values.

Meta flavor: PM wants to peek at the dashboard daily without inflating Type I
error. Use mSPRT or always-valid confidence sequences.

How to Think:
- Standard fixed-horizon z-test inflates false positives if you peek.
- Always-valid p-values use mixture-of-normals to bound Type I error at all t.
- At final decision time, behaves like a standard p-value.

How to Remember:
- "Always-valid p = p_fixed * mixture(0, t^2)."

AI Use Cases:
- Continuous monitoring of live experiments.
- Auto-stop experiments when significance is reached.
- Real-time dashboards.
"""
import math


def always_valid_p(z: float, t_fraction: float) -> float:
    """
    mSPRT-style always-valid p-value approximation.
    z is the current z-statistic; t_fraction in (0, 1] is fraction of planned sample size.
    """
    # Mixture factor: alpha_eff = alpha * sqrt(t_fraction)
    # Always-valid p ≈ p_fixed / sqrt(t_fraction)
    from math import erf, sqrt
    p_fixed = 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))
    if t_fraction <= 0 or t_fraction > 1:
        return p_fixed
    return min(1.0, p_fixed / math.sqrt(t_fraction))


if __name__ == "__main__":
    # Same z=2.0 at different fractions of the planned sample
    for t in [0.25, 0.5, 1.0]:
        p = always_valid_p(2.0, t)
        print(f"t={t:.2f}  p={p:.4f}")
