"""
Deterministic Experiment Assignment.

The single most important property: given (user_id, experiment_id, salt),
the same variant is returned everywhere — across services, languages, time.

We use SHA-256 with a layered salt scheme so:
- A user can be in multiple experiments on different layers
- Experiments within a mutex group do not collide
- The global holdout (layer 0) is independent of product layers

References:
- "Overlapping Experiment Infrastructure" — Tang, Young, Harper et al. (Microsoft)
- "Experimentation at Yelp" — Bottger et al.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import List, Optional


# --------------------------------------------------------------------- #
# Hash primitives
# --------------------------------------------------------------------- #

def _stable_hash(user_id: str, experiment_id: str, salt: str) -> int:
    """SHA-256 based deterministic hash → integer in [0, 10_000)."""
    payload = f"{user_id}:{experiment_id}:{salt}".encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    # take first 8 hex chars (32 bits) → int
    return int(digest[:8], 16) % 10_000


# --------------------------------------------------------------------- #
# Domain objects
# --------------------------------------------------------------------- #

@dataclass(frozen=True)
class Variant:
    variant_id: str
    name: str
    allocation: float  # 0..1, sum of all variants <= 1


@dataclass(frozen=True)
class Experiment:
    experiment_id: str
    layer: str
    traffic_allocation: float
    variants: List[Variant]
    mutex_group: Optional[str] = None

    def __post_init__(self):
        total = sum(v.allocation for v in self.variants)
        if total > 1.0 + 1e-9:
            raise ValueError(f"variant allocations sum to {total} > 1.0")
        if not 0.0 <= self.traffic_allocation <= 1.0:
            raise ValueError("traffic_allocation must be in [0,1]")


@dataclass(frozen=True)
class Assignment:
    user_id: str
    experiment_id: str
    variant_id: Optional[str]  # None => user not in experiment
    layer: str
    bucket: int


# --------------------------------------------------------------------- #
# Layered bucketing — global holdout, mutex groups, traffic allocation
# --------------------------------------------------------------------- #

LAYER_SALTS = {
    "layer_0_holdout": "holdout-salt-v1",
    "layer_1_feed":    "feed-salt-v1",
    "layer_2_ranking": "rank-salt-v1",
    "layer_3_product": "product-salt-v1",
    "layer_4_lifecycle": "lifecycle-salt-v1",
}

GLOBAL_HOLDOUT_ALLOCATION = 0.05  # 5% persistent holdout


def is_in_global_holdout(user_id: str) -> bool:
    bucket = _stable_hash(user_id, "global_holdout", LAYER_SALTS["layer_0_holdout"])
    return bucket < GLOBAL_HOLDOUT_ALLOCATION * 10_000


def assign(user_id: str, experiment: Experiment) -> Assignment:
    """Return the user's variant for an experiment. None means not enrolled."""

    layer_salt = LAYER_SALTS.get(experiment.layer, f"custom-{experiment.layer}")

    # 1. Eligibility check: traffic_allocation
    bucket = _stable_hash(user_id, experiment.experiment_id, layer_salt)
    if bucket >= experiment.traffic_allocation * 10_000:
        return Assignment(user_id, experiment.experiment_id, None,
                          experiment.layer, bucket)

    # 2. Variant selection: another hash on a different salt namespace
    var_bucket = _stable_hash(
        user_id, experiment.experiment_id, f"{layer_salt}-variant"
    )
    var_pct = var_bucket / 10_000.0

    cumulative = 0.0
    for variant in experiment.variants:
        cumulative += variant.allocation
        if var_pct < cumulative:
            return Assignment(user_id, experiment.experiment_id, variant.variant_id,
                              experiment.layer, bucket)

    # Numerical edge case (var_pct == 1.0)
    return Assignment(user_id, experiment.experiment_id,
                      experiment.variants[-1].variant_id,
                      experiment.layer, bucket)


# --------------------------------------------------------------------- #
# Helper: assign user to many experiments at once
# --------------------------------------------------------------------- #

def assign_many(user_id: str, experiments: List[Experiment]) -> List[Assignment]:
    """
    Assign a user to all experiments respecting:
    - Global holdout (no experiments if user is in holdout)
    - Mutex groups (only one experiment per mutex group per user)
    """
    if is_in_global_holdout(user_id):
        return []

    chosen_mutex_groups: set[str] = set()
    results: List[Assignment] = []

    # Sort by priority so mutex conflicts resolve deterministically
    sorted_exps = sorted(experiments, key=lambda e: e.experiment_id)

    for exp in sorted_exps:
        if exp.mutex_group and exp.mutex_group in chosen_mutex_groups:
            continue
        a = assign(user_id, exp)
        if a.variant_id is not None:
            results.append(a)
            if exp.mutex_group:
                chosen_mutex_groups.add(exp.mutex_group)

    return results


# --------------------------------------------------------------------- #
# Sample data generation for testing
# --------------------------------------------------------------------- #

def generate_sample() -> dict:
    return {
        "experiments": [
            {
                "experiment_id": "exp_feed_rank_v2",
                "layer": "layer_2_ranking",
                "traffic_allocation": 0.8,
                "mutex_group": "feed_ranking",
                "variants": [
                    {"variant_id": "control", "name": "Control", "allocation": 0.5},
                    {"variant_id": "v1",      "name": "NewRanker", "allocation": 0.5},
                ],
            },
            {
                "experiment_id": "exp_home_redesign",
                "layer": "layer_3_product",
                "traffic_allocation": 0.5,
                "mutex_group": None,
                "variants": [
                    {"variant_id": "control", "name": "Old Home", "allocation": 0.34},
                    {"variant_id": "v1",      "name": "New Home A", "allocation": 0.33},
                    {"variant_id": "v2",      "name": "New Home B", "allocation": 0.33},
                ],
            },
        ]
    }


if __name__ == "__main__":
    sample = generate_sample()
    print(json.dumps(sample, indent=2))

    # Quick sanity: 100k assignments should distribute ~ 50/50
    from collections import Counter
    exp = Experiment(
        experiment_id="test_exp",
        layer="layer_1_feed",
        traffic_allocation=1.0,
        variants=[Variant("control", "C", 0.5), Variant("v1", "V1", 0.5)],
    )
    counts = Counter()
    for i in range(100_000):
        a = assign(f"user_{i}", exp)
        counts[a.variant_id] += 1
    print("variant distribution:", counts)
