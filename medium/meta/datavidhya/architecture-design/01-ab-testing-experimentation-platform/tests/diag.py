"""Diagnostic for KILL/SHIP recommendation tests."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

import numpy as np
from stats_engine import welch_ttest, msprt_pvalue, always_valid_ci
from peeking_protection import PeekSafeEngine

rng = np.random.default_rng(1)
c = rng.normal(0.5, 0.05, 1000)
t = rng.normal(-0.5, 0.05, 1000)
print("Welch:", welch_ttest(c, t))
print("mSPRT:", msprt_pvalue(c, t))
print("CI:", always_valid_ci(c, t, alpha=0.05))

engine = PeekSafeEngine(target_alpha=0.05, max_days=3)
r = engine.update(3, c, t)
print("Result:", r)
