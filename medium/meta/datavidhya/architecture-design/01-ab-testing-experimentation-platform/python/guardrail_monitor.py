"""
Streaming Guardrail Monitor.

Hourly job that:
  1. Reads last hour of guardrail events per experiment variant
  2. Compares treatment vs control using Welch's t-test
  3. If breach → emit alert + auto-pause webhook

Guardrail examples:
  - crash_rate     (count_crashes / count_sessions)
  - p99_latency_ms (quantile)
  - revenue_per_user
  - dau_drop_pct
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import numpy as np
from stats_engine import welch_ttest


@dataclass
class GuardrailRule:
    metric_id: str
    direction: str                # 'INCREASE_IS_BAD' or 'DECREASE_IS_BAD'
    threshold_pct: float          # e.g. 0.05 = 5% regression triggers
    min_sample: int = 1000
    severity: str = "CRITICAL"    # WARN | CRITICAL
    auto_action: str = "PAUSE"    # NONE | PAUSE | ROLLBACK


@dataclass
class GuardrailAlert:
    experiment_id: str
    variant_id: str
    rule: GuardrailRule
    observed_lift_pct: float
    p_value: float
    triggered_ts: float = field(default_factory=time.time)


class GuardrailMonitor:
    """
    State is held per (experiment, variant). Each tick:
      - aggregate last hour of metric events
      - run test against control
      - if any rule fires, fire alert and optionally auto-pause
    """

    def __init__(
        self,
        rules: List[GuardrailRule],
        on_alert: Optional[Callable[[GuardrailAlert], None]] = None,
        on_auto_pause: Optional[Callable[[str, str], None]] = None,
    ):
        self.rules = rules
        self.on_alert = on_alert
        self.on_auto_pause = on_auto_pause

    def evaluate(
        self,
        experiment_id: str,
        control_values: np.ndarray,
        treatment_values_by_variant: Dict[str, np.ndarray],
    ) -> List[GuardrailAlert]:
        alerts: List[GuardrailAlert] = []
        for variant, values in treatment_values_by_variant.items():
            for rule in self.rules:
                if rule.metric_id not in {"crash_rate", "p99_latency_ms",
                                          "revenue_per_user", "dau_drop_pct"}:
                    continue
                if len(values) < rule.min_sample or len(control_values) < rule.min_sample:
                    continue

                # One-sided test depending on direction
                res = welch_ttest(control_values, values)
                lift = res.lift_pct
                bad = (
                    (rule.direction == "INCREASE_IS_BAD" and lift > rule.threshold_pct) or
                    (rule.direction == "DECREASE_IS_BAD" and lift < -rule.threshold_pct)
                )
                if bad and res.p_value < 0.01:
                    alert = GuardrailAlert(
                        experiment_id=experiment_id,
                        variant_id=variant,
                        rule=rule,
                        observed_lift_pct=lift,
                        p_value=res.p_value,
                    )
                    alerts.append(alert)
                    if self.on_alert:
                        self.on_alert(alert)
                    if rule.auto_action == "PAUSE" and self.on_auto_pause:
                        self.on_auto_pause(experiment_id, variant)
        return alerts


# --------------------------------------------------------------------- #
# Default ruleset (a real org would store this in config)
# --------------------------------------------------------------------- #

DEFAULT_RULES = [
    GuardrailRule("crash_rate",     "INCREASE_IS_BAD",  0.10, severity="CRITICAL", auto_action="PAUSE"),
    GuardrailRule("p99_latency_ms", "INCREASE_IS_BAD",  0.05, severity="CRITICAL", auto_action="PAUSE"),
    GuardrailRule("revenue_per_user", "DECREASE_IS_BAD", 0.02, severity="CRITICAL", auto_action="PAUSE"),
    GuardrailRule("dau_drop_pct",   "DECREASE_IS_BAD",  0.01, severity="WARN",    auto_action="NONE"),
]


def alert_handler(alert: GuardrailAlert):
    print(json.dumps({
        "type": "GUARDRAIL_BREACH",
        "experiment_id": alert.experiment_id,
        "variant_id": alert.variant_id,
        "metric": alert.rule.metric_id,
        "lift_pct": alert.observed_lift_pct,
        "p_value": alert.p_value,
        "severity": alert.rule.severity,
        "action": alert.rule.auto_action,
    }, default=str))


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    n = 5_000
    control = rng.normal(100, 10, n)             # 100ms p99
    bad_variant = rng.normal(120, 10, n)         # +20% latency regression

    monitor = GuardrailMonitor(DEFAULT_RULES, on_alert=alert_handler)
    alerts = monitor.evaluate("exp_feed_rank_v2", control, {"v1": bad_variant})

    print(f"\nFired {len(alerts)} alerts")
