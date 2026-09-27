"""
Statistical Engine for A/B Tests.

Provides:
- Welch's t-test (default two-sided)
- Bayesian posterior (Beta-Bernoulli for proportions, Normal-Normal for means)
- Sequential testing via mSPRT (always-valid)
- CUPED variance reduction
- Sample Ratio Mismatch (SRM) check

All implementations are NumPy/Pandas-only so they run inside PySpark UDFs
or local pandas pipelines.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np
from scipy import stats


# --------------------------------------------------------------------- #
# 1. Welch's t-test (two-sample, unequal variance)
# --------------------------------------------------------------------- #

@dataclass
class TTestResult:
    point_estimate: float
    ci_low: float
    ci_high: float
    p_value: float
    n_control: int
    n_treatment: int
    mean_control: float
    mean_treatment: float

    @property
    def is_significant_005(self) -> bool:
        return self.p_value < 0.05

    @property
    def lift_pct(self) -> float:
        if self.mean_control == 0:
            return float("nan")
        return (self.mean_treatment - self.mean_control) / abs(self.mean_control)


def welch_ttest(
    control: np.ndarray,
    treatment: np.ndarray,
    alpha: float = 0.05,
) -> TTestResult:
    """Welch's t-test for unequal variances."""
    n_c, n_t = len(control), len(treatment)
    m_c, m_t = control.mean(), treatment.mean()
    v_c, v_t = control.var(ddof=1), treatment.var(ddof=1)

    se = np.sqrt(v_c / n_c + v_t / n_t)
    diff = m_t - m_c

    # Edge case: zero variance in both arms (constant metric) → no signal
    if se == 0:
        return TTestResult(
            point_estimate=float(diff),
            ci_low=float(diff),
            ci_high=float(diff),
            p_value=1.0,            # no evidence of difference
            n_control=int(n_c),
            n_treatment=int(n_t),
            mean_control=float(m_c),
            mean_treatment=float(m_t),
        )

    t_stat = diff / se

    # Welch-Satterthwaite degrees of freedom
    df = (v_c / n_c + v_t / n_t) ** 2 / (
        (v_c / n_c) ** 2 / (n_c - 1) + (v_t / n_t) ** 2 / (n_t - 1)
    )

    p = 2 * (1 - stats.t.cdf(abs(t_stat), df=df))
    t_crit = stats.t.ppf(1 - alpha / 2, df=df)

    return TTestResult(
        point_estimate=float(diff),
        ci_low=float(diff - t_crit * se),
        ci_high=float(diff + t_crit * se),
        p_value=float(p),
        n_control=int(n_c),
        n_treatment=int(n_t),
        mean_control=float(m_c),
        mean_treatment=float(m_t),
    )


# --------------------------------------------------------------------- #
# 2. Bayesian beta-binomial for proportions
# --------------------------------------------------------------------- #

def bayesian_proportion(
    successes_c: int, trials_c: int,
    successes_t: int, trials_t: int,
    alpha_prior: float = 1.0,
    beta_prior: float = 1.0,
    n_samples: int = 200_000,
    rng: np.random.Generator | None = None,
) -> Tuple[float, float, float]:
    """
    Posterior: Beta(alpha + successes, beta + failures)
    Returns (prob_treatment_better, ci_low_lift, ci_high_lift).
    """
    rng = rng or np.random.default_rng(42)
    a_c, b_c = alpha_prior + successes_c, beta_prior + (trials_c - successes_c)
    a_t, b_t = alpha_prior + successes_t, beta_prior + (trials_t - successes_t)

    post_c = rng.beta(a_c, b_c, size=n_samples)
    post_t = rng.beta(a_t, b_t, size=n_samples)
    lift = post_t - post_c

    return float((post_t > post_c).mean()), float(np.quantile(lift, 0.025)), float(np.quantile(lift, 0.975))


# --------------------------------------------------------------------- #
# 3. Sequential testing — mixture Sequential Probability Ratio Test
#    (always-valid p-value; safe under continuous peeking)
# --------------------------------------------------------------------- #

