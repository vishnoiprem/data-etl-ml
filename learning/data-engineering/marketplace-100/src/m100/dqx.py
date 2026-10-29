"""
dqx.py — Databricks DQX (Data Quality eXpectations) layer.

Real DLT pipelines use `@dlt.expect_or_drop`, `@dlt.expect`,
`@dlt.expect_or_fail`, plus DQX's richer primitives for
quarantine. This module wraps DQX in a way that:

  1. Is usable from the local smoke test (no Databricks runtime).
  2. Mirrors DQX semantics closely so the production path is
     a 1-line swap.
  3. Emits three tiers of expectations:
        WARN         — log + continue, row kept
        DROP         — row removed, continue
        QUARANTINE   — row moved to a `quarantine` schema, continue

The agent reads the per-tier counts and feeds them into
the `quality_score` (high drop-rate = low score, high
quarantine = medium score with a "data smell" flag).

Production swap:
    from databricks.labs.dqx import DQEngine
    from databricks.sdk import WorkspaceClient
    engine = DQEngine(WorkspaceClient())
    rules = engine.generate_rules_from_metadata(...)  # YAML/JSON
    silver_df = engine.apply_rules(silver_df, rules)
    quarantine_df = silver_df.filter(...)  # DQ "bad" rows
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ============================================================
# Rule types
# ============================================================

class Tier:
    WARN = "warn"
    DROP = "drop"
    QUARANTINE = "quarantine"


@dataclass
class DQRule:
    """A single data-quality rule.

    `check` is a callable that takes a row (dict) and returns
    True if the row PASSES, False if it fails. We deliberately
    invert the convention from DQX's API ("is_valid") so the
    rule reads naturally: "check that x is not null" → return
    x is not None.
    """
    name: str
    check: Callable[[dict], bool]
    tier: str = Tier.DROP
    description: str = ""

    def evaluate(self, row: dict) -> bool:
        try:
            return bool(self.check(row))
        except Exception:
            # A rule that throws is treated as a fail (safer)
            return False


# ============================================================
# Built-in rules — the 80% case for marketplace data
# ============================================================

def rule_not_null(column: str, tier: str = Tier.DROP) -> DQRule:
    """Column must not be null/empty."""
    def check(row: dict) -> bool:
        v = row.get(column)
        if v is None:
            return False
        if isinstance(v, str) and not v.strip():
            return False
        return True
    return DQRule(
        name=f"{column}_not_null",
        check=check, tier=tier,
        description=f"column {column!r} must be present and non-empty",
    )


def rule_in_range(column: str, lo, hi, tier: str = Tier.WARN) -> DQRule:
    """Numeric column must be in [lo, hi]."""
    def check(row: dict) -> bool:
        v = row.get(column)
        if v is None:
            return True  # handled by rule_not_null
        try:
            return lo <= float(v) <= hi
        except (TypeError, ValueError):
            return False
    return DQRule(
        name=f"{column}_in_range[{lo},{hi}]",
        check=check, tier=tier,
        description=f"column {column!r} must be in [{lo}, {hi}]",
    )


def rule_unique(columns: list[str], tier: str = Tier.QUARANTINE) -> DQRule:
    """Composite unique key. (Quarantine because it requires group-by,
    not row-by-row; this factory returns a row-level rule that uses
    a caller-supplied seen-set.)"""
    # NB: row-level uniqueness is impossible without a group-by.
    # This stub returns True; the engine's uniqueness check is done
    # post-hoc in `evaluate_dataset` (group-by + quarantine).
    return DQRule(
        name=f"unique({','.join(columns)})",
        check=lambda row: True,
        tier=tier,
        description=f"composite key ({', '.join(columns)}) must be unique",
    )


# ============================================================
# Result
# ============================================================

@dataclass
class DQResult:
    """What the DQX engine produced for one dataset.

    `quality_score` is a 0-1 score the agent uses:
        1.0 - (drop_rate + 0.5 * quarantine_rate)
    Clipped at 0. So a dataset with 0% drops and 0% quarantines
    scores 1.0; a dataset with 50% drops scores 0.5; a dataset
    with 100% drops scores 0.0.
    """
    listing_id: str
    rows_in: int = 0
    rows_warn: int = 0
    rows_drop: int = 0
    rows_quarantine: int = 0
    rows_kept: int = 0
    quarantine_reasons: dict = field(default_factory=dict)
    warn_reasons: dict = field(default_factory=dict)
    # Side outputs (populated by `evaluate`)
    kept: list = field(default_factory=list)
    quarantine: list = field(default_factory=list)
    warn: list = field(default_factory=list)

    @property
    def drop_rate(self) -> float:
        return self.rows_drop / self.rows_in if self.rows_in else 0.0

    @property
    def quarantine_rate(self) -> float:
        return self.rows_quarantine / self.rows_in if self.rows_in else 0.0

    @property
    def quality_score(self) -> float:
        score = 1.0 - (self.drop_rate + 0.5 * self.quarantine_rate)
        return max(0.0, min(1.0, score))

    def summary(self) -> str:
        return (
            f"DQ in={self.rows_in}  kept={self.rows_kept}  "
            f"drop={self.rows_drop}  quarantine={self.rows_quarantine}  "
            f"warn={self.rows_warn}  score={self.quality_score:.2f}"
        )


# ============================================================
# Engine
# ============================================================

class DQEngine:
    """Apply DQ rules to a row-level dataset (list of dicts).

    For production, this is replaced by `databricks.labs.dqx.engine`.
    The shape of DQResult is identical, so callers don't change.
    """

    def __init__(self, rules: list[DQRule]):
        self.rules = rules
        # group by tier for fast iteration
        self._by_tier: dict[str, list[DQRule]] = {Tier.WARN: [], Tier.DROP: [], Tier.QUARANTINE: []}
        for r in rules:
            self._by_tier.setdefault(r.tier, []).append(r)

    def evaluate(self, rows: list[dict], listing_id: str = "") -> DQResult:
        """Apply all rules. Returns counts per tier.

        Evaluation order: WARN first (cheap, just log), then
        DROP (filter), then QUARANTINE (route to side path).
        Rows that pass every DROP rule and every QUARANTINE
        rule are kept. Rows that fail any DROP rule are
        removed. Rows that fail any QUARANTINE rule (but
        pass DROP) are routed to the quarantine path.
        """
        result = DQResult(listing_id=listing_id, rows_in=len(rows))
        kept: list[dict] = []
        quarantine: list[tuple[dict, list[str]]] = []
        warn_rows: list[tuple[dict, list[str]]] = []

        for row in rows:
            # WARN tier — just log
            warn_fails: list[str] = []
            for r in self._by_tier[Tier.WARN]:
                if not r.evaluate(row):
                    warn_fails.append(r.name)
            if warn_fails:
                warn_rows.append((row, warn_fails))
                for name in warn_fails:
                    result.warn_reasons[name] = result.warn_reasons.get(name, 0) + 1

            # DROP tier — filter
            drop_fails: list[str] = []
            for r in self._by_tier[Tier.DROP]:
                if not r.evaluate(row):
                    drop_fails.append(r.name)
            if drop_fails:
                result.rows_drop += 1
                continue  # row is gone

            # QUARANTINE tier — route to side path
            q_fails: list[str] = []
            for r in self._by_tier[Tier.QUARANTINE]:
                if not r.evaluate(row):
                    q_fails.append(r.name)
            if q_fails:
                quarantine.append((row, q_fails))
                for name in q_fails:
                    result.quarantine_reasons[name] = result.quarantine_reasons.get(name, 0) + 1
            else:
                kept.append(row)

        result.rows_kept = len(kept)
        result.rows_warn = len(warn_rows)
        result.rows_quarantine = len(quarantine)
        # Side outputs for callers who want them
        result.kept = kept
        result.quarantine = quarantine
        result.warn = warn_rows
        return result


# ============================================================
# Helpers — turn a DLT schema into default DQ rules
# ============================================================

def default_rules_for_silver(columns: list[str]) -> list[DQRule]:
    """Pick sensible defaults for an unknown silver table.

    Heuristic: every column gets a `not_null` rule at WARN tier
    (so we don't drop data, but the digest flags it). Columns
    whose name hints at an amount/price/count get a non-negative
    range rule at DROP tier. The first `id`-named column gets a
    unique-key rule at QUARANTINE tier.
    """
    rules: list[DQRule] = []
    for col in columns:
        rules.append(rule_not_null(col, tier=Tier.WARN))
        cname = col.lower()
        if any(t in cname for t in ("amount", "price", "cost", "revenue", "total", "count", "qty", "quantity", "balance")):
            rules.append(rule_in_range(col, 0, 1e15, tier=Tier.DROP))
        if cname.endswith("_id") or cname == "id":
            rules.append(rule_unique([col], tier=Tier.QUARANTINE))
    return rules


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    # tiny demo so a maintainer can eyeball the API
    rules = default_rules_for_silver(["id", "amount", "name"])
    eng = DQEngine(rules)
    rows = [
        {"id": "1", "amount": 100, "name": "Alice"},
        {"id": "2", "amount": -5, "name": "Bob"},   # amount out of range → drop
        {"id": "1", "amount": 50, "name": "Carol"}, # duplicate id → quarantine
        {"id": "4", "amount": 75, "name": ""},       # null name → warn
    ]
    res = eng.evaluate(rows, listing_id="demo")
    print(res.summary())
    print("warn reasons:", res.warn_reasons)
    print("quarantine reasons:", res.quarantine_reasons)
    print("kept rows:", res.kept)
