"""Bayesian A/B testing for prompt experiments.

Beta-binomial model: each variant has a Beta prior over its success rate.
After observing successes/failures, the posterior is Beta(α + s, β + f).
We compute P(B > A) by Monte Carlo sampling from each posterior — no SciPy.

This is robust to peeking, small samples, and continuous monitoring, which
matters for prompt experiments where a/b cohorts are usually slow to fill.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Variant:
    name: str
    successes: int = 0
    failures: int = 0

    def record(self, success: bool):
        if success:
            self.successes += 1
        else:
            self.failures += 1

    @property
    def n(self) -> int:
        return self.successes + self.failures

    @property
    def rate(self) -> float:
        return self.successes / self.n if self.n else 0.0


@dataclass
class BayesianAB:
    a: Variant
    b: Variant
    alpha_prior: float = 1.0   # Beta(1, 1) = Uniform = no prior info
    beta_prior: float = 1.0
    n_samples: int = 20_000

    def posterior_prob_b_better(self, seed: int = 0) -> float:
        rng = np.random.default_rng(seed)
        a_post = rng.beta(self.alpha_prior + self.a.successes,
                          self.beta_prior + self.a.failures, size=self.n_samples)
        b_post = rng.beta(self.alpha_prior + self.b.successes,
                          self.beta_prior + self.b.failures, size=self.n_samples)
        return float(np.mean(b_post > a_post))

    def credible_interval(self, variant: Variant, alpha: float = 0.05, seed: int = 0) -> tuple[float, float]:
        rng = np.random.default_rng(seed)
        post = rng.beta(self.alpha_prior + variant.successes,
                        self.beta_prior + variant.failures, size=self.n_samples)
        return float(np.percentile(post, 100 * alpha / 2)), float(np.percentile(post, 100 * (1 - alpha / 2)))

    def decide(self, threshold: float = 0.95, seed: int = 0) -> str:
        p = self.posterior_prob_b_better(seed=seed)
        if p >= threshold:
            return "ship_b"
        if p <= 1.0 - threshold:
            return "keep_a"
        return "continue"