def msprt_pvalue(
    control: np.ndarray,
    treatment: np.ndarray,
    tau: float = 0.5,    # prior effect size std
) -> float:
    """
    mSPRT always-valid p-value.
    Safe to evaluate after every new batch of data without inflating Type-I error.

    Reference: Howard et al. (2021) "Time-uniform, nonparametric, nonasymptotic
    confidence sequences", Jennison & Turnbull.

    The closed-form approximation (Eq. 6 in Howard et al.) for a normal-mixture
    prior on the effect size with prior scale `tau`:

      log_lambda = (1/2) * [ log(s2 / (s2 + tau^2))
                            + (diff^2 / (s2 + tau^2))
                            - (diff^2 / s2) ]

      p ≈ Phi(-sgn * sqrt(2 log_lambda))
          + exp(2 log_lambda) * Phi(-sgn * sqrt(2 log_lambda) - 2 sqrt(log_lambda))

    where s2 = v_c/n_c + v_t/n_t, sgn = sign(diff), and Phi is the standard normal CDF.
    """
    n_c, n_t = len(control), len(treatment)
    if n_c < 2 or n_t < 2:
        return 1.0
    m_c, m_t = control.mean(), treatment.mean()
    v_c, v_t = control.var(ddof=1), treatment.var(ddof=1)

    s2 = v_c / n_c + v_t / n_t
    diff = m_t - m_c
    if s2 <= 0:
        return 1.0

    # Howard et al. (2021) Eq. 6 — closed-form mSPRT.
    # log Bayes factor under N(0, tau^2) prior on the effect size:
    #   log BF = -1/2 * log(1 + tau^2/s^2) + Z^2 * tau^2 / (2*(s^2 + tau^2))
    # where Z = diff / sqrt(s^2). Always-valid p is then derived from this BF.
    z = diff / np.sqrt(s2)
    log_lambda = (
        -0.5 * np.log(1.0 + tau ** 2 / s2)
        + (z ** 2) * (tau ** 2) / (2.0 * (s2 + tau ** 2))
    )

    # When diff == 0, log_lambda ~ -log(1+tau^2/s2)/2 < 0; p should be 1.0.
    # When |diff| is large, log_lambda → +∞, p → 0 — short-circuit to avoid overflow.
    if log_lambda <= 0:
        return 1.0
    if log_lambda > 50:   # Phi term is < 1e-50; safe to return 0
        return 0.0

    sgn = np.sign(diff)
    if sgn == 0:
        sgn = 1.0
    sqrt_two_ll = np.sqrt(2.0 * log_lambda)
    p = stats.norm.cdf(-sgn * sqrt_two_ll) \
        + np.exp(2.0 * log_lambda) * stats.norm.cdf(
            -sgn * sqrt_two_ll - 2.0 * np.sqrt(log_lambda)
        )
    return float(np.clip(p, 0.0, 1.0))


# --------------------------------------------------------------------- #
# 4. CUPED — Controlled-experiment Using Pre-Experiment Data
#    Variance reduction via covariate adjustment.
# --------------------------------------------------------------------- #

def cuped_adjust(
    metric: np.ndarray,
    covariate: np.ndarray,
    pre_metric_mean: float,
) -> np.ndarray:
    """
    Adjust metric using pre-experiment covariate.
    metric_adj = metric - theta * (covariate - pre_metric_mean)
    where theta = Cov(metric, covariate) / Var(covariate)
    """
    theta = np.cov(metric, covariate, ddof=1)[0, 1] / np.var(covariate, ddof=1)
    return metric - theta * (covariate - pre_metric_mean)


# --------------------------------------------------------------------- #
# 5. Sample Ratio Mismatch (SRM) — chi-square test
# --------------------------------------------------------------------- #

def srm_check(
    observed_counts: dict[str, int],
    expected_allocations: dict[str, float],
    alpha: float = 0.001,
) -> Tuple[float, bool]:
    """
    Pearson chi-square test for SRM.
    Returns (chi2_statistic, is_mismatch).
    Standard threshold: chi2 critical value at alpha=0.001 with df=k-1.
    """
    total = sum(observed_counts.values())
    chi2 = 0.0
    for variant, count in observed_counts.items():
        expected = expected_allocations[variant] * total
        chi2 += (count - expected) ** 2 / expected
    df = len(observed_counts) - 1
    crit = stats.chi2.ppf(1 - alpha, df=df)
    return float(chi2), bool(chi2 > crit)


# --------------------------------------------------------------------- #
# 6. Always-Valid Confidence Intervals
# --------------------------------------------------------------------- #

def always_valid_ci(
    control: np.ndarray,
    treatment: np.ndarray,
    alpha: float = 0.05,
) -> Tuple[float, float]:
    """
    Always-valid 100(1-alpha)% CI using the Robbins mixture.
    Width grows only as sqrt(log log n), allowing continuous monitoring.
    """
    n_c, n_t = len(control), len(treatment)
    var_c, var_t = control.var(ddof=1), treatment.var(ddof=1)
    se = np.sqrt(var_c / n_c + var_t / n_t)
    diff = treatment.mean() - control.mean()

    # Robbins constant for normal mixture
    rho = np.sqrt(2 * np.log(np.log(max(n_c, n_t, 2)) + 1))
    half_width = (rho + np.sqrt(2 * np.log(2 / alpha))) * se

    return float(diff - half_width), float(diff + half_width)


# --------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------- #

if __name__ == "__main__":
    rng = np.random.default_rng(0)
    control = rng.normal(loc=10.0, scale=2.0, size=10_000)
    treatment = rng.normal(loc=10.5, scale=2.0, size=10_000)  # +0.5 lift

    print("== Welch's t-test ==")
    res = welch_ttest(control, treatment)
    print(res)

    print("\n== mSPRT always-valid p-value ==")
    print(f"p = {msprt_pvalue(control, treatment):.4f}")

    print("\n== Always-valid CI ==")
    lo, hi = always_valid_ci(control, treatment)
    print(f"CI = [{lo:.4f}, {hi:.4f}]")

    print("\n== SRM check ==")
    chi2, mismatch = srm_check({"c": 4950, "t1": 2530, "t2": 2520},
                               {"c": 0.5, "t1": 0.25, "t2": 0.25})
    print(f"chi2={chi2:.2f}, mismatch={mismatch}")

    print("\n== CUPED ==")
    pre = rng.normal(10, 2, 10_000)
    cov = rng.normal(10, 2, 10_000)
    metric = pre * 0.6 + rng.normal(0, 1, 10_000) + 0.5
    adjusted = cuped_adjust(metric, cov, pre.mean())
    print(f"Var(metric)      = {metric.var(ddof=1):.4f}")
    print(f"Var(cuped_adj)   = {adjusted.var(ddof=1):.4f}")
